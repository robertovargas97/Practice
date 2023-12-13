from itg_django_utils.api.serializers import ApiResponseSerializer
from rest_framework import serializers
from .models import (
    TransactionRequest,
    TransactionResponse,
    PROCESSOR_CHOICES,
    TRANSACTION_TYPE_CHOICES,
    TENDER_TYPE_CHOICES,
    CARD_TYPE_CHOICES,
    ACH_ACCOUNT_TYPE_CHOICES,
    TENDER_TYPE_CREDIT_CARD,
    TENDER_TYPE_ACH,
    TENDER_TYPE_NOT_REQUIRED_TRANSACTIONS,
    TENDER_TYPE_ACH_ALLOWED_TRANSACTIONS,
    AMOUNT_NOT_REQUIRED_TRANSACTIONS
)
from luhn import verify as luhn_verify
from datetime import datetime, timedelta
import dateparser
from core_payments.models import (
    MODE_CHOICES,
    INTERACTION_CHOICES,
    RESULT_CHOICES
)


class TransactionResponseSerializer(serializers.Serializer):
    result = serializers.ChoiceField(choices=RESULT_CHOICES, allow_blank=False)
    transaction_id = serializers.CharField(allow_blank=True)
    message = serializers.CharField(allow_blank=True)
    client_reference_code = serializers.CharField(allow_blank=True)
    processor_response = serializers.DictField(allow_null=True)

    def create(self, validated_data):
        return TransactionResponse(**validated_data)

    def update(self, instance, validated_data):
        instance.result = validated_data.get('result', instance.result)
        instance.transaction_id = validated_data.get('transaction_id', instance.transaction_id)
        instance.message = validated_data('message', instance.message)
        instance.client_reference_code = validated_data('client_reference_code', instance.client_reference_code)
        instance.processor_response = validated_data('processor_response', instance.processor_response)


