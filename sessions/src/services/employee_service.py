from typing import List, Optional
from uuid import UUID
from src.models.employee_model import Employee

class EmployeeService:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(EmployeeService, cls).__new__(cls)
            cls._instance.employees = []
        return cls._instance

    def create_employee(self, employee: Employee) -> Employee:
        self.employees.append(employee)
        return employee

    def get_employees(self) -> List[Employee]:
        return self.employees

    def get_employee(self, employee_id: UUID) -> Optional[Employee]:
        return next((e for e in self.employees if e.id == employee_id), None)

    def update_employee(self, employee_id: UUID, firstName: str, lastName: str, age: int) -> Optional[Employee]:
        for e in self.employees:
            if e.id == employee_id:
                e.firstName = firstName
                e.lastName = lastName
                e.age = age
                return e
        return None

    def delete_employee(self, employee_id: UUID) -> bool:
        for idx, e in enumerate(self.employees):
            if e.id == employee_id:
                del self.employees[idx]
                return True
        return False


employee_service = EmployeeService()

def get_employee_service() -> EmployeeService:
    return employee_service
