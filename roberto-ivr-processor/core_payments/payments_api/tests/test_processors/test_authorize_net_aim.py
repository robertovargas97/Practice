import random
import uuid

from django.utils import timezone
from unittest import TestCase

from . import ProcessorMixin
from ...models import PROCESSOR_AUTHORIZE_NET


class AuthorizeNetProcessorTestCase(ProcessorMixin, TestCase):
    """Test suite for Authorize.Net implementation."""
    processor = PROCESSOR_AUTHORIZE_NET
    credentials = {
        'login': '8GW4n8gMv92x',
        'tran_key': '8z979NXGc77vhN7E'
    }

    def setUp(self):
        super().setUp()
        self.payload['credentials'] = self.credentials
        # populate the payload with some standard test data
        self.populate_payload()

    def test_refund_original_credit_card_transaction(self):
        """
        Special case for testing refund using a reference Id from an earlier transaction.

        This transaction results in an error with the following error codes:
        API error code E00027 - The transaction was unsuccessful.
        Transaction error code 054 - The referenced transaction does not meet the criteria for issuing a credit.

        https://community.developer.authorize.net/t5/Integration-and-Testing/The-referenced-transaction-does-not-meet-the-criteria-for/m-p/26317#M13996

        Authorize.Net runs a settlement every 24 hours automatically. Attempting to refund a transaction that has not
        been settled results in this error.
        """
        client_reference_code = str(random.randint(1000000000, 9999999999))
        # do sale transaction and test for success
        self.payload['client_reference_code'] = client_reference_code
        self.payload['tender_type'] = 'credit_card'
        self.payload['transaction_type'] = 'sale'
        self.payload['card_account_number'] = '5105105105105100'
        self.payload['card_verification_value'] = '123'
        self.payload['card_expiry_month'] = str(timezone.now().strftime('%m'))
        self.payload['card_expiry_year'] = str(timezone.now().strftime('%y'))
        self.payload['card_type'] = 'mastercard'
        self._execute(assert_status_code=200)
        self.assertEqual('approved', self.response.json()['data'][0].get('result'))

        # on success, do refund and test for success
        sale_response = self.response.json()
        self.payload = {
            'processor': self.processor,
            'credentials': self.credentials,
            'project_id': self.project_id,
            'mode': self.mode,
            'interaction_id': str(uuid.uuid4()),
            'interaction_type': self.interaction_type,
            'transaction_type': 'refund',
            'original_transaction_id': sale_response['data'][0].get('transaction_id'),
            'client_reference_code': client_reference_code,
            'tender_type': 'credit_card',
            'card_account_number': '5105105105105100',
            'card_expiry_month': str(timezone.now().strftime('%m')),
            'card_expiry_year': str(timezone.now().strftime('%y')),
            'amount': self.amount
        }
        self._execute(assert_status_code=400)
        self.assertEqual('error', self.response.json()['data'][0].get('result'))

    def test_refund_valid_ach(self, ach_account_number='123456789', ach_routing_number='022000127'):
        """
        Special case for testing refund using valid ACH.

        As a part of Authorize.Net's fraud detection service, all echeck.Net refunds will be under review while
        the system checks to make sure there is enough money in the reserve account to go through with the refund.
        """
        client_reference_code = str(random.randint(1000000000, 9999999999))
        # do sale transaction and test for success
        self.payload['client_reference_code'] = client_reference_code
        self.payload['tender_type'] = 'ach'
        self.payload['transaction_type'] = 'sale'
        self.payload['ach_name_on_account'] = 'John Doe'
        self.payload['ach_account_number'] = ach_account_number
        self.payload['ach_routing_number'] = ach_routing_number
        self.payload['ach_account_type'] = 'checking'
        self.payload['ach_check_number'] = str(random.randint(100, 999))
        self._execute(assert_status_code=200)
        self.assertEqual('approved', self.response.json()['data'][0].get('result'))

        # on success, do refund and test for success
        self.payload = {
            'processor': self.processor,
            'credentials': self.credentials,
            'project_id': self.project_id,
            'mode': self.mode,
            'interaction_id': str(uuid.uuid4()),
            'interaction_type': self.interaction_type,
            'transaction_type': 'refund',
            'client_reference_code': client_reference_code,
            'tender_type': 'ach',
            'ach_name_on_account': 'John Doe',
            'ach_account_number': ach_account_number,
            'ach_routing_number': ach_routing_number,
            'ach_account_type': 'checking',
            'ach_check_number': str(random.randint(100, 999)),
            'amount': self.amount,
            'bill_to_first_name': 'John',
            'bill_to_last_name': 'Doe',
            'bill_to_company': 'IVR Technology Group',
            'bill_to_address': '2350 N. Forest Rd',
            'bill_to_city': 'Getzville',
            'bill_to_county': 'Erie',
            'bill_to_state': 'NY',
            'bill_to_zip': '14228',
            'bill_to_country': 'USA',
            'bill_to_phone': '7162502800',
            'bill_to_email': 'reporting@ivrtechgroup.com',
        }
        self._execute(assert_status_code=200)
        self.assertEqual('review', self.response.json()['data'][0].get('result'))

    def test_bad_credentials(self):
        self.payload['credentials'] = {
            'login': '8GW4n8gMv92a',
            'tran_key': '8z979NXGc77vhN7E'
        }
        client_reference_code = str(random.randint(1000000000, 9999999999))
        # do sale transaction and test for success
        self.payload['client_reference_code'] = client_reference_code
        self.payload['tender_type'] = 'credit_card'
        self.payload['transaction_type'] = 'sale'
        self.payload['card_account_number'] = '5105105105105100'
        self.payload['card_verification_value'] = '123'
        self.payload['card_expiry_month'] = str(timezone.now().strftime('%m'))
        self.payload['card_expiry_year'] = str(timezone.now().strftime('%y'))
        self.payload['card_type'] = 'mastercard'
        self._execute(assert_status_code=400)
        self.assertEqual('error', self.response.json()['data'][0].get('result'))

    def test_supported_description_and_invoice_number(self):
        self.payload = {
            'processor': self.processor,
            'credentials': self.credentials,
            'mode': self.mode,
            'interaction_id': str(uuid.uuid4()),
            'interaction_type': self.interaction_type,
            'transaction_type': 'sale',
            'tender_type': 'credit_card',
            'card_account_number': '5105105105105100',
            'card_expiry_month': str(timezone.now().strftime('%m')),
            'card_expiry_year': str(timezone.now().strftime('%y')),
            'amount': self.amount,
            'description': 'Integration Test',
            'invoice_number': self.get_random_number()
        }
        self._execute(assert_status_code=200)
        self.assertEqual('approved', self.response.json()['data'][0].get('result'))

    def test_not_supported_description_and_invoice_number(self):
        self.payload = {
            'processor': self.processor,
            'credentials': self.credentials,
            'mode': self.mode,
            'interaction_id': str(uuid.uuid4()),
            'interaction_type': self.interaction_type,
            'transaction_type': 'void',
            'amount': self.amount,
            'original_transaction_id': self.get_random_number(),
            'description': 'Integration Test',
            'invoice_number': self.get_random_number()
        }
        self._execute(assert_status_code=400)
        self.assertEqual('error', self.response.json()['data'][0].get('result'))
