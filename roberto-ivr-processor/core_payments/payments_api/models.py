from django.db import models
import dateparser

from core_payments.models import (
    BaseTransaction,
    BaseTransactionRequest,
    BaseTransactionResponse
)


# Define common constant here

PROCESSOR_AUTHORIZE_NET = 'authorize_net'
PROCESSOR_CYBERSOURCE = 'cybersource'
PROCESSOR_PAYRAZR = 'payrazr'
PROCESSOR_PAYRAZR_REST = 'payrazr_rest'
PROCESSOR_PAYTRACE = 'paytrace'
PROCESSOR_TRUST_COMMERCE = 'trustcommerce'
PROCESSOR_BLUEFIN = 'bluefin'
PROCESSOR_USAEPAY = 'usaepay'
PROCESSOR_ELAVON_CONVERGEPAY = 'elavon_convergepay'
PROCESSOR_ELAVON_INSTAMED = 'elavon_instamed'
PROCESSOR_CONVENIENT_PAYMENTS = 'convenient_payments'
PROCESSOR_CHASE = 'chase'
PROCESSOR_STRIPE = 'stripe'

PROCESSOR_CHOICES = [
    (PROCESSOR_AUTHORIZE_NET, 'Authorize.Net'),
    (PROCESSOR_CYBERSOURCE, 'Cybersource'),
    (PROCESSOR_PAYRAZR, 'Payrazr'),
    (PROCESSOR_PAYRAZR_REST, 'Payrazr REST'),
    (PROCESSOR_PAYTRACE, 'PayTrace'),
    (PROCESSOR_TRUST_COMMERCE, 'TrustCommerce'),
    (PROCESSOR_USAEPAY, 'USAePay'),
    (PROCESSOR_BLUEFIN, 'Bluefin PayConex'),
    (PROCESSOR_ELAVON_CONVERGEPAY, 'Elavon Convergepay'),
    (PROCESSOR_ELAVON_INSTAMED, 'Elavon Instamed'),
    (PROCESSOR_CONVENIENT_PAYMENTS, 'Convenient Payments'),
    (PROCESSOR_CHASE, 'Chase'),
    (PROCESSOR_STRIPE,'Stripe')
]

TRANSACTION_TYPE_AUTHORIZE = 'authorize'
TRANSACTION_TYPE_CAPTURE = 'capture'
TRANSACTION_TYPE_SALE = 'sale'
TRANSACTION_TYPE_VOID = 'void'
TRANSACTION_TYPE_REFUND = 'refund'
TRANSACTION_TYPE_CHOICES = [
    (TRANSACTION_TYPE_AUTHORIZE, 'Authorize'),
    (TRANSACTION_TYPE_CAPTURE, 'Capture'),
    (TRANSACTION_TYPE_SALE, 'Sale'),
    (TRANSACTION_TYPE_VOID, 'Void'),
    (TRANSACTION_TYPE_REFUND, 'Refund'),
]

TENDER_TYPE_CREDIT_CARD = 'credit_card'
TENDER_TYPE_ACH = 'ach'
TENDER_TYPE_CHOICES = [
    (TENDER_TYPE_CREDIT_CARD, 'Credit Card'),
    (TENDER_TYPE_ACH, 'ACH / e-Check')
]

TENDER_TYPE_NOT_REQUIRED_TRANSACTIONS = [
    TRANSACTION_TYPE_CAPTURE,
    TRANSACTION_TYPE_VOID
]

TENDER_TYPE_ACH_ALLOWED_TRANSACTIONS = [
    TRANSACTION_TYPE_SALE,
    TRANSACTION_TYPE_REFUND
]

AMOUNT_NOT_REQUIRED_TRANSACTIONS = [
    TRANSACTION_TYPE_VOID
]

CARD_TYPE_VISA = 'visa'
CARD_TYPE_MASTERCARD = 'mastercard'
CARD_TYPE_AMERICAN_EXPRESS = 'american_express'
CARD_TYPE_DISCOVER = 'discover'
CARD_TYPE_JCB = 'jcb'
CARD_TYPE_AMEX = 'amex'
CARD_DINERS_CLUB ='diners club'
CARD_TYPE_CHOICES = [
    (CARD_TYPE_VISA, 'Visa'),
    (CARD_TYPE_MASTERCARD, 'MasterCard'),
    (CARD_TYPE_AMERICAN_EXPRESS, 'American Express'),
    (CARD_TYPE_DISCOVER, 'Discover'),
    (CARD_TYPE_JCB, 'JCB'),
    (CARD_TYPE_AMEX, 'Amex'),
    (CARD_DINERS_CLUB ,'Diners Club')
]

