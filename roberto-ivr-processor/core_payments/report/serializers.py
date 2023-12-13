from itg_django_utils.api.serializers import ApiResponseSerializer
from rest_framework import serializers

from core_payments.models import INTERACTION_CHOICES
from payments_api.models import Transaction as PaymentTransaction
from lookup.models import Transaction as LookupTransaction
from wiretap.models import Message

ASCENDING = 'asc'
DESCENDING = 'desc'
SORT_DIR_CHOICES = [(ASCENDING, 'Ascending'), (DESCENDING, 'Descending')]


class SingleInteractionRequestSerializer(serializers.Serializer):
    interaction_id = serializers.CharField(allow_null=False, allow_blank=False)


class MultipleInteractionsRequestSerializer(serializers.Serializer):
    start_date = serializers.DateField(required=False, allow_null=False)
    end_date = serializers.DateField(required=False, allow_null=False)
    interaction_type = serializers.ChoiceField(choices=INTERACTION_CHOICES, allow_blank=False, required=False)
    skip = serializers.IntegerField(required=False, allow_null=True)
    limit = serializers.IntegerField(required=False, allow_null=True)
    sort_by = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    sort_dir = serializers.ChoiceField(required=False, allow_null=True, allow_blank=True, choices=SORT_DIR_CHOICES)

    def validate(self, data):
        if not data.get('interaction_type') and not all([data.get('start_date'), data.get('end_date')]):
            raise serializers.ValidationError({
                'required': 'Either start_date and end_date or interaction_type need to be provided.'})
        return data


class WiretapMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = ['req_body', 'res_body']


class PaymentTransactionSerializer(serializers.ModelSerializer):
    created_on = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S")
    modified_on = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S")
    message = WiretapMessageSerializer()

    class Meta:
        model = PaymentTransaction
        fields = '__all__'


class LookupTransactionSerializer(serializers.ModelSerializer):
    created_on = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S")
    modified_on = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S")
    message = WiretapMessageSerializer()

    class Meta:
        model = LookupTransaction
        fields = '__all__'


class InteractionSerializer(serializers.Serializer):
    project_id = serializers.IntegerField(required=False)
    interaction_id = serializers.CharField(required=False)
    payments = serializers.ListField(child=PaymentTransactionSerializer())
    lookups = serializers.ListField(child=LookupTransactionSerializer())


class PaymentsReportResponseSerializer(serializers.Serializer):
    total = serializers.IntegerField(required=False)
    transactions = serializers.ListField(child=PaymentTransactionSerializer())


class LookupsReportResponseSerializer(serializers.Serializer):
    total = serializers.IntegerField(required=False)
    transactions = serializers.ListField(child=LookupTransactionSerializer())


class PaymentsReportApiResponseSerializer(ApiResponseSerializer):
    data = serializers.ListField(child=PaymentsReportResponseSerializer())


class LookupsReportApiResponseSerializer(ApiResponseSerializer):
    data = serializers.ListField(child=LookupsReportResponseSerializer())


class SingleInteractionReportApiResponseSerializer(ApiResponseSerializer):
    data = serializers.ListField(child=InteractionSerializer())

