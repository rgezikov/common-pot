# Phase 2 — Runbook: Pot Management

> **Conventions:**
> - `[local]` — run on your developer machine
> - `[server]` — run on the server as `potdev`
> - `[server/root]` — run on the server as `root`

## Prerequisites

- Phase 1 complete
- Telegram account

---

## Step 1 — Create a Telegram Bot

1. Open Telegram and start a chat with [@BotFather](https://t.me/BotFather)
2. Send `/newbot`
3. Choose a name: `Common Pot`
4. Choose a username: `common_pot_bot` (must end in `bot`, must be unique)
5. BotFather will return a **bot token** — save it securely
6. Set the login domain:
   - Send `/setdomain` to BotFather
   - Select your bot
   - Enter `pot.respobit.eu`

Add the bot token to the server `.env` file:

**[server]**
```bash
vi ~/app/.env
```

Add:
```
COMPOT_TELEGRAM_BOT_TOKEN=<your bot token>
```

Add to `commonpot/settings.py`:

**[local]**
```python
TELEGRAM_BOT_TOKEN = os.environ.get('COMPOT_TELEGRAM_BOT_TOKEN', '')
TELEGRAM_BOT_NAME = os.environ.get('COMPOT_TELEGRAM_BOT_NAME', '')
```

Also add bot name to `.env` on the server:
```
COMPOT_TELEGRAM_BOT_NAME=common_pot_bot
```

And locally for development, create a `.env.local` file (not committed):
```
COMPOT_TELEGRAM_BOT_TOKEN=<your bot token>
COMPOT_TELEGRAM_BOT_NAME=common_pot_bot
```

---

## Step 2 — Load Environment Variables Locally

**[local]** Install `python-dotenv`:

```bash
source .venv/bin/activate
uv pip install python-dotenv
uv pip freeze > requirements.txt
```

Add to the top of `commonpot/settings.py`:

```python
from dotenv import load_dotenv
load_dotenv('.env.local')
```

Add `.env.local` to `.gitignore`:

```
.env.local
```

---

## Step 3 — Telegram Authentication View

Telegram Login Widget sends user data as GET parameters to a callback URL. The server must verify the data using HMAC-SHA256 with the bot token.

**[local]** Create `pots/telegram_auth.py`:

```python
import hashlib
import hmac
from django.conf import settings


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
    from functools import wraps
    from django.shortcuts import redirect

    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not get_telegram_user(request):
            return redirect('home')
        return view_func(request, *args, **kwargs)
    return wrapper
```

---

## Step 4 — Views

**[local]** Replace `pots/views.py`:

```python
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST
from .models import Pot, Member
from .telegram_auth import verify_telegram_auth, get_telegram_user, login_required


def home(request):
    user = get_telegram_user(request)
    pots = []
    if user:
        pots = Pot.objects.filter(members__telegram_user_id=user['id'])
    return render(request, 'home.html', {'user': user, 'pots': pots})


def telegram_login(request):
    data = request.GET.dict()
    if not verify_telegram_auth(data):
        return render(request, 'auth_failed.html', status=403)
    request.session['telegram_user'] = {
        'id': int(data['id']),
        'first_name': data.get('first_name', ''),
        'last_name': data.get('last_name', ''),
        'username': data.get('username', ''),
    }
    return redirect('home')


def logout(request):
    request.session.flush()
    return redirect('home')


@login_required
def create_pot(request):
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        description = request.POST.get('description', '').strip()
        if name:
            user = get_telegram_user(request)
            pot = Pot.objects.create(name=name, description=description)
            Member.objects.create(
                pot=pot,
                telegram_user_id=user['id'],
                name=f"{user['first_name']} {user.get('last_name', '')}".strip(),
            )
            return redirect('pot_detail', token=pot.invite_token)
    return render(request, 'create_pot.html')


def pot_detail(request, token):
    pot = get_object_or_404(Pot, invite_token=token)
    members = pot.members.all()
    return render(request, 'pot_detail.html', {'pot': pot, 'members': members})


@login_required
def join_pot(request, token):
    pot = get_object_or_404(Pot, invite_token=token)
    user = get_telegram_user(request)
    Member.objects.get_or_create(
        pot=pot,
        telegram_user_id=user['id'],
        defaults={'name': f"{user['first_name']} {user.get('last_name', '')}".strip()},
    )
    return redirect('pot_detail', token=pot.invite_token)
```

---

## Step 5 — URLs

**[local]** Edit `commonpot/urls.py`:

```python
from django.contrib import admin
from django.urls import path
from pots import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.home, name='home'),
    path('auth/telegram/', views.telegram_login, name='telegram_login'),
    path('logout/', views.logout, name='logout'),
    path('pot/new/', views.create_pot, name='create_pot'),
    path('pot/<uuid:token>/', views.pot_detail, name='pot_detail'),
    path('join/<uuid:token>/', views.join_pot, name='join_pot'),
]
```

---

## Step 6 — Templates

**[local]** Update `pots/templates/base.html` — add logout link to header:

```html
<!DOCTYPE html>
<html lang="en" class="dark">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}Common Pot{% endblock %}</title>
    <script src="https://unpkg.com/htmx.org@2.0.4" integrity="sha384-HGfztofotfshcF7+8n44JQL2oJmowVChPTg48S+jvZoztPfvwD79OC/LTtG6dMp+" crossorigin="anonymous"></script>
    <script src="https://cdn.tailwindcss.com"></script>
    <script>tailwind.config = { darkMode: 'class' }</script>
</head>
<body class="bg-gray-50 text-gray-900 dark:bg-gray-900 dark:text-gray-100 min-h-screen">
    <header class="bg-white dark:bg-gray-800 shadow px-4 py-3 flex items-center justify-between">
        <a href="/" class="text-xl font-bold">Common Pot</a>
        {% if request.session.telegram_user %}
        <a href="/logout/" class="text-sm text-gray-400 hover:text-gray-200">Logout</a>
        {% endif %}
    </header>
    <main class="px-4 py-6 max-w-lg mx-auto">
        {% block content %}{% endblock %}
    </main>
</body>
</html>
```

**[local]** Update `pots/templates/home.html`:

```html
{% extends "base.html" %}
{% block content %}
{% if user %}
    <div class="flex items-center justify-between mb-6">
        <h2 class="text-lg font-semibold">Hello, {{ user.first_name }}</h2>
        <a href="{% url 'create_pot' %}" class="bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium px-4 py-2 rounded-lg">+ New Pot</a>
    </div>
    {% if pots %}
        <ul class="space-y-3">
        {% for pot in pots %}
            <li>
                <a href="{% url 'pot_detail' pot.invite_token %}" class="block bg-white dark:bg-gray-800 rounded-lg px-4 py-3 shadow hover:shadow-md transition">
                    <span class="font-medium">{{ pot.name }}</span>
                    <span class="text-gray-400 text-sm ml-2">{{ pot.members.count }} members</span>
                </a>
            </li>
        {% endfor %}
        </ul>
    {% else %}
        <p class="text-gray-400">No pots yet. Create one or join via an invite link.</p>
    {% endif %}
{% else %}
    <div class="text-center mt-12">
        <h2 class="text-2xl font-bold mb-2">Common Pot</h2>
        <p class="text-gray-400 mb-8">Track shared expenses with your group.</p>
        <script async src="https://telegram.org/js/telegram-widget.js?22"
            data-telegram-login="{{ TELEGRAM_BOT_NAME }}"
            data-size="large"
            data-auth-url="/auth/telegram/"
            data-request-access="write">
        </script>
    </div>
{% endif %}
{% endblock %}
```

**[local]** Create `pots/templates/create_pot.html`:

```html
{% extends "base.html" %}
{% block title %}New Pot{% endblock %}
{% block content %}
<h2 class="text-lg font-semibold mb-4">Create a New Pot</h2>
<form method="post" class="space-y-4">
    {% csrf_token %}
    <div>
        <label class="block text-sm font-medium mb-1">Name</label>
        <input type="text" name="name" required autofocus
            class="w-full bg-gray-100 dark:bg-gray-800 rounded-lg px-4 py-3 text-base focus:outline-none focus:ring-2 focus:ring-blue-500">
    </div>
    <div>
        <label class="block text-sm font-medium mb-1">Description <span class="text-gray-400">(optional)</span></label>
        <input type="text" name="description"
            class="w-full bg-gray-100 dark:bg-gray-800 rounded-lg px-4 py-3 text-base focus:outline-none focus:ring-2 focus:ring-blue-500">
    </div>
    <button type="submit"
        class="w-full bg-blue-600 hover:bg-blue-700 text-white font-medium py-3 rounded-lg text-base">
        Create Pot
    </button>
</form>
{% endblock %}
```

**[local]** Create `pots/templates/pot_detail.html`:

```html
{% extends "base.html" %}
{% block title %}{{ pot.name }}{% endblock %}
{% block content %}
<div class="flex items-center justify-between mb-4">
    <h2 class="text-lg font-semibold">{{ pot.name }}</h2>
</div>
{% if pot.description %}
    <p class="text-gray-400 text-sm mb-4">{{ pot.description }}</p>
{% endif %}

<div class="mb-6">
    <h3 class="text-sm font-medium text-gray-400 uppercase tracking-wide mb-2">Invite Link</h3>
    <div class="bg-gray-100 dark:bg-gray-800 rounded-lg px-4 py-3 text-sm break-all">
        {{ request.scheme }}://{{ request.get_host }}{% url 'join_pot' pot.invite_token %}
    </div>
</div>

<div>
    <h3 class="text-sm font-medium text-gray-400 uppercase tracking-wide mb-2">Members</h3>
    <ul class="space-y-2">
    {% for member in members %}
        <li class="bg-white dark:bg-gray-800 rounded-lg px-4 py-3 shadow text-sm">
            {{ member.name }}
        </li>
    {% endfor %}
    </ul>
</div>
{% endblock %}
```

**[local]** Create `pots/templates/auth_failed.html`:

```html
{% extends "base.html" %}
{% block content %}
<p class="text-red-400">Authentication failed. Please try again.</p>
{% endblock %}
```

---

## Step 7 — Pass Bot Name to Templates

**[local]** Add a context processor in `pots/context_processors.py`:

```python
from django.conf import settings

def telegram_bot(request):
    return {'TELEGRAM_BOT_NAME': settings.TELEGRAM_BOT_NAME}
```

Register it in `commonpot/settings.py` under `TEMPLATES > OPTIONS > context_processors`:

```python
'pots.context_processors.telegram_bot',
```

---

## Step 8 — Deploy to Server

**[local]** Sync files:

```bash
rsync -av --exclude='.venv' --exclude='__pycache__' --exclude='*.sqlite3' --exclude='.git' --exclude='.env.local' \
  <project-root>/ potdev@pot.respobit.eu:~/app/
```

**[server]** Install new dependencies and restart:

```bash
cd ~/app
source .venv/bin/activate
uv pip install -r requirements.txt
python manage.py migrate
sudo systemctl restart commonpot
```

---

## Step 9 — Verify DoD

Go through `dod.md` and confirm all checkboxes are met.
