from typing import List
from fastapi import Form
from uuid import UUID
from fastapi import APIRouter, HTTPException, Depends
from src.models.employee import Employee, EmployeeService, get_employee_service

router = APIRouter()

@router.get("/employees", response_model=List[Employee])
def get_employees(employee_service: EmployeeService = Depends(get_employee_service)):
    return employee_service.get_employees()


@router.get("/employees/{employee_id}", response_model=Employee)
def get_employee(employee_id: UUID, employee_service: EmployeeService = Depends(get_employee_service)):
    employee = employee_service.get_employee(employee_id)
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    return employee

@router.post("/employees", response_model=Employee, status_code=201)
def create_employee(employee: Employee, employee_service: EmployeeService = Depends(get_employee_service)):
    for existing in employee_service.get_employees():
        if (existing.firstName.lower() == employee.firstName.lower() and
            existing.lastName.lower() == employee.lastName.lower() and
            existing.age == employee.age):
            raise HTTPException(status_code=400, detail="Employee with these details already exists")
    
    return employee_service.create_employee(employee)

@router.put("/employees/{employee_id}", response_model=Employee)
def update_employee(
    employee_id: UUID,
    firstName: str = Form(...),
    lastName: str = Form(...),
    age: int = Form(...),
    employee_service: EmployeeService = Depends(get_employee_service)
):
    employee = employee_service.update_employee(employee_id, firstName, lastName, age)
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    return employee

@router.delete("/employees/{employee_id}", status_code=200)
def delete_employee(employee_id: UUID, employee_service: EmployeeService = Depends(get_employee_service)):
    success = employee_service.delete_employee(employee_id)
    if not success:
        raise HTTPException(status_code=404, detail="Employee not found")