from abc import ABC, abstractmethod
from ..models import (
    TransactionRequest,
    TransactionResponse,
    Transaction,
    TRANSACTION_TYPE_AUTHORIZE,
    TRANSACTION_TYPE_CAPTURE,
    TRANSACTION_TYPE_SALE,
    TRANSACTION_TYPE_VOID,
    TRANSACTION_TYPE_REFUND
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
        self.transaction_response = TransactionResponse(client_reference_code=self.transaction_request.client_reference_code)

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
        assign_if_not_none(self.transaction, 'customer_id', self.transaction_request.customer_id)
        assign_if_not_none(self.transaction, 'processor', self.transaction_request.processor)
        assign_if_not_none(self.transaction, 'transaction_type', self.transaction_request.transaction_type)
        assign_if_not_none(self.transaction, 'tender_type', self.transaction_request.tender_type)
        assign_if_not_none(self.transaction, 'amount', self.transaction_request.amount)
        assign_if_not_none(self.transaction, 'original_transaction_id', self.transaction_request.original_transaction_id)
        assign_if_not_none(self.transaction, 'ach_name_on_account', self.transaction_request.ach_name_on_account)
        if self.transaction_request.card_account_number:
            self.transaction.card_account_number = self.transaction_request.card_account_number[-4:]
        assign_if_not_none(self.transaction, 'card_type', self.transaction_request.card_type)
        if self.transaction_request.ach_account_number:
            self.transaction.ach_account_number = self.transaction_request.ach_account_number[-4:]
        assign_if_not_none(self.transaction, 'ach_routing_number', self.transaction_request.ach_routing_number)
        assign_if_not_none(self.transaction, 'ach_account_type', self.transaction_request.ach_account_type)
        assign_if_not_none(self.transaction, 'ach_check_number', self.transaction_request.ach_check_number)
        assign_if_not_none(self.transaction, 'bill_to_first_name', self.transaction_request.bill_to_first_name)
        assign_if_not_none(self.transaction, 'bill_to_last_name', self.transaction_request.bill_to_last_name)
        assign_if_not_none(self.transaction, 'bill_to_company', self.transaction_request.bill_to_company)
        assign_if_not_none(self.transaction, 'bill_to_address', self.transaction_request.bill_to_address)
        assign_if_not_none(self.transaction, 'bill_to_city', self.transaction_request.bill_to_city)
        assign_if_not_none(self.transaction, 'bill_to_county', self.transaction_request.bill_to_county)
        assign_if_not_none(self.transaction, 'bill_to_state', self.transaction_request.bill_to_state)
        assign_if_not_none(self.transaction, 'bill_to_zip', self.transaction_request.bill_to_zip)
        assign_if_not_none(self.transaction, 'bill_to_country', self.transaction_request.bill_to_country)
        assign_if_not_none(self.transaction, 'bill_to_phone', self.transaction_request.bill_to_phone)
        assign_if_not_none(self.transaction, 'bill_to_email', self.transaction_request.bill_to_email)
        assign_if_not_none(self.transaction, 'ship_to_first_name', self.transaction_request.ship_to_first_name)
        assign_if_not_none(self.transaction, 'ship_to_last_name', self.transaction_request.ship_to_last_name)
        assign_if_not_none(self.transaction, 'ship_to_company', self.transaction_request.ship_to_company)
        assign_if_not_none(self.transaction, 'ship_to_address', self.transaction_request.ship_to_address)
        assign_if_not_none(self.transaction, 'ship_to_city', self.transaction_request.ship_to_city)
        assign_if_not_none(self.transaction, 'ship_to_county', self.transaction_request.ship_to_county)
        assign_if_not_none(self.transaction, 'ship_to_state', self.transaction_request.ship_to_state)
        assign_if_not_none(self.transaction, 'ship_to_zip', self.transaction_request.ship_to_zip)
        assign_if_not_none(self.transaction, 'ship_to_country', self.transaction_request.ship_to_country)
        assign_if_not_none(self.transaction, 'ship_to_phone', self.transaction_request.ship_to_phone)
        assign_if_not_none(self.transaction, 'ship_to_email', self.transaction_request.ship_to_email)
        assign_if_not_none(self.transaction, 'description', self.transaction_request.description)
        assign_if_not_none(self.transaction, 'invoice_number', self.transaction_request.invoice_number)
        self.transaction.save()

    def _log_transaction_response(self):
        assign_if_not_none(self.transaction, 'processor_result', self.transaction_response.result)
        assign_if_not_none(self.transaction, 'processor_transaction_id', self.transaction_response.transaction_id)
        assign_if_not_none(self.transaction, 'processor_message', self.transaction_response.message)
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
        if TRANSACTION_TYPE_AUTHORIZE == self.transaction_request.transaction_type:
            self._authorize()
        elif TRANSACTION_TYPE_CAPTURE == self.transaction_request.transaction_type:
            self._capture()
        elif TRANSACTION_TYPE_SALE == self.transaction_request.transaction_type:
            self._sale()
        elif TRANSACTION_TYPE_VOID == self.transaction_request.transaction_type:
            self._void()
        elif TRANSACTION_TYPE_REFUND == self.transaction_request.transaction_type:
            self._refund()
        else:
            raise NotImplementedError('{} is not implemented.'.format(self.transaction_request.transaction_type))

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
    def _authorize(self):
        """Prepare the authorize request."""
    
    @abstractmethod
    def _capture(self):
        """Prepare the capture request."""

    @abstractmethod
    def _sale(self):
        """Prepare the sale request."""

    @abstractmethod
    def _void(self):
        """Prepare the void request."""
    
    @abstractmethod
    def _refund(self):
        """Prepare the refund request."""

    @abstractmethod
    def _parse_processor_response(self):
        """Parses the processor response and returns a transaction response object."""
