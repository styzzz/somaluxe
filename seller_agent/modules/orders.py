"""ORDER OPERATIONS: open orders, shipping deadlines, returns, refunds."""
from datetime import date

from ..backend import TODAY
from ..tools import INT, NUM, STR, WRITE, Tool, schema


def tools(backend, queue):
    def list_orders(status: str = "Unshipped", limit: int = 20):
        rows = [o for o in backend.orders() if o["status"] == status]
        return rows[:limit]

    def late_shipment_risk():
        return [{"order_id": o["order_id"], "sku": o["sku"], "ship_by": o["ship_by"],
                 "overdue": date.fromisoformat(o["ship_by"]) < TODAY}
                for o in backend.orders()
                if o["status"] in ("Unshipped", "Pending") and (date.fromisoformat(o["ship_by"]) - TODAY).days <= 1]

    def returns_report():
        rets = backend.returns()
        by_reason = {}
        for r in rets:
            by_reason[r["reason"]] = by_reason.get(r["reason"], 0) + 1
        shipped = [o for o in backend.orders() if o["status"] == "Shipped"]
        return {"returns": len(rets), "by_reason": by_reason,
                "return_rate_pct": round(100 * len(rets) / len(shipped), 1) if shipped else 0.0,
                "refunded_total": round(sum(r["refund_amount"] for r in rets), 2)}

    def propose_refund(order_id: str, amount: float, reason: str):
        o = next((o for o in backend.orders() if o["order_id"] == order_id), None)
        if o is None:
            return {"error": f"unknown order {order_id}"}
        if amount <= 0 or amount > o["total"]:
            return {"error": f"amount must be between 0 and order total {o['total']}"}
        return queue.propose("refund", {"order_id": order_id, "amount": amount, "reason": reason},
                             f"Refund ${amount} on {order_id} ({reason})")

    return [
        Tool("list_orders", "ORDER OPERATIONS", "List orders by status (Unshipped, Pending, Shipped, Canceled).",
             schema({"status": STR, "limit": INT}), list_orders),
        Tool("late_shipment_risk", "ORDER OPERATIONS", "Orders due to ship within a day or already overdue.",
             schema({}), late_shipment_risk),
        Tool("returns_report", "ORDER OPERATIONS", "Return count, reasons, rate and refunded dollars.",
             schema({}), returns_report),
        Tool("propose_refund", "ORDER OPERATIONS", "Propose a refund. Requires human approval.",
             schema({"order_id": STR, "amount": NUM, "reason": STR}, ["order_id", "amount", "reason"]),
             propose_refund, WRITE),
    ]
