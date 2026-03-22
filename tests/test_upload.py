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

def test_valid_csv_sucess():
    transaction_id1 = str(uuid.uuid4())
    transaction_id2 = str(uuid.uuid4())
    test_csv = f"""transaction_id,account_id,user_id,timestamp,amount,currency,merchant_id,category
{transaction_id1},ACC-0012,USR-0003,2024-01-15T09:23:11Z,-42.50,GBP,MRC-0042,groceries
{transaction_id2},ACC-0012,USR-0003,2024-01-16T14:05:00Z,1850.00,GBP,MRC-0017,income"""

    response = client.post(
        "/transactions/upload",
        files = {"file": ("test.csv", test_csv, "text/csv")},
    )

    assert response.status_code == 200

    upload_id = response.json()["upload_id"]
    assert response.json() == {
        "upload_id": upload_id,
        "status": "completed",
        "rows_ingested": 2,
        "rows_failed": 0,
        "failure_report_url": None,
    }

    