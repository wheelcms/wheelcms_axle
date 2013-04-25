AUTHENTICATION_BACKENDS = (
    'userena.backends.UserenaAuthenticationBackend',
    'guardian.backends.ObjectPermissionBackend',
    'django.contrib.auth.backends.ModelBackend',
)

AUTH_PROFILE_MODULE="wheelcms_axle.WheelProfile"

ANONYMOUS_USER_ID = -1

LOGIN_REDIRECT_URL = '/accounts/%(username)s/'
LOGIN_URL = '/accounts/signin/'
LOGOUT_URL = '/accounts/signout/'

USERENA_SIGNIN_REDIRECT_URL = "/"
USERENA_ACTIVATION_REQUIRED = True

USERENA_FORBIDDEN_USERNAMES = ('signup', 'signout', 'signin', 'activate', 'me', 'password', 'www', 'wheel', 'root', 'support')

## guardian config

GUARDIAN_RAISE_403 = True

ALLOW_SIGNUP = True
