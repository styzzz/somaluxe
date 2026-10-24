import pytest

from seller_agent.actions import ActionQueue
from seller_agent.backend import FixtureBackend
from seller_agent.modules import MODULES, all_tools


@pytest.fixture
def env():
    b = FixtureBackend()
    q = ActionQueue(b)
    return b, q, {t.name: t for t in all_tools(b, q)}


def test_five_modules_registered():
    assert set(MODULES) == {"sales", "order_operations", "marketing_growth", "inventory_storage", "administration"}


def test_sales_summary_matches_orders(env):
    b, _, t = env
    s = t["sales_summary"].fn(days=60)
    expect = round(sum(o["total"] for o in b.orders() if o["status"] != "Canceled"), 2)
    assert s["revenue"] == expect and s["orders"] > 0


def test_write_tools_only_propose(env):
    b, q, t = env
    before = b.products()["SKU-MUG-01"]["price"]
    r = t["propose_price_change"].fn(sku="SKU-MUG-01", new_price=22.0, reason="test")
    assert b.products()["SKU-MUG-01"]["price"] == before
    assert q.get(r["action_id"]).status == "pending"
    q.approve(r["action_id"], "tester")
    assert b.products()["SKU-MUG-01"]["price"] == 22.0


def test_reject_does_not_apply(env):
    b, q, t = env
    r = t["propose_ad_budget_change"].fn(campaign_id="C1", new_daily_budget=500.0, reason="x")
    q.reject(r["action_id"], "tester")
    assert b.campaigns()[0]["daily_budget"] == 30.0
    with pytest.raises(ValueError):
        q.approve(r["action_id"], "tester")


def test_refund_validation(env):
    _, _, t = env
    oid = "111-0000001-0000001"
    assert "error" in t["propose_refund"].fn(order_id=oid, amount=99999, reason="x")
    assert "error" in t["propose_refund"].fn(order_id="nope", amount=1, reason="x")


def test_ads_flag_and_payout_variance(env):
    _, _, t = env
    assert [c["id"] for c in t["ad_efficiency_flags"].fn()] == ["C2"]
    assert any(r["needs_review"] for r in t["reconcile_payouts"].fn())


def test_inventory_and_health(env):
    _, _, t = env
    assert all(r["suggested_qty"] > 0 for r in t["replenishment_recommendations"].fn())
    assert t["account_health"].fn()["status"]["order_defect_rate"] == "ok"
