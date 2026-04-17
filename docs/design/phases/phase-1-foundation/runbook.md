# Phase 1 — Runbook: Project Foundation

> **Conventions used in this runbook:**
> - `[local]` — run on your developer machine
> - `[server]` — run on the server as `potdev` unless noted as `[server/root]`

## Prerequisites

- Phase 0 complete (server running, gunicorn + nginx working)
- uv installed locally
- Git repo cloned locally (referred to as `<project-root>` below)

---

## Step 1 — Local Development Setup

**[local]** In the project root, create a virtual environment and install Django:

```bash
cd <project-root>
uv venv --python 3.12
source .venv/bin/activate
uv pip install django
uv pip freeze > requirements.txt
```

---

## Step 2 — Create Django Project and App

**[local]** Create the Django project in the repo root:

```bash
django-admin startproject commonpot .
python manage.py startapp pots
```

This produces:

```
<project-root>/
  commonpot/
    settings.py
    urls.py
    wsgi.py
  pots/
    models.py
    views.py
    ...
  manage.py
```

**[local]** Register the app in `commonpot/settings.py`:

```python
INSTALLED_APPS = [
    ...
    'pots',
]
```

---

## Step 3 — Configure Database and Settings

**[local]** In `commonpot/settings.py`, set the allowed hosts:

```python
ALLOWED_HOSTS = ['pot.respobit.eu', 'localhost', '127.0.0.1']
```

SQLite is configured by default — no changes needed.

**[local]** Run initial migrations:

```bash
python manage.py migrate
```

**[local]** Verify the dev server runs:

```bash
python manage.py runserver
```

Open `http://localhost:8000` — should show the Django welcome page.

---

## Step 4 — Define Data Models

**[local]** Edit `pots/models.py`:

```python
import uuid
from django.db import models


class Pot(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    invite_token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Member(models.Model):
    pot = models.ForeignKey(Pot, on_delete=models.CASCADE, related_name='members')
    telegram_user_id = models.BigIntegerField()
    name = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('pot', 'telegram_user_id')

    def __str__(self):
        return f"{self.name} ({self.pot.name})"


class Drop(models.Model):
    SOURCE_WEB = 'web'
    SOURCE_TELEGRAM = 'telegram'
    SOURCE_CHOICES = [(SOURCE_WEB, 'Web'), (SOURCE_TELEGRAM, 'Telegram')]

    pot = models.ForeignKey(Pot, on_delete=models.CASCADE, related_name='drops')
    description = models.CharField(max_length=200)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    paid_by = models.ForeignKey(Member, on_delete=models.PROTECT, related_name='drops_paid')
    date = models.DateField()
    source = models.CharField(max_length=20, choices=SOURCE_CHOICES, default=SOURCE_WEB)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.description} ({self.amount})"


class Split(models.Model):
    drop = models.ForeignKey(Drop, on_delete=models.CASCADE, related_name='splits')
    member = models.ForeignKey(Member, on_delete=models.PROTECT, related_name='splits')
    amount = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.member.name}: {self.amount}"
```

**[local]** Create and run migrations:

```bash
python manage.py makemigrations
python manage.py migrate
```

---

## Step 5 — Register Models in Admin

**[local]** Edit `pots/admin.py`:

```python
from django.contrib import admin
from .models import Pot, Member, Drop, Split

admin.site.register(Pot)
admin.site.register(Member)
admin.site.register(Drop)
admin.site.register(Split)
```

**[local]** Create a superuser:

```bash
python manage.py createsuperuser
```

Verify: open `http://localhost:8000/admin` — all four models should be visible.

---

## Step 6 — Base Template with HTMX and TailwindCSS

**[local]** Create the templates directory:

```bash
mkdir -p pots/templates
```

**[local]** Configure template directory in `commonpot/settings.py`:

```python
TEMPLATES = [
    {
        ...
        'DIRS': [BASE_DIR / 'pots' / 'templates'],
        ...
    }
]
```

**[local]** Create `pots/templates/base.html`:

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
        <h1 class="text-xl font-bold">Common Pot</h1>
    </header>
    <main class="px-4 py-6 max-w-lg mx-auto">
        {% block content %}{% endblock %}
    </main>
</body>
</html>
```

**[local]** Create a placeholder home view in `pots/views.py`:

```python
from django.shortcuts import render

def home(request):
    return render(request, 'home.html')
```

**[local]** Create `pots/templates/home.html`:

```html
{% extends "base.html" %}
{% block content %}
<p class="text-lg">Welcome to Common Pot.</p>
{% endblock %}
```

---

## Step 7 — URL Routing Skeleton

**[local]** Edit `commonpot/urls.py`:

```python
from django.contrib import admin
from django.urls import path
from pots import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.home, name='home'),
]
```

Verify: open `http://localhost:8000` — should show the Welcome page with TailwindCSS styling.

---

## Step 8 — Deploy to Server

### 8.1 — Push code to server

**[local]** Copy the project to the server:

```bash
rsync -av --exclude='.venv' --exclude='__pycache__' --exclude='*.sqlite3' \
  <project-root>/ potdev@pot.respobit.eu:~/app/
```

### 8.2 — Configure production settings

**[local]** Edit `commonpot/settings.py` to read secrets from environment variables:

```python
import os

SECRET_KEY = os.environ.get('COMPOT_SECRET_KEY', 'dev-secret-key-change-in-production')
DEBUG = os.environ.get('COMPOT_DEBUG', 'False') == 'True'
```

**[local]** Generate a secret key:

```bash
python -c "import secrets; print(secrets.token_urlsafe(50))"
```

**[server]** Create an environment file:

```bash
vi ~/app/.env
```

Content:

```
COMPOT_SECRET_KEY=<paste generated secret key>
COMPOT_DEBUG=False
```

### 8.3 — Install dependencies on server

**[server]** Set up the virtual environment:

```bash
cd ~/app
uv venv --python 3.12
source .venv/bin/activate
uv pip install -r requirements.txt
```

### 8.4 — Run migrations on server

**[server]**

```bash
cd ~/app
source .venv/bin/activate
python manage.py migrate
python manage.py collectstatic --noinput
```

### 8.5 — Set up gunicorn as a systemd service

**[server/root]** Create a systemd service file:

```bash
vi /etc/systemd/system/commonpot.service
```

Content:

```ini
[Unit]
Description=Common Pot gunicorn daemon
After=network.target

[Service]
User=potdev
Group=potdev
WorkingDirectory=/home/potdev/app
EnvironmentFile=/home/potdev/app/.env
ExecStart=/home/potdev/app/.venv/bin/gunicorn \
    --bind 127.0.0.1:8000 \
    --workers 2 \
    commonpot.wsgi:application

[Install]
WantedBy=multi-user.target
```

**[server/root]** Enable and start the service:

```bash
systemctl daemon-reload
systemctl enable commonpot
systemctl start commonpot
systemctl status commonpot
```

### 8.6 — Reload nginx

**[server/root]** The nginx config already proxies to port 8000 from Phase 0 — no changes needed. Just reload:

```bash
systemctl reload nginx
```

Verify: open `https://pot.respobit.eu` — should show the Welcome page.

---

## Step 9 — Verify DoD

Go through `dod.md` and confirm all checkboxes are met.
