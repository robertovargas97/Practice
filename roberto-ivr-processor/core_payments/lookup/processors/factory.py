from ..models import TransactionRequest
from ..processors import ConvenientPayments


class ProcessorFactory(object):
    # add your processor to this list
    PROCESSORS = [
        ConvenientPayments
    ]

    def get_processor(self, transaction_request):
        """The factory method to pick the correct processor based on the incoming request."""
        assert transaction_request, TransactionRequest

        for processor in self.PROCESSORS:
            if processor.should_process(transaction_request):
                return processor
        raise NotImplementedError('No implementation available for {}.'.format(transaction_request.processor))
