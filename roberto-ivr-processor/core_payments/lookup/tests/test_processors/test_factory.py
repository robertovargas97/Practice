from django.test import TestCase
from ...processors import ConvenientPayments
from ...processors.factory import ProcessorFactory
from ...models import TransactionRequest, PROCESSOR_CONVENIENT_PAYMENTS


class ProcessorFactoryTestCase(TestCase):
    def test_get_factory_authorize_net(self):
        transaction_request = TransactionRequest(processor=PROCESSOR_CONVENIENT_PAYMENTS)
        processor = ProcessorFactory().get_processor(transaction_request)
        self.assertTrue(processor.__module__ == ConvenientPayments.__module__
                        and processor.__name__ == ConvenientPayments.__name__)

    def test_get_factory_not_implemented(self):
        transaction_request = TransactionRequest(processor='Not Implemented')
        with self.assertRaises(NotImplementedError):
            ProcessorFactory().get_processor(transaction_request)
