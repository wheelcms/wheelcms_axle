try:
    import os
    pj = os.path.join

    base = pj(os.path.dirname(__file__), "..", "..")
    BRANCH = open(pj(base, './.git/HEAD')).readline().split('/')[-1].strip()
    COMMIT = open(pj(base, './.git/refs/heads/%s' % BRANCH)).readline().strip()
    BUILD = '%s-%s' % ( BRANCH, COMMIT )
except:
    BUILD = '- unknown -'

import pkg_resources
VERSION = pkg_resources.require("wheelcms_axle")[0].version
