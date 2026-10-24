"""SALES: revenue, profit, top products, pricing."""
from datetime import date, timedelta

from ..backend import TODAY
from ..tools import INT, NUM, READ, STR, WRITE, Tool, schema

REFERRAL = 0.15


def _recent(orders, days):
    cutoff = TODAY - timedelta(days=days)
    return [o for o in orders if o["status"] != "Canceled" and date.fromisoformat(o["date"]) > cutoff]


def tools(backend, queue):
    def sales_summary(days: int = 30):
        os_ = _recent(backend.orders(), days)
        p = backend.products()
        rev = sum(o["total"] for o in os_)
        profit = sum(o["total"] * (1 - REFERRAL) - o["qty"] * (p[o["sku"]]["cost"] + p[o["sku"]]["fba_fee"])
                     for o in os_)
        return {"days": days, "orders": len(os_), "units": sum(o["qty"] for o in os_),
                "revenue": round(rev, 2), "est_profit": round(profit, 2),
                "est_margin_pct": round(100 * profit / rev, 1) if rev else 0.0}

    def top_products(days: int = 30, n: int = 5):
        agg = {}
        for o in _recent(backend.orders(), days):
            a = agg.setdefault(o["sku"], {"sku": o["sku"], "units": 0, "revenue": 0.0})
            a["units"] += o["qty"]; a["revenue"] = round(a["revenue"] + o["total"], 2)
        return sorted(agg.values(), key=lambda a: -a["revenue"])[:n]

    def product_margin(sku: str):
        p = backend.products()[sku]
        fees = p["price"] * REFERRAL + p["fba_fee"]
        net = p["price"] - fees - p["cost"]
        return {"sku": sku, "price": p["price"], "cost": p["cost"], "fees": round(fees, 2),
                "net_per_unit": round(net, 2), "margin_pct": round(100 * net / p["price"], 1)}

    def propose_price_change(sku: str, new_price: float, reason: str):
        p = backend.products()[sku]
        if new_price <= 0:
            return {"error": "price must be positive"}
        pct = round(100 * (new_price - p["price"]) / p["price"], 1)
        return queue.propose("price_change", {"sku": sku, "old_price": p["price"], "new_price": new_price,
                                              "change_pct": pct, "reason": reason},
                             f"{sku}: ${p['price']} -> ${new_price} ({pct:+}%)")

    return [
        Tool("sales_summary", "SALES", "Revenue, units, orders and estimated profit over the last N days.",
             schema({"days": INT}), sales_summary),
        Tool("top_products", "SALES", "Top SKUs by revenue over the last N days.",
             schema({"days": INT, "n": INT}), top_products),
        Tool("product_margin", "SALES", "Unit economics (fees, net, margin) for one SKU.",
             schema({"sku": STR}, ["sku"]), product_margin),
        Tool("propose_price_change", "SALES", "Propose a price change. Requires human approval.",
             schema({"sku": STR, "new_price": NUM, "reason": STR}, ["sku", "new_price", "reason"]),
             propose_price_change, WRITE),
    ]
