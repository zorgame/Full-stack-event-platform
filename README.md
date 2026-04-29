# EventTix

Full-stack ticket sales platform built with **FastAPI** (Python) + **Vue 3** with MySQL, Redis, and payment processing via Crossmint.

## Overview

EventTix is a complete ticket commerce system with real-time inventory management, secure payment flows, user/admin panels, and metrics dashboards.

### Features

- **Product & category management** — hierarchical product/category system with per-user limits and real-time stock
- **Shopping cart & checkout** — client-side cart with inline payment (Checkout.com via Crossmint)
- **Payment orchestration** — Crossmint-powered on-ramp for crypto/fiat payments with KYC flows
- **Order lifecycle** — pendiente &rarr; pagado / cancelado / fallido with stock adjustments and ticket assignment
- **User system** — JWT auth, admin roles, ticket transfers between users
- **Admin dashboard** — CRUD for products, categories, users, orders with metrics (revenue, trends, top products)
- **Visitors analytics** — Redis HyperLogLog-based unique visit tracking
- **Rate limiting** — per-endpoint Redis/local sliding window rate limiter
- **PDF document generation** — ticket reports and billing summaries with QR and barcodes
- **Email notifications** — transactional emails for order events and payment confirmations
- **SEO & metadata** — structured data (JSON-LD), Open Graph, Twitter cards, sitemap
- **Docker Compose** — local development with MySQL + Redis + backend + frontend

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.12, FastAPI, SQLAlchemy 2.0, Alembic |
| Frontend | Vue 3, Pinia, Vue Router, Bootstrap 5 |
| Database | MySQL 8.4 |
| Cache | Redis 7 (caching, rate limiting, visit tracking) |
| Payments | Crossmint (Checkout.com, Persona KYC) |
| Auth | JWT (python-jose), bcrypt |

## Project Structure

```
Backend/
  app/
    api/routes/     — FastAPI endpoint definitions
    controllers/    — Request handling / HTTP logic
    services/       — Business logic layer
    repositories/   — Data access layer (SQLAlchemy)
    models/         — ORM models
    schemas/        — Pydantic request/response schemas
    middleware/     — Logging, rate limiting, security headers
    utils/          — Email, media, cache, security, pagination
    core/           — Settings & constants
    db/             — Database session & base
    scripts/        — Admin bootstrap, data import
  alembic/          — Database migrations
  docker-compose.yml

Frontend/
  src/
    components/     — Reusable Vue components
    views/          — Page-level components
    config/         — App config (routes, theme, checkout, env)
    stores/         — Pinia stores (auth, cart, catalog)
    services/       — API clients
    sdk/            — Backend SDK
    utils/          — SEO, PDF, WhatsApp, animations
    router/         — Vue Router definitions
    assets/         — Styles & images
  public/           — Static assets, sitemap, manifest
  Dockerfile
```

## Getting Started

### Prerequisites

- Docker & Docker Compose

### Quick Start

```bash
# Clone and enter the project
git clone <your-repo-url> && cd eventtix

# Start all services
docker compose -f docker-compose.local.yml up -d

# The backend will be at http://localhost:8010
# The frontend will be at http://localhost:2010
```

### Environment Variables

Each service reads from `.env` files:

- `Backend/.env.local` — backend configuration
- `Frontend/.env` — frontend configuration

Copy the example files and adjust:

```bash
cp Frontend/.env.example Frontend/.env
```

### Bootstrap Admin

```bash
docker compose -f docker-compose.local.yml exec backend python -m app.scripts.bootstrap_admin \
  --email admin@example.com \
  --password "YourStr0ng!Passw0rd#2024"
```

## API Endpoints

| Prefix | Description |
|--------|-------------|
| `/auth` | Login, profile |
| `/productos` | Product & category CRUD |
| `/categorias` | Category management |
| `/pedidos` | Order creation, listing, metrics |
| `/payments` | Payment creation, status, sync |
| `/usuarios` | User management, ticket assignment |
| `/health` | Health check (DB + Redis) |
| `/media` | Static media files |

## Key Decisions

- **Repository pattern** separates data access from business logic
- **Controller layer** handles HTTP concerns (exceptions, status codes)
- **Redis** for caching, rate limiting, and visitor analytics (HyperLogLog)
- **Crossmint** handles payment processing, KYC, and fiat/crypto on-ramp
- **Alembic** for schema migrations with compare_type enabled
