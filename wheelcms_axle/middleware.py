from django.contrib.messages.storage.cookie import CookieStorage

class FixMessageMiddleware(object):
    """
        The message cookie format has changed from Django 1.4 to
        Django 1.5. Django 1.5 probably supported both formats,
        but if you move from 1.4.x to 1.6.x directly, you will run into
        an IndexError:

        Exception Type: IndexError
        Exception Value:
        list index out of range
        Exception Location: (...) django/contrib/messages/storage/cookie.py in process_messages, line 37

        This small piece of middleware will track those cookies and destroy
        them (leaving new-style in tact)

        https://code.djangoproject.com/ticket/22426

        DISCLAIMER:

        This middleware will not attempt to rewrite the messages! You may
        miss important notifications because of this!
    """
    def process_request(self, request):
        data = request.COOKIES.get("messages")
        storage = CookieStorage(request)
        try:
            storage._decode(data)
        except IndexError:
            del request.COOKIES['messages']

from .toolbar import create_toolbar

class ToolbarMiddleware(object):
    def process_request(self, request):
        create_toolbar(request)

