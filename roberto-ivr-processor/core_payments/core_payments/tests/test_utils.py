from django.test import TestCase
from rest_framework.serializers import ValidationError

from core_payments.utils import assign_if_not_none, list_to_string, validate_keys_in_dict


class Temp(object):
    """An object to quickly test assigning a value."""


class UtilsTest(TestCase):
    def test_assign_if_not_none_dict_value(self):
        temp = dict()
        assign_if_not_none(temp, 'value', 'value')
        self.assertIn('value', temp)

    def test_assign_if_not_none_dict_none(self):
        temp = dict()
        assign_if_not_none(temp, 'value', None)
        self.assertNotIn('value', temp)

    def test_assign_if_not_none_obj_value(self):
        temp = Temp()
        assign_if_not_none(temp, 'value', 'value')
        self.assertTrue(hasattr(temp, 'value'))

    def test_assign_if_not_none_obj_none(self):
        temp = Temp()
        assign_if_not_none(temp, 'value', None)
        self.assertFalse(hasattr(temp, 'value'))

    def test_list_to_string(self):
        values = ['value1', 'value2', 'value3']
        expected_result = '`value1`, `value2`, `value3`'
        result = list_to_string(values)
        self.assertEqual(result, expected_result)

    def test_validate_keys_not_in_dict(self):
        keys_list = ['value1', 'value2', 'value3']
        dict_to_validate = {}
        with self.assertRaises(ValidationError):
            validate_keys_in_dict(keys_list, dict_to_validate)

    def test_validate_keys_in_dict(self):
        keys_list = ['value1', 'value2', 'value3']
        dict_to_validate = {
            'value1': '',
            'value2': '',
            'value3': '',
            'value4': ''
        }
        try:
            validate_keys_in_dict(keys_list, dict_to_validate)
        except ValidationError:
            self.fail('validate_keys_in_dict() raised ValidationError unexpectedly.')
