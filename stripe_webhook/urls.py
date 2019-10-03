from django.urls import path

from . import views

app_name = 'stripe'

urlpatterns = [
    path(
        'webhook/',
        views.webhook,
        name='stripe_webhook'
    ),
]
