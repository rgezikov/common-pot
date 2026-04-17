# Tech Stack

## Overview

Mobile-first web application, accessible via browser on any device. No app install required.

## Backend

- **Python 3.12+** managed via **uv**
- **Django 5.x** — full-stack web framework
  - Built-in ORM with migrations
  - Django templates for server-side rendering
  - Built-in admin panel for data management and debugging
  - Form handling and validation

## Frontend

- **HTMX** (via CDN) — dynamic partial page updates without writing JavaScript
- **TailwindCSS** (via CDN) — utility-first CSS, mobile-first responsive design
- No JavaScript framework, no Node.js build step

## Database

- **SQLite** — default, zero-config, file-based
- Easily swappable to PostgreSQL via Django settings if needed

## Deployment

- **gunicorn** — Python WSGI application server
- **nginx** — reverse proxy, serves static files
- **Ubuntu 24.04 LTS** — server OS (Hetzner VPS)
  - Python 3.12 available in default repos
  - Security updates supported until 2029

## Testing

- **pytest** + **pytest-django** — test runner and Django integration
- **GitHub Actions** — CI pipeline runs tests automatically on every push and pull request
- Business logic must have unit tests; views and templates tested selectively
- Test infrastructure introduced in Phase 3 (first business logic phase)

## Progressive Web App (future)

- `manifest.json` + service worker can be added later to allow home screen installation and basic offline support

## Design Principles

- Mobile-first: touch-friendly UI, single-column layouts, minimal typing
- Fast: HTMX partial updates avoid full page reloads
- Simple deployment: standard Python WSGI stack
