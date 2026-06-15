from abc import ABC, abstractmethod
from typing import Optional
from app.domain.entities import User

class IUserRepository(ABC):
    """
    Contrato que qualquer banco de dados precisará cumprir para funcionar no sistema.
    """
    @abstractmethod
    def save(self, user: User) -> User:
        pass

    @abstractmethod
    def get_by_email(self, email: str) -> Optional[User]:
        pass

    @abstractmethod
    def update(self, user: User) -> User:
        pass

class IEmailService(ABC):
    """
    Contrato para o serviço de e-mails (SOLID - Princípio da Inversão de Dependência).
    """
    @abstractmethod
    def send_welcome_email(self, to_email: str) -> None:
        pass

    @abstractmethod
    def send_mfa_code(self, to_email: str, code: str) -> None:
        pass