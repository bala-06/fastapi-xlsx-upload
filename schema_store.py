import json
from typing import Dict, Any, List
from pathlib import Path

from database import SessionLocal
from models import ColumnDefinition


def ensure_schema_loaded(json_path: str | Path) -> None:
    """
    If `column_definitions` table is empty, load definitions from the provided JSON file.
    """
    path = Path(json_path)
    if not path.exists():
        raise FileNotFoundError(f"Schema file not found: {path}")

    db = SessionLocal()
    try:
        count = db.query(ColumnDefinition).count()
        if count > 0:
            return

        with open(path, "r", encoding="utf-8") as fh:
            data = json.load(fh)

        for col in data.get("columns", []):
            cd = ColumnDefinition(
                name=col.get("name"),
                required=bool(col.get("required", False)),
                type=col.get("type", "string"),
                format=col.get("format"),
                max_length=col.get("max_length"),
                enum=col.get("enum"),
                minimum=col.get("minimum"),
                maximum=col.get("maximum"),
            )
            db.add(cd)
        db.commit()
    finally:
        db.close()


def get_schema_from_db() -> Dict[str, Any]:
    """
    Read all ColumnDefinition rows and return a schema dict in the format expected by the processor.
    This function performs a fresh DB read and is intended to be called per-row (intentionally slow).
    """
    db = SessionLocal()
    try:
        rows: List[ColumnDefinition] = db.query(ColumnDefinition).order_by(ColumnDefinition.id).all()
        return {"columns": [r.to_dict() for r in rows]}
    finally:
        db.close()
