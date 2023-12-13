from rest_framework import serializers

from core_payments.chd_utils import get_values_to_mask
from .base import AbstractProcessor
from core_payments.models import (
    RESULT_APPROVED,
    RESULT_DECLINED,
    RESULT_ERROR,
    RESULT_REVIEW,
    MODE_LIVE,
    MODE_TEST
)
from ..models import (
    PROCESSOR_AUTHORIZE_NET,
    ACH_ACCOUNT_TYPE_SAVINGS,
    ACH_ACCOUNT_TYPE_CHECKING,
    ACH_ACCOUNT_TYPE_COMMERCIAL,
    TENDER_TYPE_CREDIT_CARD,
    TRANSACTION_TYPE_REFUND,
    TRANSACTION_TYPE_AUTHORIZE, TRANSACTION_TYPE_SALE)
from core_payments.utils import assign_if_not_none, validate_keys_in_dict
from core_payments.requests_wrapper import Requests
import json
import codecs
import requests
from collections import OrderedDict

# ***************************************************************************** #
# IMPORTANT - Authorize.Net API requires the elements to be in order.
# If out of order, you will get errors.
# This is why we are using OrderedDict() to preserve the order.
# Use the documentation here to compare the requests being sent.
# https://developer.authorize.net/api/reference/index.html#payment-transactions
# Select the transaction type and look at the JSON example
# ***************************************************************************** #


