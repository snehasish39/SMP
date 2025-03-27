from fastapi import FastAPI
from controller import upi_controller, transaction_controller

app = FastAPI()

# Include routes
app.include_router(upi_controller.router)
app.include_router(transaction_controller.router)

# Middleware (currently disabled)
# from middleware.middleware import auth_middleware
# app.middleware("http")(auth_middleware)
# app.middleware("http")(logging_middleware)

@app.get("/")
def home():
    return {"message": "Polyglot UPI System Running"}
