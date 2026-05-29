from dataclasses import dataclass
from enum import Enum
import re

class UserRole(Enum):
    ADMIN = "admin"
    DIRECTOR = "director"
    ACCOUNTANT = "accountant"
    ADMINISTRATOR = "administrator"
    PHOTOGRAPHER = "photographer"
    CLIENT = "client"

class OrderStatus(Enum):
    NEW = "new"
    CONFIRMED = "confirmed"
    IN_PROGRESS = "in_progress"
    READY = "ready"
    COMPLETED = "completed"
    PAID = "paid"
    CANCELLED = "cancelled"

class ServiceType(Enum):
    PHOTO_SESSION = "photo_session"
    PRINT = "print"
    RETOUCH = "retouch"
    STUDIO_RENT = "studio_rent"

@dataclass(frozen=True)
class Email:
    value: str

    def __post_init__(self):
        if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', self.value):
            raise ValueError(f"Invalid email: {self.value}")

@dataclass(frozen=True)
class Phone:
    value: str

    def __post_init__(self):
        digits = re.sub(r'\D', '', self.value)
        if len(digits) < 10 or len(digits) > 12:
            raise ValueError(f"Invalid phone: {self.value}")

@dataclass(frozen=True)
class Money:
    amount: float
    currency: str = "RUB"

    def __post_init__(self):
        if self.amount < 0:
            raise ValueError("Amount cannot be negative")

    def __add__(self, other):
        if self.currency != other.currency:
            raise ValueError("Cannot add different currencies")
        return Money(self.amount + other.amount, self.currency)
