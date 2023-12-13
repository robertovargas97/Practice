from itg_django_utils.api.serializers import ApiResponseSerializer
from rest_framework import serializers
from .models import (
    TransactionRequest,
    TransactionResponse,
    PROCESSOR_CHOICES,
)
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
    balance_amount = serializers.DecimalField(max_digits=10, decimal_places=2, allow_null=True)
    balance_due_date = serializers.DateField(allow_null=True)
    processor_response = serializers.DictField(allow_null=True)

    def create(self, validated_data):
        return TransactionResponse(**validated_data)

    def update(self, instance, validated_data):
        instance.result = validated_data.get('result', instance.result)
        instance.transaction_id = validated_data.get('transaction_id', instance.transaction_id)
        instance.message = validated_data('message', instance.message)
        instance.client_reference_code = validated_data('client_reference_code', instance.client_reference_code)
        instance.balance_amount = validated_data('balance_amount', instance.balance_amount)
        instance.balance_due_date = validated_data('balance_due_date', instance.balance_due_date)
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
    extra = serializers.DictField(child=serializers.CharField(), required=False)
    account_number = serializers.CharField(allow_blank=True, required=False)
    invoice_number = serializers.CharField(allow_blank=True, required=False)
    bill_year = serializers.CharField(allow_blank=True, required=False)
    date_of_birth = serializers.DateField(allow_null=True, required=False)
    zip_code = serializers.CharField(allow_blank=True, required=False)

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
        instance.extra = validated_data.get('extra', instance.extra)
        instance.account_number = validated_data.get('account_number', instance.account_number)
        instance.invoice_number = validated_data.get('invoice_number', instance.invoice_number)
        instance.bill_year = validated_data.get('bill_year', instance.bill_year)
        instance.date_of_birth = validated_data.get('date_of_birth', instance.date_of_birth)
        instance.zip_code = validated_data.get('zip_code', instance.zip_code)

    def validate(self, data):
        """We want to make sure at the very least one of the values is populated prior to performing a lookup."""
        is_valid = False
        is_valid = is_valid or data.get('customer_id', False)
        is_valid = is_valid or data.get('account_number', False)
        is_valid = is_valid or data.get('invoice_number', False)
        is_valid = is_valid or data.get('bill_year', False)
        is_valid = is_valid or data.get('date_of_birth', False)
        is_valid = is_valid or data.get('zip_code', False)
        if not is_valid:
            raise serializers.ValidationError('At least one parameter is required to perform a lookup.')
        return data


class ApiResponseTransactionResponseSerializer(ApiResponseSerializer):
    data = serializers.ListField(child=TransactionResponseSerializer())
