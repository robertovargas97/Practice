from rest_framework import serializers


def assign_if_not_none(obj, param, value):
    """A method to quickly assign a value if it is not none to either a dictionary or an object."""
    if value:
        if isinstance(obj, dict):
            obj[param] = value
        else:
            setattr(obj, param, value)
        return True
    return False


def format_error_dict(error):
    """
    Formats different types of error to be the same format as serializer errors, so we can use the same serializer and
    methods to format the response no matter where the error comes from or what format it has
    """
    formatted_error = {}
    if isinstance(error, dict):
        for key, value in error.items():
            if not isinstance(value, list):
                value = [value]
            formatted_error[key] = value
    else:
        formatted_error["detail"] = [error]
    return formatted_error


def list_to_string(values):
    """
    Returns a nicely formatted string from the credentials list which can be used for informative purposes like logging
    or returning informative error messages.
    """
    return ', '.join(['`{}`'.format(value) for value in values])


def validate_keys_in_dict(keys_list, dict_to_validate):
    """Validates the presence of the keys from the list in the dict. Raises validation error if keys are not present."""
    if not set(keys_list).issubset(set(dict_to_validate.keys())):
        raise serializers.ValidationError(
            '{} are required as part of credentials.'.format(list_to_string(keys_list))
        )


def key_value_string_to_dict(value, line_separator='\n', key_value_separator='='):
    """Parsers a key/value string and returns a dictionary."""
    result = dict()
    lines = value.split(line_separator)
    for item in lines:
        parts = item.split(key_value_separator)
        if len(parts) > 1:
            result[parts[0]] = parts[1]
        else:
            if parts[0]:
                if 'extra' not in result:
                    result['extra'] = []
                result['extra'].append(parts[0])
    return result
