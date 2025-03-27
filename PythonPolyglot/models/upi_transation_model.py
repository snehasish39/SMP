from sqlalchemy import Column, String, Numeric, ForeignKey, DateTime
from sqlalchemy.dialects.mssql import UNIQUEIDENTIFIER
from sqlalchemy.orm import relationship, declarative_base
import uuid
import datetime
from decimal import Decimal

Base = declarative_base()

class User(Base):
    __tablename__ = "Users"
    user_id = Column(UNIQUEIDENTIFIER, primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    phone = Column(String(15), unique=True, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class Account(Base):
    __tablename__ = "Accounts"
    account_id = Column(UNIQUEIDENTIFIER, primary_key=True, default=uuid.uuid4)
    user_id = Column(UNIQUEIDENTIFIER, ForeignKey("Users.user_id"), nullable=False)
    bank_name = Column(String(255), nullable=False)
    account_number = Column(String(20), unique=True, nullable=False)
    ifsc_code = Column(String(11), nullable=False)
    balance = Column(Numeric(12,2), default=Decimal("0.00"))
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class UPIMapping(Base):
    __tablename__ = "UPI_Mappings"
    upi_id = Column(String(50), primary_key=True)
    user_id = Column(UNIQUEIDENTIFIER, ForeignKey("Users.user_id"), nullable=False)
    account_id = Column(UNIQUEIDENTIFIER, ForeignKey("Accounts.account_id"), nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


class Transaction(Base):
    __tablename__ = "Transactions"
    #txn_id = Column(UNIQUEIDENTIFIER, primary_key=True, default=lambda: str(uuid.uuid4())) # Update this line
    txn_id = Column(UNIQUEIDENTIFIER, primary_key=True, default=uuid.uuid4)  # Ensure this matches the SQL
    sender_upi_id = Column(String(50), ForeignKey("UPI_Mappings.upi_id"), nullable=False)
    receiver_upi_id = Column(String(50), ForeignKey("UPI_Mappings.upi_id"), nullable=False)
    amount = Column(Numeric(12, 2), nullable=False)
    txn_status = Column(String(20), nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)