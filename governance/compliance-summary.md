# Seller Agent: AI Regulatory Compliance Summary (one page)

**System:** Amazon seller operations assistant. Five modules (Sales, Order Operations, Marketing & Growth, Inventory & Storage, Administration) plus a Claude tool-use assistant.
**Status:** Prototype. Runs on synthetic fixture data. No live Amazon or Shopify connection.
**Basis:** Code as of this commit. Regulatory status as of June 2026 knowledge; items marked **VERIFY** must be checked against current text before reliance. This is not legal advice.

## Bottom line
As built, the system does not make consequential decisions about people, and every write action needs human approval. Regulatory exposure is low. The gaps are operational controls, which matter for production use and for buyer data once a live connection exists.

## Regime-by-regime

| Regime | Applies? | Why | Status | Gap before production |
|---|---|---|---|---|
| **EU AI Act** (Reg. 2024/1689) | Likely not high-risk | Pricing, ads and inventory tools are not in Annex III (credit, employment, essential services, etc.) | Prohibited practices (Art. 5): not triggered. Art. 4 AI literacy: applies to deployers from Feb 2025. Art. 50 transparency: assistant is an AI interface and should say so. | Add AI-interaction disclosure in the assistant UI. Document AI literacy for operators. **VERIFY** the high-risk timeline; EU proposals to delay it were under debate. |
| **Colorado AI Act** (SB 24-205) | No | Covers "consequential decisions" (employment, lending, housing, insurance, etc.), not seller operations | Out of scope | Re-check if the system ever scores or decides on people. **VERIFY** effective date and amendments. |
| **California CCPA / CPPA ADMT rules** | Unlikely | Rules target significant automated decisions about consumers | Out of scope for own-store operations | Relevant only if prices or offers are personalized per buyer. The system uses one price per SKU. |
| **FTC Act §5** | Yes | Deceptive or unfair practices apply to any AI-driven pricing, claims and ads | Partly controlled: price changes and refunds need approval; no price-floor or claims check | Add price floor (no sale below cost), a max % change guard, and check ad copy against claims rules. Fake-review rule (16 CFR 465): system does not generate reviews. |
| **FTC Safeguards Rule** | No | Applies to financial institutions | Out of scope | None. |
| **PCI DSS** | No | System holds no card data; payouts are handled by Amazon | Out of scope | Keep it that way. Any card data would bring it in scope. |
| **SOX-style financial controls** | Not required | Private seller, not an issuer | Partly applied: payout reconciliation with a $1 variance flag; refund and price validation | Add an audit trail and approval thresholds before using outputs for books. |
| **OMB M-25-21 / M-24-10** | No | Federal-agency AI use. M-25-21 replaced M-24-10 in April 2025 | Out of scope | Relevant only if you sell to a federal agency. |
| **EO 14179 (Jan 2025)** | Context only | Revoked EO 14110; federal posture is deregulatory | No obligation | None. |
| **Amazon SP-API / Seller agreements** | Yes, once connected | Automated access and buyer data are governed by Amazon's terms | Not connected | Review the SP-API developer and data-protection terms before any live access. Restrict buyer data to permitted purposes. |
| **GDPR** (if EU buyers' data is processed) | Possibly | Buyer data is personal data | Fixture data is synthetic | Data minimization, retention limits and a DPA with the model provider before live data. |

## Voluntary standards referenced
- **NIST AI RMF 1.0 and GenAI Profile (AI 600-1):** mapped in the full framework document. Partially met.
- **ISO/IEC 42001:** not certified. Gap analysis only.
- **EU AI Act alignment:** governance, logging and human oversight are partly designed in. Logging is not built yet.

## What the controls do now
- Write tools only propose. Approval is outside the model. The assistant has no approve tool.
- Input validation on refunds (amount ≤ order total), prices (> 0), ad budgets (≥ 0), restocks (> 0).
- Schemas reject unknown fields. Tool errors are returned to the model, not raised.
- Turn limit (8 steps). 11 unit tests pass.

## Critical gaps (ranked)
1. No audit log of model calls or actions.
2. No dollar or percent approval thresholds. Every action needs approval but there is no tiering.
3. Approver identity is a hard-coded string, not authenticated.
4. Prompt injection: buyer notes and listing text reach the model. The rule to ignore them is in the prompt only, not enforced in code.
5. No price floor, so the system can propose a price below cost.
6. No evals, KRI monitors or model card.
