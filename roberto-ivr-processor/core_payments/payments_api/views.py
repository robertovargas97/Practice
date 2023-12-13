from itg_django_utils.api.models import ApiResponse, Metadata
from itg_django_utils.common.utils import serializer_errors_to_list
from rest_framework import viewsets, status
from rest_framework.response import Response
from core_payments.utils import format_error_dict
from .models import TransactionResponse
from .serializers import TransactionRequestSerializer, ApiResponseTransactionResponseSerializer
from .processors.factory import ProcessorFactory
from core_payments.models import (
    RESULT_ERROR,
    RESULT_DECLINED
)


class TransactionViewSet(viewsets.ViewSet):
    serializer_class = TransactionRequestSerializer

    def create(self, request, project_id):
        transaction_response = None
        try:
            data = request.data.copy()
            # even if project_id comes in request we override it with the right one with permissions already ensured
            # by the middleware, user might be sending a different one in the json data - not allowed
            data['project_id'] = project_id

            # get request and validate it
            request_serializer = TransactionRequestSerializer(data=data)
            request_serializer.is_valid(raise_exception=True)
            transaction_request = request_serializer.save()

            # get the processor and process the transaction
            Processor = ProcessorFactory().get_processor(transaction_request)
            transaction_response = Processor(request, transaction_request).execute()

            # any of those 2 status are considered error - need to send the error message in metadata
            if transaction_response.result == RESULT_ERROR or \
                    transaction_response.result == RESULT_DECLINED:
                raise Exception(transaction_response.message)

            # return result
            api_response = ApiResponse(data=[transaction_response])
            response_serializer = ApiResponseTransactionResponseSerializer(api_response)
            return Response(response_serializer.data)
        except Exception as e:
            # get the error -> maybe comes from the processor (transaction response) or exception detail if it's
            # serializer validation error or just the exception message per se in any other case
            error = transaction_response.message if transaction_response else (getattr(e, 'detail', None) or str(e))
            temp = transaction_response or TransactionResponse(result=RESULT_ERROR)
            temp.message = None  # we clean the message if any since it will be in metadata errors
            temp.client_reference_code = request.data.get('client_reference_code', None)
            api_response = ApiResponse(data=[temp],
                                       metadata=Metadata(errors=serializer_errors_to_list(format_error_dict(error))))
            response_serializer = ApiResponseTransactionResponseSerializer(api_response)
            return Response(response_serializer.data, status=status.HTTP_400_BAD_REQUEST)
