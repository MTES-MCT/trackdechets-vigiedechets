import logging
import os
from urllib.parse import quote

import requests
from django.conf import settings
from django.http import HttpResponse, StreamingHttpResponse
from django.urls import reverse
from django.views import View
from django.views.generic import TemplateView

from common.mixins import FullyLoggedMixin
from accounts.constants import PERMS_DASHBOARD
from common.constants import SSHTarget
from common.ssh import ssh_tunnel, get_tunnel_port
from .metabase import generate_metabase_token

logger = logging.getLogger(__name__)


def _sanitize_path(path: str) -> str:
    """Sanitize user-provided path to prevent SSRF/injection attacks."""
    # Strip leading slashes to prevent //evil.com attacks
    normalized_path = path.lstrip("/")
    # Remove path traversal attempts
    normalized_path = normalized_path.replace("../", "").replace("..\\", "")
    # URL-encode to prevent breaking out into query/fragment components
    return quote(normalized_path, safe="/")


# Allowed static asset extensions for MetabaseStaticProxyView
ALLOWED_STATIC_EXTENSIONS = {
    ".js",
    ".css",
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".svg",
    ".ico",
    ".woff",
    ".woff2",
    ".ttf",
    ".eot",
    ".map",
}

# Headers that should not be forwarded from the proxy response
HOP_BY_HOP_HEADERS = {
    "connection",
    "keep-alive",
    "proxy-authenticate",
    "proxy-authorization",
    "te",
    "trailers",
    "transfer-encoding",
    "upgrade",
}


class DashboardView(FullyLoggedMixin, TemplateView):
    template_name = "dashboard/dashboard.html"
    allowed_user_categories = PERMS_DASHBOARD

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Generate the token and build the proxy URL
        token = generate_metabase_token(resource_type="dashboard", resource_id=2)
        proxy_path = f"embed/dashboard/{token}"
        context["iframe_url"] = f"{reverse('metabase_proxy', kwargs={'path': proxy_path})}#bordered=true&titled=true"
        return context


class MetabaseProxyView(FullyLoggedMixin, View):
    """Proxy view that forwards requests to Metabase through the SSH tunnel."""

    allowed_user_categories = PERMS_DASHBOARD

    def dispatch(self, request, *args, **kwargs):
        # Ensure SSH tunnel is active before processing any request
        ssh_tunnel(settings, SSHTarget.METABASE)
        return super().dispatch(request, *args, **kwargs)

    def _proxy_request(self, request, path: str, method: str = "GET"):
        """Forward a request to Metabase and return the response."""
        tunnel_port = get_tunnel_port()
        if not tunnel_port:
            logger.error("Metabase SSH tunnel is not active")
            return HttpResponse("Metabase connection unavailable", status=503)

        # Sanitize user-provided path to prevent SSRF/injection attacks
        safe_path = _sanitize_path(path)

        # Build the target URL
        target_url = f"http://127.0.0.1:{tunnel_port}/{safe_path}"
        if request.GET:
            target_url += f"?{request.GET.urlencode()}"

        # Prepare headers to forward (filter out host and other problematic headers)
        headers = {}
        for key, value in request.headers.items():
            key_lower = key.lower()
            if key_lower not in ("host", "cookie", "content-length") and key_lower not in HOP_BY_HOP_HEADERS:
                headers[key] = value

        try:
            # Make the request to Metabase
            resp = requests.request(
                method=method,
                url=target_url,
                headers=headers,
                data=request.body if method in ("POST", "PUT", "PATCH") else None,
                stream=True,
                timeout=30,
            )

            # Build the Django response
            content_type = resp.headers.get("Content-Type", "application/octet-stream")

            # Use streaming response for larger content
            if int(resp.headers.get("Content-Length", 0)) > 1024 * 1024:  # > 1MB
                response = StreamingHttpResponse(
                    resp.iter_content(chunk_size=8192),
                    content_type=content_type,
                    status=resp.status_code,
                )
            else:
                response = HttpResponse(
                    content=resp.content,
                    content_type=content_type,
                    status=resp.status_code,
                )

            # Forward relevant headers from Metabase response
            for key, value in resp.headers.items():
                key_lower = key.lower()
                if key_lower not in HOP_BY_HOP_HEADERS and key_lower not in (
                    "content-encoding",
                    "content-length",
                    "x-frame-options",
                ):
                    response[key] = value

            return response

        except requests.exceptions.Timeout:
            logger.error("Timeout connecting to Metabase")
            return HttpResponse("Request timeout", status=504)
        except requests.exceptions.ConnectionError as e:
            logger.error(f"Connection error to Metabase: {e}")
            return HttpResponse("Connection error", status=502)
        except Exception as e:
            logger.exception(f"Error proxying request to Metabase: {e}")
            return HttpResponse("Internal proxy error", status=500)

    def get(self, request, path: str):
        return self._proxy_request(request, path, method="GET")

class MetabaseStaticProxyView(View):
    """Proxy view for Metabase static assets (/app/* paths)."""

    def get(self, request, path: str):
        """Forward static asset requests to Metabase through SSH tunnel."""
        # Validate path: reject directory traversal and paths starting with /
        if ".." in path or path.startswith("/"):
            logger.warning(f"Rejected suspicious static asset path: {path}")
            return HttpResponse("Not found", status=404)

        # Validate file extension against allowlist to prevent XSS via dynamic content
        _, ext = os.path.splitext(path)
        if ext.lower() not in ALLOWED_STATIC_EXTENSIONS:
            logger.warning(f"Rejected static asset with disallowed extension: {path}")
            return HttpResponse("Not found", status=404)

        ssh_tunnel(settings, SSHTarget.METABASE)

        tunnel_port = get_tunnel_port()
        if not tunnel_port:
            logger.error("Metabase SSH tunnel is not active")
            return HttpResponse("Metabase connection unavailable", status=503)

        # Sanitize user-provided path to prevent SSRF/injection attacks
        safe_path = _sanitize_path(path)

        target_url = f"http://127.0.0.1:{tunnel_port}/app/{safe_path}"

        try:
            resp = requests.get(url=target_url, stream=True, timeout=30)
            content_type = resp.headers.get("Content-Type", "application/octet-stream")

            if int(resp.headers.get("Content-Length", 0)) > 1024 * 1024:
                response = StreamingHttpResponse(
                    resp.iter_content(chunk_size=8192),
                    content_type=content_type,
                    status=resp.status_code,
                )
            else:
                response = HttpResponse(
                    content=resp.content,
                    content_type=content_type,
                    status=resp.status_code,
                )

            if resp.status_code == 200:
                response["Cache-Control"] = "public, max-age=31536000"

            return response

        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching Metabase static asset: {e}")
            return HttpResponse("Asset unavailable", status=502)
