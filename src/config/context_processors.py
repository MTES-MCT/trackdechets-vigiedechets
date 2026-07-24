from django.conf import settings


def settings_processor(request):
    # return the value you want as a dictionnary. you may add multiple values in there.
    return {
        "GUN_DATA_UPDATE_DATE_STRING": settings.GUN_DATA_UPDATE_DATE_STRING,
        "GISTRID_DATA_UPDATE_DATE_STRING": settings.GISTRID_DATA_UPDATE_DATE_STRING,
        "RNDTS_DATA_UPDATE_DATE_STRING": settings.RNDTS_DATA_UPDATE_DATE_STRING,
        "MATOMO_SITE_ID": settings.MATOMO_SITE_ID,
        "MATOMO_URL": settings.MATOMO_URL,
    }
