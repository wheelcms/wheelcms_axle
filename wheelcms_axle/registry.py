from warnings import warn

warn("wheelcms_axle.registry is deprecated, "
     "please use wheelcms_axle.registries.registry in stead",
     DeprecationWarning)

from .registries.registry import Registry
