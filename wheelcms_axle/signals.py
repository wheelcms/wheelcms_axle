import django.dispatch

state_changed = django.dispatch.Signal(providing_args=["oldstate", "newstate"])


