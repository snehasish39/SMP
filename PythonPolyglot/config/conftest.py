import pytest
from sqlalchemy.orm import Session
from models.upi_transation_model import Transaction, UPIMapping, Account  # Adjust imports

@pytest.fixture(autouse=True)
def clean_db(db_session: Session):
    # Clean the tables before each test to avoid conflicts with constraints like UNIQUE
    db_session.query(Transaction).delete()
    db_session.query(UPIMapping).delete()
    db_session.query(Account).delete()
    db_session.commit()
