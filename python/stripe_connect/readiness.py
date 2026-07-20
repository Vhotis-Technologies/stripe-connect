"""Readiness helpers derived from Stripe account capability flags."""

from __future__ import annotations

from stripe_connect.types import AccountCapabilityState, ConnectedAccount, Readiness


def is_account_ready(*, charges_enabled: bool, payouts_enabled: bool) -> bool:
    """Return True only when both Stripe capability flags are enabled."""
    return bool(charges_enabled) and bool(payouts_enabled)


def derive_status(
    *,
    charges_enabled: bool,
    payouts_enabled: bool,
    disabled_reason: str | None,
    requirements_currently_due: tuple[str, ...] = (),
    requirements_past_due: tuple[str, ...] = (),
) -> AccountCapabilityState:
    """Map Stripe flags/requirements to a coarse status.

    Never returns ``NOT_STARTED`` — that state is owned by the app when no
    ``acct_`` id exists yet.
    """
    if is_account_ready(charges_enabled=charges_enabled, payouts_enabled=payouts_enabled):
        return AccountCapabilityState.READY

    if disabled_reason or requirements_past_due:
        return AccountCapabilityState.RESTRICTED

    if requirements_currently_due and not (charges_enabled and payouts_enabled):
        # Outstanding requirements without an explicit disable still block go-live;
        # treat as pending until Stripe marks a disabled reason / past_due.
        return AccountCapabilityState.PENDING

    return AccountCapabilityState.PENDING


def from_account(account: ConnectedAccount) -> Readiness:
    """Build a :class:`Readiness` snapshot from a normalized account."""
    ready = is_account_ready(
        charges_enabled=account.charges_enabled,
        payouts_enabled=account.payouts_enabled,
    )
    status = derive_status(
        charges_enabled=account.charges_enabled,
        payouts_enabled=account.payouts_enabled,
        disabled_reason=account.requirements_disabled_reason,
        requirements_currently_due=account.requirements_currently_due,
        requirements_past_due=account.requirements_past_due,
    )
    return Readiness(
        account_id=account.id,
        charges_enabled=account.charges_enabled,
        payouts_enabled=account.payouts_enabled,
        details_submitted=account.details_submitted,
        is_ready=ready,
        status=status,
        disabled_reason=account.requirements_disabled_reason,
    )
