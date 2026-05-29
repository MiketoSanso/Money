from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional

@dataclass
class CreateClientDTO:
    full_name: str
    phone: str
    email: str
    birthday: Optional[str] = None

@dataclass
class CreateOrderDTO:
    client_id: int
    photographer_id: Optional[int]
    items: List[dict]
    deadline: Optional[str]
    notes: str = ""

@dataclass
class OrderResponseDTO:
    id: int
    client_name: str
    photographer_name: Optional[str]
    status: str
    total_cost: float
    created_at: str
    items_count: int

@dataclass
class ReportDTO:
    period_start: str
    period_end: str
    total_orders: int
    total_revenue: float
    avg_order_value: float
    top_clients: List[dict]
    photographer_stats: List[dict]
