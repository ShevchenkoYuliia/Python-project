from fastapi import FastAPI
from src.api import employees, secure_communication_router
from src.middleware.error_handler import ErrorHandlerMiddleware
from src.middleware import error_handler

app = FastAPI()
app.include_router(employees.router)
app.include_router(secure_communication_router.router)

app.add_middleware(ErrorHandlerMiddleware)
error_handler.setup_exception_handlers(app)



@app.get("/")
def root():
    return {"message": "Secure Communication Server is running"}