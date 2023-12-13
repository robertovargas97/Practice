from itg_django_utils.api.models import ApiResponse, Metadata
from itg_django_utils.common.utils import serializer_errors_to_list
from rest_framework import viewsets, status
from rest_framework.response import Response

from report.serializers import SingleInteractionRequestSerializer, SingleInteractionReportApiResponseSerializer, \
    MultipleInteractionsRequestSerializer, PaymentsReportApiResponseSerializer, LookupsReportApiResponseSerializer
from payments_api.models import Transaction as PaymentTransaction
from lookup.models import Transaction as LookupTransaction
from report.utils import get_query_and_sort_params, get_paginated_data, get_wiretap_messages


class SingleInteractionReportViewSet(viewsets.ViewSet):

    def list(self, request, project_id):
        request_serializer = SingleInteractionRequestSerializer(data=request.GET)
        if request_serializer.is_valid():  # validate the request
            # get the response data
            interaction_id = request_serializer.validated_data.get('interaction_id')
            query_params = {'interaction_id': interaction_id, 'project_id': project_id}

            # get those transactions that actually called the payments processor
            payments = PaymentTransaction.objects.filter(**query_params)
            lookups = LookupTransaction.objects.filter(**query_params)

            # get those transactions that failed on validation and didn't call the processor - we get them from
            # wiretap - we exclude those messages we already have in the result because they're related to a transaction
            payments = list(payments) + get_wiretap_messages(interaction_id, 'payments',
                                                             exclude=payments.values_list('message_id', flat=True))
            lookups = list(lookups) + get_wiretap_messages(interaction_id, 'lookups',
                                                           exclude=lookups.values_list('message_id', flat=True))

            # put together the whole response we need to return
            response_data = {'project_id': project_id, 'interaction_id': interaction_id, 'payments': payments,
                             'lookups': lookups}

            # return query results
            api_response = ApiResponse(data=[response_data])
            api_response_serializer = SingleInteractionReportApiResponseSerializer(api_response)
            return Response(api_response_serializer.data, status=status.HTTP_200_OK)
        else:
            errors = serializer_errors_to_list(request_serializer.errors)
            api_response = ApiResponse(metadata=Metadata(errors))
            api_response_serializer = SingleInteractionReportApiResponseSerializer(api_response)
            return Response(api_response_serializer.data, status=status.HTTP_400_BAD_REQUEST)


class PaymentsReportViewSet(viewsets.ViewSet):

    def list(self, request, project_id):
        request_serializer = MultipleInteractionsRequestSerializer(data=request.GET)
        if request_serializer.is_valid():  # validate the request params
            response_data = {}
            clean_data = request_serializer.validated_data
            skip = clean_data.get('skip')
            limit = clean_data.get('limit')

            # get the response data according to params received
            query_params, sort_by = get_query_and_sort_params(clean_data, project_id)
            payments = PaymentTransaction.objects.filter(**query_params).order_by(sort_by)

            # get the required page if pagination requested
            if skip or limit:
                response_data['total'] = payments.count()  # we return the total when paginated data
                payments = get_paginated_data(payments, skip, limit)

            response_data['transactions'] = payments

            # return query results
            api_response = ApiResponse(data=[response_data])
            api_response_serializer = PaymentsReportApiResponseSerializer(api_response)
            return Response(api_response_serializer.data, status=status.HTTP_200_OK)
        else:
            errors = serializer_errors_to_list(request_serializer.errors)
            api_response = ApiResponse(metadata=Metadata(errors))
            api_response_serializer = PaymentsReportApiResponseSerializer(api_response)
            return Response(api_response_serializer.data, status=status.HTTP_400_BAD_REQUEST)


class LookupsReportViewSet(viewsets.ViewSet):

    def list(self, request, project_id):
        request_serializer = MultipleInteractionsRequestSerializer(data=request.GET)
        if request_serializer.is_valid():  # validate the request params
            response_data = {}
            clean_data = request_serializer.validated_data
            skip = clean_data.get('skip')
            limit = clean_data.get('limit')

            # get the response data according to params received
            query_params, sort_by = get_query_and_sort_params(clean_data, project_id)
            lookups = LookupTransaction.objects.filter(**query_params).order_by(sort_by)

            # get the required page if pagination requested
            if skip or limit:
                response_data['total'] = lookups.count()  # we return the total when paginated data
                lookups = get_paginated_data(lookups, skip, limit)

            response_data['transactions'] = lookups

            # return query results
            api_response = ApiResponse(data=[response_data])
            api_response_serializer = LookupsReportApiResponseSerializer(api_response)
            return Response(api_response_serializer.data, status=status.HTTP_200_OK)
        else:
            errors = serializer_errors_to_list(request_serializer.errors)
            api_response = ApiResponse(metadata=Metadata(errors))
            api_response_serializer = LookupsReportApiResponseSerializer(api_response)
            return Response(api_response_serializer.data, status=status.HTTP_400_BAD_REQUEST)