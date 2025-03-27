import pytest
from fastapi.testclient import TestClient
from main import app  # Import your FastAPI app
from config.db_config import SessionLocal

from sqlalchemy.orm import Session
import uuid
from decimal import Decimal
from models.upi_transation_model import Transaction
from models.upi_transation_model import User
from models.upi_transation_model import Account
from models.upi_transation_model import UPIMapping

# Create a test client
client = TestClient(app)

# Fixture to create a new test database session
@pytest.fixture
def db_session():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()

@pytest.fixture(autouse=True)
def clean_db(db_session):
    db_session.query(Transaction).delete()
    db_session.query(UPIMapping).delete()
    db_session.query(Account).delete()
    db_session.query(User).delete()   # <-- add this line
    db_session.commit()

# ✅ Corrected Test Case 2: Check insufficient balance
def test_create_transaction_insufficient_balance(db_session):
    # Setup sender with low balance
    sender_user = User(user_id=uuid.uuid4(), name="LowBalanceSender", email="lowbalance@example.com", phone="9999999999")
    receiver_user = User(user_id=uuid.uuid4(), name="Receiver", email="receiver@example.com", phone="8888888888")
    db_session.add(sender_user)
    db_session.add(receiver_user)
    db_session.commit()

    sender_upi = UPIMapping(upi_id="low_balance_sender@upi", user_id=sender_user.user_id)
    receiver_upi = UPIMapping(upi_id="receiver@upi", user_id=receiver_user.user_id)
    db_session.add(sender_upi)
    db_session.add(receiver_upi)
    db_session.commit()

    sender_account = Account(
        user_id=sender_user.user_id,
        bank_name="Low Bank",
        account_number="ACCLOWBAL",
        ifsc_code="TESTLOW001",
        balance=Decimal('50.00')  # Low balance!
    )
    receiver_account = Account(
        user_id=receiver_user.user_id,
        bank_name="Receiver Bank",
        account_number="ACCREC",
        ifsc_code="RECV0001",
        balance=Decimal('100.00')
    )
    db_session.add(sender_account)
    db_session.add(receiver_account)
    db_session.commit()

    request_data = {
        "sender_upi": "low_balance_sender@upi",
        "receiver_upi": "receiver@upi",
        "amount": 10000.00  # Amount > sender balance
    }

    response = client.post("/transactions/", json=request_data)
    print(response.json())

    assert response.status_code == 400
    assert "Insufficient funds" in response.json()["detail"]

# ✅ Test Case 3: Fetch transaction by ID
def test_get_transaction(db_session):
    txn_id = str(uuid.uuid4())  # Replace with actual transaction ID

    response = client.get(f"/transactions/{txn_id}")

    assert response.status_code in [200, 404]  # It may or may not exist in test DB

def test_create_transaction(db_session):
    # Create sender and receiver users (linked to accounts)
    sender_user = User(user_id=uuid.uuid4(), name="Sender", email="sender@example.com", phone="1234567890") # Assuming 'User' is a table that stores user details
    receiver_user = User(user_id=uuid.uuid4(), name="Receiver", email="receiver@example.com", phone="0987654321")

    db_session.add(sender_user)
    db_session.add(receiver_user)
    db_session.commit()

    # Create UPIMapping for sender and receiver
    sender_upi = UPIMapping(upi_id="test_sender@upi", user_id=sender_user.user_id)
    receiver_upi = UPIMapping(upi_id="test_receiver@upi", user_id=receiver_user.user_id)
    db_session.add(sender_upi)
    db_session.add(receiver_upi)
    db_session.commit()

    # Create accounts with required fields
    sender_account = Account(
        user_id=sender_user.user_id,
        bank_name="Test Bank",
        account_number="ACC123SENDER",
        ifsc_code="TEST000001",
        balance=Decimal('500.00')
    )
    receiver_account = Account(
        user_id=receiver_user.user_id,
        bank_name="Test Bank",
        account_number="ACC123RECEIVER",
        ifsc_code="TEST000002",
        balance=Decimal('200.00')
    )
    db_session.add(sender_account)
    db_session.add(receiver_account)
    db_session.commit()

    # Prepare request data
    request_data = {
        "sender_upi": "test_sender@upi",
        "receiver_upi": "test_receiver@upi",
        "amount": 100.50
    }

    # Perform POST request to the /transactions/ endpoint
    response = client.post("/transactions/", json=request_data)

    print(f"Response status: {response.status_code}")
    print(f"Response body: {response.json()}")

    # Assert the response
    assert response.status_code == 200
    assert response.json()["status"] == "success"
    assert "txn_id" in response.json() # Ensure txn_id is returned

    # Verify balance changes
    sender_after = db_session.query(Account).filter_by(user_id=sender_user.user_id).first()
    receiver_after = db_session.query(Account).filter_by(user_id=receiver_user.user_id).first()

    assert sender_after.balance == Decimal('399.50') # Should be reduced by 100.50
    assert receiver_after.balance == Decimal('300.50') # Should be increased by 100.50
