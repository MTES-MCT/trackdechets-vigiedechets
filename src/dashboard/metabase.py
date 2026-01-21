import time

import jwt
from django.conf import settings


def generate_metabase_token(question_id: int = 192) -> str:
    """Generate a JWT token for Metabase embedding."""
    payload = {
        "resource": {"question": question_id},
        "params": {},
        "exp": round(time.time()) + (60 * 10),  # 10 minute expiration
    }

    return jwt.encode(payload, settings.METABASE_SECRET_KEY, algorithm="HS256")


def get_metabase_iframe_url(question_id: int = 192) -> str:
    """Get the full iframe URL for a Metabase question."""
    token = generate_metabase_token(question_id)
    return f"{settings.METABASE_SITE_URL}/embed/question/{token}#bordered=true&titled=true"