from .template_settings import get_template_runtime_settings


def settings_processor(request):
    # Keep existing keys + merge shared runtime settings
    ctx = {
        "GUN_DATA_UPDATE_DATE_STRING": get_template_runtime_settings().get("GUN_DATA_UPDATE_DATE_STRING", ""),
        "GISTRID_DATA_UPDATE_DATE_STRING": get_template_runtime_settings().get("GISTRID_DATA_UPDATE_DATE_STRING", ""),
        "RNDTS_DATA_UPDATE_DATE_STRING": get_template_runtime_settings().get("RNDTS_DATA_UPDATE_DATE_STRING", ""),
        "MATOMO_SITE_ID": get_template_runtime_settings().get("MATOMO_SITE_ID", ""),
        "MATOMO_URL": get_template_runtime_settings().get("MATOMO_URL", ""),
    }
    return ctx
