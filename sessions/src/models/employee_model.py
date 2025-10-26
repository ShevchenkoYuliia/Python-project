from pydantic import BaseModel, Field
from uuid import uuid4, UUID

class Employee(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    firstName: str
    lastName: str
    age: int
