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
