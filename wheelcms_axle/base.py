from two.ol.base import context
from wheelcms_axle.models import Configuration

class WheelHandlerMixin(object):
    @context
    def config(self):
        return Configuration.config()

