from unittest import TestCase
import random

from lookup.models import PROCESSOR_CONVENIENT_PAYMENTS
from . import ProcessorMixin


class ConvenientPaymentsTestCase(ProcessorMixin, TestCase):
    processor = PROCESSOR_CONVENIENT_PAYMENTS
    credentials = {
        "merchant_key": "9J7575",
        "api_access_key": "ZAKYUWNOZHSR"
    }
    customer_id = '19491528'

    def setUp(self):
        super().setUp()
        self.payload['credentials'] = self.credentials

    def test_lookup(self):
        """Performs a lookup and returns a response."""
        self.payload['customer_id'] = self.customer_id
        self._execute(assert_status_code=200)
        self.assertEqual('approved', self.response.json()['data'][0].get('result'))

    def test_lookup_with_client_reference_code(self):
        """Performs a lookup and returns a response."""
        self.payload['customer_id'] = self.customer_id
        client_reference_code = str(random.randint(1000000000, 9999999999))
        self.payload['client_reference_code'] = client_reference_code
        self._execute(assert_status_code=200)
        self.assertEqual('approved', self.response.json()['data'][0].get('result'))
        self.assertEqual(client_reference_code, self.response.json()['data'][0].get('client_reference_code'))
