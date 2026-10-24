"""MARKETING & GROWTH: advertising performance and budgets."""
from ..tools import NUM, STR, WRITE, Tool, schema

TARGET_ACOS = 0.30


def tools(backend, queue):
    def _row(c):
        acos = c["spend_30d"] / c["sales_30d"] if c["sales_30d"] else None
        return {**c, "acos_pct": round(100 * acos, 1) if acos is not None else None,
                "roas": round(c["sales_30d"] / c["spend_30d"], 2) if c["spend_30d"] else None,
                "over_target": acos is not None and acos > TARGET_ACOS}

    def campaign_performance():
        return [_row(c) for c in backend.campaigns()]

    def ad_efficiency_flags():
        return [r for r in campaign_performance() if r["over_target"]]

    def propose_ad_budget_change(campaign_id: str, new_daily_budget: float, reason: str):
        c = next((c for c in backend.campaigns() if c["id"] == campaign_id), None)
        if c is None:
            return {"error": f"unknown campaign {campaign_id}"}
        if new_daily_budget < 0:
            return {"error": "budget cannot be negative"}
        return queue.propose("ad_budget", {"campaign_id": campaign_id, "old_budget": c["daily_budget"],
                                           "new_budget": new_daily_budget, "reason": reason},
                             f"{c['name']}: daily budget ${c['daily_budget']} -> ${new_daily_budget}")

    return [
        Tool("campaign_performance", "MARKETING & GROWTH", "30-day spend, sales, ACOS and ROAS per campaign.",
             schema({}), campaign_performance),
        Tool("ad_efficiency_flags", "MARKETING & GROWTH", f"Campaigns with ACOS above {int(TARGET_ACOS*100)}%.",
             schema({}), ad_efficiency_flags),
        Tool("propose_ad_budget_change", "MARKETING & GROWTH", "Propose a daily ad budget change. Requires human approval.",
             schema({"campaign_id": STR, "new_daily_budget": NUM, "reason": STR},
                    ["campaign_id", "new_daily_budget", "reason"]), propose_ad_budget_change, WRITE),
    ]
