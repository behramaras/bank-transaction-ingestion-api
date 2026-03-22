import uuid
from app.main import app
from app.ingest import row_validation
from fastapi.testclient import TestClient
client = TestClient(app)

row_data = {
    "transaction_id": "T-0000000001",
    "account_id": "ACC-0012",
    "user_id": "USR-0003",
    "timestamp": "2024-01-15T09:23:11Z",
    "amount": "-42.50",
    "currency": "GBP",
    "merchant_id": "MRC-0042",
    "category": "groceries",
}
