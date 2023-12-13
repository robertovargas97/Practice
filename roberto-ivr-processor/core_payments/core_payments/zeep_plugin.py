from zeep import Plugin
from lxml import etree
from core_payments.chd_utils import verify_and_mask_message


class LogPlugin(Plugin):
    def __init__(self, transaction, sanitize_request=True, sanitize_response=True, to_mask=None):
        self.transaction = transaction
        self.sanitize_request = sanitize_request
        self.sanitize_response = sanitize_response
        self.to_mask = to_mask or []

    def egress(self, envelope, http_headers, operation, binding_options):
        # handle outgoing data here - requests to API
        processor_request = etree.tostring(envelope, pretty_print=True, encoding='unicode')
        if self.sanitize_request:
            processor_request = verify_and_mask_message(processor_request, self.to_mask)
        self.transaction.processor_request = processor_request
        self.transaction.save()
        return envelope, http_headers

    def ingress(self, envelope, http_headers, operation):
        # handle inbound data here - responses from API
        processor_response = etree.tostring(envelope, pretty_print=True, encoding='unicode')
        if self.sanitize_response:
            processor_response = verify_and_mask_message(processor_response, self.to_mask)
        self.transaction.processor_response = processor_response
        self.transaction.save()
        return envelope, http_headers

