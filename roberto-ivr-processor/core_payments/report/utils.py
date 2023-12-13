import datetime

from payments_api.models import Transaction as PaymentTransaction
from lookup.models import Transaction as LookupTransaction
from wiretap.models import Message


def get_query_and_sort_params(clean_data, project_id):
    start_date = clean_data.get('start_date')
    end_date = clean_data.get('end_date')
    interaction_type = clean_data.get('interaction_type')

    # default sort is by created on date and descending
    sort_by = clean_data.get('sort_by', 'created_on')
    sort_dir = clean_data.get('sort_dir', 'desc')
    sort_by = sort_by if sort_dir == 'asc' else '-{0}'.format(sort_by)

    query_params = {'project_id': project_id}
    if start_date and end_date:
        query_params['created_on__gte'] = datetime.datetime.combine(start_date, datetime.time(hour=0, minute=0,
                                                                                              second=0))
        query_params['created_on__lte'] = datetime.datetime.combine(end_date, datetime.time(hour=23, minute=59,
                                                                                            second=59))
    if interaction_type:
        query_params['interaction_type'] = interaction_type
    return query_params, sort_by


def get_paginated_data(queryset, skip, limit):
    # default we return first page and use page size of 10 - if only one param is provided
    skip = skip or 0
    limit = limit or 10
    data = list(queryset[skip:skip + limit])  # get the elements in the required page
    return data


def get_wiretap_messages(interaction_id, transaction_type, exclude):
    # transaction type will be payments or lookups depending on what it needs to search for
    # exclude contains the list of message ids we already have, so we don't add it twice to the end result
    transactions = []
    exclude = [a for a in exclude if a]  # get rid of None and empty in the list to exclude
    transaction_model = PaymentTransaction if transaction_type == 'payments' else LookupTransaction
    messages = Message.objects.filter(interaction_id=interaction_id, req_path__contains='api/{}/'.
                                      format(transaction_type)).exclude(id__in=exclude)
    for message in messages:
        transactions.append(transaction_model(message=message, created_on=message.started_at,
                                              interaction_id=message.interaction_id))
    return transactions
