from django.db import models


# declare some constants here which are used throughout the project

# request constants

INTERACTION_CALL = 'call'
INTERACTION_TEXT = 'text'
INTERACTION_WEB = 'web'
INTERACTION_CHOICES = [
    (INTERACTION_CALL, 'Call'),
    (INTERACTION_TEXT, 'Text'),
    (INTERACTION_WEB, 'Web')
]

MODE_LIVE = 'live'
MODE_TEST = 'test'
MODE_CHOICES = [
    (MODE_LIVE, 'Live'),
    (MODE_TEST, 'Test')
]

# response constants

RESULT_APPROVED = 'approved'
RESULT_REVIEW = 'review'
RESULT_ERROR = 'error'
RESULT_DECLINED = 'declined'
RESULT_CHOICES = [
    (RESULT_APPROVED, 'Approved'),
    (RESULT_REVIEW, 'Held For Review'),
    (RESULT_ERROR, 'Error'),
    (RESULT_DECLINED, 'Declined'),
]


class BaseTransactionResponse(object):
    def __init__(self, result=None, transaction_id=None, message=None, client_reference_code=None,
                 processor_response=None):
        # result of the transaction, for e.g., approved, declined, review, error
        self.result = result
        # a unique id from the processor that identifies a transaction
        self.transaction_id = transaction_id
        # the response from the processor indicating why a transaction succeeded or failed
        self.message = message
        # a unique value that was passed in the request
        self.client_reference_code = client_reference_code
        # send the processor response back for furthe processing
        self.processor_response = processor_response


class BaseTransactionRequest(object):
    def __init__(self, project_id=None, mode=None, test_request=None,
                 interaction_id=None, interaction_type=None, client_reference_code=None,
                 processor=None, credentials=None, customer_id=None, extra=None):
        # required field to associate requests with projects for billing
        self.project_id = project_id
        # set whether to use UAT or live processor end points
        self.mode = mode
        # some processors support this, you are able to do test requests even in live mode
        # this will by pass certain validations like, refund can be performed after 24 hours, and validate the request
        # support for this flag is not implemented by all processors
        self.test_request = test_request
        # useful to track where the request originated from, for e.g., call, text, web etc
        self.interaction_id = interaction_id
        self.interaction_type = interaction_type
        # a unique value that will be passed back in the response
        self.client_reference_code = client_reference_code
        # party responsible for processing the payment, for e.g., authorize_net, cybersource etc.
        self.processor = processor
        self.credentials = credentials
        # a unique field that can be used to identify a customer
        self.customer_id = customer_id
        # for any extra processor specific fields not covered by the fields listed above
        self.extra = extra


class BaseTransaction(models.Model):

    class Meta:
        abstract = True
        indexes = [
            models.Index(fields=['interaction_id', 'interaction_type'])
        ]

    message = models.ForeignKey('wiretap.Message', null=True, on_delete=models.PROTECT)
    project_id = models.IntegerField(null=False, blank=False, db_index=True)
    mode = models.CharField(null=True, blank=True, max_length=16, choices=MODE_CHOICES)
    test_request = models.BooleanField(default=False)
    interaction_id = models.CharField(null=True, blank=True, max_length=64, db_index=True)
    interaction_type = models.CharField(null=True, blank=True, max_length=32, choices=INTERACTION_CHOICES)
    client_reference_code = models.CharField(null=True, blank=True, max_length=128)
    customer_id = models.CharField(null=True, blank=True, max_length=32, db_index=True)
    processor = models.CharField(null=True, blank=True, max_length=128, db_index=True)
    processor_result = models.CharField(null=True, blank=True, max_length=32, choices=RESULT_CHOICES, db_index=True)
    processor_transaction_id = models.CharField(null=True, blank=True, max_length=128, db_index=True)
    processor_message = models.TextField(null=True, blank=True)
    processor_request = models.TextField(null=True, blank=True)
    processor_response = models.TextField(null=True, blank=True)
    created_on = models.DateTimeField(auto_now_add=True, db_index=True)
    modified_on = models.DateTimeField(auto_now=True, db_index=True)
