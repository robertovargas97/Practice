from rest_framework import serializers

from core_payments.chd_utils import get_values_to_mask
from .base import AbstractProcessor
from core_payments.models import (
    RESULT_APPROVED,
    RESULT_DECLINED,
    RESULT_ERROR,
    RESULT_REVIEW,
    MODE_LIVE,
)


from ..models import (
    ACH_ACCOUNT_TYPE_CHECKING,
    ACH_ACCOUNT_TYPE_SAVINGS,
    ACH_ACCOUNT_TYPE_CORPORATE,
    CARD_TYPE_VISA,
    CARD_TYPE_MASTERCARD,
    CARD_TYPE_AMERICAN_EXPRESS,
    CARD_TYPE_DISCOVER,
    CARD_TYPE_JCB,
    CARD_DINERS_CLUB,
    PROCESSOR_CYBERSOURCE,
    TENDER_TYPE_CREDIT_CARD,
    TENDER_TYPE_ACH,
    TRANSACTION_TYPE_CAPTURE,
    TRANSACTION_TYPE_VOID,
    TRANSACTION_TYPE_AUTHORIZE,
    TRANSACTION_TYPE_SALE,
    TRANSACTION_TYPE_REFUND
)

from core_payments.zeep_plugin import LogPlugin
from zeep import Client
from zeep.cache import InMemoryCache
from zeep.transports import Transport
from zeep.helpers import serialize_object
from zeep.wsse.username import UsernameToken

from core_payments.utils import assign_if_not_none, validate_keys_in_dict, list_to_string


