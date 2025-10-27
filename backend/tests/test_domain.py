import pytest
from kitchen.domain import (
    validate_order,
    prep_time,
    make_food_event_ok,
    make_food_event_err,
    Order,
    ValidationError,
)

def test_validate_order_ok():
    data = {"orderId": "abc", "table": 2, "food": "Soup", "ts": 12345}
    o = validate_order(data)
    assert isinstance(o, Order)
    assert o.table == 2
    assert o.food == "Soup"

def test_validate_order_bad():
    with pytest.raises(ValidationError):
        validate_order({"orderId": "", "table": 0, "food": "", "ts": 0})

def test_prep_time_in_range():
    lo, hi = 10, 20
    for _ in range(20):
        ms = prep_time(lo, hi)
        assert lo <= ms <= hi

def test_make_food_event_ok():
    o = validate_order({"orderId": "x1", "table": 1, "food": "Pizza", "ts": 999})
    evt = make_food_event_ok(o, 1530)
    assert evt.status == "ready"
    assert evt.prepMs == 1530
    assert evt.food == "Pizza"
    assert evt.table == 1

def test_make_food_event_err_best_effort():
    bad = {"orderId": "maybe", "table": "5", "food": ""}
    evt = make_food_event_err(bad, "invalid")
    assert evt.status == "error"
    assert evt.table == 5
    assert evt.orderId == "maybe"
    assert evt.error == "invalid"
