"""ADMINISTRATION: account health, payouts and reconciliation, compliance notices. Read-only."""
from ..tools import STR, Tool, schema

LIMITS = {"order_defect_rate": 0.01, "late_shipment_rate": 0.04, "cancellation_rate": 0.025}


def tools(backend, queue):
    def account_health():
        h = backend.account_health()
        status = {k: ("at_risk" if h[k] > lim else "ok") for k, lim in LIMITS.items()}
        return {**h, "status": status, "limits": LIMITS}

    def reconcile_payouts():
        rows = []
        for s in backend.settlements():
            diff = round(s["actual_payout"] - s["expected_payout"], 2)
            rows.append({**s, "variance": diff, "needs_review": abs(diff) > 1.0})
        return rows

    def compliance_notices():
        return backend.account_health()["notices"]

    return [
        Tool("account_health", "ADMINISTRATION", "Defect, late-shipment and cancellation rates vs Amazon limits.",
             schema({}), account_health),
        Tool("reconcile_payouts", "ADMINISTRATION", "Compare expected vs actual settlement payouts; flag variances.",
             schema({}), reconcile_payouts),
        Tool("compliance_notices", "ADMINISTRATION", "Open policy and compliance notices.", schema({}), compliance_notices),
    ]