class CybersourceProcessor(AbstractProcessor):
    name = PROCESSOR_CYBERSOURCE
    version = "1.171"
    merchant_id = None
    transaction_key = None

    # a map between cybersource's's card types and our API's values
    api_credit_card_type_map = {
        CARD_TYPE_VISA: '001',
        CARD_TYPE_MASTERCARD: '002',
        CARD_TYPE_AMERICAN_EXPRESS: '003',
        CARD_TYPE_DISCOVER: '004',
        CARD_DINERS_CLUB: '005',
        CARD_TYPE_JCB: '007'
    }

    # a map between cybersource's's check types and our API's values
    api_check_account_type_map = {
        ACH_ACCOUNT_TYPE_SAVINGS: 'S',
        ACH_ACCOUNT_TYPE_CHECKING: 'C',
        ACH_ACCOUNT_TYPE_CORPORATE: 'X'
    }

    # a map betweeb Cybersource's decision and our API's values
    api_decision_map = {
        'REJECT': RESULT_DECLINED,
        'ACCEPT': RESULT_APPROVED,
        'ERROR': RESULT_ERROR,
        'REVIEW': RESULT_REVIEW
    }

    def _set_credentials(self):
        """Setups credentials fields"""
        self.merchant_id = self.transaction_request.credentials['merchant_id']
        self.transaction_key = self.transaction_request.credentials['transaction_key']

    def _set_endpoint(self):
        """Setups api endpoint according to request mode"""
        if MODE_LIVE == self.transaction_request.mode:
            self.api_url = 'https://ics2ws.ic3.com/commerce/1.x/transactionProcessor/CyberSourceTransaction_1.170.wsdl'
        else:
            self.api_url = 'https://ics2wstest.ic3.com/commerce/1.x/transactionProcessor/CyberSourceTransaction_1.171.wsdl'

    def _validate_field_list(self, field_list, tender_type, option='individual'):
        """Takes a field list to verify if each field is present in the request and returns a message with an indivial field or a list of fields according with the given option"""
        message = ''
        for field in field_list:
            if not getattr(self.transaction_request, field):
                if option == 'individual':
                    message = '{} is required for {} transactions in the provided processor ({}).'.format(
                        field, tender_type, self.name)
                elif option == 'list':
                    message = '{} are required for {} transactions in the provided processor ({}).'.format(
                        list_to_string(field_list), tender_type, self.name)

                raise serializers.ValidationError(message)

    def _validate_request(self):
        """Validates required and valid/invalid options in the request"""
        # Billing information is required by the provided procesor
        required_billing_field_list = [
            'bill_to_first_name', 'bill_to_last_name', 'bill_to_email', 'bill_to_country', 'bill_to_city', 'bill_to_state', 'bill_to_zip', 'bill_to_address', 'bill_to_phone'
        ]

        tender_required_field_list = ['card_expiry_month', 'card_expiry_year', 'card_type',
                                      'card_verification_value'] if self.transaction_request.tender_type == TENDER_TYPE_CREDIT_CARD else ['ach_account_type', 'ach_name_on_account']

        # we want to validate processor credentials here
        credentials = ['merchant_id', 'transaction_key']
        validate_keys_in_dict(
            credentials, self.transaction_request.credentials
        )
        if self.transaction_request.transaction_type in (TRANSACTION_TYPE_AUTHORIZE, TRANSACTION_TYPE_SALE) or (not self.transaction_request.original_transaction_id and TRANSACTION_TYPE_REFUND):
            self._validate_field_list(
                required_billing_field_list, 'ACH and CC', 'list'
            )
        # check not supported fields that were provided
        for field in ['invoice_number', 'description']:
            if getattr(self.transaction_request, field):
                raise serializers.ValidationError(
                    '{} is not supported in the provided processor ({}).'.format(
                        field, self.name)
                )

        if self.transaction_request.transaction_type in (TRANSACTION_TYPE_CAPTURE, TRANSACTION_TYPE_VOID) and not self.transaction_request.original_transaction_id:
            raise serializers.ValidationError(
                'original_transaction_id is required for void and capture transactions.'
            )

        if (self.transaction_request.tender_type == TENDER_TYPE_CREDIT_CARD and
                self.transaction_request.transaction_type in (TRANSACTION_TYPE_SALE, TRANSACTION_TYPE_AUTHORIZE,)) or (not self.transaction_request.original_transaction_id and self.transaction_request.tender_type == TRANSACTION_TYPE_REFUND):
            self._validate_field_list(tender_required_field_list, 'CC')

        elif self.transaction_request.tender_type == TENDER_TYPE_ACH:
            self._validate_field_list(tender_required_field_list, 'ACH')
            # The ach_account_type comes in the request, so is necessary to validate it
            if self.transaction_request.ach_account_type not in (ACH_ACCOUNT_TYPE_SAVINGS, ACH_ACCOUNT_TYPE_CHECKING, ACH_ACCOUNT_TYPE_CORPORATE):
                raise serializers.ValidationError(
                    'ach_account_type must be savings , checking or corporate in the provided processor ({}).'.format(self.name))

    def _set_client_meta(self):
        """Setups the SOAP client."""
        self._cast_tender_info_attributes()
        # it is imperative to use LogPlugin here so processor request and response is sanitized and logged
        self.client = Client(
            wsdl=self.api_url,
            transport=Transport(cache=InMemoryCache()),
            wsse=UsernameToken(self.merchant_id, self.transaction_key),
            plugins=[
                LogPlugin(self.transaction, to_mask=get_values_to_mask(self.request.data))]
        )
        # get the object factory
        self.factory = self.client.type_factory('ns0')

    def _cast_tender_info_attributes(self):
        """Takes the original card_account_number and card_verification_value or ach_account_number of the request that will be used by the LogPlugin and cast them to string to avoid errors"""
        # If card_account_number comes in the request, so the card_verification_value too due the validations, for that reason those fields need to be casted
        if self.request.data.get('card_account_number'):
            self.request.data['card_account_number'] = str(
                self.request.data.get('card_account_number')
            )
            self.request.data['card_verification_value'] = str(
                self.request.data.get('card_verification_value')
            )
        # If ach_account_number comes in the request, needs to be casted
        if self.request.data.get('ach_account_number'):
            self.request.data['ach_account_number'] = str(
                self.request.data.get('ach_account_number')
            )

    def _fill_payload_meta(self):
        """Setups the request with common details."""
        self.payload = dict()
        self.payload['merchantID'] = self.merchant_id
        # The merchantReferenceCode should be genereated by us
        assign_if_not_none(self.payload, 'merchantReferenceCode', self.transaction_request.client_reference_code)
        if self.transaction_request.ignore_avs_result:
            self.payload['businessRules'] = self.factory.BusinessRules(ignoreAVSResult='true')

    def _fill_payload_billing_info(self):
        """Setups the payload with the billing info if available and returns an object that represent that information for Cybersource."""
        billing_info_payload = dict()
        assign_if_not_none(billing_info_payload, 'firstName',
                           self.transaction_request.bill_to_first_name)
        assign_if_not_none(billing_info_payload, 'lastName',
                           self.transaction_request.bill_to_last_name)
        assign_if_not_none(billing_info_payload, 'email',
                           self.transaction_request.bill_to_email)
        assign_if_not_none(billing_info_payload, 'country',
                           self.transaction_request.bill_to_country)
        assign_if_not_none(billing_info_payload, 'city',
                           self.transaction_request.bill_to_city)
        assign_if_not_none(billing_info_payload, 'state',
                           self.transaction_request.bill_to_state)
        assign_if_not_none(billing_info_payload, 'postalCode',
                           self.transaction_request.bill_to_zip)
        assign_if_not_none(billing_info_payload, 'street1',
                           self.transaction_request.bill_to_address)
        assign_if_not_none(billing_info_payload, 'phoneNumber',
                           self.transaction_request.bill_to_phone)

        billTo_object = self.factory.BillTo(**billing_info_payload)
        return billTo_object

    def _fill_payload_shipping_info(self):
        """Setups the payload with the shipping info if available and returns an object that represent that information for Cybersource.."""
        shipping_info_payload = dict()
        full_name = '{} {}'.format(self.transaction_request.bill_to_first_name,
                                   self.transaction_request.bill_to_last_name)
        assign_if_not_none(shipping_info_payload, 'name', full_name.strip())
        assign_if_not_none(shipping_info_payload, 'city',
                           self.transaction_request.ship_to_city)
        assign_if_not_none(shipping_info_payload, 'state',
                           self.transaction_request.ship_to_state)
        assign_if_not_none(shipping_info_payload, 'postalCode',
                           (self.transaction_request.ship_to_zip))
        assign_if_not_none(shipping_info_payload, 'country',
                           self.transaction_request.ship_to_country)
        assign_if_not_none(shipping_info_payload, 'phoneNumber',
                           self.transaction_request.ship_to_phone)
        assign_if_not_none(shipping_info_payload, 'email',
                           self.transaction_request.ship_to_email)

        shipTo_object = self.factory.ShipTo(**shipping_info_payload)
        return shipTo_object

    def _fill_payload_tender_info(self):
        """Setups the tender information for CC or ACH payments."""
        if TENDER_TYPE_CREDIT_CARD == self.transaction_request.tender_type:
            self.payload['card'] = self._fill_credit_card_payload()
        else:
            self.payload['check'] = self.fill_e_check_payload()

    def _fill_credit_card_payload(self):
        """"Setups the information for a credit card and returns an object that represents that information for Cybersource"""
        card_payload = dict()
        card_payload['accountNumber'] = self.transaction_request.card_account_number
        card_payload['expirationMonth'] = self.transaction_request.card_expiry_month
        card_payload['expirationYear'] = self.transaction_request.card_expiry_year
        card_payload['cvNumber'] = self.transaction_request.card_verification_value
        card_payload['cardType'] = self.api_credit_card_type_map.get(
            self.transaction_request.card_type
        )
        card_object = self.factory.Card(**card_payload)
        return card_object

    def fill_e_check_payload(self):
        """Setups the information for a electronic check and returns an object that represents that information for Cybersource"""
        check_payload = dict()
        check_payload['accountNumber'] = self.transaction_request.ach_account_number
        check_payload['fullName'] = self.transaction_request.ach_name_on_account
        check_payload['accountType'] = self.api_check_account_type_map.get(
            self.transaction_request.ach_account_type)
        check_payload['bankTransitNumber'] = self.transaction_request.ach_routing_number

        check_object = self.factory.Check(**check_payload)
        return check_object

    def _fill_payload_currency(self):
        """Setups the currency information for Cybersource"""
        self.payload['purchaseTotals'] = self.factory.PurchaseTotals(
            currency='USD',
            grandTotalAmount=self.transaction_request.amount_in_cents
        )

    def _fill_credit_service_payload(self):
        """Setups the params to ccCreditService or ecCreditService according to the given information in the request"""
        if self.transaction_request.original_transaction_id:
            if self.transaction_request.tender_type == TENDER_TYPE_CREDIT_CARD:
                self.payload['ccCreditService'] = self.factory.CCCreditService(
                    run="true",
                    captureRequestID=self.transaction_request.original_transaction_id
                )
            else:
                self.payload['ecCreditService'] = self.factory.ECCreditService(
                    run="true",
                    debitRequestID=self.transaction_request.original_transaction_id
                )
        else:
            self._fill_payload_tender_info()
            self.payload['billTo'] = self._fill_payload_billing_info()
            self.payload['shipTo'] = self._fill_payload_shipping_info()
            if self.transaction_request.tender_type == TENDER_TYPE_CREDIT_CARD:
                self.payload['ccCreditService'] = self.factory.CCCreditService(
                    run="true"
                )
            else:
                self.payload['ecCreditService'] = self.factory.ECCreditService(
                    run="true",
                )

    def _fill_sale_service_payload(self):
        """Setups the params to perform a sale transaction according with the tender type"""
        if self.transaction_request.tender_type == TENDER_TYPE_CREDIT_CARD:
            self.payload['ccAuthService'] = self.factory.CCAuthService(
                run="true")
            self.payload['ccCaptureService'] = self.factory.CCCaptureService(
                run="true"
            )
        else:
            self.payload['ecDebitService'] = self.factory.ECDebitService(
                run="true"
            )

    def _fill_merchant_defined_data(self):
        """Method populates the payload with MerchantDefinedData if any"""
        extra = self.transaction_request.extra or {}
        merchant_defined = self.factory.MerchantDefinedData()
        has_changed = False

        for k, v in extra.items():
            if 'field' in k:
                has_changed = assign_if_not_none(merchant_defined, k, v) or has_changed

        if has_changed:
            self.payload['merchantDefinedData'] = merchant_defined

    def _send_request(self):
        """Makes the request to Cybersource and gets the response."""
        response = self.client.service.runTransaction(**self.payload)
        self.api_response = serialize_object(response)

    def _authorize(self):
        """Performs an authorize transaction."""
        self._set_client_meta()
        self._fill_payload_meta()
        self._fill_payload_tender_info()
        self._fill_payload_currency()
        self._fill_merchant_defined_data()
        self.payload['billTo'] = self._fill_payload_billing_info()
        self.payload['shipTo'] = self._fill_payload_shipping_info()
        self.payload['ccAuthService'] = self.factory.CCAuthService(run="true")
        self._send_request()

    def _capture(self):
        """Performs a capture transaction."""
        self._set_client_meta()
        self._fill_payload_meta()
        self._fill_payload_currency()
        self._fill_merchant_defined_data()
        self.payload['ccCaptureService'] = self.factory.CCCaptureService(
            run="true", authRequestID=self.transaction_request.original_transaction_id
        )
        self._send_request()

    def _sale(self):
        """Performs a sale transaction."""
        self._set_client_meta()
        self._fill_payload_meta()
        self._fill_payload_tender_info()
        self._fill_payload_currency()
        self._fill_sale_service_payload()
        self._fill_merchant_defined_data()
        self.payload['billTo'] = self._fill_payload_billing_info()
        self.payload['shipTo'] = self._fill_payload_shipping_info()
        self._send_request()

    def _refund(self):
        """Performs a refund transaction."""
        self._set_client_meta()
        self._fill_payload_meta()
        self._fill_payload_currency()
        self._fill_merchant_defined_data()
        self._fill_credit_service_payload()
        self._send_request()

    def _void(self):
        """Performs a void transaction."""
        self._set_client_meta()
        self._fill_payload_meta()
        self._fill_merchant_defined_data()
        self.payload['voidService'] = self.factory.VoidService(
            run="true", voidRequestID=self.transaction_request.original_transaction_id
        )
        self._send_request()

    def _parse_processor_response(self):
        """Parses the processor response into the format we need to return in this API"""
        result = RESULT_APPROVED  # we infer ok by default
        message = ''
        reason_code = self.api_response.get('reasonCode')
        decision = self.api_response.get('decision')

        # Decision = ERROR and reason code != 100 represent an error coming from cybersource
        if decision == 'ERROR' and reason_code != 100:
            message = self._get_reason_code_message(reason_code)
            result = RESULT_ERROR
        else:
            result = self.api_decision_map.get(decision)
            message = self._get_reason_code_message(reason_code)
            self.transaction_response.transaction_id = self.api_response.get(
                'requestID')
        self.transaction_response.message = message
        self.transaction_response.result = result
        self.transaction_response.processor_response = self.api_response

    def _get_reason_code_message(self, reason_code):
        """There are 2 reason codes that is important to explain 101 and 101, because they need specific things to be solved, other reason codes just provide information, so the reason code is specified only"""
        message = ''
        if reason_code == 101:
            message = 'Reason code: {} - The request is missing one or more required fields : {}.'.format(
                reason_code, list_to_string(self.api_response.get('missingField')))
        elif reason_code == 102:
            message = 'Reason code: {} - One or more fields in the request contain invalid data : {}'.format(
                reason_code, list_to_string(self.api_response.get('invalidField')))
        else:
            message = 'Transaction type: {} - Reason code returned: {}'.format(
                self.transaction_request.transaction_type, reason_code)
        return message
