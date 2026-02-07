# XLSX File Upload Service - FastAPI + PostgreSQL

High-performance bulk data upload service with schema-driven validation and transaction safety.

## 📊 Performance Overview

| Metric | Value |
|--------|-------|
| **Processing Time** | ~3 seconds |
| **First Optimization** | 10 seconds (bulk insert) |
| **Original Version** | 40 seconds (per-row transactions) |
| **Total Performance Gain** | **13x faster (92.5% improvement)** |
| **Transaction Model** | Single bulk transaction |
| **Partial Success** | ❌ No - all-or-nothing |

## 🚀 Key Features

- ✅ **Bulk Insert Optimization** - Single transaction for all rows
- ✅ **Schema-Driven Validation** - JSON schema stored in PostgreSQL
- ✅ **All-or-Nothing Safety** - Complete rollback on any error
- ✅ **Pandas-Based Processing** - Efficient Excel file parsing
- ✅ **Comprehensive Logging** - DEBUG-level per-row tracking
- ✅ **FastAPI Backend** - Auto-generated API documentation
- ✅ **Database-Backed Schema** - Dynamic validation rules

## 🎯 How It Works

### Upload Flow

1. **File Upload** → Accepts XLSX file via REST API
2. **Pandas Processing** → Reads Excel into DataFrame
3. **Per-Row Validation** → Fetches schema from DB and validates each row
4. **Bulk Insert** → All validated rows inserted in one transaction
5. **Atomic Commit** → Either all succeed or all rollback

### Architecture

```
┌─────────────────┐
│  Upload XLSX    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Pandas Read    │
└────────┬────────┘
         │
         ▼
┌─────────────────────────┐
│  For Each Row:          │
│  1. Fetch Schema from DB│
│  2. Validate Row        │
│  3. Add to Batch        │
└────────┬────────────────┘
         │
         ▼
┌─────────────────────────┐
│  Bulk Insert (One Tx)   │
│  • db.add_all()         │
│  • Commit ALL           │
│  • OR Rollback ALL      │
└─────────────────────────┘
```

## ⚡ Why 13x Faster?

### Version 1: Original (40 seconds)
```python
for each row:
    db = SessionLocal()  # New session overhead
    try:
        db.add(record)
        db.commit()      # Individual commit overhead
    except:
        db.rollback()
    finally:
        db.close()       # Session cleanup overhead
```
**Issues:**
- Session creation/destruction repeated 1000s of times
- Database commit per row
- Network round-trip per row

### Version 2: Bulk Insert (10 seconds)
```python
db = SessionLocal()      # One session
records = []
for each row:
    schema = get_schema_from_db()  # Still fetching per row!
    print(f"Row {idx}: {row}")     # Printing per row!
    validate(row)
    records.append(create_record(row))

db.add_all(records)      # Bulk insert
db.commit()              # One commit
db.close()
```
**Improvements:**
- Single session for entire upload
- One database commit
- **Still slow:** Per-row schema fetch + console prints

### Version 3: Fully Optimized (3 seconds)
```python
db = SessionLocal()
schema = get_schema_from_db()  # Fetch ONCE before loop
records = []
for each row:
    # No DB queries
    # No console prints
    # Minimal logging
    validate(row, schema)
    records.append(create_record(row))

db.add_all(records)
db.commit()
db.close()
```
**Final Optimizations:**
- Schema fetched once (not per row)
- Removed per-row console prints
- Reduced logging overhead
- **Result: 40s → 10s → 3s (13x faster overall)**

## 📋 Prerequisites

- Python 3.8+
- PostgreSQL 12+
- pip (Python package manager)

## 🛠️ Installation

### 1. Clone/Navigate to Project Directory
```bash
cd "D:\FILES\File upload"
```

