from enum import Enum

STATE_RUNNING = "running"
STATE_DONE = "done"
HISTORY_SIZE = 5


class SSHTarget(Enum):
    DWH = "dwh"
    METABASE = "metabase"
