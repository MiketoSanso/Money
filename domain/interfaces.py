from abc import ABC, abstractmethod
from typing import List, Optional
from datetime import datetime
from .entities import User, Client, Order, Service, ScheduleSlot, Payment
from .value_objects import UserRole, OrderStatus

class UserRepository(ABC):
    @abstractmethod
    def get_by_id(self, user_id: int) -> Optional[User]: pass
    @abstractmethod
    def get_by_login(self, login: str) -> Optional[User]: pass
    @abstractmethod
    def get_by_role(self, role: UserRole) -> List[User]: pass
    @abstractmethod
    def create(self, user: User) -> User: pass
    @abstractmethod
    def update(self, user: User) -> User: pass
    @abstractmethod
    def delete(self, user_id: int) -> bool: pass
    @abstractmethod
    def get_all(self) -> List[User]: pass

class ClientRepository(ABC):
    @abstractmethod
    def get_by_id(self, client_id: int) -> Optional[Client]: pass
    @abstractmethod
    def get_by_phone(self, phone: str) -> Optional[Client]: pass
    @abstractmethod
    def search(self, query: str) -> List[Client]: pass
    @abstractmethod
    def create(self, client: Client) -> Client: pass
    @abstractmethod
    def update(self, client: Client) -> Client: pass
    @abstractmethod
    def delete(self, client_id: int) -> bool: pass
    @abstractmethod
    def get_all(self) -> List[Client]: pass
    @abstractmethod
    def get_top_clients(self, limit: int = 10) -> List[Client]: pass

class OrderRepository(ABC):
    @abstractmethod
    def get_by_id(self, order_id: int) -> Optional[Order]: pass
    @abstractmethod
    def get_by_client(self, client_id: int) -> List[Order]: pass
    @abstractmethod
    def get_by_status(self, status: OrderStatus) -> List[Order]: pass
    @abstractmethod
    def get_by_period(self, start: datetime, end: datetime) -> List[Order]: pass
    @abstractmethod
    def create(self, order: Order) -> Order: pass
    @abstractmethod
    def update(self, order: Order) -> Order: pass
    @abstractmethod
    def update_status(self, order_id: int, status: OrderStatus) -> Order: pass
    @abstractmethod
    def get_all(self) -> List[Order]: pass

class ServiceRepository(ABC):
    @abstractmethod
    def get_by_id(self, service_id: int) -> Optional[Service]: pass
    @abstractmethod
    def get_all_active(self) -> List[Service]: pass
    @abstractmethod
    def create(self, service: Service) -> Service: pass

class ScheduleRepository(ABC):
    @abstractmethod
    def get_free_slots(self, photographer_id: int, date: str) -> List[ScheduleSlot]: pass
    @abstractmethod
    def book_slot(self, slot_id: int, order_id: int) -> ScheduleSlot: pass
    @abstractmethod
    def get_slots_by_photographer(self, photographer_id: int, date: str) -> List[ScheduleSlot]: pass
    @abstractmethod
    def create_slots(self, slots: List[ScheduleSlot]) -> List[ScheduleSlot]: pass

class PaymentRepository(ABC):
    @abstractmethod
    def create(self, payment: Payment) -> Payment: pass
    @abstractmethod
    def get_by_order(self, order_id: int) -> List[Payment]: pass
    @abstractmethod
    def get_total_by_period(self, start: datetime, end: datetime) -> float: pass

class UnitOfWork(ABC):
    @abstractmethod
    def __enter__(self): pass
    @abstractmethod
    def __exit__(self, exc_type, exc_val, exc_tb): pass
    @abstractmethod
    def commit(self): pass
    @abstractmethod
    def rollback(self): pass
