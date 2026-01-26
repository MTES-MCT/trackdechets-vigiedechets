import time
import logging

import jwt
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

logger = logging.getLogger(__name__)


def generate_metabase_token(
    resource_type: str,
    resource_id: int,
) -> str:
    """Generate a JWT token for Metabase embedding."""
    if not settings.METABASE_SECRET_KEY:
        raise ImproperlyConfigured("METABASE_SECRET_KEY must be set")
    
    if resource_type == "question":
        resource = {"question": resource_id}
    elif resource_type == "dashboard":
        resource = {"dashboard": resource_id}
    else:
        raise ValueError(f"Invalid resource type: {resource_type}")
    
    payload = {
        "resource": resource,
        "params": {},
        "exp": round(time.time()) + (60 * 10),
    }
    try:
        return jwt.encode(payload, settings.METABASE_SECRET_KEY, algorithm="HS256")
    except Exception as e:
        logger.error(f"Failed to generate Metabase token: {e}")
        raise