ACH_ACCOUNT_TYPE_SAVINGS = 'savings'
ACH_ACCOUNT_TYPE_CHECKING = 'checking'
ACH_ACCOUNT_TYPE_COMMERCIAL = 'commercial'
ACH_ACCOUNT_TYPE_INDIVIDUAL = 'individual'
ACH_ACCOUNT_TYPE_COMPANY = 'company'
ACH_ACCOUNT_TYPE_CORPORATE = 'corporate'
ACH_ACCOUNT_TYPE_CHOICES = [
    (ACH_ACCOUNT_TYPE_SAVINGS, 'Savings'),
    (ACH_ACCOUNT_TYPE_CHECKING, 'Checking'),
    (ACH_ACCOUNT_TYPE_COMMERCIAL, 'Commercial'),
    (ACH_ACCOUNT_TYPE_INDIVIDUAL,'Individual'),
    (ACH_ACCOUNT_TYPE_COMPANY , 'Company'),
    (ACH_ACCOUNT_TYPE_CORPORATE , 'Corporate')
]


class TransactionResponse(BaseTransactionResponse):
    pass


class TransactionRequest(BaseTransactionRequest):
    def __init__(self, project_id=None, mode=None, test_request=None,
                 interaction_id=None, interaction_type=None, client_reference_code=None,
                 processor=None, credentials=None, customer_id=None,
                 transaction_type=None, tender_type=None, amount=None, original_transaction_id=None,
                 card_account_number=None, card_verification_value=None,
                 card_expiry_month=None, card_expiry_year=None, card_type=None,
                 ach_account_number=None, ach_routing_number=None, ach_account_type=None,
                 ach_check_number=None, ach_name_on_account=None,
                 bill_to_first_name=None, bill_to_last_name=None, bill_to_company=None,
                 bill_to_address=None, bill_to_city=None, bill_to_county=None,
                 bill_to_state=None, bill_to_zip=None, bill_to_country=None,
                 bill_to_phone=None, bill_to_email=None,
                 ship_to_first_name=None, ship_to_last_name=None, ship_to_company=None,
                 ship_to_address=None, ship_to_city=None, ship_to_county=None,
                 ship_to_state=None, ship_to_zip=None, ship_to_country=None,
                 ship_to_phone=None, ship_to_email=None,
                 extra=None, ignore_avs_result=None,
                 description=None, invoice_number=None):
        # invoke super init
        super().__init__(
            project_id, mode, test_request,
            interaction_id, interaction_type, client_reference_code,
            processor, credentials, customer_id, extra
        )
        # transaction type, for e.g., sale, void etc
        self.transaction_type = transaction_type
        # tender type, for e.g. ach, credit card etc
        self.tender_type = tender_type
        # payment amount
        self.amount = amount
        # original transaction id for capture or void transactions
        self.original_transaction_id = original_transaction_id
        # card details
        self.card_account_number = card_account_number
        self.card_verification_value = card_verification_value
        self.card_expiry_month = card_expiry_month
        self.card_expiry_year = card_expiry_year
        self.card_type = card_type
        # bank details for ACH payments
        self.ach_name_on_account = ach_name_on_account
        self.ach_account_number = ach_account_number
        self.ach_routing_number = ach_routing_number
        self.ach_account_type = ach_account_type
        self.ach_check_number = ach_check_number
        # billing address
        self.bill_to_first_name = bill_to_first_name
        self.bill_to_last_name = bill_to_last_name
        self.bill_to_company = bill_to_company
        self.bill_to_address = bill_to_address
        self.bill_to_city = bill_to_city
        self.bill_to_county = bill_to_county
        self.bill_to_state = bill_to_state
        self.bill_to_zip = bill_to_zip
        self.bill_to_country = bill_to_country
        self.bill_to_phone = bill_to_phone
        self.bill_to_email = bill_to_email
        # shipping address
        self.ship_to_first_name = ship_to_first_name
        self.ship_to_last_name = ship_to_last_name
        self.ship_to_company = ship_to_company
        self.ship_to_address = ship_to_address
        self.ship_to_city = ship_to_city
        self.ship_to_county = ship_to_county
        self.ship_to_state = ship_to_state
        self.ship_to_zip = ship_to_zip
        self.ship_to_country = ship_to_country
        self.ship_to_phone = ship_to_phone
        self.ship_to_email = ship_to_email
        # other options
        self.ignore_avs_result = ignore_avs_result
        self.description = description
        self.invoice_number = invoice_number
        #Used by stripre processor

    @property
    def card_expiry_date(self):
        """A utility method to quickly return the expiry date of the card as a valid Python datetime object."""
        if not self.card_expiry_month or not self.card_expiry_year:
            return None
        # gather the separate months and year and combine them
        inferred_date = '{}{}'.format(str(self.card_expiry_month).zfill(2), str(self.card_expiry_year).zfill(2))
        # dateparser will always give us the last date of the month when parsing just month and year
        return dateparser.parse(inferred_date, ['%m%y', ])

    @property
    def amount_in_cents(self):
        """A utility method to quickly return the payment amount in cents."""
        if not self.amount:
            return None
        return int(self.amount * 100)


