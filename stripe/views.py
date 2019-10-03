import json
import stripe
from django.conf import settings
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from .tasks import queue, send_stripe_transaction_to_basket

stripe.api_key = settings.STRIPE_API_KEY
stripe_webhook_secret = settings.STRIPE_WEBHOOK_SECRET


@csrf_exempt
@require_POST
def webhook(request):
    payload = request.body
    sig_header = request.META['HTTP_STRIPE_SIGNATURE']
    event = None

    try:
        event = stripe.Event.construct_from(
            json.loads(payload),
            sig_header,
            stripe_webhook_secret
        )
    except ValueError as e:
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError as e:
        return HttpResponse(status=400)

    if event.type != 'charge.succeeded':
        # only process charge.succeeded events
        return HttpResponse(status=200)

    charge_id = event.data.object.id
    try:
        charge = stripe.Charge.retrieve(
            charge_id,
            expand=['invoice', 'balance_transaction']
        )
    except stripe.error.StripeError as e:
        print('Error fetching Stripe Charge %s' % e.get('message'))
        return HttpResponse(status=400)

    if not charge.invoice or not charge.invoice.subscription:
        return HttpResponse(status=400)

    balance_transaction = charge.balance_transaction
    conversion_amount = balance_transaction.amount / 100
    net_amount = balance_transaction.net / 100

    transaction_fee = 0
    for fee in balance_transaction.fee_details:
        transaction_fee += (fee.amount / 100)

    subscription_id = charge.invoice.subscription

    try:
        subscription = stripe.Subscription.retrieve(subscription_id)
    except stripe.error.StripeError as e:
        print('Error fetching Stripe Subscription %s' % e.get('message'))
        return HttpResponse(status=400)

    metadata = subscription.metadata
    update_data = {'metadata': metadata}
    donation_url = None

    if metadata.donation_url:
        donation_url = metadata.donation_url

    if metadata.thunderbird:
        update_data['description'] = 'Thunderbird monthly'
    elif metadata.glassroomnyc:
        update_data['description'] = 'glassroomnyc monthly'
    else:
        update_data['description'] = 'Mozilla Foundation Monthly Donation'

    try:
        stripe.Charge.update(charge_id, update_data)
    except stripe.error.StripeError as e:
        print('Error updating Stripe Charge description and metadata %s' % e.get('message'))
        return HttpResponse(status=400)

    queue.enqueue(send_stripe_transaction_to_basket, {
        'subscription': subscription,
        'charge': charge,
        'metadata': metadata,
        'donation_url': donation_url,
        'conversion_amount': conversion_amount,
        'net_amount': net_amount,
        'transaction_fee': transaction_fee
    })

    return HttpResponse(status=200)
