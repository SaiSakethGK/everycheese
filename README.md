# CheeseAtlas

A full-stack Django platform for cataloguing artisan cheeses, with community ratings and a REST API.

[![CI](https://github.com/SaiSakethGK/everycheese/actions/workflows/ci.yml/badge.svg)](https://github.com/SaiSakethGK/everycheese/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/python-3.10%20%7C%203.11-blue.svg)](https://python.org)
[![Django](https://img.shields.io/badge/django-3.1-green.svg)](https://djangoproject.com)
[![DRF](https://img.shields.io/badge/DRF-3.14-red.svg)](https://www.django-rest-framework.org/)

---

## Overview

CheeseAtlas is a community-driven cheese catalogue. Users can add cheeses, rate them on a 1–5 scale, filter by country of origin and firmness, and consume the same data through a REST API.

**Key capabilities:**

- **CRUD with ownership** — only the cheese creator (or staff) can edit or delete an entry
- **Community ratings** — per-user scores aggregated at the database level with a single `Avg()` query
- **REST API** — full DRF ViewSet at `/api/v1/`, documented with OpenAPI 3 (Swagger UI + ReDoc)
- **Search and filter** — server-side `Q`-filter on name and description, plus firmness dropdown
- **Authentication** — `django-allauth` with email verification
- **Dark-mode UI** — Bootstrap 5, Font Awesome 6, custom CSS design system

---

## Quick Start

The fastest way to run CheeseAtlas locally is with Docker.

### With Docker

**Prerequisites:** Docker Desktop installed and running.

```bash
git clone https://github.com/SaiSakethGK/everycheese.git
cd everycheese
docker compose up
```

In a second terminal, set up the database and create an admin user:

```bash
docker compose exec web python manage.py migrate
docker compose exec web python manage.py createsuperuser
```

Open **http://localhost:8000** in your browser.

### Without Docker

**Prerequisites:** Python 3.10 or 3.11, PostgreSQL 14+.

1. **Create a virtual environment**

   ```bash
   conda create python=3.11 -n cheeseatlas && conda activate cheeseatlas
   # or: python -m venv .venv && source .venv/bin/activate
   ```

2. **Install dependencies**

   ```bash
   pip install -r requirements/local.txt
   ```

3. **Set environment variables**

   Copy the sample file and edit `DATABASE_URL` and `DJANGO_SECRET_KEY`:

   ```bash
   # macOS / Linux
   cp env.sample.mac_or_linux .env

   # Windows
   copy env.sample.windows .env
   ```

4. **Apply migrations and start the server**

   ```bash
   python manage.py migrate
   python manage.py createsuperuser
   python manage.py runserver
   ```

---

## How-to Guides

### Run the test suite

```bash
coverage run -m pytest          # run all tests
coverage report -m              # show coverage by file
```

The test suite covers models, views (including permission enforcement), and API endpoints. Coverage target is 70%.

### Use the REST API

All endpoints are browsable at `/api/v1/docs/` (Swagger UI) or `/api/v1/redoc/`.

**List cheeses** — supports `?search=`, `?firmness=`, `?ordering=`, `?page=`:

```bash
curl http://localhost:8000/api/v1/cheeses/?firmness=soft&ordering=name
```

**Create a cheese** (authenticated):

```bash
curl -X POST http://localhost:8000/api/v1/cheeses/ \
     -H "Content-Type: application/json" \
     -u myuser:mypassword \
     -d '{"name": "Gouda", "firmness": "semi-hard", "country_of_origin": "NL"}'
```

**Rate a cheese** — upserts the calling user's rating:

```bash
curl -X POST http://localhost:8000/api/v1/cheeses/gouda/rate/ \
     -H "Content-Type: application/json" \
     -u myuser:mypassword \
     -d '{"score": 5}'
# {"average": 4.3}
```

### Deploy to production

Set these environment variables before starting the server:

| Variable | Description |
|---|---|
| `DJANGO_SECRET_KEY` | A long random string |
| `DATABASE_URL` | PostgreSQL connection string |
| `REDIS_URL` | Redis connection string (for caching) |
| `DJANGO_ALLOWED_HOSTS` | Comma-separated list of domains |
| `MAILGUN_API_KEY` | Mailgun key for transactional email |

Run the production Docker image:

```bash
docker build --target runtime -t cheeseatlas:latest .
docker run -p 8000:8000 --env-file .env cheeseatlas:latest
```

---

## Reference

### API endpoints

| Method | Endpoint | Auth required | Description |
|--------|----------|:---:|-------------|
| GET | `/api/v1/cheeses/` | No | Paginated, filterable list |
| POST | `/api/v1/cheeses/` | Yes | Create a cheese |
| GET | `/api/v1/cheeses/{slug}/` | No | Detail with nested ratings |
| PUT / PATCH | `/api/v1/cheeses/{slug}/` | Staff | Update a cheese |
| DELETE | `/api/v1/cheeses/{slug}/` | Staff | Delete a cheese |
| POST | `/api/v1/cheeses/{slug}/rate/` | Yes | Upsert a rating (score 1–5) |
| GET | `/api/v1/docs/` | No | Swagger UI |
| GET | `/api/v1/redoc/` | No | ReDoc |
| GET | `/api/v1/schema/` | No | Raw OpenAPI 3 schema |

### Query parameters (GET /api/v1/cheeses/)

| Parameter | Example | Description |
|---|---|---|
| `search` | `?search=gouda` | Matches name or description |
| `firmness` | `?firmness=soft` | Filter by firmness |
| `country_of_origin` | `?country_of_origin=FR` | Filter by ISO country code |
| `ordering` | `?ordering=-created` | Sort field (prefix `-` for descending) |
| `page` | `?page=2` | Page number (20 results per page) |

### Data models

**Cheese**

| Field | Type | Notes |
|---|---|---|
| `name` | CharField | Max 255 characters |
| `slug` | AutoSlugField | Auto-generated from name, unique |
| `description` | TextField | Optional |
| `country_of_origin` | CountryField | ISO 3166-1 alpha-2 |
| `firmness` | CharField | `unspecified`, `soft`, `semi-soft`, `semi-hard`, `hard` |
| `creator` | ForeignKey(User) | Set automatically on create |
| `created` / `modified` | DateTimeField | Auto-managed timestamps |

**Rating**

| Field | Type | Notes |
|---|---|---|
| `score` | PositiveSmallIntegerField | 0–5; unique per (creator, cheese) pair |
| `creator` | ForeignKey(User) | |
| `cheese` | ForeignKey(Cheese) | |

### Configuration

All settings are read from environment variables via `django-environ`. See `env.sample.mac_or_linux` for a full list.

---

## Explanation

### Why DB-level rating aggregation?

`Cheese.average_rating` runs a single SQL `AVG()` query:

```python
result = self.ratings.aggregate(avg=Avg("score"))
return round(result["avg"] or 0.0, 1)
```

This is constant-time regardless of how many ratings exist. The previous approach fetched every rating row into Python memory and looped — O(n) in both time and memory.

The list view takes this further by annotating the queryset once, so all 12 cards on a page share a single aggregation query rather than triggering one per card.

### Why `CreatorRequiredMixin`?

Django provides `LoginRequiredMixin` (redirect unauthenticated users) and `UserPassesTestMixin` (run an arbitrary test and return 403 on failure). Composing them is more explicit and testable than a custom decorator:

```python
class CreatorRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        cheese = get_object_or_404(Cheese, slug=self.kwargs["slug"])
        return (
            cheese.creator == self.request.user
            or self.request.user.is_staff
        )
```

Any non-creator hitting an update or delete URL receives a `403 Forbidden` — no data is modified.

### Project structure

```
everycheese/
├── config/              # Django settings (base / local / production / test)
├── everycheese/
│   ├── cheeses/         # Core app — models, views, API, admin, tests
│   ├── users/           # Custom User model (AbstractUser + bio)
│   ├── templates/       # Django templates (Bootstrap 5)
│   └── static/css/      # Custom design system
├── Dockerfile           # Multi-stage build (builder → slim runtime)
├── docker-compose.yml   # Local dev stack (Postgres + Redis + app)
└── .github/workflows/   # CI: lint → test matrix → Docker build
```

---

**Author:** Sai Saketh Gooty Kase — [saisaketh.gootykase@gmail.com](mailto:saisaketh.gootykase@gmail.com)
