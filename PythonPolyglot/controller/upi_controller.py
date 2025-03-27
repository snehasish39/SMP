from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from models.upi_transation_model import User, Transaction  # Import relevant models
from persistence.sql_repo import SQLUserRepository, SQLTransactionRepository, SQLUPIRepository
from config.db_config import SessionLocal  # Database session

# Create the router instance for handling UPI operations
router = APIRouter(prefix="/upi")  # Prefix for UPI-related routes

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_repositories(db: Session = Depends(get_db)):
    return {
        "user_repo": SQLUserRepository(db),
        "txn_repo": SQLTransactionRepository(db),
        "upi_repo": SQLUPIRepository(db)
    }

@router.post("/transactions/")
def create_upi_transaction(sender_upi: str, receiver_upi: str, amount: float, repositories: dict = Depends(get_repositories)):
    txn_repo = repositories["txn_repo"]
    user_repo = repositories["user_repo"]
    upi_repo = repositories["upi_repo"]

    # Fetch users and UPI mappings
    sender = user_repo.get_user_by_email(sender_upi)
    receiver = user_repo.get_user_by_email(receiver_upi)

    if not sender or not receiver:
        raise HTTPException(status_code=404, detail="Sender or Receiver not found.")

    sender_upi_data = upi_repo.get_by_upi_id(sender_upi)
    receiver_upi_data = upi_repo.get_by_upi_id(receiver_upi)

    if not sender_upi_data or not receiver_upi_data:
        raise HTTPException(status_code=404, detail="UPI mapping not found.")

    # Check if sender has enough funds
    sender_account = user_repo.get_account_by_user(sender)  # Assuming you have a method to get account details by user
    if sender_account.balance < amount:
        raise HTTPException(status_code=400, detail="Insufficient funds")

    # Create the transaction object
    transaction = Transaction(
        sender_upi=sender_upi_data,
        receiver_upi=receiver_upi_data,
        amount=amount
    )

    # Save the transaction using the repository
    txn_repo.create_transaction(transaction)

    return {"status": "success", "txn_id": str(transaction.transaction_id)}


@router.get("/get_user/{email}")
def get_user_by_email(email: str, repositories: dict = Depends(get_repositories)):
    user_repo = repositories["user_repo"]
    user = user_repo.get_user_by_email(email)

    if user is None:
        raise HTTPException(status_code=404, detail="User not found.")

    return user
