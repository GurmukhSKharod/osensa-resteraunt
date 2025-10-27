"""
Domain-layer:
- Validate incoming orders
- Compute prep time
- Shape outgoing events (success/error)
"""

from dataclasses import dataclass
from typing import Literal, Optional
import random


@dataclass(frozen=True)
class Order:
    orderId: str
    table: int
    food: str
    ts: int  # epoch ms


@dataclass(frozen=True)
class FoodEvent:
    orderId: str
    table: int
    food: str
    status: Literal["ready", "error"]
    prepMs: Optional[int] = None
    error: Optional[str] = None


class ValidationError(ValueError):
    """Raised when an incoming order payload is invalid."""


def _require(cond: bool, msg: str) -> None:
    if not cond:
        raise ValidationError(msg)


def validate_order(data: dict) -> Order:
    """
    Validate arbitrary input into an Order. Raises ValidationError on failure.
    Expected keys: orderId(str, non-empty), table(int>0), food(str, non-empty), ts(int>0)
    """
    if not isinstance(data, dict):
        raise ValidationError("payload must be a JSON object")

    order_id = data.get("orderId", "")
    table = data.get("table", 0)
    food = data.get("food", "")
    ts = data.get("ts", 0)

    _require(isinstance(order_id, str) and order_id.strip(), "orderId must be non-empty string")

    if isinstance(table, str) and table.isdigit():
        table = int(table)
    _require(isinstance(table, int) and table > 0, "table must be positive integer")

    _require(isinstance(food, str) and food.strip(), "food must be non-empty string")

    if isinstance(ts, str) and ts.isdigit():
        ts = int(ts)
    _require(isinstance(ts, int) and ts > 0, "ts must be positive integer")

    return Order(orderId=order_id.strip(), table=table, food=food.strip(), ts=ts)


def prep_time(min_ms: int, max_ms: int) -> int:
    """Random prep time in milliseconds, inclusive bounds."""
    if min_ms > max_ms or min_ms < 0:
        raise ValueError("invalid prep time range")
    return random.randint(min_ms, max_ms)


def make_food_event_ok(order: Order, ms: int) -> FoodEvent:
    """Success event from a validated Order and a measured prep time."""
    return FoodEvent(
        orderId=order.orderId,
        table=order.table,
        food=order.food,
        status="ready",
        prepMs=ms,
    )


def make_food_event_err(order_like: dict, message: str) -> FoodEvent:
    """Error event using best-effort fields from an invalid payload."""
    table = 0
    if isinstance(order_like, dict):
        raw_table = order_like.get("table", 0)
        try:
            t = int(raw_table)
            if t > 0:
                table = t
        except Exception:
            pass
        order_id = str(order_like.get("orderId", "")) if "orderId" in order_like else ""
        food = str(order_like.get("food", "")) if "food" in order_like else ""
    else:
        order_id = ""
        food = ""

    return FoodEvent(
        orderId=order_id,
        table=table,
        food=food,
        status="error",
        error=message,
    )
