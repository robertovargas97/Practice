import random
import uuid
from unittest import TestCase
from django.utils import timezone

from payments_api.models import PROCESSOR_CHASE
from . import ProcessorMixin


class ChaseProcessorTestCase(ProcessorMixin, TestCase):
    processor = PROCESSOR_CHASE
    credentials = {
        "username": "T1559IVR",
        "password": "Z8Zhn7l7",
        "merchant_id": "041756",
        "terminal_id": "001"
    }

    def setUp(self):
        super().setUp()
        self.payload['credentials'] = self.credentials
        # populate the payload with some standard test data
        self.populate_payload()

        # we use the credit card numbers the chase API recommends to - so tests work fine
        self.test_cards = {
            'mastercard': {
                'number': '5116561111111119',
                'exp_month': str(timezone.now().strftime('%m')),
                'exp_year': str(int(timezone.now().strftime('%y')) + 1),
                'cvv': '998',
                'type': 'mastercard'
            },
            'visa': {
                'number': '4077041111111112',
                'exp_month': str(timezone.now().strftime('%m')),
                'exp_year': str(int(timezone.now().strftime('%y')) + 1),
                'cvv': '998',
                'type': 'visa'
            }
        }

    def test_auth_valid_credit_card(self):
        """
        Authorize requires the field invoice_number to be present
        """
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
        self.payload['invoice_number'] = self.get_random_number()
        self._execute(assert_status_code=200)
        self.assertEqual('approved', self.response.json()['data'][0].get('result'))

    def test_capture_valid_credit_card(self):
        """
        Both authorize and capture needs to have same orderID (invoice_number) field setup for this processor
        in order to be successful
        """
        client_reference_code = self.get_random_number()
        invoice_number = self.get_random_number()

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
        self.payload['invoice_number'] = invoice_number
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
            'client_reference_code': client_reference_code,
            'invoice_number': invoice_number
        }
        self._execute(assert_status_code=200)
        self.assertEqual('approved', self.response.json()['data'][0].get('result'))

    def test_authorize_invoice_number_not_provided(self):
        """
        Both authorize and capture needs to have same invoice number (orderID) field setup for this processor, if not
        an error is raised.  Because of this we have invoice_number as required for capture and authorize transactions
        """
        card = self.test_cards['visa']
        self.payload['tender_type'] = 'credit_card'
        self.payload['transaction_type'] = 'authorize'
        self.payload['card_account_number'] = card['number']
        self.payload['card_verification_value'] = card['cvv']
        self.payload['card_expiry_month'] = card['exp_month']
        self.payload['card_expiry_year'] = card['exp_year']
        self.payload['card_type'] = card['type']
        self.payload['client_reference_code'] = self.get_random_number()
        self._execute(assert_status_code=400)
        self.assertEqual('error', self.response.json()['data'][0].get('result'))
        self.assertEqual("detail: ['invoice_number is required for capture and authorize transactions and it should "
                         "be the same for both (when capturing an authorized transaction).']",
                         self.response.json()['metadata'].get('errors', [''])[0])

    def test_capture_invoice_number_not_provided(self):
        """
        Both authorize and capture needs to have same invoice number (orderID) field setup for this processor, if not
        an error is raised.  Because of this we have invoice_number as required for capture and authorize transactions
        """
        client_reference_code = self.get_random_number()
        invoice_number = self.get_random_number()

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
        self.payload['invoice_number'] = invoice_number
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
        self._execute(assert_status_code=400)
        self.assertEqual('error', self.response.json()['data'][0].get('result'))
        self.assertEqual("detail: ['invoice_number is required for capture and authorize transactions and it should "
                         "be the same for both (when capturing an authorized transaction).']",
                         self.response.json()['metadata'].get('errors', [''])[0])

    def test_void_ach_sale(self):
        """
        If the original_transaction_id is from an ACH transaction it still can be voided in this processor
        """
        client_reference_code = str(random.randint(1000000000, 9999999999))

        # do sale transaction and test for success
        self.payload['client_reference_code'] = client_reference_code
        self.payload['tender_type'] = 'ach'
        self.payload['transaction_type'] = 'sale'
        self.payload['ach_name_on_account'] = 'John Doe'
        self.payload['ach_account_number'] = '123456789'
        self.payload['ach_routing_number'] = '022000127'
        self.payload['ach_account_type'] = 'checking'
        self.payload['ach_check_number'] = str(random.randint(100, 999))
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
            'transaction_type': 'void',
            'original_transaction_id': auth_response['data'][0].get('transaction_id'),
            'client_reference_code': client_reference_code
        }
        self._execute(assert_status_code=200)
        self.assertEqual('approved', self.response.json()['data'][0].get('result'))

    def test_void_valid_credit_card(self):
        """
        invoice_number field is required for authorize transactions in this processor
        """
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
        self.payload['invoice_number'] = self.get_random_number()
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

    def test_void_error(self):
        """
        Void is a special case in this processor, you cannot void a refund credit card transaction but know
        we got an error programmatically is hard because of the status hierarchy they have, so we test we are
        returning errors correctly in this case
        """
        client_reference_code = str(random.randint(1000000000, 9999999999))

        # do refund transaction and test for success
        card = self.test_cards['mastercard']
        self.payload['tender_type'] = 'credit_card'
        self.payload['transaction_type'] = 'refund'
        self.payload['card_account_number'] = card['number']
        self.payload['card_verification_value'] = card['cvv']
        self.payload['card_expiry_month'] = card['exp_month']
        self.payload['card_expiry_year'] = card['exp_year']
        self.payload['card_type'] = card['type']
        self.payload['client_reference_code'] = client_reference_code
        self._execute(assert_status_code=200)
        self.assertEqual('approved', self.response.json()['data'][0].get('result'))

        # on success, do void and test for error
        auth_response = self.response.json()
        self.payload = {
            'processor': self.processor,
            'credentials': self.credentials,
            'project_id': self.project_id,
            'mode': self.mode,
            'interaction_id': str(uuid.uuid4()),
            'interaction_type': self.interaction_type,
            'transaction_type': 'void',
            'original_transaction_id': auth_response['data'][0].get('transaction_id'),
            'client_reference_code': client_reference_code
        }
        self._execute(assert_status_code=400)
        self.assertEqual('error', self.response.json()['data'][0].get('result'))
        self.assertNotIn(self.response.json()['data'][0].get('processor_response').get('respCode'), ['00', None])

    def test_original_transaction_id_not_provided(self):
        """
        Original_transaction_id is required for void and capture transactions
        """
        card = self.test_cards['mastercard']
        self.payload['tender_type'] = 'credit_card'
        self.payload['transaction_type'] = 'capture'
        self.payload['card_account_number'] = card['number']
        self.payload['card_verification_value'] = card['cvv']
        self.payload['card_expiry_month'] = card['exp_month']
        self.payload['card_expiry_year'] = card['exp_year']
        self.payload['card_type'] = card['type']
        self.payload['client_reference_code'] = self.get_random_number()
        self._execute(assert_status_code=400)
        self.assertEqual('error', self.response.json()['data'][0].get('result'))
        self.assertEqual("detail: ['original_transaction_id is required for void and capture transactions.']",
                         self.response.json()['metadata'].get('errors', [''])[0])

    def test_bad_credentials(self):
        """
        An error response (parsed correctly) is returned when invalid credentials provided
        """
        self.payload['credentials'] = {
            "username": "abcdefg123",
            "password": "578IO994",
            "merchant_id": "041756",
            "terminal_id": "001"
        }
        client_reference_code = str(random.randint(1000000000, 9999999999))
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

    def test_supported_invoice_number(self):
        """
        Invoice number is supported everywhere - it will be orderID in the processor
        """
        card = self.test_cards['visa']
        invoice_number = '1235354ab878a'
        self.payload = {
            'processor': self.processor,
            'credentials': self.credentials,
            'mode': self.mode,
            'interaction_id': str(uuid.uuid4()),
            'interaction_type': self.interaction_type,
            'transaction_type': 'sale',
            'tender_type': 'credit_card',
            'card_account_number': card['number'],
            'card_expiry_month': card['exp_month'],
            'card_expiry_year': card['exp_year'],
            'card_verification_value': card['cvv'],
            'amount': self.amount,
            'invoice_number': invoice_number
        }
        self._execute(assert_status_code=200)
        self.assertEqual('approved', self.response.json()['data'][0].get('result'))
        self.assertEqual(invoice_number, self.response.json()['data'][0].get('processor_response').get('orderID'))

    def test_not_supported_description(self):
        """
        Description is not supported by any transaction type in this processor
        """
        card = self.test_cards['mastercard']
        self.payload = {
            'processor': self.processor,
            'credentials': self.credentials,
            'mode': self.mode,
            'interaction_id': str(uuid.uuid4()),
            'interaction_type': self.interaction_type,
            'transaction_type': 'sale',
            'tender_type': 'credit_card',
            'card_account_number': card['number'],
            'card_expiry_month': card['exp_month'],
            'card_expiry_year': card['exp_year'],
            'amount': self.amount,
            'description': 'Integration Test',
        }
        self._execute(assert_status_code=400)
        self.assertEqual('error', self.response.json()['data'][0].get('result'))

    def test_setup_default_order_id_if_not_provided(self):
        """
        orderID is a required field in the processor (we get an error if not provided) - if invoice number is not
        provided then we send a default value, based on the interaction id, and we still have an approved transaction
        """
        card = self.test_cards['mastercard']
        interaction_id = str(uuid.uuid4())
        self.payload = {
            'processor': self.processor,
            'credentials': self.credentials,
            'mode': self.mode,
            'interaction_id': interaction_id,
            'interaction_type': self.interaction_type,
            'transaction_type': 'sale',
            'tender_type': 'credit_card',
            'card_account_number': card['number'],
            'card_expiry_month': card['exp_month'],
            'card_expiry_year': card['exp_year'],
            'amount': self.amount
        }
        self._execute(assert_status_code=200)
        self.assertEqual('approved', self.response.json()['data'][0].get('result'))
        self.assertIsNotNone(self.response.json()['data'][0].get('processor_response').get('orderID'))
        self.assertIn(self.response.json()['data'][0].get('processor_response').get('orderID'), interaction_id)

    def test_required_interaction_id(self):
        """
        interaction id is required in this processor, since it will be used for orderID when no invoice number provided
        and orderID is a required field - if none of them are provided then we won't have what to send
        """
        card = self.test_cards['visa']
        self.payload = {
            'processor': self.processor,
            'credentials': self.credentials,
            'mode': self.mode,
            'interaction_type': self.interaction_type,
            'transaction_type': 'sale',
            'tender_type': 'credit_card',
            'card_account_number': card['number'],
            'card_expiry_month': card['exp_month'],
            'card_expiry_year': card['exp_year'],
            'card_verification_value': card['cvv'],
            'amount': self.amount
        }
        self._execute(assert_status_code=400)
        self.assertEqual('error', self.response.json()['data'][0].get('result'))
        self.assertEqual("detail: ['interaction_id is required by the provided processor.']",
                         self.response.json()['metadata'].get('errors', [''])[0])

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
            'ach_account_number': '123456789',
            'ach_routing_number': '022000127',
            'ach_account_type': 'checking',
            'tender_type': 'ach',
            'amount': self.amount
        }
        self._execute(assert_status_code=400)
        self.assertEqual('error', self.response.json()['data'][0].get('result'))
        self.assertEqual("detail: ['bill_to_first_name is required for ACH transactions in the provided processor.']",
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
            'ach_account_number': '123456789',
            'ach_routing_number': '022000127',
            'ach_account_type': 'checking',
            'tender_type': "ach",
            'amount': self.amount,
            'bill_to_first_name': "Joe"
        }
        self._execute(assert_status_code=400)
        self.assertEqual('error', self.response.json()['data'][0].get('result'))
        self.assertEqual("detail: ['bill_to_last_name is required for ACH transactions in the provided processor.']",
                         self.response.json()['metadata'].get('errors', [''])[0])

    def test_required_card_expiry_cc_sale(self):
        card = self.test_cards['mastercard']
        self.payload = {
            'processor': self.processor,
            'credentials': self.credentials,
            'mode': self.mode,
            'interaction_id': str(uuid.uuid4()),
            'interaction_type': self.interaction_type,
            'transaction_type': 'sale',
            'tender_type': 'credit_card',
            'card_account_number': card['number'],
            'amount': self.amount,
            'description': 'Integration Test',
            'invoice_number': self.get_random_number()
        }
        self._execute(assert_status_code=400)
        self.assertEqual('error', self.response.json()['data'][0].get('result'))
        self.assertEqual("detail: ['card_expiry_month and card_expiry_year are required for CC transactions "
                         "in the provided processor.']", self.response.json()['metadata'].get('errors', [''])[0])

    def test_required_card_expiry_cc_authorize(self):
        card = self.test_cards['mastercard']
        self.payload = {
            'processor': self.processor,
            'credentials': self.credentials,
            'mode': self.mode,
            'interaction_id': str(uuid.uuid4()),
            'interaction_type': self.interaction_type,
            'transaction_type': 'authorize',
            'tender_type': 'credit_card',
            'card_account_number': card['number'],
            'amount': self.amount,
            'description': 'Integration Test',
            'invoice_number': self.get_random_number()
        }
        self._execute(assert_status_code=400)
        self.assertEqual('error', self.response.json()['data'][0].get('result'))
        self.assertEqual("detail: ['card_expiry_month and card_expiry_year are required for CC transactions "
                         "in the provided processor.']", self.response.json()['metadata'].get('errors', [''])[0])

    def test_required_card_expiry_cc_refund(self):
        card = self.test_cards['mastercard']
        self.payload = {
            'processor': self.processor,
            'credentials': self.credentials,
            'mode': self.mode,
            'interaction_id': str(uuid.uuid4()),
            'interaction_type': self.interaction_type,
            'transaction_type': 'refund',
            'tender_type': 'credit_card',
            'card_account_number': card['number'],
            'amount': self.amount,
            'description': 'Integration Test',
            'invoice_number': self.get_random_number()
        }
        self._execute(assert_status_code=400)
        self.assertEqual('error', self.response.json()['data'][0].get('result'))
        self.assertEqual("detail: ['card_expiry_month and card_expiry_year are required for CC transactions "
                         "in the provided processor.']", self.response.json()['metadata'].get('errors', [''])[0])

    def test_not_required_card_expiry_ach(self):
        self.payload['tender_type'] = 'ach'
        self.payload['transaction_type'] = 'sale'
        self.payload['ach_name_on_account'] = 'John Doe'
        self.payload['ach_account_number'] = '123456789'
        self.payload['ach_routing_number'] = '022000127'
        self.payload['ach_account_type'] = 'checking'
        self.payload['ach_check_number'] = str(random.randint(100, 999))
        self._execute(assert_status_code=200)
        self.assertEqual('approved', self.response.json()['data'][0].get('result'))

    def test_invoice_number_max_len(self):
        """
        This processor matches invoice_number to orderID - it has a max allowed len of 22, so we check that len for
        invoice_number as well
        """
        card = self.test_cards['visa']
        self.payload = {
            'processor': self.processor,
            'credentials': self.credentials,
            'mode': self.mode,
            'interaction_id': str(uuid.uuid4()),
            'interaction_type': self.interaction_type,
            'transaction_type': 'sale',
            'tender_type': 'credit_card',
            'card_account_number': card['number'],
            'card_expiry_month': card['exp_month'],
            'card_expiry_year': card['exp_year'],
            'card_verification_value': card['cvv'],
            'amount': self.amount,
            'invoice_number': "12345678910123456789012345"
        }
        self._execute(assert_status_code=400)
        self.assertEqual('error', self.response.json()['data'][0].get('result'))
        self.assertEqual("invoice_number: Ensure this field has no more than 22 characters.",
                         self.response.json()['metadata'].get('errors', [''])[0])