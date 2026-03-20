import io
import os
import csv
import uuid
import tempfile
from datetime import datetime
from fastapi import UploadFile, HTTPException
from sqlalchemy.orm import Session
from app.models import Upload
from app.failure_report import omit_report, write_report
from app.consts import DEFAULT_FAILURE_THRESHOLD, valid_categories, valid_field_names

def row_validation(row: dict) -> list[str]:
    errors = []

    transaction_id = row.get("transaction_id", "").strip()
    if not transaction_id:
        errors.append("transaction_id: cannot be empty")

    account_id = row.get("account_id", "").strip()
    if not account_id:
        errors.append("account_id: cannot be empty")

    user_id = row.get("user_id", "").strip()
    if not user_id:
        errors.append("user_id: cannot be empty")

    merchant_id = row.get("merchant_id", "").strip()
    if not merchant_id:
        errors.append("merchant_id: cannot be empty")
    
    # Time stamp should be ISO-8601 UTC format
    timestamp_str = row.get("timestamp", "")
    try:
        parsed_time = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
    except ValueError:
        errors.append("timestamp: invalid format")
    
    amount = row.get("amount")
    try:
        amount_float = float(amount)
    except (ValueError, TypeError):
        errors.append("amount: not a valid number or cannot be empty")

    # Currency should be ISO-4217 format
    currency = row.get("currency", "")
    if len(currency) != 3:
        errors.append("currency: must be 3 characters")
    
    category = row.get("category")
    if category not in valid_categories:
        errors.append("category: invalid category")

    return errors


def ingestion(file: UploadFile, db: Session, failure_threshold: int = DEFAULT_FAILURE_THRESHOLD):
    omit_report()
    upload_id = str(uuid.uuid4())

    row_index = 0
    rows_ingested = 0
    rows_failed = 0

    # Create temperory file for valid rows
    temperory_file = tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False, newline="")
    temperory_path = temperory_file.name
    
    # Setup CSV writer for temperory file
    temperory_writer = csv.DictWriter(temperory_file, fieldnames=valid_field_names)
    temperory_writer.writeheader()

    file.file.seek(0)
    row_reader = csv.DictReader(io.TextIOWrapper(file.file, encoding="utf-8"))
    for row in row_reader:
        row_index += 1
        errors = row_validation(row)

        if errors:
            rows_failed += 1
            write_report(upload_id, row_index, data=", ".join(row.values()), error=", ".join(errors))
            
            # Stop and fail if it exceeds threshold
            if rows_failed > failure_threshold:
                temperory_file.close()
                os.remove(temperory_path)
                raise HTTPException(
                    status_code=422,
                    detail={
                        "upload_id": upload_id,
                        "status": "aborted",
                        "rows_processed": row_index,
                        "rows_failed": rows_failed,
                        "failure_report_url": f"/transactions/upload/{upload_id}/failures",
                    },
                )

        else:
            rows_ingested += 1
            temperory_writer.writerow(
                {
                    "transaction_id": row["transaction_id"],
                    "account_id": row["account_id"],
                    "user_id": row["user_id"],
                    "timestamp": row["timestamp"],
                    "amount": row["amount"],
                    "currency": row["currency"],
                    "merchant_id": row["merchant_id"],
                    "category": row["category"],
                    "upload_id": upload_id,
                }
            )
    temperory_file.close()

    try: 
        db_copy(temperory_path, db)

        # Save Upload object to database
        upload = Upload(
            upload_id = upload_id,
            status = "completed",
            rows_ingested = rows_ingested,
            rows_failed = rows_failed,
            created_at = datetime.now(),
        )
        
        db.add(upload)
        db.commit()

    except Exception:
        db.rollback()
        raise
    
    finally:
        # Clean up temperory file in any case
        os.remove(temperory_path)

    return {
        "upload_id": upload_id,
        "status": "completed",
        "rows_ingested": rows_ingested,
        "rows_failed": rows_failed,
        "failure_report_url": f"/transactions/upload/{upload_id}/failures" if rows_failed > 0 else None,
    }

def db_copy(temperory_path: str, db: Session):
    # Get the raw psycopg2 connection because we need it for COPY
    connection = db.connection().connection
    cursor = connection.cursor()

    with open(temperory_path, "r") as f:
        next(f)
        cursor.copy_expert(
            """copy transactions (
                transaction_id,
                upload_id,
                account_id,
                user_id,
                timestamp,
                amount,
                currency,
                merchant_id,
                category
            ) from stdin with csv""",
            f,
        )
    cursor.close()
