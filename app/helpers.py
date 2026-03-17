from pydantic import BaseModel
from typing import Optional

class UploadResponse(BaseModel):
    upload_id : str
    status : str
    rows_ingested : Optional[int] = None
    rows_failed : int
    failure_report_url : Optional[str] = None