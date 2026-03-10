from fastapi import FastAPI, Depends, UploadFile, File
from sqlalchemy.orm import Session
from app.databases import Base, engine, get_db
from app.helpers import UploadResponse
from app.ingest import ingestion
from app.failure_report import generate_csv
from app.consts import DEFAULT_FAILURE_THRESHOLD


app = FastAPI()

# Create database
Base.metadata.create_all(bind=engine)

@app.post("/transactions/upload", response_model=UploadResponse)
async def upload_csv(
    file: UploadFile = File(...),
    failure_threshold: int = DEFAULT_FAILURE_THRESHOLD,
    db: Session = Depends(get_db)
):
    return ingestion(file, db, failure_threshold)

@app.get("/transactions/upload/{upload_id}/failures")
def get_failures(upload_id: str):
    return generate_csv(upload_id)
