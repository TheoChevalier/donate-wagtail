import json
import logging

from django.conf import settings
from django.core.serializers.json import DjangoJSONEncoder

import django_rq

from donate.payments.sqs import sqs_client

logger = logging.getLogger(__name__)

queue = django_rq.get_queue('default')

ZERO_DECIMAL_CURRENCIES = [
  'BIF',
  'CLP',
  'DJF',
  'GNF',
  'JPY',
  'KMF',
  'KRW',
  'MGA',
  'PYG',
  'RWF',
  'VND',
  'VUV',
  'XAF',
  'XOF',
  'XPF'
];


def zero_decimal_currency_fix(amount, currency):
    if currency.upper() not in ZERO_DECIMAL_CURRENCIES:
        return amount / 100

    return amount


def send_stripe_transaction_to_basket(transaction_data):
    client = sqs_client()
    if client is None:
        return

    subscription = transaction_data.subscription
    charge = transaction_data.charge
    metadata = transaction_data.metadata
    donation_url = transaction_data.donation_url
    conversion_amount = transaction_data.conversion_amount
    net_amount = transaction_data.net_amount
    transaction_fee = transaction_data.transaction_fee

    project = 'mozillafoundation'

    if metadata.thunderbird:
        project = 'thunderbird'
    elif metadata.glassroomnyc:
        project = 'glassroomnyc'

    payload = {
        'data': {
            'event_type': 'donation',
            'last_name': subscription.customer.sources.data[0].name,
            'email': subscription.customer.email,
            'donation_amount': zero_decimal_currency_fix(charge.amount, charge.currency),
            'currency': charge.currency,
            'created': charge.created,
            'recurring': True,
            'frequency': 'monthly',
            'service': 'stripe',
            'transaction_id': charge.id,
            'subscription_id': subscription.id,
            'donation_url': donation_url,
            'project': project,
            'locale': subscription.metadata.locale,
            'last_4': subscription.customer.sources.data[0].last4,
            'conversion_amount': conversion_amount,
            'net_amount': net_amount,
            'transaction_fee': transaction_fee
        }
    }

    client.send_message(
        QueueUrl=settings.BASKET_SQS_QUEUE_URL,
        MessageBody=json.dumps(payload, cls=DjangoJSONEncoder, sort_keys=True),
    )
