"""INVENTORY & STORAGE MANAGEMENT: stock levels, replenishment, aged stock."""
from ..tools import INT, STR, WRITE, Tool, schema

LEAD_TIME_DAYS = 21
SAFETY_DAYS = 14


def tools(backend, queue):
    def _cover(i):
        daily = i["units_sold_30d"] / 30
        total = i["fulfillable"] + i["inbound"]
        return {"daily_rate": round(daily, 2), "days_of_cover": round(total / daily, 1) if daily else None}

    def inventory_levels():
        return [{**i, **_cover(i)} for i in backend.inventory()]

    def replenishment_recommendations():
        out = []
        for i in backend.inventory():
            c = _cover(i)
            need = c["daily_rate"] * (LEAD_TIME_DAYS + SAFETY_DAYS) - (i["fulfillable"] + i["inbound"])
            if need > 0:
                out.append({"sku": i["sku"], "days_of_cover": c["days_of_cover"],
                            "suggested_qty": int(round(need, -1)) or 10})
        return out

    def storage_risk():
        return [{"sku": i["sku"], "aged_90plus_units": i["aged_90plus"],
                 "cube_ft3": round(i["aged_90plus"] * i["unit_cube_ft3"], 2)}
                for i in backend.inventory() if i["aged_90plus"] > 0]

    def propose_restock(sku: str, qty: int, reason: str):
        if sku not in backend.products():
            return {"error": f"unknown sku {sku}"}
        if qty <= 0:
            return {"error": "qty must be positive"}
        unit_cost = backend.products()[sku]["cost"]
        return queue.propose("restock", {"sku": sku, "qty": qty, "est_cost": round(qty * unit_cost, 2),
                                         "reason": reason},
                             f"Create inbound shipment: {qty} x {sku} (~${qty * unit_cost:,.2f} at cost)")

    return [
        Tool("inventory_levels", "INVENTORY & STORAGE", "Stock, inbound, run rate and days of cover per SKU.",
             schema({}), inventory_levels),
        Tool("replenishment_recommendations", "INVENTORY & STORAGE",
             f"SKUs that will run out within lead time ({LEAD_TIME_DAYS}d) plus safety stock ({SAFETY_DAYS}d).",
             schema({}), replenishment_recommendations),
        Tool("storage_risk", "INVENTORY & STORAGE", "SKUs with aged (90+ day) inventory that risks surcharges.",
             schema({}), storage_risk),
        Tool("propose_restock", "INVENTORY & STORAGE", "Propose an inbound shipment. Requires human approval.",
             schema({"sku": STR, "qty": INT, "reason": STR}, ["sku", "qty", "reason"]), propose_restock, WRITE),
    ]
