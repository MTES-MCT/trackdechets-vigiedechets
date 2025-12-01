from django.contrib.sites.models import Site
from django.core.cache import cache
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

DOMAIN_CACHE_KEY = "current_site_domain"
CACHE_TIMEOUT = 3600  # 1 hour


def get_domain():
    """This function should be updated if multiple domains are served"""
    domain_value = cache.get(DOMAIN_CACHE_KEY)

    if domain_value is None:
        current_site = Site.objects.get_current()
        domain_value = current_site.domain
        cache.set(DOMAIN_CACHE_KEY, domain_value, CACHE_TIMEOUT)

    return domain_value


# Invalidate cache when Site model changes
@receiver([post_save, post_delete], sender=Site)
def clear_domain_cache(sender, **kwargs):
    cache.delete(DOMAIN_CACHE_KEY)
