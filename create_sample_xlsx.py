"""
Script to create a 500-row XLSX file for FastAPI upload testing.
Includes valid and intentionally invalid rows.
Run: python create_500_sample_xlsx.py
"""

from openpyxl import Workbook


def create_sample_xlsx(filename="employees_500.xlsx"):
    wb = Workbook()
    ws = wb.active
    ws.title = "Employees"

    # Header
    ws.append(["name", "email", "department", "salary"])

    departments = ["Engineering", "HR", "Finance", "Marketing", "Operations"]

    valid_count = 0
    invalid_count = 0

    for i in range(1, 7001):
        name = f"Employee {i}"
        email = f"employee{i}@example.com"
        department = departments[i % len(departments)]
        salary = 50000 + (i % 10) * 3000

        # ---- Inject invalid data intentionally ----
        if i % 50 == 0:
            email = "invalid-email"          # invalid email
            invalid_count += 1
        elif i % 75 == 0:
            name = ""                         # empty name
            invalid_count += 1
        elif i % 120 == 0:
            salary = 99999999999              # unrealistic salary
            invalid_count += 1
        else:
            valid_count += 1
        # ------------------------------------------

        ws.append([name, email, department, salary])

    wb.save(filename)

    print(f"✅ XLSX file created: {filename}")
    print(f"📊 Total rows: 500")
    print(f"✔ Valid rows: {valid_count}")
    print(f"✖ Invalid rows: {invalid_count}")


if __name__ == "__main__":
    create_sample_xlsx()
