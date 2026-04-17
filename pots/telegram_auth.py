import hashlib
import hmac
from functools import wraps
from django.conf import settings
from django.shortcuts import redirect


def verify_telegram_auth(data: dict) -> bool:
    """Verify Telegram Login Widget data using HMAC-SHA256."""
    received_hash = data.get('hash')
    if not received_hash:
        return False

    check_dict = {k: v for k, v in data.items() if k != 'hash'}
    check_string = '\n'.join(f"{k}={v}" for k, v in sorted(check_dict.items()))

    secret_key = hashlib.sha256(settings.TELEGRAM_BOT_TOKEN.encode()).digest()
    expected_hash = hmac.new(secret_key, check_string.encode(), hashlib.sha256).hexdigest()

    return hmac.compare_digest(expected_hash, received_hash)


def get_telegram_user(request):
    """Return the Telegram user dict from session, or None."""
    return request.session.get('telegram_user')


def login_required(view_func):
    """Decorator: redirect to home if not authenticated via Telegram."""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not get_telegram_user(request):
            request.session['next'] = request.get_full_path()
            return redirect('home')
        return view_func(request, *args, **kwargs)
    return wrapper
