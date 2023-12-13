import random
import uuid
from unittest import TestCase
from django.utils import timezone
from datetime import datetime
from core_payments.utils import assign_if_not_none

from payments_api.models import PROCESSOR_CYBERSOURCE
from . import ProcessorMixin

TRANSACTION_KEY = 'HSTuCJ5Kcc+XAwDw3hc2tkNEHQtzlM96QmWer3uEoInw30rmuM47jwEkUbJwRqhpXukYQ8pQ79bSVUoOGmXOZDalG5CPyL2fPqekiWP9dBTXIq/HgEmvIlA1U+q/ycjsc4wl2AkjeE15jQ3PLCtKLYtwFiekdOuz26J4PVsVkWVSp2btIso0Npi/LlTg/28GbTBVVVVsVAmm6guu0hqiZScZwjFuuOZBIdEN3pNF0EngPIhdoWkTFC/GUUV7ohoECOPN+47ayHBHzAH3ufCrvAQ2aJ71Xi4GELNDGIXNH6c4OyB0RtbA4jbu+x7CZ4bZsBaEwE+A3tDk3Y9E9O3Dbw=='


class CybersourceProcessorTestCase(ProcessorMixin, TestCase):
    processor = PROCESSOR_CYBERSOURCE
    credentials = {
        'merchant_id': "test_roberto",
        'transaction_key': TRANSACTION_KEY
    }

    ach_credentials = {
        'merchant_id': 'evalitgivr',
        'transaction_key': 'MKT5OJYDKO0wkKa+jEsqNy8XAoPAFaignmpNBSvL7DreLhznf5fq51qV5eGDPjQSwlODJJUQ5PXRyeHuu6f7wxLed7DWT1kwT86n1o+CRcd3PvaNNvM8xv1LuzpW0j0vHFzxuf8pGQ3JNsKWBo6PbCRDuqf6GhkSWfKQPKYOBEs55x0H1y8QLoL5L+4bYtt1Y5cC6G3hKBcUYT2NDurDlwhW79E0/sVvtKvCpnN3BMknJPtbfopOupRos3+eTbaYe5wHnxbGn6D/ahFtDghQR0O9s7cjRNyE4/8syPGqlZr9LG63xjunUt9n4H9QrjpoJ0HiLY2SVYEnoWEep1NEBQ=='
    }

    def setUp(self):
        super().setUp()
        self.payload = {
            "client_reference_code":'mrf-123456789',
            "bill_to_country": "CR",
            "bill_to_city": "SAN JOSE",
            "bill_to_state": "SAN JOSE",
            "bill_to_last_name": "Vargas",
            "bill_to_first_name": "Rob",
            "bill_to_email": "r@mail.com",
            "bill_to_address": "Location",
            "bill_to_zip": "10555",
            'bill_to_phone': '9162502800'
        }
        self.payload['credentials'] = self.credentials

        # we use the credit card numbers the chase API recommends to - so tests work fine
        self.test_cards = {
            'visa': {
                'number': '4622943127013705',
                'exp_month': 12,
                'exp_year': 22,
                'cvc': '838',
                'type': 'visa'
            },
            'visa_2': {
                'number': '4622943127013713',
                'exp_month': 12,
                'exp_year': 22,
                'cvc': '043',
                'type': 'visa'
            },
            'invalid': {
                'number': '42423482938483873',
                'exp_month': str(timezone.now().strftime('%m')),
                'exp_year': str(int(timezone.now().strftime('%y')) + 1),
                'cvc': '998',
                'type': 'visa'
            },
            'expired': {
                'number': '2222630000001125',
                'exp_month': str(timezone.now().strftime('%m')),
                'exp_year': 19,
                'cvc': '998',
                'type': 'visa'
            },
            'no_cvc': {
                'number': '2222 6300 0000 1125',
                'exp_month': str(timezone.now().strftime('%m')),
                'exp_year': 19,
                'cvc': None,
                'type': 'visa'
            }
        }

        self.test_accounts = {
            'valid': {
                'account_number': '4100',
                'routing_number': '121042882',
                'type': 'checking'
            },
            'invalid': {
                'account_number': '1111',
                'routing_number': '121107882',
                'type': 'savings'
            }
        }

    def tearDown(self):
        return super().tearDown()
        self.payload = dict()

    def payload_meta(self, transaction_type, tender_type):
        """Setups the common fields for each transaction"""
        self.payload['transaction_type'] = transaction_type
        self.payload['tender_type'] = tender_type
        self.payload['client_reference_code'] = self.get_random_number()
        self.payload["processor"] = self.processor
        self.payload["amount"] = 1000
        self.payload['project_id'] = self.project_id
        self.payload['mode'] = self.mode
        self.payload['interaction_id'] = str(uuid.uuid4())
        self.payload['interaction_type'] = self.interaction_type
        self.payload['customer_id'] = self.get_random_number()
        self.payload['client_reference_code'] = self.get_random_number()

    def payload_cc(self, card):
        """Setups the information for CC transactions"""
        card = self.test_cards[card]
        self.payload['card_account_number'] = card['number']
        assign_if_not_none(
            self.payload, 'card_verification_value', card['cvc']
        )
        self.payload['card_expiry_month'] = card['exp_month']
        self.payload['card_expiry_year'] = card['exp_year']
        self.payload['card_type'] = card['type']

    def payload_ach(self, account):
        """Setups the information for CC transactions"""
        self.payload['ach_account_number'] = account['account_number']
        self.payload['ach_routing_number'] = account['routing_number']
        self.payload['ach_name_on_account'] = 'Roberto Vargas'
        self.payload['ach_account_type'] = account['type']

    def get_new_payload(self,
                        tender_type,
                        transaction_type,
                        original_transaction_id,
                        client_reference_code,
                        card_account_number,
                        ):
        """Returns a new payload to use in a second transaction in tests"""
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
            'card_account_number': card_account_number,
            "bill_to_country": "CR",
            "bill_to_city": "SAN JOSE",
            "bill_to_state": "SAN JOSE",
            "bill_to_last_name": "Vargas",
            "bill_to_first_name": "Rob",
            "bill_to_email": "r@mail.com",
            "bill_to_address": "Location",
            "bill_to_zip": "10555",
            'bill_to_phone': '9162502800'
        }

    def test_bad_credentials(self):
        """
        An error response (parsed correctly) is returned when invalid credentials provided
        """
        # do auth transaction and test for success
        self.payload_meta('authorize', 'credit_card')
        self.payload_cc('visa')
        self.payload['credentials'] = {
            'transaction_key': TRANSACTION_KEY,
            'merchant_id': "test"
        }
        self._execute(assert_status_code=400)

        self.assertEqual('error', self.response.json()
                         ['data'][0].get('result'))

    def test_client_reference_code_good_request(self):
        """
        A test to ensure client reference code is being passed back on good requests.
        """
        # do auth transaction and test for success
        self.payload_meta('sale', 'credit_card')
        self.payload_cc('visa')
        request_client_reference_code = self.payload['client_reference_code']
        self._execute(assert_status_code=200)

        self.assertEqual('approved', self.response.json()
                         ['data'][0].get('result'))

        self.assertEqual(request_client_reference_code, self.response.json()
                         ['data'][0].get('client_reference_code'))

    def test_auth_valid_credit_card(self):
        """
        Authorize a transaction with valid credit card
        """
        # do auth transaction and test for success
        self.payload_meta('authorize', 'credit_card')
        self.payload_cc('visa')
        self._execute(assert_status_code=200)

        self.assertEqual('approved', self.response.json()
                         ['data'][0].get('result'))

    def test_capture_valid_credit_card(self):
        """
        Capture transaction with valid credit card
        """
        # do auth transaction and test for success
        self.payload_meta('authorize', 'credit_card')
        self.payload_cc('visa')
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
            self.test_cards.get('visa').get('number')

        )
        self._execute(assert_status_code=200)
        self.assertEqual('approved', self.response.json()['data'][0].get('result'))
        self.assertEqual(100, self.response.json()['data'][0].get('processor_response').get('reasonCode'))

    def test_sale_valid_credit_card(self):
        """
        Sale needs to return a success status and an amount captured equal to the original amount in valid transactions
        """
        # do sale transaction and test for success
        self.payload_meta('sale', 'credit_card')
        self.payload_cc('visa')
        self._execute(assert_status_code=200)

        self.assertEqual('approved', self.response.json()['data'][0].get('result'))
        self.assertEqual(100, self.response.json()['data'][0].get('processor_response').get('reasonCode'))

    def test_sale_invalid_credit_card(self):
        """
        Sale with invalid card returns an error
        """
        # do sale transaction and test for success
        self.payload_meta('sale', 'credit_card')
        self.payload_cc('invalid')
        self._execute(assert_status_code=400)

        self.assertEqual('declined', self.response.json()['data'][0].get('result'))

    def test_sale_expired_credit_card(self):
        """
        Sale needs to return a bad request if  expired card is used
        """
        # do sale transaction and test for success
        self.payload_meta('sale', 'credit_card')
        self.payload_cc('expired')
        self._execute(assert_status_code=400)

        self.assertEqual('error', self.response.json()['data'][0].get('result'))

    def test_sale_valid_credit_card_no_cvv(self):
        """
        Returns an error indicating the cvc is required for CC payments
        """
        # do sale transaction and test for success
        self.payload_meta('sale', 'credit_card')
        self.payload_cc('no_cvc')
        self._execute(assert_status_code=400)

        self.assertEqual('error', self.response.json()['data'][0].get('result'))

    def test_void_valid_credit_card(self):
        """
        A special test case for voiding credit card transactions in Cybersource.
        https://stackoverflow.com/a/13870343/399435

        The way the CyberSource Test Environment is configured, it does not permit voids to take place.
        The reason for this is a 'void' simply prevents a transaction from being batched out.
        However, in the Test Environment, there is no batching of transactions.
        As a result, you are unable to void any orders in the Test Environment.
        """
        # do auth transaction and test for success
        self.payload_meta('authorize', 'credit_card')
        self.payload_cc('visa')
        self._execute(assert_status_code=200)

        self.assertEqual('approved', self.response.json()['data'][0].get('result'))
        self.assertEqual(100, self.response.json()['data'][0].get('processor_response').get('reasonCode'))

        # on success, do refund and test for success
        auth_response = self.response.json()
        self.payload = self.get_new_payload(
            'credit_card',
            'void',
            auth_response['data'][0].get('transaction_id'),
            self.payload['client_reference_code'],
            self.test_cards.get('visa').get('number')
        )
        self._execute(assert_status_code=400)
        self.assertEqual('declined', self.response.json()['data'][0].get('result'))

    def test_refund_valid_credit_card(self):
        """
        Refund needs to return a success status and an reason code equals to 100
        """
        # do sale transaction and test for success
        self.payload = {
            "mode": "test",
            "interaction_type": self.interaction_type,
            "processor": self.processor,
            "transaction_type": "sale",
            "credentials": self.credentials,
            "tender_type": "credit_card",
            "amount": 1000,
            "client_reference_code":'mrf-123456789',
            "card_account_number": self.test_cards.get('visa_2').get('number'),
            "card_expiry_month": self.test_cards.get('visa_2').get('exp_month'),
            "card_expiry_year": self.test_cards.get('visa_2').get('exp_year'),
            "card_verification_value": self.test_cards.get('visa_2').get('cvc'),
            "card_type": self.test_cards.get('visa_2').get('type'),
            "bill_to_country": "CR",
            "bill_to_city": "SAN JOSE",
            "bill_to_state": "SAN JOSE",
            "bill_to_last_name": "Vargas",
            "bill_to_first_name": "Rob",
            "bill_to_email": "r@mail.com",
            "bill_to_address": "Location",
            "bill_to_zip": "10555",
            'bill_to_phone': '9162502800'
        }
        self._execute(assert_status_code=200)

        self.assertEqual('approved', self.response.json()['data'][0].get('result'))
        self.assertEqual(100, self.response.json()['data'][0].get('processor_response').get('reasonCode'))

        # on success, do refund and test for success
        sale_response = self.response.json()

        self.payload = {
            "client_reference_code":'mrf-123456789',
            "mode": "test",
            "interaction_type": self.interaction_type,
            "processor": self.processor,
            "transaction_type": "refund",
            "credentials": self.credentials,
            "original_transaction_id": sale_response['data'][0].get('transaction_id'),
            "tender_type": "credit_card",
            "amount": 1000,
            "card_account_number": self.test_cards.get('visa_2').get('number')
        }

        self._execute(assert_status_code=200)
        self.assertEqual('approved', self.response.json()['data'][0].get('result'))
        self.assertEqual(100, self.response.json()['data'][0].get('processor_response').get('reasonCode'))

    def test_original_transaction_id_not_provided(self):
        """
        Original_transaction_id is required for void and capture transactions
        """
        self.payload_meta('capture', 'credit_card')
        card = self.test_cards['visa']
        self.payload['tender_type'] = 'credit_card'
        self.payload['card_account_number'] = card['number']
        self.payload['card_verification_value'] = card['cvc']
        self.payload['card_expiry_month'] = card['exp_month']
        self.payload['card_expiry_year'] = card['exp_year']
        self.payload['client_reference_code'] = self.get_random_number()
        self._execute(assert_status_code=400)
        self.assertEqual('error', self.response.json()['data'][0].get('result'))
        expected_message = "detail: ['original_transaction_id is required for void and capture transactions.']".format(self.processor)
        self.assertEqual(expected_message, self.response.json()['metadata'].get('errors', [''])[0])

    def test_invoice_number_provided(self):
        """
        invoice_number is not supported by the provided processor
        """
        # do auth transaction and test for success
        self.payload_meta('capture', 'credit_card')
        self.payload_cc('visa')
        self.payload['invoice_number'] = 'A1234b5Q612'
        self._execute(assert_status_code=400)
        self.assertEqual('error', self.response.json()['data'][0].get('result'))
        expected_message = "detail: ['invoice_number is not supported in the provided processor ({}).']".format(self.processor)
        self.assertEqual(expected_message, self.response.json()['metadata'].get('errors', [''])[0])

    def test_sale_valid_ach(self):
        """Sale transaction with valid account"""
        self.payload = {
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
        }
        self.payload_meta('sale', 'ach')
        self.payload_ach(self.test_accounts['valid'])
        self.payload['credentials'] = self.ach_credentials
        self._execute(assert_status_code=200)
        self.assertEqual('approved', self.response.json()['data'][0].get('result'))

    def test_sale_invalid_ach(self):
        """Sale transaction with invalid account"""
        self.payload = {
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
        }
        self.payload_meta('sale', 'ach')
        self.payload_ach(self.test_accounts['invalid'])
        self._execute(assert_status_code=400)

        self.assertEqual('error', self.response.json()['data'][0].get('result'))

    def test_refund_valid_ach(self):
        """Refund transaction with valid account"""
        self.payload = {
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
        }
        self.payload_meta('sale', 'ach')
        self.payload_ach(self.test_accounts['valid'])
        self.payload['credentials'] = self.ach_credentials
        self._execute(assert_status_code=200)

        self.assertEqual('approved', self.response.json()['data'][0].get('result'))

        # on success, do refund and test for success
        sale_response = self.response.json()
        self.payload_meta('refund', 'ach')
        self.payload_ach(self.test_accounts['valid'])
        self.payload["original_transaction_id"] = sale_response['data'][0].get('transaction_id')

        self._execute(assert_status_code=200)
        self.assertEqual('approved',self.response.json()['data'][0].get('result')
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
            'ach_account_type': 'savings',
            'tender_type': "ach",
            'amount': self.amount,
            'bill_to_country': "CR",
            'bill_to_city': "SAN JOSE",
            'bill_to_state': "SAN JOSE",
            'bill_to_last_name': "Vargas",
            'bill_to_email': "r@mail.com",
            'bill_to_address': "Location",
            'bill_to_zip': "10555",
            'bill_to_phone': '9162502800'
        }
        self._execute(assert_status_code=400)
        self.assertEqual('error', self.response.json()['data'][0].get('result'))

        expected_result = "detail: ['`bill_to_first_name`, `bill_to_last_name`, `bill_to_email`, `bill_to_country`, `bill_to_city`, `bill_to_state`, `bill_to_zip`, `bill_to_address`, `bill_to_phone` are required for ACH and CC transactions in the provided processor ({}).']".format(self.processor)
        are_equals = expected_result == self.response.json()['metadata'].get('errors', [''])[0]

        self.assertTrue(are_equals)

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
            'ach_account_type': 'savings',
            'tender_type': "ach",
            'amount': self.amount,
            "bill_to_country": "CR",
            "bill_to_city": "SAN JOSE",
            "bill_to_state": "SAN JOSE",
            "bill_to_first_name": "Rob",
            "bill_to_email": "r@mail.com",
            "bill_to_address": "Location",
            "bill_to_zip": "10555",
            "bill_to_phone": '9162502800'
        }
        self._execute(assert_status_code=400)
        self.assertEqual('error', self.response.json()
                         ['data'][0].get('result'))

        expected_result = "detail: ['`bill_to_first_name`, `bill_to_last_name`, `bill_to_email`, `bill_to_country`, `bill_to_city`, `bill_to_state`, `bill_to_zip`, `bill_to_address`, `bill_to_phone` are required for ACH and CC transactions in the provided processor ({}).']".format(self.processor)
        are_equals = expected_result == self.response.json()['metadata'].get('errors', [''])[0]

        self.assertTrue(are_equals)

    def test_different_account_type(self):
        """
        ach_account_type must be savings , checking or corporate 
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
            "bill_to_country": "CR",
            "bill_to_city": "SAN JOSE",
            "bill_to_state": "SAN JOSE",
            "bill_to_last_name": "Vargas",
            "bill_to_first_name": "Rob",
            "bill_to_email": "r@mail.com",
            "bill_to_address": "Location",
            "bill_to_zip": "10555",
            'bill_to_phone': '9162502800'
        }

        self._execute(assert_status_code=400)
        self.assertEqual('error', self.response.json()['data'][0].get('result'))
        self.assertEqual("detail: ['ach_account_type must be savings , checking or corporate in the provided processor ({}).']".format(self.processor),self.response.json()['metadata'].get('errors', [''])[0])

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
            "bill_to_country": "CR",
            "bill_to_city": "SAN JOSE",
            "bill_to_state": "SAN JOSE",
            "bill_to_last_name": "Vargas",
            "bill_to_first_name": "Rob",
            "bill_to_email": "r@mail.com",
            "bill_to_address": "Location",
            "bill_to_zip": "10555",
            'bill_to_phone': '9162502800'
        }
        self._execute(assert_status_code=400)
        self.assertEqual('error', self.response.json()['data'][0].get('result'))
        self.assertEqual("detail: ['ach_name_on_account is required for ACH transactions in the provided processor ({}).']".format(self.processor),self.response.json()['metadata'].get('errors', [''])[0])
