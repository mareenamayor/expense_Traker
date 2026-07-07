from django.conf import settings

def currency_context(request):
    # Return currency symbol from settings file
    return {
        'CURRENCY_SYMBOL': getattr(settings, 'CURRENCY_SYMBOL', 'Rs.')
    }
