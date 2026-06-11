# Smart Digital Complaint Management System

A full-stack web application for managing student complaints at a college, built with Python/Flask, SQLite/MySQL, Bootstrap, and JavaScript.

## Run & Operate

- **Start Flask app:** `cd flask-app && python run.py` (port 5000)
- **With Docker + MySQL:** `cd flask-app && docker-compose up --build`
- **Access app:** http://localhost:5000
- **API docs:** See `flask-app/API_DOCUMENTATION.md`

## Demo Credentials

| Role    | Email                   | Password   |
|---------|-------------------------|------------|
| Admin   | admin@college.edu       | admin123   |
| Student | student1@college.edu    | student123 |

## Stack

- **Backend:** Python 3.11, Flask 3.0, SQLAlchemy 3.1
- **Auth:** Flask-Login (session) + Flask-JWT-Extended (API)
- **Security:** bcrypt password hashing, input sanitization (bleach), RBAC
- **Reports:** ReportLab (PDF), openpyxl (Excel)
- **Frontend:** Bootstrap 5.3, Chart.js, Bootstrap Icons, Google Fonts (Inter)
- **Database:** SQLite (dev) / MySQL 8 (Docker/prod)
- **Deployment:** Docker + docker-compose

## Where things live

```
flask-app/
├── run.py                  ← Entry point (dev server)
├── wsgi.py                 ← Gunicorn entry point (production)
├── requirements.txt        ← Python dependencies
├── Dockerfile              ← Multi-stage production Docker image
├── docker-compose.yml      ← Full stack (Flask + MySQL)
├── schema.sql              ← MySQL DDL schema
├── API_DOCUMENTATION.md    ← REST API docs
└── app/
    ├── __init__.py         ← App factory
    ├── config.py           ← Dev/Prod/Testing configs (OOP, Abstraction)
    ├── models/             ← SQLAlchemy ORM models (OOP, Inheritance)
    │   ├── user.py
    │   ├── complaint.py
    │   ├── complaint_log.py
    │   └── notification.py
    ├── routes/             ← Flask Blueprints
    │   ├── auth.py         ← Register, Login, Logout
    │   ├── complaints.py   ← Student complaint flows
    │   ├── admin.py        ← Admin dashboard, CRUD, analytics
    │   ├── reports.py      ← PDF + Excel downloads
    │   └── api.py          ← REST API (JWT-protected)
    ├── utils/
    │   ├── decorators.py   ← @admin_required, @log_execution_time
    │   ├── validators.py   ← OOP input validation
    │   ├── file_handler.py ← Secure uploads
    │   ├── report_generator.py ← PDF + Excel (Generators)
    │   ├── analytics.py    ← Statistics + chart data (Lambda, Generator)
    │   ├── notifications.py ← In-app + email (Multithreading)
    │   └── seed.py         ← Sample data seeder
    ├── templates/          ← Jinja2 + Bootstrap HTML
    └── static/             ← CSS, JS, uploads
```

## Architecture decisions

- SQLite in dev for zero-setup; `CMS_DATABASE_URL` overrides to MySQL for Docker/prod — avoids clash with default `DATABASE_URL`.
- App factory pattern (`create_app`) enables multiple config environments and clean testing.
- Blueprints split auth, student, admin, API, and reports into separate modules.
- Abstract base class `BaseReportGenerator` — subclassed by PDF and Excel generators — demonstrates Polymorphism cleanly.
- Background thread in `NotificationService.send_email_async` keeps request latency low.

## Python Concepts Demonstrated

| Concept | Location |
|---|---|
| Functions | everywhere |
| OOP / Classes / Objects | `models/`, `utils/` |
| Inheritance | `config.py`, `models/user.py` (TimestampMixin), `utils/report_generator.py` |
| Polymorphism | `utils/report_generator.py` (get_report_generator), `utils/validators.py` |
| Encapsulation | `models/user.py` (_password_hash), `utils/file_handler.py` |
| Abstraction | `config.py` (BaseConfig), `utils/validators.py` (BaseValidator), `utils/report_generator.py` (BaseReportGenerator) |
| Exception Handling | all routes and utils |
| Lambda Functions | `routes/admin.py`, `utils/analytics.py` |
| Decorators | `utils/decorators.py` (admin_required, log_execution_time, cache_result) |
| Generators | `models/complaint.py`, `utils/report_generator.py`, `utils/analytics.py` |
| Multithreading | `utils/notifications.py` |
| Logging | `run.py`, all modules |
| File Handling | `utils/file_handler.py`, `utils/report_generator.py` |
| Database Operations | all models via SQLAlchemy |

## Gotchas

- Use `CMS_DATABASE_URL` (not `DATABASE_URL`) to set a custom DB — this allows custom database configuration without conflicts.
- Set `SEED_DB=false` after the first run if you don't want sample data re-inserted.
- Uploaded files go to `app/static/uploads/` — this directory is created automatically.
- Docker Compose brings up MySQL first and waits for the healthcheck before starting Flask.

## User preferences

_Populate as you build._
