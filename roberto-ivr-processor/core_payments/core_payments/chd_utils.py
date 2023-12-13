from django.conf import settings


def _mask(value, chars_to_leave_unmasked):
    """Returns a masked string."""
    value = str(value)
    if chars_to_leave_unmasked < 1:
        return ''.rjust(len(value), settings.MASK_CHAR)
    return value[-chars_to_leave_unmasked:].rjust(len(value), settings.MASK_CHAR)


def verify_and_mask_message(message, to_mask):
    """
    Searches for cc/cvv/chd information in the message and masks them when required
    :param message: the message that needs to be checked for sensitive information
    :param to_mask: list that contains the sensitive information we need to mask
    :return: the message with sensitive information, if any, masked
    """
    for element in to_mask:
        if len(element) > 2:  # if not it's just invalid so we don't care about masking it
            leave_unmasked = 4  # we leave the last 4 for other fields
            if len(element) <= 4:
                leave_unmasked = 0  # we masked everything in cvv
            message = message.replace(element, _mask(element, leave_unmasked))
    return message


def get_values_to_mask(request_data):
    """
    Returns the exact values we need to search and replace/mask in the messages we log in database
    :param request_data: the data sent in the request
    :return: a list that contains the values that need to be masked (cc, cvv, etc)
    """
    to_mask = [request_data[element] for element in settings.FIELDS_TO_MASK if request_data.get(element, None)]
    return to_mask
