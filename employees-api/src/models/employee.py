
from pydantic import BaseModel, Field
from uuid import uuid4
from typing import List, Optional
from uuid import UUID

from uuid import UUID, uuid4

class Employee(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    firstName: str
    lastName: str
    age: int

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
        return next((employee for employee in self.employees if employee.id == employee_id), None)
    def update_employee(self, employee_id: UUID, updated_employee: Employee) -> Optional[Employee]:
        for idx, employee in enumerate(self.employees):
            if employee.id == employee_id:
                self.employees[idx] = updated_employee
                return updated_employee
        return None
    def delete_employee(self, employee_id: UUID) -> bool:
        for idx, employee in enumerate(self.employees):
            if employee.id == employee_id:
                del self.employees[idx]
                return True
        return False
def get_employee_service() -> EmployeeService:   
    return EmployeeService()