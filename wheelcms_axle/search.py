import urllib

from django.core.paginator import Paginator, InvalidPage
from two.ol.base import FormHandler, applyrequest
from two.bootstrap.paginator import SectionedPaginator

from haystack.forms import SearchForm as BaseForm
from haystack.query import SearchQuerySet

from wheelcms_axle.base import WheelHandlerMixin
from wheelcms_axle import utils

class SearchForm(BaseForm):
    pass


class SearchHandler(FormHandler, WheelHandlerMixin):
    results_per_page = 10

    @applyrequest(page=int)
    def index(self, page=1):
        sqs = SearchQuerySet()
        language = utils.get_active_language(self.request)

        sqs = sqs.filter(language__in=(language, "any"))

        if not self.hasaccess():
            sqs = sqs.filter(state__in=("visible", "published"))

        form = self.context['form'] = SearchForm(self.request.REQUEST,
                                          searchqueryset=sqs)

        if page < 1:
            page = 1

        if form.is_valid():
            self.context['query'] = form.cleaned_data['q']

            self.context['paginator'] = paginator = \
                      SectionedPaginator(form.search(), self.results_per_page)

            try:
                self.context['page'] = paginator.page(page)
            except InvalidPage:
                return self.notfound()

            self.context['GET_string'] = urllib.urlencode([(k, v)
                    for (k, v) in self.request.REQUEST.iteritems()
                    if k != 'page'])

            b, m, e = paginator.sections(page, windowsize=4)

            self.context['begin'] = b
            self.context['middle'] = m
            self.context['end'] = e

        ## move to wheecms_axle folder?
        return self.template("search/search.html")

    ## POST == GET
    process = index
