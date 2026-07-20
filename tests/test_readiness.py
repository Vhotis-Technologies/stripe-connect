"""Readiness derivation tests (no Stripe network)."""

from __future__ import annotations

from stripe_connect.readiness import derive_status, from_account, is_account_ready
from stripe_connect.types import AccountCapabilityState, ConnectedAccount


def _account(**overrides: object) -> ConnectedAccount:
    base: dict[str, object] = {
        "id": "acct_test",
        "email": "seller@example.com",
        "country": "GB",
        "type": "express",
        "charges_enabled": False,
        "payouts_enabled": False,
        "details_submitted": False,
        "requirements_currently_due": (),
        "requirements_past_due": (),
        "requirements_disabled_reason": None,
        "metadata": {},
        "raw": {},
    }
    base.update(overrides)
    return ConnectedAccount(**base)  # type: ignore[arg-type]


def test_is_ready_requires_both_flags() -> None:
    assert is_account_ready(charges_enabled=True, payouts_enabled=True) is True
    assert is_account_ready(charges_enabled=True, payouts_enabled=False) is False
    assert is_account_ready(charges_enabled=False, payouts_enabled=True) is False


def test_derive_status_ready() -> None:
    status = derive_status(charges_enabled=True, payouts_enabled=True, disabled_reason=None)
    assert status is AccountCapabilityState.READY


def test_derive_status_restricted_when_disabled_reason() -> None:
    status = derive_status(
        charges_enabled=False,
        payouts_enabled=False,
        disabled_reason="requirements.past_due",
    )
    assert status is AccountCapabilityState.RESTRICTED


def test_derive_status_restricted_when_past_due() -> None:
    status = derive_status(
        charges_enabled=False,
        payouts_enabled=False,
        disabled_reason=None,
        requirements_past_due=("individual.verification.document",),
    )
    assert status is AccountCapabilityState.RESTRICTED


def test_derive_status_pending_otherwise() -> None:
    status = derive_status(
        charges_enabled=False,
        payouts_enabled=False,
        disabled_reason=None,
        requirements_currently_due=("business_profile.url",),
    )
    assert status is AccountCapabilityState.PENDING


def test_from_account_ready_snapshot() -> None:
    readiness = from_account(
        _account(charges_enabled=True, payouts_enabled=True, details_submitted=True)
    )
    assert readiness.is_ready is True
    assert readiness.status is AccountCapabilityState.READY
    assert readiness.account_id == "acct_test"


def test_from_account_never_emits_not_started() -> None:
    readiness = from_account(_account())
    assert readiness.status is not AccountCapabilityState.NOT_STARTED
    assert readiness.is_ready is False
