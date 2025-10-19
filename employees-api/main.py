from fastapi import FastAPI
from src.api import employees
from src.middleware.error_handler import ErrorHandlerMiddleware
from src.middleware import error_handler

app = FastAPI()
app.include_router(employees.router)
app.add_middleware(ErrorHandlerMiddleware)
error_handler.setup_exception_handlers(app)