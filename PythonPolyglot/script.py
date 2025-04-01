from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy import create_engine, Column, Integer, DateTime, String, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from pymongo import MongoClient
from pydantic import BaseModel
import uuid

# --------------------------- SQLAlchemy Setup (MSSQL) ---------------------------

SQLALCHEMY_DATABASE_URL = "mssql+pyodbc://GroupX:CepK837+Gy@mcruebs04.isad.isadroot.ex.ac.uk/BEMM459_GroupX?driver=ODBC+Driver+17+for+SQL+Server"

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class SQLUser(Base):
    __tablename__ = "users"
    user_id = Column(Integer, primary_key=True, index=True)  # Rename 'id' to 'user_id'
    name = Column(String, index=True)
    email = Column(String, unique=True, index=True)
    phone = Column(String, unique=True, index=True)
    created_at = Column(DateTime, default=func.now())  # Add 'created_at'

# Create tables in the database
Base.metadata.create_all(bind=engine)

# --------------------------- MongoDB Setup ---------------------------

MONGO_URI = "mongodb://localhost:27017"
mongo_client = MongoClient(MONGO_URI)
mongo_db = mongo_client["mydatabase"]
mongo_collection = mongo_db["users"]

# --------------------------- Pydantic Models ---------------------------

class UserCreateRequest(BaseModel):
    name: str
    email: str
    phone: str


class UserResponse(BaseModel):
    id: str
    name: str
    email: str
    phone: str

    class Config:
        orm_mode = True  # Enables compatibility with ORM models


# --------------------------- FastAPI App Setup ---------------------------

app = FastAPI()


# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# --------------------------- SQL CRUD Operations ---------------------------

@app.post("/users/sql/", response_model=UserResponse)
def create_user_sql(request: UserCreateRequest, db: Session = Depends(get_db)):
    """Create a new user in SQL database"""
    sql_user = SQLUser(name=request.name, email=request.email, phone=request.phone)

    # Check for duplicates
    if db.query(SQLUser).filter(SQLUser.email == request.email).first():
        raise HTTPException(status_code=400, detail="Email already exists.")

    db.add(sql_user)
    db.commit()
    db.refresh(sql_user)
    return sql_user


@app.get("/users/sql/{user_id}", response_model=UserResponse)
def get_user_sql(user_id: int, db: Session = Depends(get_db)):
    """Fetch a user from SQL database"""
    user = db.query(SQLUser).filter(SQLUser.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@app.delete("/users/sql/{user_id}", response_model=dict)
def delete_user_sql(user_id: int, db: Session = Depends(get_db)):
    """Delete a user from SQL database"""
    user = db.query(SQLUser).filter(SQLUser.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    db.delete(user)
    db.commit()
    return {"message": "User deleted successfully"}


@app.put("/users/sql/{user_id}", response_model=UserResponse)
def update_user_sql(user_id: int, request: UserCreateRequest, db: Session = Depends(get_db)):
    """Update user details in SQL database"""
    user = db.query(SQLUser).filter(SQLUser.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.name = request.name
    user.email = request.email
    user.phone = request.phone
    db.commit()
    db.refresh(user)
    return user


# --------------------------- MongoDB CRUD Operations ---------------------------

@app.post("/users/mongo/", response_model=UserResponse)
def create_user_mongo(request: UserCreateRequest):
    """Create a new user in MongoDB"""
    if mongo_collection.find_one({"email": request.email}):
        raise HTTPException(status_code=400, detail="Email already exists.")

    user_data = {
        "_id": str(uuid.uuid4()),  # Use UUID for MongoDB IDs
        "name": request.name,
        "email": request.email,
        "phone": request.phone
    }

    mongo_collection.insert_one(user_data)
    return user_data


@app.get("/users/mongo/{user_id}", response_model=UserResponse)
def get_user_mongo(user_id: str):
    """Fetch a user from MongoDB"""
    user = mongo_collection.find_one({"_id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return UserResponse(id=user["_id"], name=user["name"], email=user["email"], phone=user["phone"])


@app.delete("/users/mongo/{user_id}", response_model=dict)
def delete_user_mongo(user_id: str):
    """Delete a user from MongoDB"""
    result = mongo_collection.delete_one({"_id": user_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    return {"message": "User deleted successfully"}


@app.put("/users/mongo/{user_id}", response_model=UserResponse)
def update_user_mongo(user_id: str, request: UserCreateRequest):
    """Update user details in MongoDB"""
    user = mongo_collection.find_one({"_id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    updated_user = {
        "name": request.name,
        "email": request.email,
        "phone": request.phone
    }

    mongo_collection.update_one({"_id": user_id}, {"$set": updated_user})
    return {**updated_user, "id": user_id}

# --------------------------- Run FastAPI ---------------------------
# Run this file with: uvicorn filename:app --reload

if __name__ == "__main__":
    # ------------------------ Execute CRUD Operations ------------------------

    db = SessionLocal()  # Get SQL session

    # 📌 1. Insert a user into SQL
    print("Creating user in SQL...")
    new_user = SQLUser(name="John Doe", email="john@example.com", phone="1234567890")

    # Check if the user exists first
    if not db.query(SQLUser).filter(SQLUser.email == new_user.email).first():
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        print(f"User created in SQL: {new_user.user_id}, {new_user.name}")

    # 📌 2. Read the user from SQL
    print("Fetching user from SQL...")
    fetched_user = db.query(SQLUser).filter(SQLUser.email == "john@example.com").first()
    if fetched_user:
        print(f"User found in SQL: {fetched_user.user_id}, {fetched_user.name}, {fetched_user.email}")

    # 📌 3. Update the user in SQL
    print("Updating user in SQL...")
    if fetched_user:
        fetched_user.name = "John Updated"
        db.commit()
        db.refresh(fetched_user)
        print(f"Updated User in SQL: {fetched_user.user_id}, {fetched_user.name}")

    # 📌 4. Delete the user from SQL
    print("Deleting user from SQL...")
    if fetched_user:
        db.delete(fetched_user)
        db.commit()
        print(f"User deleted from SQL: {fetched_user.user_id}")

    db.close()  # Close SQL session

    # ------------------------ MongoDB CRUD ------------------------

    print("Creating user in MongoDB...")
    mongo_user = {
        "_id": str(uuid.uuid4()),
        "name": "Alice",
        "email": "alice@example.com",
        "phone": "9998887770"
    }

    if not mongo_collection.find_one({"email": mongo_user["email"]}):
        mongo_collection.insert_one(mongo_user)
        print(f"User created in MongoDB: {mongo_user['_id']}")

    print("Fetching user from MongoDB...")
    fetched_mongo_user = mongo_collection.find_one({"email": "alice@example.com"})
    if fetched_mongo_user:
        print(f"User found in MongoDB: {fetched_mongo_user['_id']}, {fetched_mongo_user['name']}")

    print("Updating user in MongoDB...")
    mongo_collection.update_one(
        {"email": "alice@example.com"},
        {"$set": {"name": "Alice Updated"}}
    )
    updated_mongo_user = mongo_collection.find_one({"email": "alice@example.com"})
    if updated_mongo_user:
        print(f"Updated User in MongoDB: {updated_mongo_user['_id']}, {updated_mongo_user['name']}")

    print("Deleting user from MongoDB...")
    mongo_collection.delete_one({"email": "alice@example.com"})
    print("User deleted from MongoDB.")

