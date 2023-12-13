import json
import random
import uuid

from django.test import Client, override_settings
from django.utils import timezone

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
    test_cards = None

    def get_random_number(self, min_value=1000000000, max_value=9999999999):
        return str(random.randint(min_value, max_value))

    def setUp(self):
        # setup wire tap so messages can be logged
        tap, created = Tap.objects.get_or_create(path_regex='/coreservices/payments/api/',
                                                 defaults={'mask_chd': True, 'is_active': True})

        self.path = 'http://127.0.0.1:8000/coreservices/payments/api/payments/transactions/{}/'.format(self.project_id)
        self.payload = {
            'processor': self.processor,
            'credentials': {},
            'project_id': self.project_id,
            'mode': self.mode,
            'amount': self.amount,
            'interaction_id': str(uuid.uuid4()),
            'interaction_type': self.interaction_type,
            'extra': {},
            'customer_id': self.get_random_number()
        }

        self.test_cards = {
            'mastercard': {
                'number': '5105105105105100',
                'exp_month': str(timezone.now().strftime('%m')),
                'exp_year': str(timezone.now().strftime('%y')),
                'cvv': '123',
                'type': 'mastercard',
            },
            'visa': {
                'number': '4444333322221111',
                'exp_month': str(timezone.now().strftime('%m')),
                'exp_year': str(timezone.now().strftime('%y')),
                'cvv': '123',
                'type': 'visa',
            }
        }

    def populate_payload(self):
        self.payload.update({
            'bill_to_first_name': 'John',
            'bill_to_last_name': 'Doe',
            'bill_to_company': 'IVR Technology Group',
            'bill_to_address': '2350 N. Forest Rd',
            'bill_to_city': 'Getzville',
            'bill_to_county': 'Erie',
            'bill_to_state': 'NY',
            'bill_to_zip': '14228',
            'bill_to_country': 'US',
            'bill_to_phone': '7162502800',
            'bill_to_email': 'reporting@ivrtechgroup.com',
            'ship_to_first_name': 'Jane',
            'ship_to_last_name': 'Smith',
            'ship_to_company': 'Argyle Technology Group',
            'ship_to_address': '535 Washington St',
            'ship_to_city': 'Buffalo',
            'ship_to_county': 'Erie',
            'ship_to_state': 'NY',
            'ship_to_zip': '14204',
            'ship_to_country': 'US',
            'ship_to_phone': '7162987603',
            'ship_to_email': 'support@argyletechnologygroup.com',
        })

    def test_bad_request(self):
        self._execute(assert_status_code=400)

    def test_client_reference_code_bad_request(self):
        '''A test to ensure client reference code is being passed back on bad requests.'''
        client_reference_code = self.get_random_number()
        self.payload['client_reference_code'] = client_reference_code
        self._execute(assert_status_code=400)
        self.assertEqual(client_reference_code, self.response.json()['data'][0].get('client_reference_code'))

    def test_client_reference_code_good_request(self):
        '''A test to ensure client reference code is being passed back on good requests.'''
        card = self.test_cards['mastercard']
        client_reference_code = self.get_random_number()
        self.payload['client_reference_code'] = client_reference_code
        self.payload['tender_type'] = 'credit_card'
        self.payload['transaction_type'] = 'sale'
        self.payload['card_account_number'] = card['number']
        self.payload['card_verification_value'] = card['cvv']
        self.payload['card_expiry_month'] = card['exp_month']
        self.payload['card_expiry_year'] = card['exp_year']
        self.payload['card_type'] = card['type']
        self._execute(assert_status_code=200)
        self.assertEqual('approved', self.response.json()['data'][0].get('result'))
        self.assertEqual(client_reference_code, self.response.json()['data'][0].get('client_reference_code'))

    def test_sale_valid_credit_card(self):
        card = self.test_cards['mastercard']
        self.payload['client_reference_code'] = self.get_random_number()
        self.payload['tender_type'] = 'credit_card'
        self.payload['transaction_type'] = 'sale'
        self.payload['card_account_number'] = card['number']
        self.payload['card_verification_value'] = card['cvv']
        self.payload['card_expiry_month'] = card['exp_month']
        self.payload['card_expiry_year'] = card['exp_year']
        self.payload['card_type'] = card['type']
        self._execute(assert_status_code=200)
        self.assertEqual('approved', self.response.json()['data'][0].get('result'))

    def test_sale_valid_credit_card_no_cvv(self):
        card = self.test_cards['visa']
        self.payload['client_reference_code'] = self.get_random_number()
        self.payload['tender_type'] = 'credit_card'
        self.payload['transaction_type'] = 'sale'
        self.payload['card_account_number'] = card['number']
        self.payload['card_expiry_month'] = card['exp_month']
        self.payload['card_expiry_year'] = card['exp_year']
        self.payload['card_type'] = card['type']
        self._execute(assert_status_code=200)
        self.assertEqual('approved', self.response.json()['data'][0].get('result'))

    def test_sale_invalid_credit_card(self):
        self.payload['tender_type'] = 'credit_card'
        self.payload['transaction_type'] = 'sale'
        self.payload['card_account_number'] = '1234567890123456'
        self.payload['card_verification_value'] = '123'
        self.payload['card_expiry_month'] = str(timezone.now().strftime('%m'))
        self.payload['card_expiry_year'] = str(timezone.now().strftime('%y'))
        self._execute(assert_status_code=400)

    def test_sale_expired_credit_card(self):
        card = self.test_cards['mastercard']
        self.payload['tender_type'] = 'credit_card'
        self.payload['transaction_type'] = 'sale'
        self.payload['card_account_number'] = card['number']
        self.payload['card_verification_value'] = card['cvv']
        self.payload['card_expiry_month'] = '01'
        self.payload['card_expiry_year'] = '01'
        self.payload['card_type'] = card['type']
        self._execute(assert_status_code=400)

    def test_sale_no_credit_card(self):
        self.payload['tender_type'] = 'credit_card'
        self.payload['transaction_type'] = 'sale'
        self._execute(assert_status_code=400)

    def test_auth_valid_credit_card(self):
        # do auth transaction and test for success
        card = self.test_cards['mastercard']
        self.payload['client_reference_code'] = self.get_random_number()
        self.payload['tender_type'] = 'credit_card'
        self.payload['transaction_type'] = 'authorize'
        self.payload['card_account_number'] = card['number']
        self.payload['card_verification_value'] = card['cvv']
        self.payload['card_expiry_month'] = card['exp_month']
        self.payload['card_expiry_year'] = card['exp_year']
        self.payload['card_type'] = card['type']
        self._execute(assert_status_code=200)
        self.assertEqual('approved', self.response.json()['data'][0].get('result'))

    def test_capture_valid_credit_card(self):
        client_reference_code = self.get_random_number()
        # do auth transaction and test for success
        card = self.test_cards['mastercard']
        self.payload['tender_type'] = 'credit_card'
        self.payload['transaction_type'] = 'authorize'
        self.payload['card_account_number'] = card['number']
        self.payload['card_verification_value'] = card['cvv']
        self.payload['card_expiry_month'] = card['exp_month']
        self.payload['card_expiry_year'] = card['exp_year']
        self.payload['card_type'] = card['type']
        self.payload['client_reference_code'] = client_reference_code
        self._execute(assert_status_code=200)
        self.assertEqual('approved', self.response.json()['data'][0].get('result'))

        # on success, do capture and test for success
        auth_response = self.response.json()
        self.payload = {
            'processor': self.processor,
            'credentials': self.credentials,
            'project_id': self.project_id,
            'mode': self.mode,
            'interaction_id': str(uuid.uuid4()),
            'interaction_type': self.interaction_type,
            'tender_type': 'credit_card',
            'transaction_type': 'capture',
            'amount': self.amount,
            'original_transaction_id': auth_response['data'][0].get('transaction_id'),
            'client_reference_code': client_reference_code
        }
        self._execute(assert_status_code=200)
        self.assertEqual('approved', self.response.json()['data'][0].get('result'))

    def test_void_valid_credit_card(self):
        client_reference_code = self.get_random_number()
        # do auth transaction and test for success
        card = self.test_cards['mastercard']
        self.payload['tender_type'] = 'credit_card'
        self.payload['transaction_type'] = 'authorize'
        self.payload['card_account_number'] = card['number']
        self.payload['card_verification_value'] = card['cvv']
        self.payload['card_expiry_month'] = card['exp_month']
        self.payload['card_expiry_year'] = card['exp_year']
        self.payload['card_type'] = card['type']
        self.payload['client_reference_code'] = client_reference_code
        self._execute(assert_status_code=200)
        self.assertEqual('approved', self.response.json()['data'][0].get('result'))

        # on success, do void and test for success
        auth_response = self.response.json()
        self.payload = {
            'processor': self.processor,
            'credentials': self.credentials,
            'project_id': self.project_id,
            'mode': self.mode,
            'interaction_id': str(uuid.uuid4()),
            'interaction_type': self.interaction_type,
            'tender_type': 'credit_card',
            'transaction_type': 'void',
            'original_transaction_id': auth_response['data'][0].get('transaction_id'),
            'client_reference_code': client_reference_code
        }
        self._execute(assert_status_code=200)
        self.assertEqual('approved', self.response.json()['data'][0].get('result'))

    def test_refund_valid_credit_card(self):
        client_reference_code = self.get_random_number()
        # do sale transaction and test for success
        card = self.test_cards['mastercard']
        self.payload['client_reference_code'] = client_reference_code
        self.payload['tender_type'] = 'credit_card'
        self.payload['transaction_type'] = 'sale'
        self.payload['card_account_number'] = card['number']
        self.payload['card_verification_value'] = card['cvv']
        self.payload['card_expiry_month'] = card['exp_month']
        self.payload['card_expiry_year'] = card['exp_year']
        self.payload['card_type'] = card['type']
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
            'tender_type': 'credit_card',
            'card_account_number': card['number'],
            'card_expiry_month': card['exp_month'],
            'card_expiry_year': card['exp_year'],
            'amount': self.amount,
            'bill_to_first_name': 'John',
            'bill_to_last_name': 'Doe',
            'bill_to_company': 'IVR Technology Group',
            'bill_to_address': '2350 N. Forest Rd',
            'bill_to_city': 'Getzville',
            'bill_to_county': 'Erie',
            'bill_to_state': 'NY',
            'bill_to_zip': '14228',
            'bill_to_country': 'US',
            'bill_to_phone': '7162502800',
            'bill_to_email': 'reporting@ivrtechgroup.com'
        }
        self._execute(assert_status_code=200)
        self.assertEqual('approved', self.response.json()['data'][0].get('result'))

    def test_sale_valid_ach(self, ach_account_number='123456789', ach_routing_number='022000127'):
        self.payload['client_reference_code'] = self.get_random_number()
        self.payload['tender_type'] = 'ach'
        self.payload['transaction_type'] = 'sale'
        self.payload['ach_name_on_account'] = 'John Doe'
        self.payload['ach_account_number'] = ach_account_number
        self.payload['ach_routing_number'] = ach_routing_number
        self.payload['ach_account_type'] = 'checking'
        self.payload['ach_check_number'] = str(random.randint(100, 999))
        self._execute(assert_status_code=200)
        self.assertEqual('approved', self.response.json()['data'][0].get('result'))

    def test_sale_no_ach(self):
        self.payload['tender_type'] = 'ach'
        self.payload['transaction_type'] = 'sale'
        self._execute(assert_status_code=400)

    def test_refund_valid_ach(self, ach_account_number='123456789', ach_routing_number='022000127'):
        client_reference_code = self.get_random_number()
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
            'bill_to_country': 'US',
            'bill_to_phone': '7162502800',
            'bill_to_email': 'reporting@ivrtechgroup.com'
        }
        self._execute(assert_status_code=200)
        self.assertEqual('approved', self.response.json()['data'][0].get('result'))

    def test_authorize_valid_ach(self):
        self.payload['tender_type'] = 'ach'
        self.payload['transaction_type'] = 'authorize'
        self.payload['ach_name_on_account'] = 'John Doe'
        self.payload['ach_account_number'] = '123456789'
        self.payload['ach_routing_number'] = '022000127'
        self.payload['ach_account_type'] = 'checking'
        self.payload['ach_check_number'] = str(random.randint(100, 999))
        self._execute(assert_status_code=400)

    def test_capture_valid_ach(self):
        self.payload['tender_type'] = 'ach'
        self.payload['transaction_type'] = 'capture'
        self.payload['ach_name_on_account'] = 'John Doe'
        self.payload['ach_account_number'] = '123456789'
        self.payload['ach_routing_number'] = '022000127'
        self.payload['ach_account_type'] = 'checking'
        self.payload['ach_check_number'] = str(random.randint(100, 999))
        self._execute(assert_status_code=400)

    def test_void_valid_ach(self):
        self.payload['tender_type'] = 'ach'
        self.payload['transaction_type'] = 'void'
        self.payload['ach_name_on_account'] = 'John Doe'
        self.payload['ach_account_number'] = '123456789'
        self.payload['ach_routing_number'] = '022000127'
        self.payload['ach_account_type'] = 'checking'
        self.payload['ach_check_number'] = str(random.randint(100, 999))
        self._execute(assert_status_code=400)

    @override_settings(APPLY_KONG_MIDDLEWARE={})  # so we don't need extra header for kong middleware during testing
    def _execute(self, assert_status_code=None):
        c = Client()
        self.response = c.post(self.path, json.dumps(self.payload), 'application/json')
        if assert_status_code:
            self.assertEqual(assert_status_code, self.response.status_code, msg=self.response.content.decode('utf-8'))
