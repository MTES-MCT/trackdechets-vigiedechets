import logging
import os
import tempfile
import threading
from typing import Any, Optional
from enum import Enum
import sshtunnel
from django.conf import LazySettings
from common.constants import SSHTarget

logger = logging.getLogger(__name__)

_tunnel_info: dict[str, Any] = {}  # Holds tunnel singleton
_tunnel_lock = threading.Lock()


def set_tunnel(tunnel: sshtunnel.SSHTunnelForwarder, key_filepath: str):
    _tunnel_info["tunnel"] = tunnel
    _tunnel_info["port"] = tunnel.local_bind_port
    _tunnel_info["key_filepath"] = key_filepath


def get_tunnel() -> Optional[sshtunnel.SSHTunnelForwarder]:
    return _tunnel_info.get("tunnel")


def get_tunnel_port() -> Optional[int]:
    return _tunnel_info.get("port")


def get_key_filepath() -> Optional[str]:
    return _tunnel_info.get("key_filepath")


def is_tunnel_active(tunnel: sshtunnel.SSHTunnelForwarder) -> bool:
    return tunnel.is_active


def ssh_tunnel(settings: LazySettings, target: SSHTarget = SSHTarget.DWH):
    """
    Maintains a single active SSH tunnel across the application lifetime.
    Reuses the tunnel if already open, and reopens it if necessary.
    """

    with _tunnel_lock:
        tunnel = get_tunnel()

        if tunnel and is_tunnel_active(tunnel):
            # Tunnel is already open and active
            logger.debug("Reusing existing ssh tunnel")
            return tunnel

        logger.info("Creating new ssh tunnel")
        # Otherwise, create a new tunnel
        temp_key_file = tempfile.NamedTemporaryFile(mode="w", prefix="trackdechets_key_", delete=False)

        try:
            temp_key_file.write(settings.DWH_SSH_KEY)
            temp_key_file.close()
            os.chmod(temp_key_file.name, 0o600)

            if target == SSHTarget.DWH:
                tunnel = sshtunnel.open_tunnel(
                (settings.DWH_SSH_HOST, int(settings.DWH_SSH_PORT)),
                ssh_username=settings.DWH_SSH_USERNAME,
                ssh_private_key_password=settings.DWH_SSH_KEY_PASSPHRASE,
                ssh_pkey=temp_key_file.name,
                remote_bind_address=("localhost", int(settings.DWH_PORT)),
                )

            elif target == SSHTarget.METABASE:
                tunnel = sshtunnel.open_tunnel(
                (settings.METABASE_SSH_HOST, int(settings.METABASE_SSH_PORT)),
                ssh_username=settings.METABASE_SSH_USERNAME,
                ssh_private_key_password=settings.METABASE_SSH_KEY_PASSPHRASE,
                ssh_pkey=temp_key_file.name,
                remote_bind_address=("localhost", int(settings.METABASE_PORT)),
            )

            else:
                raise ValueError(f"Invalid target: {target}")
            tunnel.start()
            set_tunnel(tunnel, temp_key_file.name)

            return tunnel
        finally:
            # Delete the key file after the tunnel has been established or if the tunnel creation has failed.
            os.unlink(temp_key_file.name)
