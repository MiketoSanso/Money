from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional
from .value_objects import UserRole, OrderStatus, ServiceType, Email, Phone, Money

@dataclass
class User:
    id: Optional[int]
    login: str
    password_hash: str
    role: UserRole
    full_name: str
    phone: str
    email: str
    created_at: datetime = field(default_factory=datetime.now)

@dataclass
class Client:
    id: Optional[int]
    full_name: str
    phone: str
    email: str
    birthday: Optional[str]
    discount_percent: int = 0
    total_spent: float = 0.0
    created_at: datetime = field(default_factory=datetime.now)

    def apply_discount(self, amount: Money) -> Money:
        if self.discount_percent > 0:
            discounted = amount.amount * (100 - self.discount_percent) / 100
            return Money(discounted, amount.currency)
        return amount

@dataclass
class Service:
    id: Optional[int]
    name: str
    service_type: ServiceType
    price: float
    unit: str
    is_active: bool = True

@dataclass
class OrderItem:
    service: Service
    quantity: float
    price_at_time: float

    def subtotal(self) -> float:
        return self.quantity * self.price_at_time

@dataclass
class Order:
    id: Optional[int]
    client_id: int
    photographer_id: Optional[int]
    status: OrderStatus
    items: List[OrderItem]
    total_cost: float
    created_at: datetime
    deadline: Optional[datetime]
    notes: str = ""

    def calculate_total(self) -> float:
        return sum(item.subtotal() for item in self.items)

    def can_cancel(self) -> bool:
        return self.status in [OrderStatus.NEW, OrderStatus.CONFIRMED]

    def can_proceed(self) -> bool:
        return self.status in [OrderStatus.NEW, OrderStatus.CONFIRMED, OrderStatus.IN_PROGRESS]

@dataclass
class ScheduleSlot:
    id: Optional[int]
    photographer_id: int
    date: str
    time_slot: str
    is_booked: bool
    order_id: Optional[int]

@dataclass
class Payment:
    id: Optional[int]
    order_id: int
    amount: float
    payment_date: datetime
    method: str
