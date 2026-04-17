# Phase 1 — Runbook: Project Foundation

## Prerequisites

- Phase 0 complete (server running, gunicorn + nginx working)
- uv installed locally
- Git repo at `/home/roman/work/courses/sdd/exp1/`

---

## Step 1 — Local Development Setup

In the project root, create a virtual environment and install Django:

```bash
cd /home/roman/work/courses/sdd/exp1
uv venv --python 3.12
source .venv/bin/activate
uv pip install django
uv pip freeze > requirements.txt
```

---

## Step 2 — Create Django Project and App

Create the Django project in the repo root:

```bash
django-admin startproject commonpot .
python manage.py startapp pots
```

This produces:

```
exp1/
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

Register the app in `commonpot/settings.py`:

```python
INSTALLED_APPS = [
    ...
    'pots',
]
```

---

## Step 3 — Configure Database and Settings

In `commonpot/settings.py`, set the allowed hosts:

```python
ALLOWED_HOSTS = ['pot.respobit.eu', 'localhost', '127.0.0.1']
```

SQLite is configured by default — no changes needed.

Run initial migrations:

```bash
python manage.py migrate
```

Verify the dev server runs:

```bash
python manage.py runserver
```

Open `http://localhost:8000` — should show the Django welcome page.

---

## Step 4 — Define Data Models

Edit `pots/models.py`:

```python
import uuid
from django.db import models


class Pot(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Member(models.Model):
    pot = models.ForeignKey(Pot, on_delete=models.CASCADE, related_name='members')
    name = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.pot.name})"


class Drop(models.Model):
    pot = models.ForeignKey(Pot, on_delete=models.CASCADE, related_name='drops')
    description = models.CharField(max_length=200)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    paid_by = models.ForeignKey(Member, on_delete=models.PROTECT, related_name='drops_paid')
    date = models.DateField()
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

Create and run migrations:

```bash
python manage.py makemigrations
python manage.py migrate
```

---

## Step 5 — Register Models in Admin

Edit `pots/admin.py`:

```python
from django.contrib import admin
from .models import Pot, Member, Drop, Split

admin.site.register(Pot)
admin.site.register(Member)
admin.site.register(Drop)
admin.site.register(Split)
```

Create a superuser:

```bash
python manage.py createsuperuser
```

Verify: open `http://localhost:8000/admin` — all four models should be visible.

---

## Step 6 — Base Template with HTMX and TailwindCSS

Create the templates directory:

```bash
mkdir -p pots/templates/pots
```

Configure template directory in `commonpot/settings.py`:

```python
TEMPLATES = [
    {
        ...
        'DIRS': [BASE_DIR / 'pots' / 'templates'],
        ...
    }
]
```

Create `pots/templates/base.html`:

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

Create a placeholder home view in `pots/views.py`:

```python
from django.shortcuts import render

def home(request):
    return render(request, 'home.html')
```

Create `pots/templates/home.html`:

```html
{% extends "base.html" %}
{% block content %}
<p class="text-lg">Welcome to Common Pot.</p>
{% endblock %}
```

---

## Step 7 — URL Routing Skeleton

Edit `commonpot/urls.py`:

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

On your local machine, copy the project to the server (for now, until we set up git-based deployment):

```bash
rsync -av --exclude='.venv' --exclude='__pycache__' --exclude='*.sqlite3' \
  /home/roman/work/courses/sdd/exp1/ potdev@pot.respobit.eu:~/app/
```

### 8.2 — Install dependencies on server

SSH into the server as `potdev` and set up the environment:

```bash
cd ~/app
uv venv --python 3.12
source .venv/bin/activate
uv pip install -r requirements.txt
```

### 8.3 — Configure production settings

On the server, set the secret key and debug mode via environment variables. Edit `commonpot/settings.py` locally:

```python
import os

SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', 'dev-secret-key-change-in-production')
DEBUG = os.environ.get('DJANGO_DEBUG', 'False') == 'True'
```

Create an environment file on the server:

```bash
vi ~/app/.env
```

Content:

```
DJANGO_SECRET_KEY=<generate a random secret key>
DJANGO_DEBUG=False
```

Generate a secret key locally:

```bash
python -c "import secrets; print(secrets.token_urlsafe(50))"
```

### 8.4 — Run migrations on server

```bash
cd ~/app
source .venv/bin/activate
python manage.py migrate
python manage.py collectstatic --noinput
```

### 8.5 — Set up gunicorn as a systemd service

As root on the server, create a systemd service file:

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

Enable and start the service:

```bash
systemctl daemon-reload
systemctl enable commonpot
systemctl start commonpot
systemctl status commonpot
```

### 8.6 — Update nginx config

As root, update the nginx location block in `/etc/nginx/sites-available/default` (in the HTTPS server block) — it should already be proxying to port 8000 from Phase 0, so no changes needed.

Reload nginx:

```bash
systemctl reload nginx
```

Verify: open `https://pot.respobit.eu` — should show the Welcome page.

---

## Step 9 — Verify DoD

Go through `dod.md` and confirm all checkboxes are met.
