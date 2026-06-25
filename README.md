# Rivyou Product Search Platform

A Django REST Framework backend for relevance-ranked product discovery.

The API prevents accessories such as chargers and back covers from ranking above the actual product category when users search broad terms such as `smartphone`.

## Features

- JWT authentication with registration, login, refresh-token logout, and 7-day access-token expiry
- Protected product APIs
- Three-tier relevance ranking:
  1. Category match
  2. Tag match
  3. Product name or description match
- Tier-specific ordering:
  - Tier 1: more matching tags rank higher
  - Tier 2: exact tag matches rank above partial tag matches
  - Tier 3: product-name matches rank above description-only matches
- Case-insensitive and partial matching
- Page-based pagination
- Search history per authenticated user
- PostgreSQL indexes for category, product name, and JSON tags
- Swagger/OpenAPI documentation
- Automated tests for ranking, authentication, pagination, and analytics

## Tech Stack

- Python 3.12
- Django
- Django REST Framework
- PostgreSQL
- Simple JWT
- drf-spectacular / Swagger
- pytest and Django Test Framework

## Project Structure

```text
apps/
├── analytics/       # Search history
├── products/        # Products, ranking engine, CSV import
└── users/           # JWT authentication
config/              # Settings and root URLs


