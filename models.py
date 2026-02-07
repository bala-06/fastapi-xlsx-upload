from sqlalchemy import Column, Integer, String, Float, DateTime
from sqlalchemy.sql import func
from database import Base

class EmployeeRecord(Base):
    """
    Example model for storing employee data from XLSX file.
    Modify fields based on your actual XLSX structure.
    """
    __tablename__ = "employee_records"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, nullable=False)
    department = Column(String, nullable=True)
    salary = Column(Float, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self):
        return f"<EmployeeRecord(name={self.name}, email={self.email})>"


from sqlalchemy import Boolean, Text
from sqlalchemy.dialects.postgresql import JSON

class ColumnDefinition(Base):
    """
    Stores the validation definition for a single column.
    Each row corresponds to one column in the JSON schema.
    """
    __tablename__ = "column_definitions"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, unique=True)
    required = Column(Boolean, nullable=False, default=False)
    type = Column(String, nullable=False, default="string")
    format = Column(String, nullable=True)
    max_length = Column(Integer, nullable=True)
    enum = Column(JSON, nullable=True)
    minimum = Column(Float, nullable=True)
    maximum = Column(Float, nullable=True)

    def to_dict(self):
        return {
            "name": self.name,
            "required": self.required,
            "type": self.type,
            "format": self.format,
            "max_length": self.max_length,
            "enum": self.enum,
            "minimum": self.minimum,
            "maximum": self.maximum,
        }