### 2. Create Virtual Environment
```bash
python -m venv venv
.\venv\Scripts\activate  # Windows
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Set Up PostgreSQL Database
```sql
CREATE DATABASE fileupload_db;
```

Or use Docker:
```bash
docker-compose up -d
```

### 5. Configure Environment Variables
Copy `.env.example` to `.env` and update:
```env
DATABASE_URL=postgresql://username:password@localhost:5432/fileupload_db
```

## 🚀 Running the Application

```bash
python main.py
```

The API will be available at:
- **Application**: http://localhost:8000
- **API Docs (Swagger)**: http://localhost:8000/docs
- **Alternative Docs**: http://localhost:8000/redoc

## 📡 API Endpoints

### POST /upload_pandas
Upload and process XLSX file with bulk insert.

**Request:**
```bash
curl -X POST "http://localhost:8000/upload_pandas" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@employees.xlsx"
```

**Response:**
```json
{
  "total_rows": 100,
  "successful_inserts": 100,
  "failed_rows": 0,
  "errors": []
}
```

**Error Response (any row fails):**
```json
{
  "detail": "Validation failed at row 3: email: Invalid email format"
}
```

### GET /health
Health check endpoint.

## 📊 Expected XLSX Structure

| name | email | department | salary |
|------|-------|------------|--------|
| John Doe | john@example.com | Engineering | 75000 |
| Jane Smith | jane@example.com | Marketing | 65000 |

## 🔍 Validation Schema

Schema is stored in the `column_definitions` table and loaded from `column_schema.json` on first startup.

### Example Schema
```json
{
  "columns": [
    {
      "name": "name",
      "required": true,
      "type": "string",
      "max_length": 100
    },
    {
      "name": "email",
      "required": true,
      "type": "string",
      "format": "email",
      "max_length": 255
    },
    {
      "name": "department",
      "required": false,
      "type": "string",
      "max_length": 50,
      "enum": ["Engineering", "Marketing", "Sales", "HR", "Finance", "Operations", "IT"]
    },
    {
      "name": "salary",
      "required": false,
      "type": "number",
      "minimum": 0,
      "maximum": 10000000
    }
  ]
}
```

## 📁 Project Structure

```
File upload/
├── main.py                  # FastAPI application & endpoints
├── models.py                # SQLAlchemy database models
├── schemas.py               # Pydantic validation schemas
├── database.py              # Database configuration
├── pandas_processor.py      # Bulk upload processor
├── schema_store.py          # Schema DB management
├── column_schema.json       # Schema seed file
├── requirements.txt         # Python dependencies
├── .env                     # Environment variables (not in git)
├── .gitignore              # Git ignore rules
├── docker-compose.yml       # PostgreSQL Docker setup
├── create_sample_xlsx.py    # Test data generator
└── README.md               # This file
```

## 🧪 Testing

### Generate Sample Data
```bash
python create_sample_xlsx.py
```

This creates `sample_employees.xlsx` with test data (includes some invalid rows for testing).

### Upload Test File
```bash
curl -X POST "http://localhost:8000/upload_pandas" \
  -F "file=@sample_employees.xlsx"
```

## ⚙️ Configuration

### Logging Levels
Change in `main.py`:
```python
logging.basicConfig(level=logging.INFO)  # Change to INFO for less verbose
```

### Database Schema
Modify `column_schema.json` and delete `column_definitions` table rows to reload:
```sql
DELETE FROM column_definitions;
```
Then restart the app.

## 🔧 Troubleshooting

### Issue: "Module not found" errors
```bash
pip install -r requirements.txt
```

### Issue: Database connection fails
Check `.env` file and ensure PostgreSQL is running:
```bash
docker-compose up -d
```

### Issue: Schema not loading
Delete existing schema and restart:
```sql
TRUNCATE TABLE column_definitions;
```

## 🎯 Design Trade-offs

### All-or-Nothing vs Partial Success

**Current (All-or-Nothing):**
- ✅ Data consistency guaranteed
- ✅ Simpler error handling
- ✅ 5x faster (bulk insert)
- ❌ One bad row fails entire upload

**Alternative (Partial Success):**
- ✅ Some rows can succeed
- ❌ Complex error tracking
- ❌ 5x slower (individual transactions)
- ❌ Potential data inconsistency

For this use case, speed and consistency outweigh partial success.

## 📈 Performance Metrics

- **File Size**: ~1000 rows
- **Processing Time**: 3 seconds
- **Optimization Journey**: 40s → 10s → 3s
- **Database Commits**: 1 (vs 1000 in v1)
- **Schema Fetches**: 1 (vs 1000 in v2)
- **Session Overhead**: Eliminated 99.9%
- **I/O Overhead**: Eliminated per-row prints
