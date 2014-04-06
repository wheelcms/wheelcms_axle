from haystack.backends import BaseEngine
from haystack.backends.solr_backend import SolrSearchBackend, SolrSearchQuery
from haystack.utils.loading import UnifiedIndex

from wheelcms_axle.content import type_registry

class WheelIndexCollector(UnifiedIndex):
    def collect_indexes(self):
        indexes = []
        for k, v in type_registry.iteritems():
            if v.add_to_index:
                indexes.append(v.index()())
        return indexes

class SolrEngine(BaseEngine):
    """
        Haystack no longer supports explicit index registration,
        it'll scan INSTALLED_APPS and search for Index classes in
        the app's search_indexes module, which won't work in a dynamic
        setup.

        This is a temporary workaround (since it's only defined on
        SolrEngine). The real solution is for haystack to support
        alternative "Index Collectors"
    """

    backend = SolrSearchBackend
    query = SolrSearchQuery

    def __init__(self, using=None):
        super(SolrEngine, self).__init__(using)
        self._index = WheelIndexCollector()


