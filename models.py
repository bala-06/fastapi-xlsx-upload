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
