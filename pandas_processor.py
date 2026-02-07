import json
from io import BytesIO
from typing import Dict, Any, List, Tuple
import re
import logging

import numpy as np
import pandas as pd

from sqlalchemy.exc import SQLAlchemyError
from database import SessionLocal
from models import EmployeeRecord
from schema_store import get_schema_from_db

logger = logging.getLogger(__name__)

EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _is_empty(val: Any) -> bool:
    if val is None:
        return True
    # pandas uses float('nan') for missing values
    try:
        import math
        if isinstance(val, float) and math.isnan(val):
            return True
    except Exception:
        pass
    if isinstance(val, str) and val.strip() == "":
        return True
    return False


def _sanitize_for_json(obj: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert any pandas/numpy missing values and numpy scalars into JSON-serializable
    Python types (None, int, float, str).
    """
    out: Dict[str, Any] = {}
    for k, v in obj.items():
        try:
            if pd.isna(v):
                out[k] = None
            elif isinstance(v, (np.generic,)):
                out[k] = v.item()
            else:
                out[k] = v
        except Exception:
            # Fallback: try converting numpy scalar or leave as string
            try:
                out[k] = v.item()
            except Exception:
                out[k] = v
    return out


def validate_row_against_schema(row_json: Dict[str, Any], schema: Dict[str, Any]) -> Tuple[bool, str, Dict[str, Any]]:
    """
    Validate a single row (dict) against the provided JSON schema (custom minimal schema).
    Returns (is_valid, error_message, cleaned_row)
    """
    cleaned: Dict[str, Any] = {}
    for col_def in schema.get("columns", []):
        col_name = col_def["name"]
        required = col_def.get("required", False)
        col_type = col_def.get("type", "string")
        value = row_json.get(col_name)

        if _is_empty(value):
            if required:
                return False, f"Missing required field '{col_name}'", row_json
            else:
                cleaned[col_name] = None
                continue

        # Type checks
        if col_type == "string":
            sval = str(value).strip()
            max_len = col_def.get("max_length")
            if max_len is not None and len(sval) > max_len:
                return False, f"Field '{col_name}' exceeds max_length {max_len}", row_json
            # enum check
            enum_vals = col_def.get("enum")
            if enum_vals is not None and sval not in enum_vals:
                return False, f"Field '{col_name}' must be one of {enum_vals}", row_json
            # format checks (e.g., email)
            fmt = col_def.get("format")
            if fmt == "email":
                if not EMAIL_REGEX.match(sval):
                    return False, f"Field '{col_name}' is not a valid email", row_json
            cleaned[col_name] = sval

        elif col_type == "number":
            try:
                num = float(value)
            except Exception:
                return False, f"Field '{col_name}' must be a number", row_json
            minimum = col_def.get("minimum")
            maximum = col_def.get("maximum")
            if minimum is not None and num < minimum:
                return False, f"Field '{col_name}' must be >= {minimum}", row_json
            if maximum is not None and num > maximum:
                return False, f"Field '{col_name}' must be <= {maximum}", row_json
            cleaned[col_name] = num

        else:
            # Unknown type - treat as string
            sval = str(value).strip()
            cleaned[col_name] = sval

    return True, "", cleaned


def _create_record(cleaned_row: Dict[str, Any]) -> EmployeeRecord:
    """Create a database record instance (not yet persisted)."""
    return EmployeeRecord(
        name=cleaned_row.get("name"),
        email=cleaned_row.get("email"),
        department=cleaned_row.get("department"),
        salary=cleaned_row.get("salary")
    )


def process_file_pandas(file_bytes: bytes, schema: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process an uploaded XLSX file (bytes) using pandas, validating each row against schema,
    inserting ALL valid rows into DB with ONE session/transaction. If any error occurs, rollback everything.
    """
    results: List[Dict[str, Any]] = []
    total_rows = 0
    successful_inserts = 0
    failed_rows = 0
    errors: List[Dict[str, Any]] = []

    # Read Excel into DataFrame
    try:
        df = pd.read_excel(BytesIO(file_bytes), engine="openpyxl")
    except Exception as e:
        logger.exception("Failed to read Excel file via pandas")
        raise ValueError(f"Failed to read Excel file via pandas: {e}")

    # Normalize headers: lower-case and strip
    df.columns = [str(c).lower().strip() for c in df.columns]

    logger.info("Processing Excel file via pandas: %d rows detected", len(df))

    # Collect validated records for bulk insert
    records_to_insert: List[EmployeeRecord] = []

    # Iterate rows one-by-one for validation
    for idx, row in df.iterrows():
        total_rows += 1
        # Build row_json mapping based on schema column names
        row_json: Dict[str, Any] = {}
        for col_def in schema.get("columns", []):
            col_name = col_def["name"]
            # If DataFrame lacks the column, value will be None
            value = row.get(col_name) if col_name in df.columns else None
            row_json[col_name] = value

        # Skip completely empty rows
        if all(_is_empty(v) for v in row_json.values()):
            continue

        # Fetch schema from DB for this row (intentionally slow per requirement)
        try:
            schema = get_schema_from_db()
        except Exception as e:
            logger.exception("Failed to fetch schema from DB for row %d", idx + 2)
            failed_rows += 1
            errors.append({"row": idx + 2, "data": _sanitize_for_json(row_json), "error": f"Failed to fetch schema: {e}"})
            # Fail entire transaction
            raise ValueError(f"Failed to fetch schema for row {idx + 2}: {e}")

        # Verbose logging: raw row preview
        sanitized_row_preview = _sanitize_for_json(row_json)
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug("Row %d raw data: %s", idx + 2, sanitized_row_preview)

        # Print every row to console while validating (helps measure logging/print impact)
        # print(f"Validating row {idx + 2}: {sanitized_row_preview}", flush=True)
        logger.info("Validating row %d: %s", idx + 2, sanitized_row_preview)

        is_valid, err_msg, cleaned = validate_row_against_schema(row_json, schema)
        if not is_valid:
            failed_rows += 1
            sanitized = _sanitize_for_json(row_json)
            logger.error("Validation failed at row %d: %s -- data: %s", idx + 2, err_msg, sanitized)
            errors.append({"row": idx + 2, "data": sanitized, "error": err_msg})
            # Fail entire transaction on validation error
            raise ValueError(f"Validation failed at row {idx + 2}: {err_msg}")

        if logger.isEnabledFor(logging.DEBUG):
            logger.debug("Row %d validated -> cleaned: %s", idx + 2, _sanitize_for_json(cleaned))

        # Create record and add to list for bulk insert
        record = _create_record(cleaned)
        records_to_insert.append(record)

    # Bulk insert all validated records in ONE transaction
    db = SessionLocal()
    try:
        logger.info("Starting bulk insert of %d records with one session", len(records_to_insert))
        db.add_all(records_to_insert)
        db.commit()
        successful_inserts = len(records_to_insert)
        logger.info("Bulk insert successful: %d records committed", successful_inserts)
    except Exception as e:
        logger.exception("Bulk insert failed, rolling back entire transaction")
        db.rollback()
        raise ValueError(f"Bulk insert failed: {str(e)}")
    finally:
        db.close()

    return {
        "total_rows": total_rows,
        "successful_inserts": successful_inserts,
        "failed_rows": failed_rows,
        "errors": errors
    }
