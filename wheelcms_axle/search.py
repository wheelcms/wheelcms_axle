import urllib

from django.core.paginator import Paginator, InvalidPage

from two.ol.base import FormHandler, applyrequest
from haystack.forms import SearchForm as BaseForm
from haystack.query import SearchQuerySet

from wheelcms_axle.base import WheelHandlerMixin

class SearchForm(BaseForm):
    pass


class SearchHandler(FormHandler, WheelHandlerMixin):
    results_per_page = 1

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

            self.context['GET_string'] = urllib.urlencode([(k, v)
                    for (k, v) in self.request.REQUEST.iteritems()
                    if k != 'page'])
            np = paginator.num_pages

            windowsize = 6

            ##
            ## provide sort of a sliding window over the available
            ## pages with the current page in the center.
            ## windowsize is the size of this window
            if np > windowsize*2:
                # import pdb; pdb.set_trace()
                
                self.context['begin'] = [1]
                self.context['end'] = [np]
                start = max(3, page - windowsize/2)
                end = start + windowsize+1
                if end > np-2:
                    end = np - 1
                    start = end - windowsize - 1

                if page < 4:
                    self.context['begin'] = range(1, windowsize)
                    self.context['end'] = [np]
                elif page > (np - 3):
                    self.context['begin'] = [1]
                    self.context['end'] = range(np+1-windowsize, np+1)
                else:
                    self.context['middle'] = range(start, end)
            else:
                self.context['begin'] = range(1, paginator.num_pages + 1)

        ## move to wheecms_axle folder?
        return self.template("search/search.html")

    ## POST == GET
    process = index
