import random
import uuid
from unittest import TestCase
from django.utils import timezone
from datetime import datetime
from core_payments.utils import assign_if_not_none

from payments_api.models import PROCESSOR_STRIPE
from . import ProcessorMixin

STRIPE_TEST_MODE_SECRET_KEY = 'sk_test_51He6djFjIuY5rTQI1kpeFTlo0LaNe607cJfZvf8ErAwkWCeLl6almqh1KgCKCHJpNSjluuCuCUWyX8qncC8xy8FK00pUVQKJdQ'


class StripeProcessorTestCase(ProcessorMixin, TestCase):
    processor = PROCESSOR_STRIPE
    credentials = {
        'api_key': STRIPE_TEST_MODE_SECRET_KEY
    }

    def setUp(self):
        super().setUp()
        self.payload['credentials'] = self.credentials
        # populate the payload with some standard test data
        self.populate_payload()

        # we use the credit card numbers the chase API recommends to - so tests work fine
        self.test_cards = {
            'mastercard': {
                'number': '5555555555554444',
                'exp_month': str(timezone.now().strftime('%m')),
                'exp_year': str(int(timezone.now().strftime('%y')) + 1),
                'cvc': '998',
            },
            'visa': {
                'number': '4242424242424242',
                'exp_month': str(timezone.now().strftime('%m')),
                'exp_year': str(int(timezone.now().strftime('%y')) + 1),
                'cvc': '998',
            },
            'invalid': {
                # Live card
                'number': '400005665566555',
                'exp_month': str(timezone.now().strftime('%m')),
                'exp_year': str(int(timezone.now().strftime('%y')) + 1),
                'cvc': '998',
            },
            'expired': {
                'number': '4242424242424242',
                'exp_month': str(timezone.now().strftime('%m')),
                'exp_year': 19,
                'cvc': '998',
            },
            'no_cvc': {
                'number': '4242424242424242',
                'exp_month': str(timezone.now().strftime('%m')),
                'exp_year': 19,
                'cvc': None
            }
        }

        self.test_accounts = {
            'valid': {
                'account_number': '000123456789',
                'routing_number': '110000000',
                'verification_amounts': [32, 45]
            },
            'invalid': {
                'account_number': '00011111111',
                'routing_number': '110000000',
                'verification_amounts': [32, 45]
            }
        }

    def tearDown(self):
        return super().tearDown()
        self.payload = dict()

    def payload_cc(self, card, transaction_type):
        card = self.test_cards[card]
        self.payload['transaction_type'] = transaction_type
        self.payload['client_reference_code'] = self.get_random_number()
        self.payload['tender_type'] = 'credit_card'
        self.payload['card_account_number'] = card['number']
        assign_if_not_none(
            self.payload, 'card_verification_value', card['cvc']
        )
        self.payload['card_expiry_month'] = card['exp_month']
        self.payload['card_expiry_year'] = card['exp_year']
        self.payload["processor"]: self.processor
        self.payload["amount"]: 1000

    def payload_ach(self, transaction_type, account, account_type):
        self.payload['transaction_type'] = transaction_type
        self.payload['ach_account_number'] = account['account_number']
        self.payload['ach_routing_number'] = account['routing_number']
        self.payload['ach_name_on_account'] = 'Roberto Vargas'
        self.payload['ach_account_type'] = account_type
        self.payload['tender_type'] = 'ach'
        self.payload["amount"] = 1000
        self.payload["processor"] = self.processor
        self.payload['client_reference_code'] = self.get_random_number()

    def get_new_payload(self,
                        tender_type,
                        transaction_type,
                        original_transaction_id,
                        client_reference_code,
                        card_account_number):
        return{
            'processor': self.processor,
            'credentials': self.credentials,
            'project_id': self.project_id,
            'mode': self.mode,
            'interaction_id': str(uuid.uuid4()),
            'interaction_type': self.interaction_type,
            'tender_type': tender_type,
            'transaction_type': transaction_type,
            'amount': self.amount,
            'original_transaction_id': original_transaction_id,
            'client_reference_code': client_reference_code,
            'card_account_number': card_account_number
        }

    def test_bad_credentials(self):
        """
        An error response (parsed correctly) is returned when invalid credentials provided
        """
        self.payload['credentials'] = {
            "api_key": "abcdefg123",
        }

        # do auth transaction and test for success
        self.payload_cc('mastercard', 'authorize')
        self.payload['credentials'] = {
            "api_key": "abcdefg123",
        }
        self._execute(assert_status_code=400)

        self.assertEqual('error', self.response.json()
                         ['data'][0].get('result'))

    def test_auth_valid_credit_card(self):
        """
        Authorize a transaction with valid credit card
        """
        # do auth transaction and test for success
        self.payload_cc('mastercard', 'authorize')
        self._execute(assert_status_code=200)

        self.assertEqual('approved', self.response.json()
                         ['data'][0].get('result'))

    def test_capture_valid_credit_card(self):
        """
        Capture transaction with valid credit card
        """
        # do auth transaction and test for success
        self.payload_cc('mastercard', 'authorize')
        self._execute(assert_status_code=200)
        self.assertEqual('approved', self.response.json()
                         ['data'][0].get('result'))

        # on success, do capture and test for success
        auth_response = self.response.json()
        self.payload = self.get_new_payload(
            'credit_card',
            'capture',
            auth_response['data'][0].get('transaction_id'),
            self.payload['client_reference_code'],
            self.test_cards.get('mastercard').get('number')

        )

        amount_in_cents = float(self.amount)*100

        self._execute(assert_status_code=200)
        self.assertEqual('approved', self.response.json()
                         ['data'][0].get('result'))
        self.assertEqual(amount_in_cents, self.response.json()['data'][0].get(
            'processor_response').get('amount_captured'))

    def test_sale_valid_credit_card(self):
        """
        Sales needs to return a success status and an amount captured equal to the original amount
        """
        # do sale transaction and test for success
        self.payload_cc('mastercard', 'sale')
        amount_in_cents = float(self.amount)*100
        self._execute(assert_status_code=200)

        self.assertEqual('approved', self.response.json()
                         ['data'][0].get('result'))
        self.assertEqual(amount_in_cents, self.response.json()['data'][0].get(
            'processor_response').get('amount_captured'))

    def test_sale_invalid_credit_card(self):
        """
        Sale with invalid card returns an error
        """
        # do sale transaction and test for success
        self.payload_cc('invalid', 'sale')
        amount_in_cents = float(self.amount)*100
        self._execute(assert_status_code=400)

        self.assertEqual('error', self.response.json()
                         ['data'][0].get('result'))
 

    def test_sale_expired_credit_card(self):
        """
        Sales needs to return a bad request
        """
        # do sale transaction and test for success
        self.payload_cc('expired', 'sale')
        self._execute(assert_status_code=400)

        self.assertEqual('error', self.response.json()
                         ['data'][0].get('result'))

    def test_sale_valid_credit_card_no_cvv(self):
        """
        Returns an error indicating the cvc is required for CC payments
        """
        # do sale transaction and test for success
        self.payload_cc('no_cvc', 'sale')
        self._execute(assert_status_code=400)

        self.assertEqual('error', self.response.json()
                         ['data'][0].get('result'))

    def test_refund_valid_credit_card(self):
        """
        Refund needs to return a success status and an amount refunded equal to the original amount
        """
        # do sale transaction and test for success
        self.payload_cc('mastercard', 'sale')
        amount_in_cents = float(self.amount)*100
        self._execute(assert_status_code=200)

        self.assertEqual('approved', self.response.json()
                         ['data'][0].get('result'))
        self.assertEqual(amount_in_cents, self.response.json()['data'][0].get(
            'processor_response').get('amount_captured'))

        # on success, do refund and test for success
        auth_response = self.response.json()
        self.payload = self.get_new_payload(
            'credit_card',
            'refund',
            auth_response['data'][0].get('transaction_id'),
            self.payload['client_reference_code'],
            self.test_cards.get('mastercard').get('number')
        )

        amount_in_cents = float(self.amount)*100
        self._execute(assert_status_code=200)
        self.assertEqual(
            'approved',
            self.response.json()['data'][0].get('result')
        )
        self.assertEqual(amount_in_cents, self.response.json()['data'][0].get(
            'processor_response').get('amount'))

    def test_void_valid_credit_card(self):
        """
        Void behavior is the same that refund, but is necessarry to test
        """
        # do sale transaction and test for success
        self.payload_cc('mastercard', 'sale')
        amount_in_cents = float(self.amount)*100
        self._execute(assert_status_code=200)

        self.assertEqual('approved', self.response.json()
                         ['data'][0].get('result'))
        self.assertEqual(amount_in_cents, self.response.json()['data'][0].get(
            'processor_response').get('amount_captured'))

        # on success, do refund and test for success
        auth_response = self.response.json()
        self.payload = self.get_new_payload(
            'credit_card',
            'void',
            auth_response['data'][0].get('transaction_id'),
            self.payload['client_reference_code'],
            self.test_cards.get('mastercard').get('number')
        )

        amount_in_cents = float(self.amount)*100
        self._execute(assert_status_code=200)
        self.assertEqual('approved', self.response.json()
                         ['data'][0].get('result'))
        self.assertEqual(amount_in_cents, self.response.json()['data'][0].get(
            'processor_response').get('amount'))

    def test_client_reference_code_good_request(self):
        """
        A test to ensure client reference code is being passed back on good requests.
        """
        # do auth transaction and test for success
        self.payload_cc('mastercard', 'authorize')
        request_client_reference_code = self.payload['client_reference_code']
        self._execute(assert_status_code=200)

        self.assertEqual('approved', self.response.json()
                         ['data'][0].get('result'))

        self.assertEqual(request_client_reference_code, self.response.json()
                         ['data'][0].get('client_reference_code'))

    def test_original_transaction_id_not_provided(self):
        """
        Original_transaction_id is required for void,refund and capture transactions
        """
        card = self.test_cards['mastercard']
        self.payload['tender_type'] = 'credit_card'
        self.payload['transaction_type'] = 'capture'
        self.payload['card_account_number'] = card['number']
        self.payload['card_verification_value'] = card['cvc']
        self.payload['card_expiry_month'] = card['exp_month']
        self.payload['card_expiry_year'] = card['exp_year']
        self.payload['client_reference_code'] = self.get_random_number()

        self._execute(assert_status_code=400)
        self.assertEqual('error', self.response.json()
                         ['data'][0].get('result'))
        self.assertEqual("detail: ['original_transaction_id is required for void, capture and refund transactions in the provided processor ({}).']".format(self.processor),
                         self.response.json()['metadata'].get('errors', [''])[0])

    def test_invoice_number_provided(self):
        """
        invoice_number is not supported by the provided processor
        """
        # do auth transaction and test for success
        self.payload_cc('mastercard', 'authorize')
        self.payload['invoice_number'] = 'A1234b5Q612'
        self._execute(assert_status_code=400)

        self.assertEqual('error', self.response.json()
                         ['data'][0].get('result'))
        self.assertEqual("detail: ['invoice_number is not supported in the provided processor ({}).']".format(
            self.processor), self.response.json()['metadata'].get('errors', [''])[0])

    def test_sale_valid_ach(self):
        """Sale transaction with valid account"""
        self.payload_ach('sale', self.test_accounts['valid'], 'individual')
        self._execute(assert_status_code=200)

        self.assertEqual('approved', self.response.json()
                         ['data'][0].get('result'))

    def test_sale_invalid_ach(self):
        """Sale transaction with invalid account"""
        self.payload_ach('sale', self.test_accounts['invalid'], 'individual')
        self._execute(assert_status_code=400)

        self.assertEqual('error', self.response.json()
                         ['data'][0].get('result'))

    def test_refund_valid_ach(self):
        """Refund transaction with valid account"""
        self.payload_ach('sale', self.test_accounts['valid'], 'individual')
        self._execute(assert_status_code=200)

        self.assertEqual('approved', self.response.json()
                         ['data'][0].get('result'))

        # on success, do refund and test for success
        sale_response = self.response.json()
        self.payload_ach('refund', self.test_accounts['valid'], 'individual')
        self.payload["original_transaction_id"] = sale_response['data'][0].get(
            'transaction_id')

        self._execute(assert_status_code=200)
        self.assertEqual(
            'approved',
            self.response.json()['data'][0].get('result')
        )

    def test_required_bill_to_first_name_ach(self):
        """
        bill_to_first_name is required for ACH transactions
        """
        self.payload = {
            'processor': self.processor,
            'credentials': self.credentials,
            'mode': self.mode,
            'interaction_id': str(uuid.uuid4()),
            'interaction_type': self.interaction_type,
            'transaction_type': 'sale',
            'ach_account_number': self.test_accounts['valid']['account_number'],
            'ach_routing_number': self.test_accounts['valid']['routing_number'],
            'ach_name_on_account': 'Roberto Vargas',
            'ach_account_type': 'individual',
            'tender_type': "ach",
            'amount': self.amount,
            'bill_to_last_name': "Vargas"
        }
        self._execute(assert_status_code=400)
        self.assertEqual('error', self.response.json()
                         ['data'][0].get('result'))

        self.assertEqual("detail: ['bill_to_first_name is required for ACH transactions in the provided processor ({}).']".format(self.processor),
                         self.response.json()['metadata'].get('errors', [''])[0])

    def test_required_bill_to_last_name_ach(self):
        """
        bill_to_last_name is required for ACH transactions
        """
        self.payload = {
            'processor': self.processor,
            'credentials': self.credentials,
            'mode': self.mode,
            'interaction_id': str(uuid.uuid4()),
            'interaction_type': self.interaction_type,
            'transaction_type': 'sale',
            'ach_account_number': self.test_accounts['valid']['account_number'],
            'ach_routing_number': self.test_accounts['valid']['routing_number'],
            'ach_name_on_account': 'Roberto Vargas',
            'ach_account_type': 'individual',
            'tender_type': "ach",
            'amount': self.amount,
            'bill_to_first_name': "Rob"
        }
        self._execute(assert_status_code=400)
        self.assertEqual('error', self.response.json()
                         ['data'][0].get('result'))
        self.assertEqual("detail: ['bill_to_last_name is required for ACH transactions in the provided processor ({}).']".format(self.processor),
                         self.response.json()['metadata'].get('errors', [''])[0])

    def test_required_name_on_account_ach(self):
        """
        ach_name_on_account is required for ACH transactions
        """
        self.payload = {
            'processor': self.processor,
            'credentials': self.credentials,
            'mode': self.mode,
            'interaction_id': str(uuid.uuid4()),
            'interaction_type': self.interaction_type,
            'transaction_type': 'sale',
            'ach_account_number': self.test_accounts['valid']['account_number'],
            'ach_routing_number': self.test_accounts['valid']['routing_number'],
            'ach_account_type': 'individual',
            'tender_type': "ach",
            'amount': self.amount,
            'bill_to_first_name': "Rob",
            'bill_to_last_name': "Vargas"
        }
        self._execute(assert_status_code=400)
        self.assertEqual('error', self.response.json()
                         ['data'][0].get('result'))
        self.assertEqual("detail: ['ach_name_on_account is required for ACH transactions in the provided processor ({}).']".format(self.processor),
                         self.response.json()['metadata'].get('errors', [''])[0])

    def test_different_account_type(self):
        """
        ach_name_on_account is required for ACH transactions
        """
        self.payload_ach('sale', self.test_accounts['invalid'], 'savings')

        self._execute(assert_status_code=400)
        self.assertEqual('error', self.response.json()
                         ['data'][0].get('result'))
        self.assertEqual("detail: ['ach_account_type must be individual or company in the provided processor ({}).']".format(self.processor),
                         self.response.json()['metadata'].get('errors', [''])[0])
