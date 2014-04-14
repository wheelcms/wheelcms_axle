import mock


from wheelcms_axle.middleware import FixMessageMiddleware


class TestFixMessageMiddleware(object):
    def test_oldstyle(self):
        """ mock CookieStorage raising IndexError """
        with mock.patch("django.contrib.messages.storage.cookie"
                        ".CookieStorage._decode", side_effect=IndexError):
            request = mock.Mock(COOKIES={'messages': 'dummy'})
            FixMessageMiddleware().process_request(request)
            assert 'messages' not in request.COOKIES

    def test_newstyle(self):
        """ mock ordinary execution """
        with mock.patch("django.contrib.messages.storage.cookie"
                        ".CookieStorage._decode", return_value=None):
            request = mock.Mock(COOKIES={'messages': 'dummy'})
            FixMessageMiddleware().process_request(request)
            assert 'messages' in request.COOKIES
