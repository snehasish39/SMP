from models.upi_transation_model import Transaction
import uuid
import datetime
from sqlalchemy.exc import SQLAlchemyError

class TransactionService:
    def __init__(self, txn_repo, upi_repo, account_repo):
        self.txn_repo = txn_repo
        self.upi_repo = upi_repo
        self.account_repo = account_repo

    def process_transaction(self, sender_upi, receiver_upi, amount):
        if amount <= 0:
            raise ValueError("Transaction amount must be greater than zero")

        # Fetch sender and receiver UPI data
        sender = self.upi_repo.get_by_upi_id(sender_upi)
        receiver = self.upi_repo.get_by_upi_id(receiver_upi)

        # Ensure sender and receiver have valid account_id values
        if not sender or sender.account_id is None:
            raise ValueError("Sender account ID is missing or invalid")
        if not receiver or receiver.account_id is None:
            raise ValueError("Receiver account ID is missing or invalid")

        # Fetch sender and receiver account details
        sender_account = self.account_repo.get_by_id(sender.account_id)
        receiver_account = self.account_repo.get_by_id(receiver.account_id)

        # Check if the account details exist
        if not sender_account:
            raise ValueError("Sender account not found")
        if not receiver_account:
            raise ValueError("Receiver account not found")

        # Check if sender has sufficient funds
        if sender_account.balance < amount:
            raise ValueError("Insufficient funds")

        # Get the DB session from any repo (they share the same DB session)
        db = self.txn_repo.db  # or upi_repo.db or account_repo.db (they all share the same session)

        try:
            # 1️⃣ Update sender and receiver balances first
            sender_account.balance -= amount
            receiver_account.balance += amount
            self.account_repo.update_balance(sender_account)
            self.account_repo.update_balance(receiver_account)

            # 2️⃣ Now create the transaction record
            transaction = Transaction(
                txn_id=str(uuid.uuid4()),  # Ensure it's a string representation of UUID
                sender_upi_id=sender_upi,
                receiver_upi_id=receiver_upi,
                amount=amount,
                txn_status="SUCCESS",
                created_at=datetime.datetime.utcnow()  # Set the timestamp for the transaction
            )

            # 3️⃣ Add the transaction to the database
            self.txn_repo.create_transaction(transaction)

            # 4️⃣ Commit the transaction and all changes
            db.commit()

        except SQLAlchemyError as e:
            # In case of an error, rollback all changes
            db.rollback()
            raise ValueError(f"Transaction failed due to a database error: {str(e)}")

        # Return the created transaction
        return transaction
