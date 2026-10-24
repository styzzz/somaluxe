"""Pending-action queue: write tools propose, a human approves, then it executes."""
import itertools
from dataclasses import dataclass, field
from typing import Any


@dataclass
class Action:
    id: str
    kind: str
    params: dict
    summary: str
    status: str = "pending"  # pending | approved | rejected | failed
    decided_by: str | None = None
    result: Any = None


@dataclass
class ActionQueue:
    backend: Any
    _items: dict[str, Action] = field(default_factory=dict)
    _ids: Any = field(default_factory=lambda: itertools.count(1))

    def propose(self, kind: str, params: dict, summary: str) -> dict:
        a = Action(f"A{next(self._ids):04d}", kind, params, summary)
        self._items[a.id] = a
        return {"action_id": a.id, "status": a.status, "summary": summary,
                "note": "Proposed only. A human must approve before anything changes."}

    def pending(self) -> list[Action]:
        return [a for a in self._items.values() if a.status == "pending"]

    def get(self, action_id: str) -> Action:
        return self._items[action_id]

    def approve(self, action_id: str, approver: str) -> Action:
        a = self._items[action_id]
        if a.status != "pending":
            raise ValueError(f"{action_id} is {a.status}, not pending")
        a.decided_by = approver
        try:
            a.result = self.backend.apply(a.kind, a.params)
            a.status = "approved"
        except Exception as e:  # keep the queue consistent if execution fails
            a.status, a.result = "failed", str(e)
        return a

    def reject(self, action_id: str, approver: str) -> Action:
        a = self._items[action_id]
        if a.status != "pending":
            raise ValueError(f"{action_id} is {a.status}, not pending")
        a.status, a.decided_by = "rejected", approver
        return a
