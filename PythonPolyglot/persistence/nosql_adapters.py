from interface.upi_repository import UserRepository

class MongoUserRepository(UserRepository):
    def __init__(self, mongo_db):
        self.collection = mongo_db["users"]

    def create_user(self, user):
        self.collection.insert_one(user.dict())
        return user

    def get_user_by_email(self, email):
        return self.collection.find_one({"email": email})

    def delete_user(self, user_id):
        self.collection.delete_one({"user_id": user_id})
