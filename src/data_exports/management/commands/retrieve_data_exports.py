import logging
import re

import boto3
from botocore.exceptions import ClientError
from django.conf import settings
from django.core.mail import EmailMessage
from django.core.management.base import BaseCommand

from ...models import DataExport

logger = logging.getLogger(__name__)

pattern = r"^(bsdd|bsda|bsdasri|bsvhu|bsff|dnd_entrant|dnd_sortant|texs_entrant|texs_sortant)\/(bsdd|bsda|bsdasri|bsvhu|bsff|dnd_entrant|dnd_sortant|texs_entrant|texs_sortant)_?(20\d{2})?.parquet$"


def verbosify_byte_size(size_bytes):
    """
    Convert bytes to human-readable format.

    """
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0


def list_s3_bucket_contents(bucket_name, prefix=""):
    """
    List contents of an S3 bucket with optional prefix filtering.

    Args:
        bucket_name (str): Name of the S3 bucket
        prefix (str, optional): Filter objects by prefix (e.g., 'folder/')

    Returns:
        list: List of object keys in the bucket
    """
    session = boto3.Session(region_name="fr-par")
    try:
        # Create an S3 client
        client = session.client(
            "s3",
            endpoint_url=settings.AWS_S3_ENDPOINT_URL,
            aws_access_key_id=settings.AWS_S3_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_S3_SECRET_ACCESS_KEY,
        )

        # List objects in the bucket
        response = client.list_objects_v2(Bucket=bucket_name)

        # Extract and return object keys
        if "Contents" in response:
            return [
                {
                    "key": obj["Key"],
                    "last_modified": obj["LastModified"],
                    "size": obj["Size"],
                    "size_human_readable": obj["Size"],
                }
                for obj in response["Contents"]
            ]
        return []

    except ClientError as e:
        logger.error(f"Error listing bucket contents: {e}")
        return []


def notify_admins():
    body = "La récupération des fichiers parquet a échoué"
    message = EmailMessage(
        subject="La récupération des fichiers parquet a échoué",
        body=body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=settings.MESSAGE_RECIPIENTS,
    )
    message.send()


class Command(BaseCommand):
    def handle(self, verbosity=0, **options):
        """List bucket content and create DataExport objects to display on relevant page"""
        try:
            data = list_s3_bucket_contents(settings.PARQUET_BUCKET_NAME)
            for el in data:
                key = el["key"]
                matches = re.search(pattern, key)

                if not matches:
                    continue
                export_type, _, year = matches.groups()
                file_name = key.split("/")[1]

                year = int(year) if year else None
                size = el["size"]

                logger.info("Creating data export for %s", file_name)
                created = DataExport.objects.create(
                    export_type=export_type.upper(),
                    year=year,
                    s3_path=key,
                    size=size,
                    verbose_size=verbosify_byte_size(size),
                    name=file_name,
                    last_modified=el["last_modified"],
                )
                DataExport.objects.filter(year=year, name=file_name).exclude(pk=created.pk).delete()
            logger.info("Data export successfully retrieved")
        except Exception as e:  # noqa
            logger.error(e)
            notify_admins()
