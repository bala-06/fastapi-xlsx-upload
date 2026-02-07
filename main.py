from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from typing import Dict, Any, List
from pydantic import ValidationError

import logging

from database import init_db, SessionLocal
from models import EmployeeRecord
from schemas import EmployeeRowSchema, UploadResponse
import json
from pathlib import Path

# pandas-based processor (row-by-row using JSON schema)
from pandas_processor import process_file_pandas

# Configure basic logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s - %(message)s")
logger = logging.getLogger(__name__)

app = FastAPI(
    title="XLSX File Upload Service",
    description="Upload XLSX files and store data row-by-row in PostgreSQL with validation",
    version="1.0.0"
)

@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    init_db()
    print("✅ Database initialized")

@app.get("/")
async def root():
    """Health check endpoint"""
    return {"message": "XLSX Upload Service is running", "status": "healthy"}

def row_to_json(row: tuple, headers: list) -> Dict[str, Any]:
    """
    Small helper retained for backward compatibility. Not used by pandas flow.
    """
    row_dict = {}
    for idx, header in enumerate(headers):
        value = row[idx] if idx < len(row) else None
        if value is None or (isinstance(value, str) and value.strip() == ""):
            row_dict[header] = None
        else:
            row_dict[header] = value
    return row_dict

async def upload_xlsx_file(file: UploadFile = File(...)):
    """
    Upload XLSX file and process row by row.
    
    Process:
    1. Read XLSX file
    2. For each row:
       - Convert to JSON
       - Validate against schema
       - Open new transaction
       - Insert to database
       - Commit if successful, rollback if failed
    3. Return summary with success/failure counts
    
    Args:
        file: Uploaded XLSX file
    
    Returns:
        UploadResponse with processing results
    """
    # Validate file type
    if not file.filename.endswith((".xlsx", ".xls")):
        raise HTTPException(status_code=400, detail="Only XLSX/XLS files are supported")

    contents = await file.read()

    # Load column schema JSON (project root)
    schema_path = Path(__file__).parent / "column_schema.json"
    if not schema_path.exists():
        raise HTTPException(status_code=500, detail="Column schema not found on server")

    try:
        with open(schema_path, "r", encoding="utf-8") as fh:
            schema = json.load(fh)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load schema: {e}")

    try:
        result = process_file_pandas(contents, schema)
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Processing failed: {e}")

    return UploadResponse(**result)


@app.post("/upload_pandas", response_model=UploadResponse)
async def upload_xlsx_file_pandas(file: UploadFile = File(...)):
    """Upload XLSX and process using pandas + JSON schema validation per row."""
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(status_code=400, detail="Only XLSX/XLS files are supported")

    contents = await file.read()

    # Load column schema JSON (project root)
    schema_path = Path(__file__).parent / "column_schema.json"
    if not schema_path.exists():
        raise HTTPException(status_code=500, detail="Column schema not found on server")

    try:
        with open(schema_path, "r", encoding="utf-8") as fh:
            schema = json.load(fh)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load schema: {e}")

    try:
        result = process_file_pandas(contents, schema)
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Processing failed: {e}")

    return UploadResponse(**result)

@app.get("/health")
async def health_check():
    """Detailed health check"""
    return {
        "status": "healthy",
        "database": "connected",
        "service": "XLSX Upload API"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
