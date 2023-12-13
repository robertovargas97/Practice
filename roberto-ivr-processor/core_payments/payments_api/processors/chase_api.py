from rest_framework import serializers

from core_payments.chd_utils import get_values_to_mask
from .base import AbstractProcessor
from core_payments.models import (
    RESULT_APPROVED,
    RESULT_DECLINED,
    RESULT_ERROR,
    MODE_LIVE,
)
from ..models import (
    PROCESSOR_CHASE,
    CARD_TYPE_VISA,
    CARD_TYPE_MASTERCARD,
    CARD_TYPE_AMERICAN_EXPRESS,
    CARD_TYPE_DISCOVER,
    CARD_TYPE_JCB,
    ACH_ACCOUNT_TYPE_SAVINGS,
    ACH_ACCOUNT_TYPE_CHECKING,
    ACH_ACCOUNT_TYPE_COMMERCIAL,
    TENDER_TYPE_CREDIT_CARD,
    TRANSACTION_TYPE_CAPTURE, TRANSACTION_TYPE_VOID, TRANSACTION_TYPE_AUTHORIZE, TENDER_TYPE_ACH, TRANSACTION_TYPE_SALE,
    TRANSACTION_TYPE_REFUND)
from core_payments.zeep_plugin import LogPlugin
from zeep.cache import InMemoryCache
from zeep.transports import Transport
from zeep import Client
from zeep.helpers import serialize_object
from core_payments.utils import assign_if_not_none, validate_keys_in_dict


