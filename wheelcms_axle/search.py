from django.core.paginator import Paginator, InvalidPage

from two.ol.base import FormHandler, applyrequest
from haystack.forms import SearchForm as BaseForm
from haystack.query import SearchQuerySet

from wheelcms_axle.base import WheelHandlerMixin

class SearchForm(BaseForm):
    pass


class SearchHandler(FormHandler, WheelHandlerMixin):
    results_per_page = 10

    @applyrequest(page=int)
    def index(self, page=1):
        sqs = SearchQuerySet()
        if not self.hasaccess():
            sqs = sqs.filter(state__in=("visible", "published"))

        form = self.context['form'] = SearchForm(self.request.REQUEST,
                                          searchqueryset=sqs)

        if page < 1:
            page = 1

        if form.is_valid():
            self.context['query'] = form.cleaned_data['q']

            paginator = Paginator(form.search(), self.results_per_page)

            try:
                self.context['page'] = paginator.page(page)
            except InvalidPage:
                return self.notfound()

        ## move to wheecms_axle folder?
        return self.template("search/search.html")

    ## POST == GET
    process = index
