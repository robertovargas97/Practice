import ast

from .models import Tap, Message
from django.utils import timezone
import json
import re
from core_payments.chd_utils import verify_and_mask_message, get_values_to_mask
from requests_toolbelt.multipart import decoder


class WireTapMiddleware(object):
    def __init__(self, get_response):
        self.get_response = get_response

    def _prettify(self, content):
        """Tries to prettify the content. If not, returns content as is."""
        try:
            # we primarily deal with JSON, so let's try and see if that works first
            result = json.loads(content.decode('utf-8'))
            result = json.dumps(result, indent=2).encode('utf-8')
        except:
            result = content
        return result

    def __call__(self, request):
        # attempt log the request if the tap is enabled
        request.wiretap_message = None
        should_tap, tap = self._needs_tapping(request)
        if should_tap:
            self._log_request(request)
        # process request as usual
        response = self.get_response(request)
        # if we logged the request, then let's attempt to log the response
        if request.wiretap_message:
            self._log_response(request, response, tap)
        # return the response
        return response

    def _needs_tapping(self, request):
        """Returns a boolean value which determines if a request/response should be stored."""
        for tap in Tap.objects.filter(is_active=True):
            if re.search(tap.path_regex, request.path):
                return True, tap
        return False, None

    def _body_to_dict(self, request):
        """Serializes body content to dict based on the content-type header."""
        content_type = request.META.get('CONTENT_TYPE', '')
        if 'multipart/form-data' in content_type:
            return self._multipart_formdata_to_dict(request.body, content_type)
        elif 'json' in content_type:
            return self._json_to_dict(request.body)
        else:
            # support has not been added for other content types, let's return an appropriate message
            return {'error': 'Support not implemented to serialize {} to dict.'.format(content_type)}

    def _json_to_dict(self, body):
        """Serializes JSON content to dict."""
        try:
            return ast.literal_eval(body.decode('utf-8'))
        except Exception as e:
            return {'error': 'Could not serialize response body to dict.\n{}'.format(str(e))}

    def _multipart_formdata_to_dict(self, content, content_type):
        """Serializes multipart form-data to dict."""
        result = dict()
        try:
            multipart_data = decoder.MultipartDecoder(content, content_type)
            for part in multipart_data.parts:
                result[part.headers[b'content-disposition'].decode('utf-8').split('"')[1]] = part.text
        except Exception as e:
            result['error'] = 'Could not serialize response body to dict.\n{}'.format(str(e))
        return result

    def _log_request(self, request):
        request.wiretap_message = Message()
        request.wiretap_message.started_at = timezone.now()
        request.wiretap_message.remote_addr = request.META.get('REMOTE_ADDR', None)
        request.wiretap_message.req_method = request.method
        request.wiretap_message.req_path = request.path
        req_headers = dict()
        for (key, value) in request.META.items():
            if 'CONTENT_LENGTH' == key:
                req_headers[key] = value
            elif 'CONTENT_TYPE' == key:
                req_headers[key] = value
            elif key.startswith('HTTP_'):
                req_headers[key[5:]] = value
        request.wiretap_message.req_headers_json = json.dumps(req_headers, indent=2)
        if request.body:
            dict_body = self._body_to_dict(request)
            # mask the sensitive data in the body
            sanitized_body = verify_and_mask_message(request.body.decode('utf-8'), get_values_to_mask(dict_body)).encode('utf-8')
            request.wiretap_message.req_body = self._prettify(sanitized_body)
            # extract and save the request interaction id
            request.wiretap_message.interaction_id = dict_body.get('interaction_id', None)
        request.wiretap_message.save()

    def _log_response(self, request, response, tap):
        request.wiretap_message.ended_at = timezone.now()
        request.wiretap_message.res_status_code = response.status_code
        request.wiretap_message.res_reason_phrase = response.reason_phrase
        res_headers = dict()
        for (key, value) in response._headers.items():
            res_headers[value[0].upper()] = value[1]
        request.wiretap_message.res_headers_json = json.dumps(res_headers, indent=2)
        if response.content:
            request.wiretap_message.res_body = self._prettify(response.content)
        request.wiretap_message.save()