class ChaseProcessor(AbstractProcessor):
    name = PROCESSOR_CHASE
    version = "4.0"
    username = None
    password = None
    merchant_id = None
    terminal_id = None

    # a map between Chase's card types and our API's values
    api_credit_card_type_map = {
        CARD_TYPE_VISA: 'VI',
        CARD_TYPE_MASTERCARD: 'MC',
        CARD_TYPE_AMERICAN_EXPRESS: 'AX',
        CARD_TYPE_DISCOVER: 'DI',
        CARD_TYPE_JCB: 'JC'
    }

    # a map between Chase's check types and our API's values
    api_check_account_type_map = {
        ACH_ACCOUNT_TYPE_SAVINGS: 'S',
        ACH_ACCOUNT_TYPE_CHECKING: 'C',
        ACH_ACCOUNT_TYPE_COMMERCIAL: 'X'
    }

    # a map betweeb Cybersource's decision and our API's values
    api_decision_map = {
        '0': RESULT_DECLINED,
        '1': RESULT_APPROVED,
        '2': RESULT_ERROR
    }

    def _authorize(self):
        """Performs an authorize transaction."""
        self._client_meta()
        self._payload_meta()
        self._payload_tender_info()
        self._payload_billing_info()
        self._payload_shipping_info()
        self.payload['amount'] = self.transaction_request.amount_in_cents
        self.payload['transType'] = 'A'
        self._process_request(method_name='NewOrder')

    def _capture(self):
        """Performs a capture transaction."""
        self._client_meta()
        self._payload_meta()
        self.payload['amount'] = self.transaction_request.amount_in_cents
        self.payload['txRefNum'] = self.transaction_request.original_transaction_id
        self._process_request(method_name='MFC')

    def _void(self):
        """Performs a void transaction."""
        self._client_meta()
        self._payload_meta()
        self.payload['txRefNum'] = self.transaction_request.original_transaction_id
        self._process_request(method_name='Reversal')
    
    def _refund(self):
        """Performs a refund transaction."""
        self._client_meta()
        self._payload_meta()
        self._payload_tender_info()
        self._payload_billing_info()
        self._payload_shipping_info()
        self.payload['amount'] = self.transaction_request.amount_in_cents
        self.payload['transType'] = 'R'
        assign_if_not_none(self.payload, 'txRefNum', self.transaction_request.original_transaction_id)
        self._process_request(method_name='NewOrder')

    def _sale(self):
        """Performs a sale transaction."""
        self._client_meta()
        self._payload_meta()
        self._payload_tender_info()
        self._payload_billing_info()
        self._payload_shipping_info()
        self.payload['amount'] = self.transaction_request.amount_in_cents
        self.payload['transType'] = 'AC'
        self._process_request(method_name='NewOrder')

    def _validate_request(self):
        """Validates required and valid/invalid options in the request"""
        # we want to validate processor credentials here
        credentials = ['merchant_id', 'username', 'password', 'terminal_id']
        validate_keys_in_dict(credentials, self.transaction_request.credentials)

        if self.transaction_request.transaction_type in (TRANSACTION_TYPE_CAPTURE, TRANSACTION_TYPE_VOID) and \
                not self.transaction_request.original_transaction_id:
            raise serializers.ValidationError('original_transaction_id is required for void and capture transactions.')

        if self.transaction_request.transaction_type in (TRANSACTION_TYPE_CAPTURE, TRANSACTION_TYPE_AUTHORIZE) and \
                not self.transaction_request.invoice_number:
            raise serializers.ValidationError('invoice_number is required for capture and authorize transactions '
                                              'and it should be the same for both (when capturing an authorized '
                                              'transaction).')

        if not self.transaction_request.interaction_id:
            raise serializers.ValidationError("interaction_id is required by the provided processor.")

        if self.transaction_request.tender_type == TENDER_TYPE_ACH:
            for field in ['bill_to_first_name', 'bill_to_last_name']:
                if not getattr(self.transaction_request, field):
                    raise serializers.ValidationError('{} is required for ACH transactions in the provided '
                                                      'processor.'.format(field))

        if not self.transaction_request.card_expiry_date and \
                self.transaction_request.tender_type == TENDER_TYPE_CREDIT_CARD and \
                self.transaction_request.transaction_type in (TRANSACTION_TYPE_SALE, TRANSACTION_TYPE_REFUND, TRANSACTION_TYPE_AUTHORIZE):
            raise serializers.ValidationError('card_expiry_month and card_expiry_year are required for CC transactions '
                                              'in the provided processor.')

        # check not supported fields that were provided
        if self.transaction_request.description:
            raise serializers.ValidationError('`description` not supported by the provided processor.')

        # max number of chars allowed for orderID is 22
        if self.transaction_request.invoice_number and len(str(self.transaction_request.invoice_number)) > 22:
            raise serializers.ValidationError({'invoice_number': 'Ensure this field has no more than 22 characters.'})

    def _parse_processor_response(self):
        """Parses the processor response into the format we need to return in this API"""
        result = RESULT_APPROVED  # we infer ok by default
        if self.api_response.get('faultCode'):
            message = self.api_response['faultString']
            result = RESULT_ERROR
        else:
            # there are 3 fields that can be checked for result: respCode, approvalStatus and procStatus, we need
            # to check what we receive in the right order to find out if the request was approved or not, sometimes we
            # don't receive them all and they have a hierarchy depending on when and what validation was being made when
            # the request failed - order here is important
            if self.api_response.get('respCode') and self.api_response.get('respCode') != '00':
                result = RESULT_ERROR
            elif self.api_response.get('approvalStatus'):
                result = self.api_decision_map[self.api_response['approvalStatus']]
            elif self.api_response.get('procStatus') != '0':
                result = RESULT_ERROR
            self.transaction_response.transaction_id = self.api_response['txRefNum']
            status_code = self.api_response.get('approvalStatus') if result == RESULT_APPROVED else self.api_response.get('respCode')
            message = "{} - {}.".format(status_code or self.api_response.get('procStatus') or '',
                                        self.api_response.get('procStatusMessage') or result.title())
        self.transaction_response.message = message
        self.transaction_response.result = result
        self.transaction_response.processor_response = self.api_response

    def _set_credentials(self):
        """Setups credentials fields"""
        self.username = self.transaction_request.credentials['username']
        self.password = self.transaction_request.credentials['password']
        self.merchant_id = self.transaction_request.credentials['merchant_id']
        self.terminal_id = self.transaction_request.credentials['terminal_id']

    def _set_endpoint(self):
        """Setups api endpoint according to request mode"""
        if MODE_LIVE == self.transaction_request.mode:
            self.api_url = 'https://ws1.chasepaymentech.com/PaymentechGateway/wsdl/ChasePaymentechGateway.wsdl'
        else:
            self.api_url = 'https://wsvar1.chasepaymentech.com/PaymentechGateway/wsdl/ChasePaymentechGateway.wsdl'

    def _client_meta(self):
        """Setups the SOAP client."""
        # it is imperative to use LogPlugin here so processor request and response is sanitized and logged
        self.client = Client(
            wsdl=self.api_url,
            transport=Transport(cache=InMemoryCache()),
            plugins=[LogPlugin(self.transaction, to_mask=get_values_to_mask(self.request.data))]
        )
        # get the object factory
        self.factory = self.client.type_factory('ns0')

    def _payload_meta(self):
        """Setups the request with common details."""
        self.payload = dict()
        self.payload['orbitalConnectionUsername'] = self.username
        self.payload['orbitalConnectionPassword'] = self.password
        self.payload['version'] = self.version
        self.payload['industryType'] = 'EC'
        self.payload['bin'] = "000001"
        self.payload['merchantID'] = self.merchant_id
        self.payload['terminalID'] = self.terminal_id
        self.payload['orderID'] = self._get_order_id_value()

    def _payload_tender_info(self):
        """Setups the tender information."""
        if TENDER_TYPE_CREDIT_CARD == self.transaction_request.tender_type:
            self.payload['ccAccountNum'] = self.transaction_request.card_account_number
            self.payload['ccExp'] = self.transaction_request.card_expiry_date.strftime('%Y%m')
            assign_if_not_none(self.payload, 'ccCardVerifyNum', self.transaction_request.card_verification_value)
            assign_if_not_none(self.payload, 'cardBrand',
                               self.api_credit_card_type_map.get(self.transaction_request.card_type, None))
        else:
            self.payload['ecpCheckRT'] = self.transaction_request.ach_routing_number
            self.payload['ecpCheckDDA'] = self.transaction_request.ach_account_number
            self.payload['cardBrand'] = 'EC'  # this brand value is required for ACH
            assign_if_not_none(self.payload, 'ecpBankAcctType',
                               self.api_check_account_type_map.get(self.transaction_request.ach_account_type, None))

    def _payload_billing_info(self):
        """Populates the payload with the billing info if available."""
        full_name = '{} {}'.format(self.transaction_request.bill_to_first_name or '',
                                   self.transaction_request.bill_to_last_name or '')
        assign_if_not_none(self.payload, 'avsName', full_name.strip())
        assign_if_not_none(self.payload, 'avsAddress1', self.transaction_request.bill_to_address)
        assign_if_not_none(self.payload, 'avsCity', self.transaction_request.bill_to_city)
        assign_if_not_none(self.payload, 'avsState', self.transaction_request.bill_to_state)
        assign_if_not_none(self.payload, 'avsZip', self.transaction_request.bill_to_zip)
        assign_if_not_none(self.payload, 'avsCountryCode', self.transaction_request.bill_to_country)
        assign_if_not_none(self.payload, 'avsPhone', self.transaction_request.bill_to_phone)
        assign_if_not_none(self.payload, 'customerEmail', self.transaction_request.bill_to_email)

    def _payload_shipping_info(self):
        """Populates the payload with the shipping info if available."""
        full_name = '{} {}'.format(self.transaction_request.ship_to_first_name or '',
                                   self.transaction_request.ship_to_last_name or '')
        assign_if_not_none(self.payload, 'avsDestName', full_name.strip())
        assign_if_not_none(self.payload, 'avsDestAddress1', self.transaction_request.ship_to_address)
        assign_if_not_none(self.payload, 'avsDestCity', self.transaction_request.ship_to_city)
        assign_if_not_none(self.payload, 'avsDestState', self.transaction_request.ship_to_state)
        assign_if_not_none(self.payload, 'avsDestZip', self.transaction_request.ship_to_zip)
        assign_if_not_none(self.payload, 'avsDestCountryCode', self.transaction_request.ship_to_country)
        assign_if_not_none(self.payload, 'avsDestPhoneNum', self.transaction_request.ship_to_phone)

    def _process_request(self, method_name):
        """Makes the request to Chase and gets the response."""
        method_to_call = getattr(self.client.service, method_name)
        response = method_to_call(self.payload)
        self.api_response = serialize_object(response)

    def _get_order_id_value(self):
        """Returns an orderID value to use in the request, it a required field but user shouldn't always provide it"""
        # orderID will be the invoice number if provided, if not it will be extracted from the interaction_id
        # max number of chars allowed for it is 22, so we use last 22 chars of the interaction_id field as backup
        return self.transaction_request.invoice_number or self.transaction_request.interaction_id[-22:]
