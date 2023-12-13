from abc import ABC, abstractmethod
from ..models import (
    TransactionRequest,
    TransactionResponse,
    Transaction
)
from rest_framework.request import Request
from core_payments.utils import assign_if_not_none


class AbstractProcessor(ABC):
    # name of the processor
    name = None
    # API version of the processor
    version = None
    # URL for the API
    api_url = None
    # transaction request and response variables
    transaction_request = None
    transaction_response = None
    transaction = None

    @classmethod
    def should_process(cls, transaction_request):
        """A method used by the factory to quickly determine the correct processor depending on the requirements."""
        return True if cls.name == transaction_request.processor else False

    def __init__(self, request, transaction_request):
        # validate request, we will use this to determine the wiretap id if it exists
        assert request, Request
        self.request = request

        # validate transaction request
        assert transaction_request, TransactionRequest
        self.transaction_request = transaction_request

        # create the transaction response object and ensure the client reference code is set if one was passed
        self.transaction_response = TransactionResponse(
            client_reference_code=self.transaction_request.client_reference_code)

    def _log_transaction_request(self):
        self.transaction = Transaction()
        if hasattr(self.request, 'wiretap_message'):
            self.transaction.message = self.request.wiretap_message
        assign_if_not_none(self.transaction, 'project_id', self.transaction_request.project_id)
        assign_if_not_none(self.transaction, 'mode', self.transaction_request.mode)
        assign_if_not_none(self.transaction, 'test_request', self.transaction_request.test_request)
        assign_if_not_none(self.transaction, 'interaction_id', self.transaction_request.interaction_id)
        assign_if_not_none(self.transaction, 'interaction_type', self.transaction_request.interaction_type)
        assign_if_not_none(self.transaction, 'client_reference_code', self.transaction_request.client_reference_code)
        assign_if_not_none(self.transaction, 'processor', self.transaction_request.processor)
        assign_if_not_none(self.transaction, 'customer_id', self.transaction_request.customer_id)
        assign_if_not_none(self.transaction, 'account_number', self.transaction_request.account_number)
        assign_if_not_none(self.transaction, 'invoice_number', self.transaction_request.invoice_number)
        assign_if_not_none(self.transaction, 'bill_year', self.transaction_request.bill_year)
        assign_if_not_none(self.transaction, 'date_of_birth', self.transaction_request.date_of_birth)
        assign_if_not_none(self.transaction, 'zip_code', self.transaction_request.zip_code)
        self.transaction.save()

    def _log_transaction_response(self):
        assign_if_not_none(self.transaction, 'processor_result', self.transaction_response.result)
        assign_if_not_none(self.transaction, 'processor_transaction_id', self.transaction_response.transaction_id)
        assign_if_not_none(self.transaction, 'processor_message', self.transaction_response.message)
        assign_if_not_none(self.transaction, 'balance_amount', self.transaction_response.balance_amount)
        assign_if_not_none(self.transaction, 'balance_due_date', self.transaction_response.balance_due_date)
        self.transaction.save()

    def execute(self):
        # log the transaction request
        self._log_transaction_request()

        # call the validation method to see if any additional validation needs to be performed
        self._validate_request()

        # do some pre-processing to ensure all processor information is good
        self._set_credentials()
        self._set_endpoint()

        # now perform payment processing depending on the transaction type
        self._lookup()

        # parse the processor response and return it
        self._parse_processor_response()
        assert self.transaction_response, TransactionResponse

        # log transaction response and then return it
        self._log_transaction_response()
        return self.transaction_response

    @abstractmethod
    def _validate_request(self):
        """Perform any additional validation to the request here."""

    @abstractmethod
    def _set_credentials(self):
        """Set processor credentials."""

    @abstractmethod
    def _set_endpoint(self):
        """Set the appropriate processor endpoint for the API here."""

    @abstractmethod
    def _lookup(self):
        """Prepare the lookup request."""

    @abstractmethod
    def _parse_processor_response(self):
        """Parses the processor response and returns a transaction response object."""
