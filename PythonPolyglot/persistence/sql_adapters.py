from sqlalchemy.orm import Session
from models import upi_transation_model
from interface.upi_repository import UserRepository

class PostgresUserRepository(UserRepository):
    def __init__(self, db_session: Session):
        self.db = db_session

    def create_user(self, user):
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def get_user_by_email(self, email):
        return self.db.query(upi_transation_model).filter(upi_transation_model.email == email).first()

    def delete_user(self, user_id):
        user = self.db.query(upi_transation_model).filter(upi_transation_model.user_id == user_id).first()
        if user:
            self.db.delete(user)
            self.db.commit()
