"""Thread-safe in-memory test run registry for Ring 1 live execution inspection."""

from __future__ import annotations

from typing import Any


class Ring1TestRunRegistry:
    """Thread-safe in-memory registry holding recent Ring 1 live test runs."""

    def __init__(self, max_runs: int = 50) -> None:
        self._runs: dict[str, dict[str, Any]] = {}
        self._order: list[str] = []
        self._max_runs = max_runs

    def save_run(self, run_id: str, data: dict[str, Any]) -> None:
        if run_id in self._runs:
            self._runs[run_id] = data
            return
        if len(self._order) >= self._max_runs:
            oldest = self._order.pop(0)
            self._runs.pop(oldest, None)
        self._order.append(run_id)
        self._runs[run_id] = data

    def get_run(self, run_id: str) -> dict[str, Any] | None:
        return self._runs.get(run_id)

    def list_runs(self, limit: int = 15) -> list[dict[str, Any]]:
        recent_ids = reversed(self._order[-limit:])
        return [
            {
                "run_id": r_id,
                "mode": self._runs[r_id].get("mode"),
                "status": self._runs[r_id].get("status"),
                "timestamp": self._runs[r_id].get("timestamp"),
                "total_events": len(self._runs[r_id].get("events", [])),
                "duration_ms": self._runs[r_id].get("duration_ms"),
            }
            for r_id in recent_ids
            if r_id in self._runs
        ]


# Singleton in-memory registry for development and test runs
test_run_registry = Ring1TestRunRegistry()
