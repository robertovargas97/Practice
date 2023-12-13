from rest_framework import serializers

from core_payments.chd_utils import get_values_to_mask
from core_payments.models import (
    RESULT_APPROVED,
    RESULT_DECLINED,
    RESULT_ERROR,
)
from core_payments.requests_wrapper import Requests
from core_payments.utils import validate_keys_in_dict
from payments_api.models import PROCESSOR_CONVENIENT_PAYMENTS
from .base import AbstractProcessor


class ConvenientPayments(AbstractProcessor):
    name = PROCESSOR_CONVENIENT_PAYMENTS
    version = '2.5'
    merchant_key = None
    api_access_key = None
    transaction_key = None
    payload = None

    api_decision_map_detail = {
        "-1": "Access Denied. The merchantkey or apikey is invalid.",
        "-2": "A system error occured. This may be due to invalid request parameters.",
        "0": "No record found.",
        "N": "Success"
    }

    api_decision_map = {
        "-1": RESULT_DECLINED,
        "-2": RESULT_ERROR,
        "0": RESULT_DECLINED,
        "N": RESULT_APPROVED
    }

    def _validate_request(self):
        # we want to validate processor credentials here
        credentials = ['api_access_key', 'merchant_key']
        validate_keys_in_dict(credentials, self.transaction_request.credentials)

        if not self.transaction_request.customer_id:
            raise serializers.ValidationError('`customer_id` is required.')

    def _set_credentials(self):
        self.api_access_key = self.transaction_request.credentials['api_access_key']
        self.merchant_key = self.transaction_request.credentials['merchant_key']

    def _set_endpoint(self):
        self.api_url = "https://secure.cpteller.com/api/25/webapi.cfc"  # Same url used for live or test mode

    def _lookup(self):
        """Performs an account lookup"""
        self.payload = {
            'merchantkey': self.merchant_key,
            'apikey': self.api_access_key,
            'method': 'cust_read',
            'custid': self.transaction_request.customer_id
        }

        r = Requests(self.transaction, to_mask=get_values_to_mask(self.request.data))
        self.api_response = r.send('POST', self.api_url, data=self.payload)

    def _parse_processor_response(self):
        response = self.api_response.json()
        status = str(response["status"])
        status_in = status in self.api_decision_map
        result = self.api_decision_map[status] if status_in else self.api_decision_map["N"]

        self.transaction_response.client_reference_code = self.transaction_request.client_reference_code

        self.transaction_response.processor_response = response
        self.transaction_response.result = result
        self.transaction_response.message = self.api_decision_map_detail[status] if status_in else \
            self.api_decision_map_detail["N"]
