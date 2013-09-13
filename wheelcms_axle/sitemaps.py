from django.contrib.sites.models import Site

from django.contrib.sitemaps import Sitemap
from django.conf import settings
from django.utils import timezone
from django.contrib.sitemaps.views import sitemap as basesitemap

from .content import Content
from .utils import get_active_language

class ContentSitemap(Sitemap):
    # changefreq = 'daily'

    def items(self):
        now = timezone.now()
        language = get_active_language()

        return Content.objects.filter(node__isnull=False,
                                      language=language,
                                      state='published',
                                      publication__lte=now,
                                      expire__gte=now)

    def lastmod(self, obj):
        return obj.modified

    def get_urls(self, page=1, site=None, protocol=None):
        language = get_active_language()
        domain = getattr(settings, 'LANGUAGE_DOMAINS', {}).get(language)
        if domain:
            site = Site(domain=domain, name=domain)

        return super(ContentSitemap, self).get_urls(page, site, protocol)
