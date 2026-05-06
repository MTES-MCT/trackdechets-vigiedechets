import datetime as dt
import logging

import httpx
from celery import chain
from celery.exceptions import MaxRetriesExceededError
from django.conf import settings
from django.utils import timezone

from config.celery_app import app

from .constants import RegistryV2ExportState
from .gql import graphql_generate_registry_export, graphql_read_registry_export
from .models import RegistryV2Export, RegistryV2ExportSiren, RegistryV2ExportSiret

logger = logging.getLogger(__name__)


def get_siret_export(registry_v2_export_pk):
    try:
        return RegistryV2ExportSiret.objects.get(pk=registry_v2_export_pk)
    except RegistryV2ExportSiret.DoesNotExist:
        try:
            return RegistryV2Export.objects.get(pk=registry_v2_export_pk)
        except RegistryV2Export.DoesNotExist:
            return None


def process_export(registry_v2_export_pk):
    """Process export - handles both SIRET and SIREN exports"""
    # Try to get as SIRET export first (backward compatibility)
    try:
        RegistryV2Export.objects.get(pk=registry_v2_export_pk)
        # Existing SIRET export logic
        if getattr(settings, "CELERY_TASK_ALWAYS_EAGER", False):
            generate_registry_export.delay(registry_v2_export_pk)
            return

        task_chain = chain(generate_registry_export.s(registry_v2_export_pk), refresh_registry_export.s())
        task_chain()
        return
    except RegistryV2Export.DoesNotExist:
        pass

    # Try as SIREN export
    try:
        siren_export = RegistryV2ExportSiren.objects.get(pk=registry_v2_export_pk)
        siret_exports = siren_export.siret_exports.all()

        for siret_export in siret_exports:
            if getattr(settings, "CELERY_TASK_ALWAYS_EAGER", False):
                generate_registry_export.delay(siret_export.pk)
            else:
                task_chain = chain(
                    generate_registry_export.s(siret_export.pk),
                    refresh_registry_export.s(),
                    update_siren_export_state.si(registry_v2_export_pk),
                )
                task_chain()

        if getattr(settings, "CELERY_TASK_ALWAYS_EAGER", False):
            update_siren_export_state.delay(registry_v2_export_pk)
        return
    except RegistryV2ExportSiren.DoesNotExist:
        logger.error(f"Export {registry_v2_export_pk} not found")
        raise


MAX__GENERATE_DELAY = dt.timedelta(minutes=15)


@app.task(bind=True)
def generate_registry_export(self, registry_v2_export_pk):
    """Create a registry export on TD api"""
    geo_retry_delay = min(10 * self.request.retries, 300)
    max_retries = getattr(self, "max_retries", 3)  # Default to 3 if not set

    export = get_siret_export(registry_v2_export_pk)
    if not export:
        logger.error(f"Export {registry_v2_export_pk} not found")
        return None

    # Distant export ID already retrieved
    if export.registry_export_id:
        return registry_v2_export_pk

    now = timezone.now()
    if now - export.created_at > MAX__GENERATE_DELAY:
        logger.info("Max delay reached")
        export.mark_as_failed()
        return None

    client = httpx.Client(timeout=60)  # 60 seconds
    variables = export.get_gql_variables()

    try:
        res = client.post(
            url=settings.TD_API_URL,
            headers={"Authorization": f"Bearer {settings.TD_API_TOKEN}"},
            json={
                "query": graphql_generate_registry_export,
                "variables": variables,
            },
        )
    except httpx.RequestError as e:
        logger.info(f"HTTP error: {e}")
        try:
            if self.request.retries >= max_retries:
                logger.error(f"Max retries exceeded for export {registry_v2_export_pk}")
                export.mark_as_failed()
                return None
            raise self.retry(countdown=geo_retry_delay)
        except MaxRetriesExceededError:
            logger.error(f"Max retries exceeded for export {registry_v2_export_pk}")
            export.mark_as_failed()
            return None

    resp = res.json()

    # Check for GraphQL errors
    if resp.get("errors"):
        logger.error(f"GraphQL errors: {resp.get('errors')}")
        try:
            if self.request.retries >= max_retries:
                logger.error(f"Max retries exceeded for export {registry_v2_export_pk}")
                export.mark_as_failed()
                return None
            raise self.retry(countdown=geo_retry_delay)
        except MaxRetriesExceededError:
            logger.error(f"Max retries exceeded for export {registry_v2_export_pk}")
            export.mark_as_failed()
            return None

    # Check if data is None (GraphQL error response)
    if resp.get("data") is None:
        logger.error(f"GraphQL response has no data for export {registry_v2_export_pk}")
        try:
            if self.request.retries >= max_retries:
                logger.error(f"Max retries exceeded for export {registry_v2_export_pk}")
                export.mark_as_failed()
                return None
            raise self.retry(countdown=geo_retry_delay)
        except MaxRetriesExceededError:
            logger.error(f"Max retries exceeded for export {registry_v2_export_pk}")
            export.mark_as_failed()
            return None

    try:
        registry_export_id = resp["data"]["generateRegistryV2ExportAsAdmin "]["id"]
        status = resp["data"]["generateRegistryV2ExportAsAdmin "]["status"]
    except (TypeError, KeyError) as e:
        logger.error(f"Api response error: {e}, response: {resp}")
        try:
            if self.request.retries >= max_retries:
                logger.error(f"Max retries exceeded for export {registry_v2_export_pk}")
                export.mark_as_failed()
                return None
            raise self.retry(countdown=geo_retry_delay)
        except MaxRetriesExceededError:
            logger.error(f"Max retries exceeded for export {registry_v2_export_pk}")
            export.mark_as_failed()
            return None

    export.registry_export_id = registry_export_id
    export.state = status
    export.save()

    return registry_v2_export_pk


