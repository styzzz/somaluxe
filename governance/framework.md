# Seller Agent: Full Framework (Amazon automated processes)

**Scope:** Amazon seller operations only. Shopify is **not implemented**. Section 7 lists it as planned.
**Data:** Synthetic fixtures (`seller_agent/backend.py`). No live SP-API or Ads API calls.
**Model:** `claude-sonnet-5-5` by default (`SELLER_AGENT_MODEL` env var). Model use: tool selection and natural-language summaries only. The model does not hold authority to act.

## 1. Architecture
```
User ──> Assistant (Claude tool-use loop, max 8 steps)
            │
            ├─ Read tools  ──> Backend (fixture now; SP-API later)
            └─ Write tools ──> ActionQueue (pending) ──> Human approve/reject ──> Backend.apply()
```
- `seller_agent/assistant.py`: tool loop, system prompt, error handling.
- `seller_agent/tools.py`: tool definitions with `additionalProperties: false`.
- `seller_agent/actions.py`: pending-action queue. States: pending, approved, rejected, failed.
- `seller_agent/backend.py`: data interface and fixture implementation.
- `seller_agent/modules/`: five modules.

## 2. Automated processes by module

### 2.1 Sales
| Tool | Type | Automation | Control |
|---|---|---|---|
| `sales_summary` | Read | Revenue, units, orders, estimated profit for N days | Excludes canceled orders. Profit uses a flat 15% referral fee (assumption, not Amazon's rate table). |
| `top_products` | Read | Top SKUs by revenue | None needed |
| `product_margin` | Read | Net per unit after fees | Same fee assumption |
| `propose_price_change` | **Write** | Proposes new price | Price > 0. Approval required. **Gap:** no price floor, no max % change. |

### 2.2 Order Operations
| Tool | Type | Automation | Control |
|---|---|---|---|
| `list_orders` | Read | Orders by status | Status filter, limit |
| `late_shipment_risk` | Read | Orders due within 1 day or overdue | Derived from `ship_by` |
| `returns_report` | Read | Return count, reasons, rate, refunded $ | None needed |
| `propose_refund` | **Write** | Proposes refund | Order must exist. Amount must be > 0 and ≤ order total. Approval required. **Gap:** no $ threshold tiering. |

### 2.3 Marketing & Growth
| Tool | Type | Automation | Control |
|---|---|---|---|
| `campaign_performance` | Read | Spend, sales, ACOS, ROAS | Divide-by-zero handled |
| `ad_efficiency_flags` | Read | Campaigns above 30% ACOS | Threshold is a code constant |
| `propose_ad_budget_change` | **Write** | Proposes daily budget | Campaign must exist. Budget ≥ 0. Approval required. **Gap:** no max increase cap. |

### 2.4 Inventory & Storage
| Tool | Type | Automation | Control |
|---|---|---|---|
| `inventory_levels` | Read | Stock, inbound, run rate, days of cover | Divide-by-zero handled |
| `replenishment_recommendations` | Read | Suggested qty = run rate × (21-day lead + 14-day safety) − stock | Lead time and safety days are constants. Suggestion rounded to 10s. |
| `storage_risk` | Read | Aged (90+ day) units and cubic feet | None needed |
| `propose_restock` | **Write** | Proposes inbound shipment, with cost at unit cost | SKU must exist. Qty > 0. Approval required. |

### 2.5 Administration
| Tool | Type | Automation | Control |
|---|---|---|---|
| `account_health` | Read | Defect, late-shipment and cancellation rates vs limits (1%, 4%, 2.5%) | Limits are code constants. **VERIFY** against Amazon's current policy. |
| `reconcile_payouts` | Read | Expected vs actual payout; flags variance > $1 | Flag only. Nothing is posted. |
| `compliance_notices` | Read | Open policy notices | Notice text is data; the model is told not to follow it. |

**Administration has no write tools.** Nothing in this module changes an account.

## 3. Approval model
- Every write action requires an explicit approve call with an approver ID.
- A rejected or failed action cannot be approved later.
- A failed execution is recorded with the error. It is not retried.
- **Gaps:** no tiered thresholds (for example, auto-approve below $X), approver is a hard-coded string, no separation of duties, no expiry on pending actions.

## 4. Tests
11 tests pass (`pytest`): module registration, sales math, propose-only behavior, reject path, refund validation, ad flags, payout variance, inventory and health, tool loop, unknown tool handling, no approve tool exposed, turn limit.
Not tested: model output quality, prompt injection, permission boundaries under adversarial input.

## 5. NIST AI RMF mapping (summary)
| Function | Status | Evidence |
|---|---|---|
| GOVERN | Partial | Propose-only policy; no written AI policy, owner, or risk appetite yet |
| MAP | Partial | Module and data flow documented here; no formal impact assessment |
| MEASURE | Weak | 11 unit tests only; no evals, metrics or drift monitoring |
| MANAGE | Partial | Human approval; no incident process, rollback or KRIs |

## 6. Known limitations
- No live data. Every number in the assistant's output comes from synthetic fixtures.
- Profit and fee figures use assumptions, not Amazon fee schedules.
- No audit log, rate limits, injection screening, or monitoring.
- Single approver string, no authentication.
- Model errors from the API are not caught in `ask()`; they propagate to the caller.

## 7. Shopify (not implemented)
Planned: catalog and pricing, discounts, orders and refunds, customer data handling, payouts, and fraud signals. The same propose/approve pattern would apply. No Shopify GraphQL calls exist in this code. Any field names must be checked against the live Shopify schema before use.

## 8. Priority controls before live use
1. Audit log: timestamp, actor, input hash, output, decision, approver.
2. Approval tiers and caps: price change > ±15%, refund > $50 per order, ad budget increase > 25%, restock > $2,000 at cost.
3. Price floor at unit cost plus fees.
4. Authenticated approvers with separation of duties.
5. Injection screening on buyer notes and listing text, enforced in code.
6. Evals for accuracy, refusal of unsafe actions, injection resistance and approval routing.
7. KRI monitors: refund rate, price-change frequency, late-shipment rate, ACOS, payout variance.