class AuthorizeNetProcessor(AbstractProcessor):
    name = PROCESSOR_AUTHORIZE_NET
    version = 'v1'
    duplicate_window = '0'
    test_request = '1'
    payload = None

    # a map between Authorize.Net's ach account types and our API's values
    api_ach_account_type_map = {
        ACH_ACCOUNT_TYPE_SAVINGS: 'savings',
        ACH_ACCOUNT_TYPE_CHECKING: 'checking',
        ACH_ACCOUNT_TYPE_COMMERCIAL: 'businessChecking'
    }

    # a map between Authorize.Net's response codes and our API's values
    api_response_code_map = {
        '1': RESULT_APPROVED,
        '2': RESULT_DECLINED,
        '3': RESULT_ERROR,
        '4': RESULT_REVIEW
    }

    def _validate_request(self):
        # we want to validate processor credentials here
        credentials = ['login', 'tran_key']
        validate_keys_in_dict(credentials, self.transaction_request.credentials)

        # check not supported fields by certain transaction types if were provided
        not_supported = {'`invoice_number`': self.transaction_request.invoice_number,
                         '`description`': self.transaction_request.description}
        not_supported_provided = [key for key, value in not_supported.items() if value]
        if not_supported_provided and \
                self.transaction_request.transaction_type not in [TRANSACTION_TYPE_AUTHORIZE, TRANSACTION_TYPE_SALE]:
            raise serializers.ValidationError('{} not supported by the provided processor and transaction_type.'.format(
                ', '.join(not_supported_provided)))

    def _set_credentials(self):
        self.login = self.transaction_request.credentials['login']
        self.tran_key = self.transaction_request.credentials['tran_key']

    def _set_endpoint(self):
        if MODE_LIVE == self.transaction_request.mode:
            self.api_url = 'https://api.authorize.net/xml/{}/request.api'.format(self.version)
        else:
            self.api_url = 'https://apitest.authorize.net/xml/{}/request.api'.format(self.version)
    
    def _authorize(self):
        """Performs an authorize transaction."""
        # payload variable is used to build the transactionRequest object
        # we will then wrap this up with whatever top level request object is necessary
        self.payload = OrderedDict()
        self.payload['createTransactionRequest'] = OrderedDict([
            ('merchantAuthentication', self._payload_auth())
        ])
        assign_if_not_none(self.payload['createTransactionRequest'], 'refId', self.transaction_request.client_reference_code)
        self.payload['createTransactionRequest']['transactionRequest'] = OrderedDict([
            ('transactionType', 'authOnlyTransaction'),
            ('amount', str(self.transaction_request.amount)),
            ('payment', self._payload_tender_info())
        ])
        has_info, order_info = self._payload_order_info()
        if has_info:
            self.payload['createTransactionRequest']['transactionRequest']['order'] = order_info
        has_info, bill_to = self._payload_billing_info()
        if has_info:
            self.payload['createTransactionRequest']['transactionRequest']['billTo'] = bill_to
        has_info, ship_to = self._payload_shipping_info()
        if has_info:
            self.payload['createTransactionRequest']['transactionRequest']['shipTo'] = ship_to
        if MODE_TEST == self.transaction_request.mode:
            self.payload['createTransactionRequest']['transactionRequest']['transactionSettings'] = OrderedDict()
            self.payload['createTransactionRequest']['transactionRequest']['transactionSettings']['setting'] = []
            self.payload['createTransactionRequest']['transactionRequest']['transactionSettings']['setting'].append(
                OrderedDict([
                    ('settingName', 'duplicateWindow'),
                    ('settingValue', self.duplicate_window)
                ]))
        if self.transaction_request.test_request:
            self.payload['createTransactionRequest']['transactionRequest']['transactionSettings']['setting'].append(
                OrderedDict([
                    ('settingName', 'testRequest'),
                    ('settingValue', self.test_request)
                ]))
        self._process_request()
    
    def _capture(self):
        """Performs a capture transaction."""
        # payload variable is used to build the transactionRequest object
        # we will then wrap this up with whatever top level request object is necessary
        self.payload = OrderedDict()
        self.payload['createTransactionRequest'] = OrderedDict([
            ('merchantAuthentication', self._payload_auth())
        ])
        assign_if_not_none(self.payload['createTransactionRequest'], 'refId', self.transaction_request.client_reference_code)
        self.payload['createTransactionRequest']['transactionRequest'] = OrderedDict([
            ('transactionType', 'priorAuthCaptureTransaction'),
            ('amount', str(self.transaction_request.amount)),
            ('refTransId', self.transaction_request.original_transaction_id)
        ])
        if MODE_TEST == self.transaction_request.mode:
            self.payload['createTransactionRequest']['transactionRequest']['transactionSettings'] = OrderedDict()
            self.payload['createTransactionRequest']['transactionRequest']['transactionSettings']['setting'] = []
            self.payload['createTransactionRequest']['transactionRequest']['transactionSettings']['setting'].append(
                OrderedDict([
                    ('settingName', 'duplicateWindow'),
                    ('settingValue', self.duplicate_window)
                ]))
        if self.transaction_request.test_request:
            self.payload['createTransactionRequest']['transactionRequest']['transactionSettings']['setting'].append(
                OrderedDict([
                    ('settingName', 'testRequest'),
                    ('settingValue', self.test_request)
                ]))
        self._process_request()

    def _sale(self):
        """Performs a sale transaction."""
        # payload variable is used to build the transactionRequest object
        # we will then wrap this up with whatever top level request object is necessary
        self.payload = OrderedDict()
        self.payload['createTransactionRequest'] = OrderedDict([
            ('merchantAuthentication', self._payload_auth())
        ])
        assign_if_not_none(self.payload['createTransactionRequest'], 'refId', self.transaction_request.client_reference_code)
        self.payload['createTransactionRequest']['transactionRequest'] = OrderedDict([
            ('transactionType', 'authCaptureTransaction'),
            ('amount', str(self.transaction_request.amount)),
            ('payment', self._payload_tender_info())
        ])
        has_info, order_info = self._payload_order_info()
        if has_info:
            self.payload['createTransactionRequest']['transactionRequest']['order'] = order_info
        has_info, bill_to = self._payload_billing_info()
        if has_info:
            self.payload['createTransactionRequest']['transactionRequest']['billTo'] = bill_to
        has_info, ship_to = self._payload_shipping_info()
        if has_info:
            self.payload['createTransactionRequest']['transactionRequest']['shipTo'] = ship_to
        if MODE_TEST == self.transaction_request.mode:
            self.payload['createTransactionRequest']['transactionRequest']['transactionSettings'] = OrderedDict()
            self.payload['createTransactionRequest']['transactionRequest']['transactionSettings']['setting'] = []
            self.payload['createTransactionRequest']['transactionRequest']['transactionSettings']['setting'].append(
                OrderedDict([
                    ('settingName', 'duplicateWindow'),
                    ('settingValue', self.duplicate_window)
                ]))
        if self.transaction_request.test_request:
            self.payload['createTransactionRequest']['transactionRequest']['transactionSettings']['setting'].append(
                OrderedDict([
                    ('settingName', 'testRequest'),
                    ('settingValue', self.test_request)
                ]))
        self._process_request()

    def _void(self):
        """Performs a void transaction."""
        # payload variable is used to build the transactionRequest object
        # we will then wrap this up with whatever top level request object is necessary
        self.payload = OrderedDict()
        self.payload['createTransactionRequest'] = OrderedDict([
            ('merchantAuthentication', self._payload_auth())
        ])
        assign_if_not_none(self.payload['createTransactionRequest'], 'refId',
                           self.transaction_request.client_reference_code)
        self.payload['createTransactionRequest']['transactionRequest'] = OrderedDict([
            ('transactionType', 'voidTransaction'),
            ('refTransId', self.transaction_request.original_transaction_id)
        ])
        if MODE_TEST == self.transaction_request.mode:
            self.payload['createTransactionRequest']['transactionRequest']['transactionSettings'] = OrderedDict()
            self.payload['createTransactionRequest']['transactionRequest']['transactionSettings']['setting'] = []
            self.payload['createTransactionRequest']['transactionRequest']['transactionSettings']['setting'].append(
                OrderedDict([
                    ('settingName', 'duplicateWindow'),
                    ('settingValue', self.duplicate_window)
                ]))
        if self.transaction_request.test_request:
            self.payload['createTransactionRequest']['transactionRequest']['transactionSettings']['setting'].append(
                OrderedDict([
                    ('settingName', 'testRequest'),
                    ('settingValue', self.test_request)
                ]))
        self._process_request()

    def _refund(self):
        """Performs a sale transaction."""
        # payload variable is used to build the transactionRequest object
        # we will then wrap this up with whatever top level request object is necessary
        self.payload = OrderedDict()
        self.payload['createTransactionRequest'] = OrderedDict([
            ('merchantAuthentication', self._payload_auth())
        ])
        assign_if_not_none(self.payload['createTransactionRequest'], 'refId',
                           self.transaction_request.client_reference_code)
        self.payload['createTransactionRequest']['transactionRequest'] = OrderedDict([
            ('transactionType', 'refundTransaction'),
            ('amount', str(self.transaction_request.amount)),
            ('payment', self._payload_tender_info()),
            ('refTransId', self.transaction_request.original_transaction_id)
        ])
        has_info, bill_to = self._payload_billing_info()
        if has_info:
            self.payload['createTransactionRequest']['transactionRequest']['billTo'] = bill_to
        has_info, ship_to = self._payload_shipping_info()
        if has_info:
            self.payload['createTransactionRequest']['transactionRequest']['shipTo'] = ship_to
        if MODE_TEST == self.transaction_request.mode:
            self.payload['createTransactionRequest']['transactionRequest']['transactionSettings'] = OrderedDict()
            self.payload['createTransactionRequest']['transactionRequest']['transactionSettings']['setting'] = []
            self.payload['createTransactionRequest']['transactionRequest']['transactionSettings']['setting'].append(
                OrderedDict([
                    ('settingName', 'duplicateWindow'),
                    ('settingValue', self.duplicate_window)
                ]))
        if self.transaction_request.test_request:
            self.payload['createTransactionRequest']['transactionRequest']['transactionSettings']['setting'].append(
                OrderedDict([
                    ('settingName', 'testRequest'),
                    ('settingValue', self.test_request)
                ]))
        self._process_request()

    def _parse_processor_response(self):
        # first we check if we have a good response on our side from the API
        if self.api_response.status_code == requests.codes.ok:
            # parse processor response to JSON
            try:
                response = self.api_response.json()
            except ValueError:
                response = json.loads(codecs.decode(self.api_response.content, 'utf-8-sig'))
            self.transaction_response.processor_response = response
            # now parse the API response and return the right values
            if 'Ok' == response['messages']['resultCode']:
                self.transaction_response.result = self.api_response_code_map[response['transactionResponse']['responseCode']]
                self.transaction_response.transaction_id = response['transactionResponse'].get('transId', None)
                if response.get('transactionResponse', {}).get('messages', []):
                    self.transaction_response.message = '\n'.join(['{} - {}'.format(item['code'], item['description']) for item in response['transactionResponse']['messages']])
            else:
                # API response was bad, let's pass the error message back
                self.transaction_response.result = RESULT_ERROR
                message = '\n'.join(['{} - {}'.format(item['code'], item['text']) for item in response['messages']['message']])
                if response.get('transactionResponse', {}).get('errors', []):
                    message += " Errors: {}".format(', '.join(['{} - {}'.format(item['errorCode'], item['errorText']) for item in response['transactionResponse']['errors']]))
                self.transaction_response.message = message
        else:
            self.transaction_response.result = RESULT_ERROR
            self.transaction_response.message = 'HTTP {} - {}'.format(self.api_response.status_code, self.api_response.text)

    def _payload_auth(self):
        return OrderedDict([
            ('name', self.login),
            ('transactionKey', self.tran_key)
        ])

    def _payload_tender_info(self):
        """Populates the payload with tender info."""
        tender_info = OrderedDict()
        if TENDER_TYPE_CREDIT_CARD == self.transaction_request.tender_type:
            if TRANSACTION_TYPE_REFUND == self.transaction_request.transaction_type \
                    and self.transaction_request.original_transaction_id:
                tender_info['creditCard'] = OrderedDict([
                    ('cardNumber', self.transaction_request.card_account_number[-4:]),
                    ('expirationDate', 'XXXX')
                ])
            else:
                tender_info['creditCard'] = OrderedDict([
                    ('cardNumber', self.transaction_request.card_account_number)
                ])
                if self.transaction_request.card_expiry_date:
                    tender_info['creditCard']['expirationDate'] = self.transaction_request.card_expiry_date.strftime('%Y-%m')
                assign_if_not_none(tender_info['creditCard'], 'cardCode', self.transaction_request.card_verification_value)
        else:
            tender_info['bankAccount'] = OrderedDict()
            if self.transaction_request.ach_account_type:
                tender_info['bankAccount']['accountType'] = self.api_ach_account_type_map[self.transaction_request.ach_account_type]
            tender_info['bankAccount']['routingNumber'] = self.transaction_request.ach_routing_number
            tender_info['bankAccount']['accountNumber'] = self.transaction_request.ach_account_number
            tender_info['bankAccount']['nameOnAccount'] = self.transaction_request.ach_name_on_account
            assign_if_not_none(tender_info['bankAccount'], 'checkNumber', self.transaction_request.ach_check_number)
        return tender_info

    def _payload_billing_info(self):
        """Populates the payload with billing info if available."""
        bill_to = OrderedDict()
        has_changed = False
        has_changed = assign_if_not_none(bill_to, 'firstName', self.transaction_request.bill_to_first_name) or has_changed
        has_changed = assign_if_not_none(bill_to, 'lastName', self.transaction_request.bill_to_last_name) or has_changed
        has_changed = assign_if_not_none(bill_to, 'company', self.transaction_request.bill_to_company) or has_changed
        has_changed = assign_if_not_none(bill_to, 'address', self.transaction_request.bill_to_address) or has_changed
        has_changed = assign_if_not_none(bill_to, 'city', self.transaction_request.bill_to_city) or has_changed
        has_changed = assign_if_not_none(bill_to, 'state', self.transaction_request.bill_to_state) or has_changed
        has_changed = assign_if_not_none(bill_to, 'zip', self.transaction_request.bill_to_zip) or has_changed
        has_changed = assign_if_not_none(bill_to, 'country', self.transaction_request.bill_to_country) or has_changed
        has_changed = assign_if_not_none(bill_to, 'phoneNumber', self.transaction_request.bill_to_phone) or has_changed
        has_changed = assign_if_not_none(bill_to, 'email', self.transaction_request.bill_to_email) or has_changed
        return has_changed, bill_to

    def _payload_shipping_info(self):
        """Populates the payload with shipping info if available."""
        ship_to = OrderedDict()
        has_changed = False
        has_changed = assign_if_not_none(ship_to, 'firstName', self.transaction_request.ship_to_first_name) or has_changed
        has_changed = assign_if_not_none(ship_to, 'lastName', self.transaction_request.ship_to_last_name) or has_changed
        has_changed = assign_if_not_none(ship_to, 'company', self.transaction_request.ship_to_company) or has_changed
        has_changed = assign_if_not_none(ship_to, 'address', self.transaction_request.ship_to_address) or has_changed
        has_changed = assign_if_not_none(ship_to, 'city', self.transaction_request.ship_to_city) or has_changed
        has_changed = assign_if_not_none(ship_to, 'state', self.transaction_request.ship_to_state) or has_changed
        has_changed = assign_if_not_none(ship_to, 'zip', self.transaction_request.ship_to_zip) or has_changed
        has_changed = assign_if_not_none(ship_to, 'country', self.transaction_request.ship_to_country) or has_changed
        return has_changed, ship_to

    def _payload_order_info(self):
        """Populates the order invoice number and description if available."""
        order_info = OrderedDict()
        has_changed = False
        has_changed = assign_if_not_none(order_info, 'invoiceNumber', self.transaction_request.invoice_number) or has_changed
        has_changed = assign_if_not_none(order_info, 'description', self.transaction_request.description) or has_changed
        return has_changed, order_info

    def _process_request(self):
        """Makes the request to Authorize.Net and gets the response."""
        # get the values of the elements we need to mask
        r = Requests(self.transaction, to_mask=get_values_to_mask(self.request.data))
        self.api_response = r.send('POST', self.api_url, json=self.payload)
