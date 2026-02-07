from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional

class EmployeeRowSchema(BaseModel):
    """
    Pydantic schema for validating each row from XLSX.
    This validates individual rows as JSON objects.
    """
    name: str = Field(..., min_length=1, max_length=100, description="Employee name")
    email: EmailStr = Field(..., description="Employee email address")
    department: Optional[str] = Field(None, max_length=50, description="Department name")
    salary: Optional[float] = Field(None, ge=0, description="Salary amount")

    @field_validator('name')
    @classmethod
    def name_must_not_be_empty(cls, v: str) -> str:
        if not v or v.strip() == "":
            raise ValueError('Name cannot be empty or whitespace')
        return v.strip()

    @field_validator('salary')
    @classmethod
    def salary_must_be_reasonable(cls, v: Optional[float]) -> Optional[float]:
        if v is not None and v > 10000000:
            raise ValueError('Salary seems unreasonably high')
        return v

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "name": "John Doe",
                    "email": "john.doe@example.com",
                    "department": "Engineering",
                    "salary": 75000.0
                }
            ]
        }
    }

class UploadResponse(BaseModel):
    """Response model for upload endpoint"""
    total_rows: int
    successful_inserts: int
    failed_rows: int
    errors: list[dict]

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "total_rows": 100,
                    "successful_inserts": 95,
                    "failed_rows": 5,
                    "errors": [
                        {"row": 3, "error": "Invalid email format"},
                        {"row": 7, "error": "Name cannot be empty"}
                    ]
                }
            ]
        }
    }
