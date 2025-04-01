import uvicorn
from fastapi import FastAPI, HTTPException, Depends
from pymongo.errors import OperationFailure
from sqlalchemy import create_engine, Column, Integer, DateTime, String, func
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from pymongo import MongoClient
from pydantic import BaseModel
import random
from datetime import datetime
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
transactions_collection = mongo_db["transactions"]  # Create or get transactions collection

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
        from_attributes = True  # Enables compatibility with ORM models


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


## --------------------------- MongoDB CRUD Operations ---------------------------

@app.post("/users/mongo/", response_model=UserResponse)
def create_user_mongo(request: UserCreateRequest):
    """Create a new user in MongoDB with associated transactions"""
    if mongo_collection.find_one({"email": request.email}):
        raise HTTPException(status_code=400, detail="Email already exists.")

    # User data
    user_data = {
        "_id": str(uuid.uuid4()),  # Use UUID for MongoDB IDs
        "name": request.name,
        "email": request.email,
        "phone": request.phone
    }

    # Transactions related to the user
    transaction_types = ["credit", "debit"]
    statuses = ["success", "pending", "failed"]

    # Possible transaction data for this user
    transactions = []
    for _ in range(5):
        transaction = {
            "_id": str(uuid.uuid4()),  # Unique ID for each transaction
            "user_id": user_data["_id"],  # Reference to the user
            "amount": round(random.uniform(10, 5000), 2),
            "transaction_type": random.choice(transaction_types),
            "status": random.choice(statuses),
            "timestamp": datetime.utcnow(),
        }
        transactions.append(transaction)

    # Log user and transaction creation process
    print("Inserting user data into MongoDB...")
    print(f"User data: {user_data}")

    try:
        # Using transaction to insert both user and related transactions in MongoDB
        with mongo_client.start_session() as session:
            session.start_transaction()
            try:
                # Inserting user data into MongoDB
                print("Inserting user into MongoDB...")
                mongo_collection.insert_one(user_data, session=session)
                print(f"User inserted: {user_data}")

                # Inserting transactions into MongoDB
                print("Inserting transactions into MongoDB...")
                result = transactions_collection.insert_many(transactions, session=session)
                print(f"{len(transactions)} transactions inserted.")

                # Commit the transaction
                session.commit_transaction()
                print("Transaction committed successfully.")

            except OperationFailure as e:
                # If something fails, abort the transaction
                session.abort_transaction()
                print(f"Transaction aborted due to error: {str(e)}")
                raise HTTPException(status_code=500, detail=f"Error creating user and transactions: {str(e)}")

        return {"message": "User and Transactions inserted successfully", "user": user_data, "transactions": transactions}

    except Exception as e:
        # Log any other errors
        print(f"Transaction failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


# --------------------------- MongoDB CRUD Operations for Verification ---------------------------

# @app.get("/users/mongo/{user_id}", response_model=UserResponse)
# def get_user_mongo(user_id: str):
#     """Fetch a user from MongoDB"""
#     user = mongo_collection.find_one({"_id": user_id})
#     if not user:
#         raise HTTPException(status_code=404, detail="User not found")
#
#     # Log the user retrieval
#     print(f"User found in MongoDB: {user}")
#     return UserResponse(id=user["_id"], name=user["name"], email=user["email"], phone=user["phone"])
#
#
# @app.get("/transactions/mongo/{user_id}", response_model=list)
# def get_transactions_mongo(user_id: str):
#     """Fetch transactions related to a user from MongoDB"""
#     transactions = transactions_collection.find({"user_id": user_id})
#     if not transactions:
#         raise HTTPException(status_code=404, detail="Transactions not found")
#
#     # Log the transaction retrieval
#     print(f"Transactions found for user {user_id}: {list(transactions)}")
#     return list(transactions)
#
#
# @app.get("/users/mongo/{user_id}", response_model=UserResponse)
# def get_user_mongo(user_id: str):
#     """Fetch a user from MongoDB"""
#     user = mongo_collection.find_one({"_id": user_id})
#     if not user:
#         raise HTTPException(status_code=404, detail="User not found")
#
#     return UserResponse(id=user["_id"], name=user["name"], email=user["email"], phone=user["phone"])
#
#
# @app.delete("/users/mongo/{user_id}", response_model=dict)
# def delete_user_mongo(user_id: str):
#     """Delete a user from MongoDB"""
#     result = mongo_collection.delete_one({"_id": user_id})
#     if result.deleted_count == 0:
#         raise HTTPException(status_code=404, detail="User not found")
#     return {"message": "User deleted successfully"}
#
#
# @app.put("/users/mongo/{user_id}", response_model=UserResponse)
# def update_user_mongo(user_id: str, request: UserCreateRequest):
#     """Update user details in MongoDB"""
#     user = mongo_collection.find_one({"_id": user_id})
#     if not user:
#         raise HTTPException(status_code=404, detail="User not found")
#
#     updated_user = {
#         "name": request.name,
#         "email": request.email,
#         "phone": request.phone
#     }
#
#     mongo_collection.update_one({"_id": user_id}, {"$set": updated_user})
#     return {**updated_user, "id": user_id}

@app.post("/transactions/mongo/", response_model=dict)
def create_transactions_mongo(request: UserCreateRequest):
    """Create transactions in MongoDB related to a user"""
    # User data
    user_data = {
        "_id": str(uuid.uuid4()),  # Use UUID for MongoDB IDs
        "name": request.name,
        "email": request.email,
        "phone": request.phone
    }

    # Transactions related to the user
    transaction_types = ["credit", "debit"]
    statuses = ["success", "pending", "failed"]

    # Possible transaction data for this user
    transactions = []
    for _ in range(5):
        transaction = {
            "_id": str(uuid.uuid4()),  # Unique ID for each transaction
            "user_id": user_data["_id"],  # Reference to the user
            "amount": round(random.uniform(10, 5000), 2),
            "transaction_type": random.choice(transaction_types),
            "status": random.choice(statuses),
            "timestamp": datetime.utcnow(),
        }
        transactions.append(transaction)

    try:
        # Using transaction to insert user and transactions in MongoDB
        with mongo_client.start_session() as session:
            session.start_transaction()
            try:
                # Insert user data into MongoDB
                mongo_db["users"].insert_one(user_data, session=session)

                # Insert transactions into MongoDB
                transactions_collection.insert_many(transactions, session=session)

                # Commit the transaction
                session.commit_transaction()
                return {"message": "Transactions inserted successfully", "user": user_data, "transactions": transactions}

            except OperationFailure as e:
                # If something fails, abort the transaction
                session.abort_transaction()
                raise HTTPException(status_code=500, detail=f"Error creating user and transactions: {str(e)}")

    except Exception as e:
        # Log any other errors
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@app.get("/transactions/mongo/{user_id}", response_model=list)
def get_transactions_mongo(user_id: str):
    """Fetch transactions related to a user from MongoDB"""
    transactions = list(transactions_collection.find({"user_id": user_id}))
    if not transactions:
        raise HTTPException(status_code=404, detail="Transactions not found")
    return transactions


# @app.delete("/transactions/mongo/{user_id}", response_model=dict)
# def delete_transactions_mongo(user_id: str):
#     """Delete transactions related to a user in MongoDB"""
#     result = transactions_collection.delete_many({"user_id": user_id})
#     if result.deleted_count == 0:
#         raise HTTPException(status_code=404, detail="Transactions not found")
#     return {"message": "Transactions deleted successfully"}


# --------------------------- Run FastAPI ---------------------------

if __name__ == "__main__":
    # This will start the FastAPI app and perform CRUD actions
    uvicorn.run("script:app", host="127.0.0.1", port=8000, reload=True)

    # For testing the CRUD operations
    # SQL CRUD
    print("Creating user in SQL...")
    sql_user = SQLUser(name="John Doe", email="john@example.com", phone="1234567890")
    db = SessionLocal()
    db.add(sql_user)
    db.commit()
    db.refresh(sql_user)
    print(f"User created in SQL: {sql_user.user_id}, {sql_user.name}")

    print("Fetching user from SQL...")
    sql_user = db.query(SQLUser).filter(SQLUser.user_id == sql_user.user_id).first()
    print(f"User found in SQL: {sql_user.user_id}, {sql_user.name}, {sql_user.email}")

    print("Updating user in SQL...")
    sql_user.name = "John Updated"
    db.commit()
    db.refresh(sql_user)
    print(f"Updated User in SQL: {sql_user.user_id}, {sql_user.name}")

    print("Deleting user from SQL...")
    db.delete(sql_user)
    db.commit()
    print(f"User deleted from SQL: {sql_user.user_id}")

    # MongoDB CRUD with Transactions
    print("Creating user and transactions in MongoDB...")
    mongo_user_id = str(uuid.uuid4())
    mongo_user_data = {
        "_id": mongo_user_id,
        "name": "Alice",
        "email": "alice@example.com",
        "phone": "9876543210"
    }

    # Transactions related to the user
    transaction_types = ["credit", "debit"]
    statuses = ["success", "pending", "failed"]

    transactions = []
    for _ in range(5):
        transaction = {
            "_id": str(uuid.uuid4()),
            "user_id": mongo_user_id,
            "amount": round(random.uniform(10, 5000), 2),
            "transaction_type": random.choice(transaction_types),
            "status": random.choice(statuses),
            "timestamp": datetime.utcnow(),
        }
        transactions.append(transaction)

    try:
        # Using MongoDB session for transaction
        with mongo_client.start_session() as session:
            session.start_transaction()
            try:
                # Inserting user data into MongoDB
                print("Inserting user data into MongoDB...")
                mongo_collection.insert_one(mongo_user_data, session=session)

                # Inserting transactions into MongoDB
                print("Inserting transactions into MongoDB...")
                transactions_collection.insert_many(transactions, session=session)

                # Commit the transaction
                session.commit_transaction()
                print("Transaction committed successfully.")
            except OperationFailure as e:
                # If something fails, abort the transaction
                session.abort_transaction()
                print(f"Transaction aborted due to error: {str(e)}")
                raise HTTPException(status_code=500, detail=f"Error creating user and transactions: {str(e)}")

        print(f"User and transactions inserted successfully into MongoDB: {mongo_user_id}")

    except Exception as e:
        # Log any other errors
        print(f"Transaction failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

    # Fetch and display MongoDB user and transaction
    print("Fetching user and transactions from MongoDB...")
    mongo_user = mongo_collection.find_one({"_id": mongo_user_id})
    print(f"User found in MongoDB: {mongo_user['_id']}, {mongo_user['name']}")

    mongo_transactions = transactions_collection.find({"user_id": mongo_user_id})
    print(f"Transactions for User {mongo_user_id}:")
    for transaction in mongo_transactions:
        print(f"Transaction ID: {transaction['_id']}, Amount: {transaction['amount']}, Status: {transaction['status']}")

    print("Updating user in MongoDB...")
    mongo_collection.update_one({"_id": mongo_user_id}, {"$set": {"name": "Alice Updated"}})
    print(f"Updated User in MongoDB: {mongo_user_id}, Alice Updated")

    # print("Deleting user and transactions from MongoDB...")
    # mongo_collection.delete_one({"_id": mongo_user_id})
    # transactions_collection.delete_many({"user_id": mongo_user_id})
    # print(f"User and transactions deleted from MongoDB.")