class Transaction(BaseTransaction):
    message = models.ForeignKey('wiretap.Message', null=True, on_delete=models.PROTECT, related_name='payments')
    processor = models.CharField(null=True, blank=True, max_length=128, choices=PROCESSOR_CHOICES,db_index=True)
    transaction_type = models.CharField(null=True, blank=True, max_length=128, choices=TRANSACTION_TYPE_CHOICES,db_index=True)
    tender_type = models.CharField(null=True, blank=True, max_length=16, choices=TENDER_TYPE_CHOICES, db_index=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, db_index=True)
    original_transaction_id = models.CharField(max_length=64, null=True, blank=True, db_index=True)
    card_account_number = models.CharField(null=True, blank=True, max_length=4, db_index=True)
    card_type = models.CharField(null=True, blank=True, max_length=32, choices=CARD_TYPE_CHOICES, db_index=True)
    ach_name_on_account = models.CharField(null=True, blank=True, max_length=256)
    ach_account_number = models.CharField(null=True, blank=True, max_length=4, db_index=True)
    ach_routing_number = models.CharField(null=True, blank=True, max_length=32, db_index=True)
    ach_account_type = models.CharField(null=True, blank=True, max_length=32, choices=ACH_ACCOUNT_TYPE_CHOICES,db_index=True)
    ach_check_number = models.CharField(null=True, blank=True, max_length=8)
    bill_to_first_name = models.CharField(null=True, blank=True, max_length=128)
    bill_to_last_name = models.CharField(null=True, blank=True, max_length=128)
    bill_to_company = models.CharField(null=True, blank=True, max_length=128)
    bill_to_address = models.CharField(null=True, blank=True, max_length=128)
    bill_to_city = models.CharField(null=True, blank=True, max_length=128)
    bill_to_county = models.CharField(null=True, blank=True, max_length=128)
    bill_to_state = models.CharField(null=True, blank=True, max_length=128)
    bill_to_zip = models.CharField(null=True, blank=True, max_length=16)
    bill_to_country = models.CharField(null=True, blank=True, max_length=128)
    bill_to_phone = models.CharField(null=True, blank=True, max_length=32)
    bill_to_email = models.EmailField(null=True, blank=True)
    ship_to_first_name = models.CharField(null=True, blank=True, max_length=128)
    ship_to_last_name = models.CharField(null=True, blank=True, max_length=128)
    ship_to_company = models.CharField(null=True, blank=True, max_length=128)
    ship_to_address = models.CharField(null=True, blank=True, max_length=128)
    ship_to_city = models.CharField(null=True, blank=True, max_length=128)
    ship_to_county = models.CharField(null=True, blank=True, max_length=128)
    ship_to_state = models.CharField(null=True, blank=True, max_length=128)
    ship_to_zip = models.CharField(null=True, blank=True, max_length=16)
    ship_to_country = models.CharField(null=True, blank=True, max_length=128)
    ship_to_phone = models.CharField(null=True, blank=True, max_length=32)
    ship_to_email = models.EmailField(null=True, blank=True)
    description = models.CharField(null=True, blank=True, max_length=256)
    invoice_number = models.CharField(null=True, blank=True, max_length=32)

    def __str__(self):
        return "project: {0} - {1} ({2})".format(self.project_id, self.processor, self.processor_result)
