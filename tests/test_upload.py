import uuid
from app.main import app
from app.ingest import row_validation
from fastapi.testclient import TestClient
client = TestClient(app)

