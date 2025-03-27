from sqlalchemy.orm import Session
from models.upi_transation_model import User, Account, UPIMapping, Transaction

class SQLUserRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_email(self, email: str):
        return self.db.query(User).filter(User.email == email).first()

class SQLAccountRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, account_id):
        return self.db.query(Account).filter(Account.account_id == account_id).first()

    def update_balance(self, account):
        try:
            self.db.merge(account)  # Merge to ensure the account is updated correctly
            self.db.commit()
        except Exception as e:
            self.db.rollback()  # Rollback on error
            raise e

class SQLUPIRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_upi_id(self, upi_id: str):
        result = self.db.query(UPIMapping).filter(UPIMapping.upi_id == upi_id).first()
        if result:
            print(f"Found UPI Mapping for {upi_id}: account_id = {result.account_id}")
        else:
            print(f"No UPI Mapping found for {upi_id}")
        return result


class SQLTransactionRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_transaction(self, transaction: Transaction):
        try:
            self.db.add(transaction)
            self.db.commit()
            self.db.refresh(transaction)  # Ensure that the transaction object is refreshed with the ID
            return transaction
        except Exception as e:
            self.db.rollback()  # Rollback in case of an error
            raise e

#-----------------------------------------------------------
class SQLTransactionRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_transaction(self, transaction: Transaction):
        self.db.add(transaction)
        self.db.flush()  # Optional, but recommended before commit
        return transaction

class SQLAccountRepository:
    def __init__(self, db: Session):
        self.db = db

    def update_balance(self, account):
        self.db.merge(account)  # Merge is like an upsert; it will update existing rows

class SQLUPIRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_upi_id(self, upi_id: str):
        return self.db.query(UPIMapping).filter(UPIMapping.upi_id == upi_id).first()
