# CRUD Analysis App

A minimal, fully functional CRUD (Create, Read, Update, Delete) REST API application built with **Python**, **FastAPI**, **SQLite**, and **SQLAlchemy**.

This project serves as a clean, predictable sample codebase designed for testing code analysis applications, linters, security scanners, and architectural evaluation tools.

---

## 1. Project Overview

The application exposes a standard REST API to manage an `Item` catalog. It emphasizes:
- **Simplicity**: No unnecessary abstractions, microservices, or complex repository layers.
- **Clean Architecture**: Clear separation of concern across routing, data validation, database modeling, and database transactions.
- **Readability**: Fully typed, PEP 8 compliant, and easy to trace for static analysis tools and developers alike.
- **Zero-Setup Database**: Automatic table initialization in SQLite on startup.
- **Isolated Testing**: Automated tests running against an in-memory database that never touches the development database.

---

## 2. Architecture & Folder Structure

### Folder Structure

```text
crud-analysis-app/
├── app/
│   ├── __init__.py          # Marks app as a Python package
│   ├── main.py              # Application entrypoint, lifespan startup, router registration, /health
│   ├── database.py          # SQLite engine configuration, SessionLocal, Base, get_db dependency
│   ├── models.py            # SQLAlchemy Item ORM entity
│   ├── schemas.py           # Pydantic schemas for request and response validation
│   ├── crud.py              # Pure database CRUD functions with transaction and rollback safety
│   └── routers/
│       ├── __init__.py      # Marks routers as a Python package
│       └── items.py         # HTTP route definitions, input handling, and HTTP status codes
├── tests/
│   └── test_items.py        # Automated test suite using TestClient and an in-memory SQLite database
├── requirements.txt         # Pinned application and test dependencies
├── README.md                # Comprehensive documentation
└── .gitignore               # Standard Python, SQLite, pytest, and IDE ignore rules
```

### Execution Flow

The flow of data and control is intentionally linear and easy to trace:

```text
Client Request
      │
      ▼
FastAPI Router (app/routers/items.py)
      │  (validates request with Pydantic schemas in app/schemas.py)
      ▼
CRUD Functions (app/crud.py)
      │  (executes queries using Session injected from app/database.py)
      ▼
SQLAlchemy Models (app/models.py)
      │
      ▼
SQLite Database (app.db or :memory: in tests)
      │
      ▼
FastAPI Serializer (Pydantic schemas in app/schemas.py)
      │
      ▼
JSON Response (HTTP 200/201/204/404/422)
```

### Module Responsibilities

| File | Primary Responsibility |
| :--- | :--- |
| `app/main.py` | Initializes FastAPI, manages the lifespan startup event (table creation), mounts routers, and defines the root `/health` endpoint. |
| `app/database.py` | Configures the SQLite engine (`app.db`), session factory (`SessionLocal`), declarative `Base`, and the `get_db` generator dependency. |
| `app/models.py` | Defines the SQLAlchemy `Item` entity mapping to the `items` table. |
| `app/schemas.py` | Defines Pydantic models (`ItemBase`, `ItemCreate`, `ItemUpdate`, `ItemResponse`) with field validation. |
| `app/crud.py` | Implements dedicated query functions (`get_item`, `get_items`, `create_item`, `update_item`, `delete_item`) with rollback handling. |
| `app/routers/items.py` | Declares REST API routes (`/items`), delegates to CRUD helpers, and maps results to appropriate HTTP statuses/exceptions. |
| `tests/test_items.py` | Implements 18 comprehensive, isolated tests using Pytest and FastAPI's `TestClient` over an in-memory SQLite database. |

---

## 3. Database Model

The `Item` entity (`app/models.py`) consists of:
- `id` (`Integer`, Primary Key, autoincremented, indexed)
- `name` (`String`, non-nullable)
- `description` (`String`, nullable/optional)
- `price` (`Float`, non-nullable, non-negative)

---

## 4. API Endpoints

| Method | Endpoint | Description | Success Code | Error Codes |
| :--- | :--- | :--- | :--- | :--- |
| `POST` | `/items` | Create a new item | `201 Created` | `422 Unprocessable Entity` |
| `GET` | `/items` | Retrieve all items (supports `skip` & `limit`) | `200 OK` | — |
| `GET` | `/items/{item_id}` | Retrieve a single item by its ID | `200 OK` | `404 Not Found` |
| `PUT` | `/items/{item_id}` | Update an existing item's fields | `200 OK` | `404 Not Found`, `422 Unprocessable Entity` |
| `DELETE` | `/items/{item_id}` | Delete an item by its ID | `204 No Content` | `404 Not Found` |
| `GET` | `/health` | Application health check (`{"status": "ok"}`) | `200 OK` | — |

---

## 5. Prerequisites

- Python 3.11, 3.12, or 3.15
- `pip` package manager

---

## 6. Virtual Environment Setup

### On Windows (PowerShell):
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### On Linux / macOS (Bash):
```bash
python3 -m venv .venv
source .venv/bin/activate
```

---

## 7. Dependency Installation

Install all required dependencies using `pip`:

```bash
pip install -r requirements.txt
```

---

## 8. Application Startup

Run the development server locally with Uvicorn:

```bash
uvicorn app.main:app --reload
```

The server will start at `http://127.0.0.1:8000`.

- The SQLite database file `app.db` is created automatically in the working directory on startup if it does not already exist.

---

## 9. Interactive API Documentation (Swagger UI)

FastAPI automatically generates interactive OpenAPI documentation:

- **Swagger UI**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **ReDoc UI**: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

You can explore request and response schemas and test all endpoints directly in the browser.

---

## 10. Automated Testing

Run the automated test suite with Pytest:

```bash
pytest -q
```

### Test Isolation & Database Behavior:
- The tests run against an **in-memory SQLite database** (`sqlite:///:memory:`) using SQLAlchemy's `StaticPool`.
- `app.dependency_overrides[get_db]` injects the in-memory test session into FastAPI.
- The development database `app.db` is **never touched or modified** during test execution.
- Tables are freshly created and dropped for each individual test function, ensuring complete isolation and order-independent execution.

---

## 11. Code Quality & Analysis Readiness

- **Standard PEP 8 formatting**: Consistent naming, standard imports, and 4-space indentation.
- **Type Annotations**: All endpoint functions, CRUD routines, and dependencies carry explicit type hints.
- **Explicit Error Paths**: Handled edge cases include 404 for missing resources, 422 for negative prices (`price < 0`) and missing required fields (`name`, `price`), and database rollbacks on failure.
- **Session Leak Prevention**: Database sessions are managed via FastAPI's `yield` dependency pattern inside a `try ... finally` block, ensuring immediate closure after each HTTP request.