class TransactionRequestSerializer(serializers.Serializer):
    project_id = serializers.IntegerField()
    mode = serializers.ChoiceField(choices=MODE_CHOICES, allow_blank=False)
    test_request = serializers.BooleanField(default=False, required=False)
    interaction_id = serializers.CharField(required=False)
    interaction_type = serializers.ChoiceField(choices=INTERACTION_CHOICES, allow_blank=False)
    client_reference_code = serializers.CharField(allow_blank=True, required=False)
    customer_id = serializers.CharField(allow_blank=True, required=False)
    processor = serializers.ChoiceField(choices=PROCESSOR_CHOICES, allow_blank=False)
    credentials = serializers.DictField(child=serializers.CharField())
    transaction_type = serializers.ChoiceField(choices=TRANSACTION_TYPE_CHOICES, allow_blank=False)
    tender_type = serializers.ChoiceField(choices=TENDER_TYPE_CHOICES, allow_blank=True, required=False)
    amount = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)
    original_transaction_id = serializers.CharField(allow_blank=True, required=False)
    card_account_number = serializers.CharField(min_length=0, max_length=900, allow_blank=True, required=False)
    card_verification_value = serializers.CharField(min_length=3, max_length=4, allow_blank=True, required=False)
    card_expiry_month = serializers.IntegerField(min_value=1, max_value=12, required=False)
    card_expiry_year = serializers.IntegerField(min_value=1, max_value=99, required=False)
    card_type = serializers.ChoiceField(choices=CARD_TYPE_CHOICES, allow_blank=True, required=False)
    ach_name_on_account = serializers.CharField(max_length=256, allow_blank=True, required=False)
    ach_account_number = serializers.CharField(min_length=1, max_length=19, allow_blank=True, required=False)
    ach_routing_number = serializers.CharField(min_length=9, max_length=9, allow_blank=True, required=False)
    ach_account_type = serializers.ChoiceField(choices=ACH_ACCOUNT_TYPE_CHOICES, allow_blank=True, required=False)
    ach_check_number = serializers.CharField(max_length=8, allow_blank=True, required=False)
    bill_to_first_name = serializers.CharField(allow_blank=True, required=False)
    bill_to_last_name = serializers.CharField(allow_blank=True, required=False)
    bill_to_company = serializers.CharField(allow_blank=True, required=False)
    bill_to_address = serializers.CharField(allow_blank=True, required=False)
    bill_to_city = serializers.CharField(allow_blank=True, required=False)
    bill_to_county = serializers.CharField(allow_blank=True, required=False)
    bill_to_state = serializers.CharField(allow_blank=True, required=False)
    bill_to_zip = serializers.CharField(allow_blank=True, required=False)
    bill_to_country = serializers.CharField(allow_blank=True, required=False)
    bill_to_phone = serializers.CharField(allow_blank=True, required=False)
    bill_to_email = serializers.EmailField(allow_blank=True, required=False)
    ship_to_first_name = serializers.CharField(allow_blank=True, required=False)
    ship_to_last_name = serializers.CharField(allow_blank=True, required=False)
    ship_to_company = serializers.CharField(allow_blank=True, required=False)
    ship_to_address = serializers.CharField(allow_blank=True, required=False)
    ship_to_city = serializers.CharField(allow_blank=True, required=False)
    ship_to_county = serializers.CharField(allow_blank=True, required=False)
    ship_to_state = serializers.CharField(allow_blank=True, required=False)
    ship_to_zip = serializers.CharField(allow_blank=True, required=False)
    ship_to_country = serializers.CharField(allow_blank=True, required=False)
    ship_to_phone = serializers.CharField(allow_blank=True, required=False)
    ship_to_email = serializers.EmailField(allow_blank=True, required=False)
    extra = serializers.DictField(child=serializers.CharField(), required=False)
    ignore_avs_result = serializers.BooleanField(default=False, required=False)
    description = serializers.CharField(allow_blank=True, required=False)
    invoice_number = serializers.CharField(allow_blank=True, required=False)


    def create(self, validated_data):
        return TransactionRequest(**validated_data)

    def update(self, instance, validated_data):
        instance.project_id = validated_data.get('project_id', instance.project_id)
        instance.mode = validated_data.get('mode', instance.mode)
        instance.test_request = validated_data.get('test_request', instance.test_request)
        instance.interaction_id = validated_data.get('interaction_id', instance.interaction_id)
        instance.interaction_type = validated_data.get('interaction_type', instance.interaction_type)
        instance.client_reference_code = validated_data.get('client_reference_code', instance.client_reference_code)
        instance.customer_id = validated_data.get('customer_id', instance.customer_id)
        instance.processor = validated_data.get('processor', instance.processor)
        instance.credentials = validated_data.get('credentials', instance.credentials)
        instance.transaction_type = validated_data.get('transaction_type', instance.transaction_type)
        instance.tender_type = validated_data.get('tender_type', instance.tender_type)
        instance.amount = validated_data.get('amount', instance.amount)
        instance.original_transaction_id = validated_data.get('original_transaction_id', instance.original_transaction_id)
        instance.card_account_number = validated_data.get('card_account_number', instance.card_account_number)
        instance.card_verification_value = validated_data.get('card_verification_value', instance.card_verification_value)
        instance.card_expiry_month = validated_data.get('card_expiry_month', instance.card_expiry_month)
        instance.card_expiry_year = validated_data.get('card_expiry_year', instance.card_expiry_year)
        instance.card_type = validated_data.get('card_type', instance.card_type)
        instance.ach_name_on_account = validated_data.get('ach_name_on_account', instance.ach_name_on_account)
        instance.ach_account_number = validated_data.get('ach_account_number', instance.ach_account_number)
        instance.ach_routing_number = validated_data.get('ach_routing_number', instance.ach_routing_number)
        instance.ach_account_type = validated_data.get('ach_account_type', instance.ach_account_type)
        instance.ach_check_number = validated_data.get('ach_check_number', instance.ach_check_number)
        instance.bill_to_first_name = validated_data.get('bill_to_first_name', instance.bill_to_first_name)
        instance.bill_to_last_name = validated_data.get('bill_to_last_name', instance.bill_to_last_name)
        instance.bill_to_company = validated_data.get('bill_to_company', instance.bill_to_company)
        instance.bill_to_address = validated_data.get('bill_to_address', instance.bill_to_address)
        instance.bill_to_city = validated_data.get('bill_to_city', instance.bill_to_city)
        instance.bill_to_county = validated_data.get('bill_to_county', instance.bill_to_county)
        instance.bill_to_state = validated_data.get('bill_to_state', instance.bill_to_state)
        instance.bill_to_zip = validated_data.get('bill_to_zip', instance.bill_to_zip)
        instance.bill_to_country = validated_data.get('bill_to_country', instance.bill_to_country)
        instance.bill_to_phone = validated_data.get('bill_to_phone', instance.bill_to_phone)
        instance.bill_to_email = validated_data.get('bill_to_email', instance.bill_to_email)
        instance.ship_to_first_name = validated_data.get('ship_to_first_name', instance.ship_to_first_name)
        instance.ship_to_last_name = validated_data.get('ship_to_last_name', instance.ship_to_last_name)
        instance.ship_to_company = validated_data.get('ship_to_company', instance.ship_to_company)
        instance.ship_to_address = validated_data.get('ship_to_address', instance.ship_to_address)
        instance.ship_to_city = validated_data.get('ship_to_city', instance.ship_to_city)
        instance.ship_to_county = validated_data.get('ship_to_county', instance.ship_to_county)
        instance.ship_to_state = validated_data.get('ship_to_state', instance.ship_to_state)
        instance.ship_to_zip = validated_data.get('ship_to_zip', instance.ship_to_zip)
        instance.ship_to_country = validated_data.get('ship_to_country', instance.ship_to_country)
        instance.ship_to_phone = validated_data.get('ship_to_phone', instance.ship_to_phone)
        instance.ship_to_email = validated_data.get('ship_to_email', instance.ship_to_email)
        instance.extra = validated_data.get('extra', instance.extra)
        instance.force_ignore_avs = validated_data.get('force_ignore_avs', instance.force_ignore_avs)
        instance.description = validated_data.get('description', instance.description)
        instance.invoice_number = validated_data.get('invoice_number', instance.invoice_number)

    def validate(self, data):
        """Call validate methods here that are outside of individual field validation."""
        data = self._validate_tender_type(data)
        data = self._validate_amount(data)
        if TENDER_TYPE_CREDIT_CARD == data.get('tender_type')\
                and data.get('transaction_type') not in TENDER_TYPE_NOT_REQUIRED_TRANSACTIONS:
            # call these validation methods if tender type is credit card
            # and transaction type is not capture or void
            data = self._validate_card_number(data)
            data = self._validate_card_expiry(data)
        elif TENDER_TYPE_ACH == data.get('tender_type'):
            # call these validation methods if tender type is ach
            data = self._validate_ach_account_number(data)
            data = self._validate_ach_routing_number(data)
        return data

    def _validate_tender_type(self, data):
        """Perform some validations based on the tender and transaction types."""
        # A tender type should be present unless it is a capture or void transaction
        if data.get('transaction_type') not in TENDER_TYPE_NOT_REQUIRED_TRANSACTIONS \
                and not data.get('tender_type'):
            raise serializers.ValidationError('Tender type is optional for capture or void transactions only. It must be present for all other transactions.')
        # ACH tender types cannot perform auth, capture and void transactions
        if TENDER_TYPE_ACH == data.get('tender_type') \
                and data.get('transaction_type') not in TENDER_TYPE_ACH_ALLOWED_TRANSACTIONS:
            raise serializers.ValidationError('ACH tender type can only be used to perform sale or refund. Authorize, capture or void transactions are not allowed.')
        return data

    def _validate_amount(self, data):
        """An amount should be present for all transactions except for void."""
        if data.get('transaction_type') not in AMOUNT_NOT_REQUIRED_TRANSACTIONS \
            and not data.get('amount'):
            raise serializers.ValidationError('Amount is not required for void transaction only. It must be present for all other transactions.')
        return data

    def _validate_card_number(self, data):
        """Validate card number."""
        if 'card_account_number' not in data:
            raise serializers.ValidationError('Credit card number is required for credit card payments.')
        try:
            int(data['card_account_number'])
        except ValueError:
            raise serializers.ValidationError('Credit card number should only consist of digits.')
        # now perform luhn check
        if luhn_verify(data['card_account_number']):
            return data
        raise serializers.ValidationError('Credit card number is invalid.')

    def _validate_card_expiry(self, data):
        """Validate card expiry date if present. Transactions are allowed without card expiry dates."""
        if 'card_expiry_month' in data and 'card_expiry_year' in data:
            # gather the separate months and year and combine them
            inferred_date = '{}{}'.format(str(data['card_expiry_month']).zfill(2), str(data['card_expiry_year']).zfill(2))
            # dateparser will always give us the last date of the month when parsing just month and year
            # add 1 day to make the expiry date inclusive of the last date
            exp_date = dateparser.parse(inferred_date, ['%m%y', ]) + timedelta(days=1)
            if datetime.today() >= exp_date:
                raise serializers.ValidationError('Credit card has expired.')
        return data

    def _validate_ach_account_number(self, data):
        """Validate bank account number."""
        if 'ach_account_number' not in data:
            raise serializers.ValidationError('Bank account number is required for ACH payments.')
        return data

    def _validate_ach_routing_number(self, data):
        """Validate bank routing numbers."""
        if 'ach_routing_number' not in data:
            raise serializers.ValidationError('Bank routing number is required for ACH payments.')
        return data


class ApiResponseTransactionResponseSerializer(ApiResponseSerializer):
    data = serializers.ListField(child=TransactionResponseSerializer())
