from django.conf import settings


def telegram_bot(request):
    return {'TELEGRAM_BOT_NAME': settings.TELEGRAM_BOT_NAME}
