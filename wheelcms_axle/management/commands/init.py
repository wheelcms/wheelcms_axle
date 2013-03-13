from django.core.management.base import BaseCommand
from django.core.management import call_command


class Command(BaseCommand):
    """ Initialize a fresh database """
    ## todo: include import
    args = '[importfrom] [importpath]'
    help = 'Initialize a new database'

    def handle(self, importfrom=None, importpath=None, *args, **options):
        call_command("syncdb")
        call_command("check_permissions")
        if importfrom:
            call_command("import", readfrom=importfrom, path=importpath)
