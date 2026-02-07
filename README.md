# XLSX File Upload Service with FastAPI and PostgreSQL

A FastAPI application that accepts XLSX file uploads and stores data in PostgreSQL with validation and bulk insert optimization.

## Features

- ✅ FastAPI backend with automatic API documentation
- ✅ PostgreSQL database with SQLAlchemy ORM
- ✅ XLSX file parsing with pandas
- ✅ JSON-based schema validation stored in database
- ✅ Bulk insert with single transaction (all-or-nothing)
- ✅ Comprehensive logging and error tracking
- ✅ Per-row validation with schema fetched from DB

## Performance

**Optimized Processing Time**: ~10 seconds for typical file uploads
- **Before optimization**: 40 seconds (one transaction per row)
- **After optimization**: 10 seconds (bulk insert with single session)

### Optimization Strategy
- Single database session for all rows
- Bulk insert using `db.add_all()`
- All-or-nothing transaction (rollback on any error)
- Schema validation against database-stored definitions

## Prerequisites

- Python 3.8+
- PostgreSQL 12+

## Installation

1. **Clone or navigate to the project directory**

2. **Create a virtual environment**
```bash
python -m venv venv
.\venv\Scripts\activate  # Windows
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Set up PostgreSQL database**
```sql
CREATE DATABASE fileupload_db;
```

5. **Configure environment variables**
```bash
# Copy .env.example to .env and update with your database credentials
cp .env.example .env
```

Update `.env`:
```
DATABASE_URL=postgresql://username:password@localhost:5432/fileupload_db
```

## Running the Application

```bash
python main.py
```

Or with uvicorn:
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at:
- **Application**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Alternative Docs**: http://localhost:8000/redoc

## API Endpoints

### 1. Health Check
```
GET /
GET /health
```

### 2. Upload XLSX File
```
POST /upload
Content-Type: multipart/form-data
```

**Request:**
- File: XLSX file with headers in first row

**Expected XLSX Structure:**
| name | email | department | salary |
|------|-------|------------|--------|
| John Doe | john@example.com | Engineering | 75000 |
| Jane Smith | jane@example.com | Marketing | 65000 |

**Response:**
```json
{
  "total_rows": 100,
  "successful_inserts": 95,
  "failed_rows": 5,
  "errors": [
    {
      "row": 3,
      "data": {"name": "", "email": "invalid"},
      "error": "Validation failed: name: Name cannot be empty"
    }
  ]
}
```

## Testing with cURL

```bash
curl -X POST "http://localhost:8000/upload" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@employees.xlsx"
```

## Testing with Python

```python
import requests

url = "http://localhost:8000/upload"
files = {"file": open("employees.xlsx", "rb")}
response = requests.post(url, files=files)
print(response.json())
```

## Data Model

### Employee Record (Modify in models.py)
- `id`: Primary key (auto-generated)
- `name`: Employee name (required, max 100 chars)
- `email`: Email address (required, validated format)
- `department`: Department name (optional, max 50 chars)
- `salary`: Salary amount (optional, must be >= 0)
- `created_at`: Timestamp (auto-generated)

## Validation Rules

Defined in `schemas.py`:
- Name: Required, non-empty, max 100 characters
- Email: Required, valid email format
- Department: Optional, max 50 characters
- Salary: Optional, >= 0, < 10,000,000

## Error Handling

The application implements comprehensive error handling:

1. **Validation Errors**: Captured per row with detailed field-level errors
2. **Database Errors**: Isolated per row, won't affect other rows
3. **File Format Errors**: Rejected before processing
4. **Empty Rows**: Skipped automatically

## Key Design Decisions

### 1. One Transaction Per Row
Each row gets its own database session and transaction. This ensures:
- Complete isolation
- Failed rows don't affect others
- Easy to track which rows failed

```python
db = SessionLocal()  # New session per row
try:
    db.add(record)
    db.commit()
except:
    db.rollback()  # Only this row's transaction
finally:
    db.close()
```

### 2. JSON-Based Validation
Convert each row to dictionary, then validate with Pydantic:
```python
row_json = row_to_json(row, headers)  # Dict
validated = EmployeeRowSchema(**row_json)  # Pydantic validation
```

### 3. Partial Success
Processing continues even when rows fail:
- Tracks success/failure counts
- Captures detailed error information
- Returns comprehensive summary

## Customization

### Modify Data Schema

1. **Update database model** in `models.py`
2. **Update validation schema** in `schemas.py`
3. **Restart application** (tables auto-create)

### Add Custom Validation

Add validators in `schemas.py`:
```python
@field_validator('field_name')
@classmethod
def validate_field(cls, v):
    if condition:
        raise ValueError('Error message')
    return v
```

## Project Structure

```
File upload/
├── main.py              # FastAPI application & endpoints
├── models.py            # SQLAlchemy database models
├── schemas.py           # Pydantic validation schemas
├── database.py          # Database configuration
├── requirements.txt     # Python dependencies
├── .env                 # Environment variables (not in git)
├── .env.example         # Environment template
└── README.md           # This file
```


## Contributing

This is Phase 1 focused on correctness. Performance optimizations welcome in Phase 2!
