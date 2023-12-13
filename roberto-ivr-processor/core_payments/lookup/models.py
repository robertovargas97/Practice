from django.db import models

from core_payments.models import BaseTransactionResponse, BaseTransactionRequest, BaseTransaction


# Define common constant here

PROCESSOR_PAYRAZR = 'payrazr'
PROCESSOR_PAYRAZR_REST = 'payrazr_rest'
PROCESSOR_CONVENIENT_PAYMENTS = 'convenient_payments'
PROCESSOR_CHOICES = [
    (PROCESSOR_PAYRAZR, 'Payrazr'),
    (PROCESSOR_PAYRAZR_REST, 'Payrazr REST'),
    (PROCESSOR_CONVENIENT_PAYMENTS, 'Convenient Payments')
]


class TransactionResponse(BaseTransactionResponse):
    def __init__(self, result=None, transaction_id=None, message=None, client_reference_code=None,
                 balance_amount=None, balance_due_date=None):
        # call the super init
        super().__init__(result, transaction_id, message, client_reference_code)
        # for balance amount
        self.balance_amount = balance_amount
        # for balance due date
        self.balance_due_date = balance_due_date


class TransactionRequest(BaseTransactionRequest):
    def __init__(self, project_id=None, mode=None, test_request=None,
                 interaction_id=None, interaction_type=None, client_reference_code=None,
                 processor=None, credentials=None, customer_id=None, extra=None,
                 account_number=None, invoice_number=None, bill_year=None,
                 date_of_birth=None, zip_code=None):
        # call super init
        super().__init__(project_id, mode, test_request,
                         interaction_id, interaction_type, client_reference_code,
                         processor, credentials, customer_id, extra)
        # for the account number
        self.account_number = account_number
        # for the invoice number
        self.invoice_number = invoice_number
        # for the bill year
        self.bill_year = bill_year
        # for DOB
        self.date_of_birth = date_of_birth
        # for zip code
        self.zip_code = zip_code


class Transaction(BaseTransaction):
    message = models.ForeignKey('wiretap.Message', null=True, on_delete=models.PROTECT, related_name='lookups')
    processor = models.CharField(null=True, blank=True, max_length=128, choices=PROCESSOR_CHOICES, db_index=True)
    account_number = models.CharField(null=True, blank=True, max_length=32, db_index=True)
    invoice_number = models.CharField(null=True, blank=True, max_length=32, db_index=True)
    bill_year = models.CharField(null=True, blank=True, max_length=8, db_index=True)
    date_of_birth = models.DateField(null=True, blank=True, max_length=32, db_index=True)
    zip_code = models.CharField(null=True, blank=True, max_length=16, db_index=True)
    balance_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, db_index=True)
    balance_due_date = models.DateField(null=True, blank=True, db_index=True)