MAX__REFRESH_DELAY = dt.timedelta(minutes=15)


@app.task(bind=True, max_retries=None)
def refresh_registry_export(self, registry_v2_export_pk):
    static_retry_delay = 10
    geo_retry_delay = min(10 * self.request.retries, 300)

    export = get_siret_export(registry_v2_export_pk)
    if not export:
        if self.request.retries < 3:
            # retry 2 times with a 1s delay
            raise self.retry(countdown=1)
        # really does not exist, exit
        return None

    if export.state in [
        RegistryV2ExportState.CANCELED,
        RegistryV2ExportState.SUCCESSFUL,
    ]:
        return None

    now = timezone.now()
    if now - export.created_at > MAX__REFRESH_DELAY:
        logger.info("Max delay reached")
        export.mark_as_failed()
        return None

    client = httpx.Client(timeout=10)  # 10 seconds

    try:
        res = client.post(
            url=settings.TD_API_URL,
            headers={"Authorization": f"Bearer {settings.TD_API_TOKEN}"},
            json={
                "query": graphql_read_registry_export,
                "variables": {
                    "id": export.registry_export_id,
                },
            },
        )
    except httpx.RequestError:
        # http error, geometric retry delay
        logger.info("HTTP error")
        raise self.retry(countdown=geo_retry_delay)

    if res.status_code == 200:
        resp = res.json()
        try:
            registry_export_state = resp["data"]["registryV2Export"]["status"]

        except (TypeError, KeyError):
            logger.info("Api error")
            raise self.retry(countdown=static_retry_delay)
        if registry_export_state not in [RegistryV2ExportState.PENDING, RegistryV2ExportState.STARTED]:
            export.state = registry_export_state
            export.save()
            return None
        else:
            # Registry not ready yet, retry after static_retry_delay
            logger.info("registry not ready")
            raise self.retry(countdown=static_retry_delay)

    else:
        # Api error, geometric retry delay
        logger.info("Api error")
        raise self.retry(countdown=geo_retry_delay)


@app.task
def update_siren_export_state(registry_v2_export_siren_pk):
    """Update parent SIREN export state based on children"""
    siren_export = RegistryV2ExportSiren.objects.get(pk=registry_v2_export_siren_pk)
    siren_export.update_aggregated_state()

    # If not all completed, schedule another check
    if siren_export.state in [RegistryV2ExportState.PENDING, RegistryV2ExportState.STARTED]:
        update_siren_export_state.apply_async(args=[registry_v2_export_siren_pk], countdown=10)
