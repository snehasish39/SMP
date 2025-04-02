import uvicorn
from fastapi import FastAPI, HTTPException, Depends
from pymongo.errors import OperationFailure
from sqlalchemy import create_engine, Column, Integer, DateTime, String, func, Numeric, ForeignKey
from sqlalchemy.dialects.mssql import UNIQUEIDENTIFIER
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

class Account(Base):
    __tablename__ = "Accounts"
    account_id = Column(UNIQUEIDENTIFIER, primary_key=True, default=uuid.uuid4)
    user_id = Column(UNIQUEIDENTIFIER, ForeignKey("users.user_id"), nullable=False)
    bank_name = Column(String, nullable=False)
    account_number = Column(String, unique=True, nullable=False)
    sort_code = Column(String, nullable=False)
    balance = Column(Numeric(12,2), default=0.00)
    account_type = Column(String, nullable=False)  # Add this line

class UPI_Mapping(Base):
    __tablename__ = "UPI_Mappings"
    upi_id = Column(String, primary_key=True)
    user_id = Column(UNIQUEIDENTIFIER, ForeignKey("users.user_id"), nullable=False)
    account_id = Column(UNIQUEIDENTIFIER, ForeignKey("Accounts.account_id"), nullable=False)

class Transaction(Base):
    __tablename__ = "Transactions"
    txn_id = Column(UNIQUEIDENTIFIER, primary_key=True, default=uuid.uuid4)
    sender_upi_id = Column(String, ForeignKey("UPI_Mappings.upi_id"), nullable=False)
    receiver_upi_id = Column(String, ForeignKey("UPI_Mappings.upi_id"), nullable=False)
    amount = Column(Numeric(12,2), nullable=False)
    txn_status = Column(String, nullable=False)

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

class AccountCreateRequest(BaseModel):
    user_id: str
    bank_name: str
    account_number: str
    ifsc_code: str
    balance: float
    # account_type: str  # Remove this line


class UPI_MappingRequest(BaseModel):
    upi_id: str
    user_id: str
    account_id: str

class TransactionRequest(BaseModel):
    sender_upi_id: str
    receiver_upi_id: str
    amount: float
    txn_status: str

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

@app.post("/accounts/")
def create_account(account: AccountCreateRequest, db: Session = Depends(get_db)):
    db_account = Account(**account.dict())
    db.add(db_account)
    db.commit()
    return {"message": "Account created", "account_id": db_account.account_id}

@app.post("/upi_mappings/")
def create_upi_mapping(upi_mapping: UPI_MappingRequest, db: Session = Depends(get_db)):
    db_upi = UPI_Mapping(**upi_mapping.dict())
    db.add(db_upi)
    db.commit()
    return {"message": "UPI Mapping created", "upi_id": db_upi.upi_id}

@app.post("/transactions/")
def create_transaction(txn: TransactionRequest, db: Session = Depends(get_db)):
    db_txn = Transaction(**txn.dict())
    db.add(db_txn)
    db.commit()
    return {"message": "Transaction created", "txn_id": db_txn.txn_id}

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


    # Creating an Account
    print("Creating Account in SQL...")
    account = Account(user_id=sql_user.user_id,bank_name="HSBC",account_number="1234567890",sort_code="40-33-30", account_type="Savings", balance=10000)
    db.add(account)
    db.commit()
    db.refresh(account)
    print(f"Account created in SQL: {account.account_id}, {account.account_number}")

    # Fetching the Account
    print("Fetching Account from SQL...")
    fetched_account = db.query(Account).filter(Account.account_id == account.account_id).first()
    print(
        f"Account found in SQL: {fetched_account.account_id}, {fetched_account.account_number}, {fetched_account.account_type}, {fetched_account.balance}")

    # Updating the Account
    print("Updating Account in SQL...")
    fetched_account.balance = 15000  # Updating balance
    db.commit()
    db.refresh(fetched_account)
    print(
        f"Updated Account in SQL: {fetched_account.account_id}, {fetched_account.account_number}, New Balance: {fetched_account.balance}")

    # Creating UPI Mapping for the Account
    print("Creating UPI Mapping for Account...")
    upi_mapping = UPI_Mapping(account_id=account.account_id, upi_id="upixyz123", user_id=sql_user.user_id)
    db.add(upi_mapping)
    db.commit()
    db.refresh(upi_mapping)
    print(
        f"UPI Mapping created for Account: {upi_mapping.account_id}, UPI ID: {upi_mapping.upi_id}, USER Id: {sql_user.user_id}")

    # Fetching UPI Mapping for the Account
    print("Fetching UPI Mapping from SQL...")
    fetched_upi_mapping = db.query(UPI_Mapping).filter(UPI_Mapping.account_id == account.account_id).first()
    print(
        f"UPI Mapping found: {fetched_upi_mapping.account_id}, UPI ID: {fetched_upi_mapping.upi_id}, UPI Name: {fetched_upi_mapping.user_id}")

    # Updating UPI Mapping
    print("Updating UPI Mapping in SQL...")
    fetched_upi_mapping.upi_name = "John Updated UPI"
    db.commit()
    db.refresh(fetched_upi_mapping)
    print(f"Updated UPI Mapping: {fetched_upi_mapping.upi_id}, {fetched_upi_mapping.upi_name}")

    # Deleting UPI Mapping
    print("Deleting UPI Mapping from SQL...")
    db.delete(fetched_upi_mapping)
    db.commit()

    # Deleting the Account
    print("Deleting Account from SQL...")
    db.delete(fetched_account)
    db.commit()
    print(f"Account deleted from SQL: {fetched_account.account_id}")

    print("Deleting user from SQL...")
    db.delete(sql_user)

    print(f"UPI Mapping deleted: {fetched_upi_mapping.upi_id}")

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

