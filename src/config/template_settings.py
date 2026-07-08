import os


def get_template_runtime_settings():
    return {
        "GUN_DATA_UPDATE_DATE_STRING": os.getenv("GUN_DATA_UPDATE_DATE_STRING", ""),
        "GISTRID_DATA_UPDATE_DATE_STRING": os.getenv("GISTRID_DATA_UPDATE_DATE_STRING", ""),
        "RNDTS_DATA_UPDATE_DATE_STRING": os.getenv("RNDTS_DATA_UPDATE_DATE_STRING", ""),
        "MATOMO_SITE_ID": os.getenv("MATOMO_SITE_ID", ""),
    }