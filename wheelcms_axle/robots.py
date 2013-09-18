"""
    We can't serve robots.txt directly; Django 1.5 no longer supports
    direct_to_template, and TemplateView does not support a mimetype
    on 1.4
"""

from django.template.response import TemplateResponse

def robots_txt(request):
    """ serve robots.txt with the appropriate content type """
    return TemplateResponse(request, "robots.txt",
                            content_type="text/plain")
