from django.db import models
import json


class _NotSet(object):
    pass


class Tap(models.Model):
    help_text_mask_chd = 'When enabled, all 3 or 4 digit CVV values are masked in the request body.' \
        ' Also masks all but last 4 characters for credit card numbers.'
    path_regex = models.CharField(max_length=1024, null=False, blank=False)
    mask_chd = models.BooleanField(default=True, help_text=help_text_mask_chd)
    is_active = models.BooleanField(default=False)

    def __str__(self):
        return self.path_regex


class Message(models.Model):
    started_at = models.DateTimeField(null=False, blank=False, db_index=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    remote_addr = models.CharField(max_length=128, null=True, blank=True, db_index=True)

    req_method = models.CharField(max_length=32, null=True, blank=True)
    req_path = models.TextField(null=True, blank=True)
    req_headers_json = models.TextField(null=True, blank=True)
    req_body = models.TextField(null=True, blank=True)

    res_status_code = models.PositiveIntegerField(null=True, blank=True)
    res_reason_phrase = models.CharField(max_length=128, null=True, blank=True)
    res_headers_json = models.TextField(null=True, blank=True)
    res_body = models.TextField(null=True, blank=True)
    interaction_id = models.CharField(null=True, blank=True, max_length=64, db_index=True)

    @property
    def duration(self):
        if self.ended_at is None:
            return None
        return (self.ended_at - self.started_at).total_seconds()

    @property
    def req_headers(self):
        return json.loads(self.req_headers_json)

    @property
    def res_headers(self):
        return json.loads(self.res_headers_json)

    def get_req_header(self, key, default=_NotSet):
        return self._get_header(self.req_headers, key, default)

    def get_res_header(self, key, default=_NotSet):
        return self._get_header(self.res_headers, key, default)

    def _get_header(self, headers, search_key, default):
        search_key = search_key.title()
        try:
            return next(
                value
                for (key, value) in headers
                if key == search_key
            )
        except StopIteration:
            if default is _NotSet:
                raise KeyError(search_key)
            else:
                return default

    def __str__(self):
        return '{} {}'.format(self.req_method, self.req_path)
