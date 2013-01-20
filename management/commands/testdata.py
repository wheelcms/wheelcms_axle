from django.core.management.base import BaseCommand

from wheelcms_axle.models import Node
from wheelcms_spokes.page import Page

lipsum = """<p><b>Lorem ipsum dolor sit amet</b>, consectetur adipiscing elit. Maecenas faucibus dolor at eros consectetur ut consequat enim mollis. Suspendisse ac leo neque, sed suscipit dui. Lorem ipsum dolor sit amet, consectetur adipiscing elit. Duis ultricies iaculis magna, vel interdum quam volutpat eu.</p>
<p><i>Proin condimentum neque ac tellus adipiscing et tincidunt arcu euismod</i>. Duis sit amet enim nec sapien rutrum faucibus. Sed eu ultricies justo. Curabitur orci odio, tincidunt ac adipiscing non, commodo vel urna. Phasellus massa elit, scelerisque id pharetra sagittis, facilisis a tortor. Donec sodales nibh in leo suscipit sagittis. Aliquam a leo vitae tortor ullamcorper interdum ac at mauris.</p>"""

def populate(node, level):
    for i in range(4):
        print "level %d page %d" % (level, i)
        n = node.add('sub%d_%d' % (level, i))
        sub = Page(title="Subpage %d level %d" % (i, level), body=lipsum, state="published", node=n)
        sub.save()
        if level > 0:
            populate(n, level-1)

class Command(BaseCommand):
    """ Normalize existing usernames to match allowed characters """
    args = ''
    help = 'setup simple content structure'

    def handle(self, *args, **options):
        root = Node.root()
        main = Page(title="Welcome", body="This is the main page", state="published", node=root)
        main.save()
        populate(root, 5)
