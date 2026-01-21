import logging
from typing import Any, Optional

from django.conf import settings
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine

from common.ssh import get_tunnel_port, ssh_tunnel

logger = logging.getLogger(__name__)

_dwh_info: dict[str, Any] = {}  # Holds datawarehouse connection singleton


def set_engine(dwh_engine: Engine, port: int):
    _dwh_info["engine"] = dwh_engine
    _dwh_info["port"] = port


def get_engine() -> Optional[Engine]:
    return _dwh_info.get("engine")


def get_engine_port() -> Optional[int]:
    return _dwh_info.get("port")


def get_wh_sqlachemy_engine() -> Engine:
    dwh_username = settings.DWH_USERNAME
    dwh_password = settings.DWH_PASSWORD
    dwh_ssh_local_bind_host = settings.DWH_SSH_LOCAL_BIND_HOST
    ssh_tunnel(settings)

    tunnel_port = get_tunnel_port()

    if (get_engine() is None) or (get_engine_port() != tunnel_port):
        logger.info("Creating new engine for datawarehouse.")
        warehouse_url = f"clickhouse+native://{dwh_username}:{dwh_password}@{dwh_ssh_local_bind_host}:{tunnel_port}"
        wh_engine = create_engine(warehouse_url)
        set_engine(wh_engine, tunnel_port)

    return get_engine()
