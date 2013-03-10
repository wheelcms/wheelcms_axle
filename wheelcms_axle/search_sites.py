import haystack
haystack.autodiscover()

from haystack import indexes

from wheelcms_spokes.page import Page

class WheelIndex(indexes.SearchIndex):
    text = indexes.CharField(document=True, model_attr='body')

    def index_queryset(self):
        ## published / visible, attached (!), not expired
        return Page.objects.all() # filter(pub_date__lte=datetime.datetime.now())


haystack.site.register(Page, WheelIndex)
