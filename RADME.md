# Bank Transaction Ingestion API

A FastAPI-based REST API for bulk ingesting bank transaction records via CSV upload. The service validates each row, streams valid records directly into PostgreSQL via `COPY`, and generates downloadable failure reports for invalid rows.

---

## Features

- CSV file upload with per-row validation
- Bulk insert via PostgreSQL `COPY` for high-throughput ingestion
- Configurable failure threshold — aborts the upload if too many rows fail
- Downloadable failure reports per upload session
- Automatic cleanup of old failure reports (TTL: 7 days)

---

## Tech Stack

- **FastAPI** — REST API framework
- **SQLAlchemy** — ORM and database session management
- **psycopg2** — PostgreSQL driver (used directly for `COPY`)
- **PostgreSQL** — Primary database
- **Pydantic** — Request/response schema validation
- **Docker & Docker Compose** — Containerised local development stack

---

## Project Structure

```
app/
├── main.py            # FastAPI app and route definitions
├── ingest.py          # CSV parsing, row validation, and ingestion logic
├── failure_report.py  # Failure report write, read, and cleanup
├── models.py          # SQLAlchemy models (Upload, Transaction)
├── databases.py       # DB engine, session factory, and Base
├── helpers.py         # Pydantic response schemas
├── consts.py          # Constants (thresholds, valid categories, field names)
Dockerfile
docker-compose.yml
requirements.txt
README.md
tests/
├── __init__.py
├── test_upload.py
```

---

## Setup

### Option 1 — Docker (recommended)

The easiest way to run the full stack (API + PostgreSQL) is with Docker Compose.

**Prerequisites:** Docker and Docker Compose installed.

1. Create a `.env` file in the project root:

```env
DATABASE_URL=postgresql://admin:mypassword@database:5432/transactions
```

> Note: the host must be `database` (the Docker Compose service name), not `localhost`.

2. Start the services:

```bash
docker compose up --build
```

The API will be available at `http://localhost:8000` and PostgreSQL at `localhost:5432`.

To stop:

```bash
docker compose down
```

---

### Option 2 — Local (manual)

**Prerequisites:** Python 3.10+, a running PostgreSQL instance.

1. Install dependencies:

```bash
pip install -r requirements.txt
```

2. Create a `.env` file in the project root:

```env
DATABASE_URL=postgresql://user:password@localhost:5432/yourdb
```

3. Run the API:

```bash
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`.

---

### .gitignore

The `.env` file contains sensitive credentials and must not be committed to version control:

```
.env
```

---

## API Reference

### `POST /transactions/upload`

Uploads a CSV file of bank transactions for ingestion.

**Request**

| Parameter           | Type    | Location    | Description                                     |
|---------------------|---------|-------------|-------------------------------------------------|
| `file`              | file    | form-data   | CSV file to upload                              |
| `failure_threshold` | integer | query param | Max failed rows before aborting. Default: `500` |

**CSV Format**

The CSV must include the following columns:

| Column           | Format / Constraints                        |
|------------------|---------------------------------------------|
| `transaction_id` | Non-empty string                            |
| `account_id`     | Non-empty string                            |
| `user_id`        | Non-empty string                            |
| `merchant_id`    | Non-empty string                            |
| `timestamp`      | ISO-8601 UTC (e.g. `2024-01-15T09:23:11Z`) |
| `amount`         | Valid decimal number                        |
| `currency`       | Exactly 3 characters (ISO-4217)             |
| `category`       | One of the valid categories listed below    |

**Valid categories:** `groceries`, `transport`, `dining`, `income`, `utilities`, `entertainment`, `other`

**Response — 200 OK**

```json
{
  "upload_id": "a1b2c3d4-...",
  "status": "completed",
  "rows_ingested": 950,
  "rows_failed": 12,
  "failure_report_url": "/transactions/upload/a1b2c3d4-.../failures"
}
```

`failure_report_url` is `null` when there are no failures.

**Response — 422 Unprocessable Entity (aborted)**

Returned when failed rows exceed `failure_threshold`:

```json
{
  "detail": {
    "upload_id": "a1b2c3d4-...",
    "status": "aborted",
    "rows_processed": 503,
    "rows_failed": 501,
    "failure_report_url": "/transactions/upload/a1b2c3d4-.../failures"
  }
}
```

---

### `GET /transactions/upload/{upload_id}/failures`

Downloads the failure report for a given upload as a streaming CSV file.

**Response — 200 OK**

| Column  | Description                              |
|---------|------------------------------------------|
| `index` | Row number in the original upload        |
| `data`  | Comma-separated values of the failed row |
| `error` | Validation error messages                |

---

## Validation Rules

A row is rejected if any of the following checks fail:

- `transaction_id`, `account_id`, `user_id`, or `merchant_id` is empty
- `timestamp` is not a valid ISO-8601 UTC datetime
- `amount` is not a valid number
- `currency` is not exactly 3 characters
- `category` is not in the list of valid categories

All errors for a row are collected and written to the failure report together.

---

## Ingestion Pipeline

1. On upload, failure reports older than 7 days are purged.
2. Each row is validated; invalid rows are appended to a per-upload failure report CSV under `/tmp/failure_report/`.
3. If the failure count exceeds `failure_threshold`, ingestion is aborted and a `422` is returned.
4. Valid rows are buffered to a temporary CSV file, then bulk-loaded into the `transactions` table via PostgreSQL `COPY`.
5. An `Upload` record is saved to the `uploads` table with the final counts and status.
6. The temporary file is deleted after ingestion regardless of outcome.

---

## Running Tests

```bash
pytest test_upload.py
```

Tests cover:

- Successful upload with all valid rows
- Upload where all rows fail validation
- Upload that exceeds the failure threshold and is aborted
- Failure report endpoint returns `200`
- `transaction_id` empty value validation
