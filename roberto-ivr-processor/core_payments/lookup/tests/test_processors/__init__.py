import json
import uuid

from django.test import Client, override_settings

from core_payments.models import (
    MODE_TEST,
    INTERACTION_WEB
)
from wiretap.models import Tap


class ProcessorMixin(object):
    """Contains test_processors tests via the API."""
    path = None
    payload = None
    processor = None
    credentials = None
    extra = None
    amount = '10.10'
    project_id = '1'
    mode = MODE_TEST
    interaction_type = INTERACTION_WEB

    def setUp(self):
        # setup wire tap so messages can be logged
        tap, created = Tap.objects.get_or_create(path_regex='/coreservices/payments/api/',
                                                 defaults={'mask_chd': True, 'is_active': True})

        self.path = 'http://127.0.0.1:8000/coreservices/payments/api/lookups/transactions/{}/'.format(self.project_id)
        self.payload = {
            'processor': self.processor,
            'credentials': {},
            'project_id': self.project_id,
            'mode': self.mode,
            'amount': self.amount,
            'interaction_id': str(uuid.uuid4()),
            'interaction_type': self.interaction_type,
            'extra': {}
        }

    def test_bad_request(self):
        self._execute(assert_status_code=400)

    @override_settings(APPLY_KONG_MIDDLEWARE={})  # so we don't need extra header for kong middleware during testing
    def _execute(self, assert_status_code=None):
        c = Client()
        self.response = c.post(self.path, json.dumps(self.payload), 'application/json')
        if assert_status_code:
            self.assertEqual(assert_status_code, self.response.status_code, msg=self.response.content.decode('utf-8'))
