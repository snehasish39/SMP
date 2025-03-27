from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy.orm import Session
from models import User
from pydantic import BaseModel
from persistence import sql_repo.
from database import SessionLocal  # Assuming SessionLocal is your DB session function

app = FastAPI()

# Pydantic model for creating a user
class UserCreateRequest(BaseModel):
    name: str
    email: str
    phone: str

# Pydantic model for user response
class UserResponse(BaseModel):
    user_id: str
    name: str
    email: str
    phone: str

    class Config:
        orm_mode = True  # To allow the SQLAlchemy model to be returned as a response

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/users/", response_model=UserResponse)
def create_user(request: UserCreateRequest, db: Session = Depends(get_db)):
    # Create instance of SQLUserRepository with the DB session
    user_repo = SQLUserRepository(db)

    # Check if the user already exists by email or phone
    if user_repo.get_by_email(request.email):
        raise HTTPException(status_code=400, detail="Email already exists.")
    if user_repo.get_by_phone(request.phone):
        raise HTTPException(status_code=400, detail="Phone number already exists.")

    # Create a new User instance
    new_user = User(
        name=request.name,
        email=request.email,
        phone=request.phone
    )

    # Create the user in the database
    created_user = user_repo.create_user(new_user)

    return created_user
