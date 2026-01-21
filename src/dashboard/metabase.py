import time
import logging

import jwt
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

logger = logging.getLogger(__name__)


def generate_metabase_token(question_id: int = 192) -> str:
    """Generate a JWT token for Metabase embedding."""
    if not settings.METABASE_SECRET_KEY:
        raise ImproperlyConfigured("METABASE_SECRET_KEY must be set")
    payload = {
        "resource": {"question": question_id},
        "params": {},
        "exp": round(time.time()) + (60 * 10),
    }
    try:
        return jwt.encode(payload, settings.METABASE_SECRET_KEY, algorithm="HS256")
    except Exception as e:
        logger.error(f"Failed to generate Metabase token: {e}")
        raise


def get_metabase_iframe_url(tunnel_port: int, question_id: int = 192) -> str:
    """Get the full iframe URL for a Metabase question."""
    token = generate_metabase_token(question_id)
    return f"http://{settings.METABASE_SITE_URL}:{tunnel_port}/embed/question/{token}#bordered=true&titled=true"
