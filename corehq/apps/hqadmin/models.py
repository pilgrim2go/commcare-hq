from datetime import date

from django.db import models

from dimagi.ext.couchdbkit import *
from dimagi.utils.parsing import json_format_datetime
from dimagi.utils.decorators.memoized import memoized
from pillowtop.utils import get_pillow_by_name, get_all_pillow_instances
from pillowtop.exceptions import PillowNotFoundError


from corehq.apps.users.models import WebUser


class HqDeploy(Document):
    date = DateTimeProperty()
    user = StringProperty()
    environment = StringProperty()
    code_snapshot = DictProperty()
    diff_url = StringProperty()

    @classmethod
    def get_latest(cls, environment, limit=1):
        result = HqDeploy.view(
            'hqadmin/deploy_history',
            startkey=[environment, {}],
            endkey=[environment],
            reduce=False,
            limit=limit,
            descending=True,
            include_docs=True
        )
        return result.all()

    @classmethod
    def get_list(cls, environment, startdate, enddate, limit=50):
        return HqDeploy.view(
            'hqadmin/deploy_history',
            startkey=[environment, json_format_datetime(startdate)],
            endkey=[environment, json_format_datetime(enddate)],
            reduce=False,
            limit=limit,
            include_docs=False
        ).all()


class PillowCheckpointSeqStore(models.Model):
    seq = models.TextField()
    checkpoint_id = models.CharField(max_length=255, db_index=True)
    date_updated = models.DateTimeField(auto_now=True)

    @classmethod
    def get_by_pillow_name(cls, pillow_name):
        try:
            pillow = get_pillow_by_name(pillow_name)
        except PillowNotFoundError:
            # Could not find the pillow
            return None

        if not pillow:
            return None

        try:
            store = cls.objects.get(checkpoint_id=pillow.checkpoint.checkpoint_id)
        except cls.DoesNotExist:
            return None

        return store


class ESRestorePillowCheckpoints(models.Model):
    seq = models.TextField()
    checkpoint_id = models.CharField(max_length=255, db_index=True)
    date_updated = models.DateField()

    @classmethod
    def create_pillow_checkpoint_snapshots(cls):
        for pillow in get_all_pillow_instances():
            checkpoint = pillow.checkpoint
            db_seq = checkpoint.get_current_sequence_id()
            cls.objects.create(seq=db_seq,
                               checkpoint_id=checkpoint.checkpoint_id,
                               date_updated=date.today())


class VCMMigration(models.Model):
    domain = models.CharField(max_length=255, null=False, unique=True)
    emailed = models.DateTimeField(null=True)
    migrated = models.DateTimeField(null=True)
    notes = models.TextField(null=True)

    @property
    @memoized
    def admins(self):
        return [admin.email or admin.username for admin in WebUser.get_admins_by_domain(self.domain)]
