# 🧀 EveryCheese

> **The Ultimate Artisan Cheese Index** — a production-grade Django web application
> with a REST API, community rating system, and a modern dark-mode UI.

[![CI](https://github.com/SaiSakethGK/everycheese/actions/workflows/ci.yml/badge.svg)](https://github.com/SaiSakethGK/everycheese/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/python-3.10%20%7C%203.11-blue.svg)](https://python.org)
[![Django](https://img.shields.io/badge/django-3.1-green.svg)](https://djangoproject.com)
[![DRF](https://img.shields.io/badge/DRF-3.14-red.svg)](https://www.django-rest-framework.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](./COPYING)

---

## Features

| Category | Details |
|---|---|
| **Cheese CRUD** | Create, read, update, delete with creator-only permissions |
| **Community Ratings** | 1–5 star ratings; DB-level `Avg()` aggregation (zero Python loops) |
| **AJAX Rating** | Real-time star picker on detail page via `fetch` POST |
| **REST API** | Full DRF ViewSet at `/api/v1/`; filterable, searchable, paginated |
| **OpenAPI Docs** | Auto-generated Swagger UI + ReDoc via `drf-spectacular` |
| **Search & Filter** | Server-side `Q` filter on name/description + firmness dropdown |
| **Auth** | `django-allauth` — signup, login, email verification |
| **Permissions** | `CreatorRequiredMixin` (LoginRequired + UserPassesTest) |
| **Modern UI** | Bootstrap 5 dark theme, Font Awesome 6, custom CSS design system |
| **Docker** | Multi-stage build (builder -> slim runtime), non-root user |
| **CI/CD** | GitHub Actions — lint, Python 3.10/3.11 matrix test, Docker build |

---

## Architecture

```
everycheese/
├── config/
│   ├── settings/
│   │   ├── base.py          # 12-factor settings with django-environ
│   │   ├── local.py         # dev overrides (debug toolbar, console email)
│   │   ├── production.py    # HSTS, Redis cache, Anymail, collectfast
│   │   └── test.py          # SQLite, fast password hasher
│   └── urls.py              # root URL conf + HomeView with live stats
│
├── everycheese/
│   ├── cheeses/
│   │   ├── models.py        # Cheese + Rating (DB-level Avg, unique_together)
│   │   ├── views.py         # CBVs with CreatorRequiredMixin, search, AJAX rate
│   │   ├── serializers.py   # CheeseSerializer, CheeseDetailSerializer, RatingSerializer
│   │   ├── api_views.py     # CheeseViewSet (DRF) with /rate/ custom action
│   │   ├── api_urls.py      # /api/v1/ router + OpenAPI schema endpoints
│   │   ├── admin.py         # Full ModelAdmin with inline ratings + star display
│   │   └── tests/
│   │       ├── factories.py # CheeseFactory, RatingFactory (factory_boy)
│   │       ├── test_models.py
│   │       ├── test_views.py
│   │       └── test_api.py
│   │
│   ├── users/               # Custom User model (AbstractUser + bio)
│   ├── templates/
│   │   ├── base.html        # Bootstrap 5 navbar, flash messages, footer
│   │   ├── pages/           # home.html (hero + stats + top-rated), about.html
│   │   └── cheeses/         # list (card grid + search), detail (AJAX star picker),
│   │                        # form (crispy BS5), delete (confirmation)
│   └── static/css/
│       └── project.css      # Custom design system (CSS variables, dark palette)
│
├── Dockerfile               # Multi-stage: builder -> slim runtime, gunicorn
├── docker-compose.yml       # Postgres 15 + Redis 7 + web with healthchecks
└── .github/workflows/ci.yml # lint -> test matrix -> docker build
```

---

## Quick Start

### Option A — Docker (recommended)

```bash
git clone https://github.com/SaiSakethGK/everycheese.git
cd everycheese
docker compose up
# In another terminal:
docker compose exec web python manage.py migrate
docker compose exec web python manage.py createsuperuser
```

Open **http://localhost:8000** in your browser.

---

### Option B — Local (conda / virtualenv)

**1. Create and activate a Python 3.11 environment**

```bash
conda create python=3.11 -n everycheese
conda activate everycheese
```

**2. Install dependencies**

```bash
pip install -r requirements/local.txt
```

**3. Configure environment variables**

```bash
# Linux / macOS
cp env.sample.mac_or_linux .env

# Windows
copy env.sample.windows .env
```

Edit `.env` and set `DATABASE_URL` (PostgreSQL) and `DJANGO_SECRET_KEY`.

**4. Apply migrations**

```bash
python manage.py migrate
python manage.py createsuperuser
```

**5. Start the dev server**

```bash
python manage.py runserver
```

---

## REST API

Base URL: `http://localhost:8000/api/v1/`

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| `GET` | `/cheeses/` | — | Paginated list; `?search=`, `?firmness=`, `?ordering=` |
| `POST` | `/cheeses/` | Yes | Create a new cheese |
| `GET` | `/cheeses/{slug}/` | — | Detail with nested ratings array |
| `POST` | `/cheeses/{slug}/rate/` | Yes | Upsert user rating `{"score": 1-5}` |
| `GET` | `/schema/` | — | Raw OpenAPI 3 schema (YAML) |
| `GET` | `/docs/` | — | Swagger UI |
| `GET` | `/redoc/` | — | ReDoc |

**Example — list cheeses filtered by firmness:**

```bash
curl "http://localhost:8000/api/v1/cheeses/?firmness=soft&ordering=name"
```

**Example — rate a cheese (authenticated):**

```bash
curl -X POST "http://localhost:8000/api/v1/cheeses/brie/rate/" \
     -H "Content-Type: application/json" \
     -u myuser:mypassword \
     -d '{"score": 5}'
# -> {"average": 4.3}
```

---

## Running Tests

```bash
# Run all tests with coverage
coverage run -m pytest

# Coverage report (target >= 70%)
coverage report -m

# Run a specific test class
pytest everycheese/cheeses/tests/test_views.py::TestCheeseDeleteView -v
```

---

## Key Engineering Decisions

### DB-Level Rating Aggregation

`Cheese.average_rating` uses `Avg("ratings__score")` — a single SQL query
regardless of how many ratings exist. The previous implementation used a Python
`for` loop that fetched every rating row into memory.

```python
# What this project does
result = self.ratings.aggregate(avg=Avg("score"))
return round(result["avg"] or 0.0, 1)
```

### N+1 Free List View

`CheeseListView.get_queryset()` annotates once — a constant number of queries
regardless of result set size:

```python
Cheese.objects.select_related("creator") \
              .annotate(avg_score=Avg("ratings__score"))
```

### Creator-Only Permissions

`CreatorRequiredMixin` composes two built-in Django mixins — no third-party
permission library needed:

```python
class CreatorRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        cheese = get_object_or_404(Cheese, slug=self.kwargs["slug"])
        return (
            cheese.creator == self.request.user
            or self.request.user.is_staff
        )
```

---

## Author

**Sai Saketh Gooty Kase** — Full-Stack Software Engineer

[saisaketh.gootykase@gmail.com](mailto:saisaketh.gootykase@gmail.com)
