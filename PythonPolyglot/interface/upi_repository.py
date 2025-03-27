from abc import ABC, abstractmethod


class UserRepository(ABC):
    @abstractmethod
    def create_user(self, user):
        pass

    @abstractmethod
    def get_user_by_email(self, email):
        pass

    @abstractmethod
    def delete_user(self, user_id):
        pass
