"""Data backend. FixtureBackend is synthetic, in-memory data for development and tests.

A live Amazon SP-API / Ads API backend is NOT implemented. Anything that talks to a real
seller account must implement the same interface (see Backend) and be added deliberately.
"""
import random
from datetime import date, timedelta
from typing import Protocol

TODAY = date(2026, 10, 24)


class Backend(Protocol):
    def orders(self) -> list[dict]: ...
    def returns(self) -> list[dict]: ...
    def products(self) -> dict[str, dict]: ...
    def campaigns(self) -> list[dict]: ...
    def inventory(self) -> list[dict]: ...
    def settlements(self) -> list[dict]: ...
    def account_health(self) -> dict: ...
    def apply(self, kind: str, params: dict) -> dict: ...


class FixtureBackend:
    """Deterministic synthetic data (seeded). Not real sales data."""

    def __init__(self, seed: int = 7):
        r = random.Random(seed)
        self._products = {
            s: {"sku": s, "asin": a, "title": t, "price": p, "cost": c, "fba_fee": f}
            for s, a, t, p, c, f in [
                ("SKU-CANDLE-01", "B0FIX00001", "Soy Candle 8oz", 24.99, 7.50, 4.10),
                ("SKU-CANDLE-02", "B0FIX00002", "Soy Candle 16oz", 39.99, 12.00, 5.60),
                ("SKU-MUG-01", "B0FIX00003", "Ceramic Mug", 18.99, 5.20, 3.85),
                ("SKU-TOTE-01", "B0FIX00004", "Canvas Tote", 21.99, 6.40, 3.95),
                ("SKU-DIFF-01", "B0FIX00005", "Oil Diffuser", 34.99, 11.30, 5.20),
                ("SKU-SOAP-01", "B0FIX00006", "Hand Soap 3-pack", 14.99, 4.10, 3.40),
            ]
        }
        skus = list(self._products)
        self._orders = []
        for i in range(1, 121):
            sku = r.choice(skus)
            d = TODAY - timedelta(days=r.randint(0, 59))
            age = (TODAY - d).days
            status = "Shipped" if age > 3 else r.choice(["Unshipped", "Pending", "Shipped"])
            if r.random() < 0.03:
                status = "Canceled"
            qty = r.choice([1, 1, 1, 2, 3])
            self._orders.append({
                "order_id": f"111-{i:07d}-0000001", "date": d.isoformat(), "sku": sku,
                "qty": qty, "status": status, "ship_by": (d + timedelta(days=2)).isoformat(),
                "total": round(self._products[sku]["price"] * qty, 2),
                "buyer_note": "" if r.random() > 0.05 else "Please gift wrap.",
            })
        shipped = [o for o in self._orders if o["status"] == "Shipped"]
        self._returns = [
            {"order_id": o["order_id"], "sku": o["sku"], "reason": r.choice(
                ["DEFECTIVE", "NOT_AS_DESCRIBED", "CUSTOMER_CHANGED_MIND"]),
             "refund_amount": o["total"], "status": "Received"}
            for o in r.sample(shipped, 6)
        ]
        self._campaigns = [
            {"id": "C1", "name": "Candles - Auto", "daily_budget": 30.0, "spend_30d": 610.0, "sales_30d": 2100.0},
            {"id": "C2", "name": "Mugs - Exact", "daily_budget": 15.0, "spend_30d": 420.0, "sales_30d": 540.0},
            {"id": "C3", "name": "Brand Defense", "daily_budget": 10.0, "spend_30d": 150.0, "sales_30d": 900.0},
        ]
        sold = {s: sum(o["qty"] for o in self._orders if o["sku"] == s and o["status"] != "Canceled"
                       and (TODAY - date.fromisoformat(o["date"])).days < 30) for s in skus}
        self._inventory = [
            {"sku": s, "fulfillable": r.randint(5, 220), "inbound": r.choice([0, 0, 100]),
             "aged_90plus": r.choice([0, 0, 0, 25]), "units_sold_30d": sold[s],
             "unit_cube_ft3": 0.12} for s in skus
        ]
        expected = round(sum(o["total"] * 0.85 - 4.0 * o["qty"] for o in shipped
                             if (TODAY - date.fromisoformat(o["date"])).days >= 14), 2)
        self._settlements = [
            {"id": "S-2026-09", "expected_payout": expected, "actual_payout": expected - 61.37,
             "period": "2026-09-01/2026-09-30"},
            {"id": "S-2026-08", "expected_payout": 3980.12, "actual_payout": 3980.12,
             "period": "2026-08-01/2026-08-31"},
        ]
        self._health = {
            "order_defect_rate": 0.004, "late_shipment_rate": 0.012, "cancellation_rate": 0.008,
            "valid_tracking_rate": 0.985,
            "notices": [{"id": "N1", "type": "POLICY_WARNING",
                         "text": "Listing SKU-DIFF-01 may need a safety data sheet."}],
        }

    def orders(self): return self._orders
    def returns(self): return self._returns
    def products(self): return self._products
    def campaigns(self): return self._campaigns
    def inventory(self): return self._inventory
    def settlements(self): return self._settlements
    def account_health(self): return self._health

    def apply(self, kind: str, params: dict) -> dict:
        """Execute an approved action against the in-memory data."""
        if kind == "price_change":
            self._products[params["sku"]]["price"] = params["new_price"]
        elif kind == "refund":
            o = next(o for o in self._orders if o["order_id"] == params["order_id"])
            self._returns.append({"order_id": o["order_id"], "sku": o["sku"], "reason": params["reason"],
                                  "refund_amount": params["amount"], "status": "Refunded"})
        elif kind == "ad_budget":
            next(c for c in self._campaigns if c["id"] == params["campaign_id"])["daily_budget"] = params["new_budget"]
        elif kind == "restock":
            next(i for i in self._inventory if i["sku"] == params["sku"])["inbound"] += params["qty"]
        else:
            raise ValueError(f"unknown action kind {kind}")
        return {"applied": kind, **params}
