import urllib.parse
from requests import Session, Request
from core_payments.chd_utils import verify_and_mask_message


class Requests(object):
    def __init__(self, transaction, sanitize_request=True, sanitize_response=True, to_mask=None):
        self.transaction = transaction
        self.sanitize_request = sanitize_request
        self.sanitize_response = sanitize_response
        self.to_mask = to_mask or []
        self.session = Session()
    
    def send(self, method, endpoint, **kwargs):
        req = Request(method, endpoint, **kwargs)
        prepared_req = self.session.prepare_request(req)
        if prepared_req.body:
            # log the request body if we have one
            body = prepared_req.body
            if type(body) == bytes:  # the body is encoded
                body = body.decode()
            processor_request = urllib.parse.unquote(body)  # so xml bodies are more readable in database
        else:
            # otherwise, log the URL parameters
            processor_request = prepared_req.path_url
        if self.sanitize_request:
            processor_request = verify_and_mask_message(processor_request, self.to_mask)
        self.transaction.processor_request = processor_request
        self.transaction.save()
        resp = self.session.send(prepared_req)
        # log the response body
        processor_response = resp.text
        if self.sanitize_response:
            processor_response = verify_and_mask_message(processor_response, self.to_mask)
        self.transaction.processor_response = processor_response
        self.transaction.save()
        return resp
