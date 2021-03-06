import logging
import os
import sys
from datetime import datetime
from optparse import make_option
from django.core.management import BaseCommand, CommandError
from corehq.blobs.migrate import EXPORTERS
from corehq.util.decorators import change_log_level


USAGE = """Usage: ./manage.py run_blob_export [options] <slug> <domain>

Slugs:

{}

""".format('\n'.join(sorted(EXPORTERS)))


class Command(BaseCommand):
    """
    Example: ./manage.py run_blob_export [options] export_domain_apps domain
    """
    help = USAGE
    option_list = BaseCommand.option_list + (
        make_option('--log-dir', help="Migration log directory."),
        make_option('--reset', action="store_true", default=False,
            help="Discard any existing migration state."),
        make_option('--chunk-size', type="int", default=100,
            help="Maximum number of records to read from couch at once."),
    )

    @change_log_level('boto3', logging.WARNING)
    @change_log_level('botocore', logging.WARNING)
    def handle(self, slug=None, domain=None, log_dir=None, reset=False,
               chunk_size=100, **options):
        try:
            migrator = EXPORTERS[slug]
        except KeyError:
            raise CommandError(USAGE)

        if not domain:
            raise CommandError(USAGE)

        if log_dir is None:
            file = None
        else:
            file = os.path.join(log_dir, "{}-blob-export-{}.txt".format(
                slug, datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
            ))
            assert not os.path.exists(file), file
        migrator.by_domain(domain)
        total, skips = migrator.migrate(file, reset=reset, chunk_size=chunk_size)
        if skips:
            sys.exit(skips)
