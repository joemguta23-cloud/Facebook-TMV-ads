"""Pure budget amendment rules. NO Meta or database side effects."""
from dataclasses import dataclass
from datetime import date
from typing import Literal

Window = Literal["DAY", "EVENING"]

@dataclass(frozen=True)
class Amendment:
    local_date: date
    window: Window
    adset_id: str
    original_baseline_cents: int
    original_allowance_cents: int
    original_lifetime_target_cents: int
    new_total_allowance_cents: int
    prior_confirmed_target_cents: int

    def validate(self):
        if self.original_baseline_cents < 0 or self.original_allowance_cents < 0:
            raise ValueError("Invalid original amounts")
        if self.original_lifetime_target_cents != self.original_baseline_cents + self.original_allowance_cents:
            raise ValueError("Original reservation inconsistent")
        if self.prior_confirmed_target_cents != self.original_lifetime_target_cents:
            raise ValueError("Live target differs; reconcile before amendment")
        if self.new_total_allowance_cents < self.original_allowance_cents:
            raise ValueError("Reduction requires separate safe handling")
        if not self.adset_id.isdecimal():
            raise ValueError("Invalid adset")
        if self.window not in ("DAY", "EVENING"):
            raise ValueError("Invalid window")

    @property
    def amendment_cents(self):
        self.validate()
        return self.new_total_allowance_cents - self.original_allowance_cents

    @property
    def new_lifetime_target_cents(self):
        self.validate()
        return self.original_baseline_cents + self.new_total_allowance_cents

    @property
    def transaction_key(self):
        self.validate()
        return f"TMV:{self.local_date.isoformat()}:{self.window}:{self.adset_id}:LIFETIME:{self.new_lifetime_target_cents}"


# Schema for an eventual database-backed single writer. The public staging service
# must not expose this as a live budget mutation endpoint.
POSTGRES_SCHEMA = """
CREATE TABLE IF NOT EXISTS budget_amendments (
    transaction_key TEXT PRIMARY KEY,
    local_date DATE NOT NULL,
    window TEXT NOT NULL CHECK (window IN ('DAY','EVENING')),
    adset_id TEXT NOT NULL,
    approved_total_cents INTEGER NOT NULL CHECK (approved_total_cents >= 0),
    target_lifetime_cents INTEGER NOT NULL CHECK (target_lifetime_cents >= 0),
    status TEXT NOT NULL CHECK (status IN (
      'RESERVED','SENT_UNVERIFIED','CONFIRMED','FAILED','BLOCKED')),
    approval_source TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (local_date, window, adset_id, target_lifetime_cents)
);
CREATE TABLE IF NOT EXISTS amendment_events (
    event_id BIGSERIAL PRIMARY KEY,
    transaction_key TEXT NOT NULL REFERENCES budget_amendments(transaction_key),
    state TEXT NOT NULL,
    evidence_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
"""
