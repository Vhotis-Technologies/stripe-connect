"""Public data types for the Stripe Connect engine."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Mapping


class AccountCapabilityState(str, Enum):
    """Capability status for a connected account.

    ``NOT_STARTED`` is app-owned (no ``acct_`` yet). The package never emits it;
    it only returns ``pending``, ``restricted``, or ``ready``.
    """

    NOT_STARTED = "not_started"
    PENDING = "pending"
    RESTRICTED = "restricted"
    READY = "ready"


class WebhookEventType(str, Enum):
    """Normalized webhook event types supported in v0.1."""

    ACCOUNT_UPDATED = "account.updated"
    UNKNOWN = "unknown"


@dataclass(frozen=True, slots=True)
class ConnectedAccount:
    """Normalized Stripe Connect Account."""

    id: str
    email: str | None
    country: str | None
    type: str
    charges_enabled: bool
    payouts_enabled: bool
    details_submitted: bool
    requirements_currently_due: tuple[str, ...]
    requirements_past_due: tuple[str, ...]
    requirements_disabled_reason: str | None
    metadata: Mapping[str, str]
    raw: Mapping[str, Any]


@dataclass(frozen=True, slots=True)
class OnboardingLink:
    """Hosted Account Link for Express onboarding."""

    url: str
    expires_at: int


@dataclass(frozen=True, slots=True)
class Readiness:
    """Source-of-truth readiness derived from Stripe account flags.

    ``is_ready`` is true only when both ``charges_enabled`` and
    ``payouts_enabled`` are true.
    """

    account_id: str
    charges_enabled: bool
    payouts_enabled: bool
    details_submitted: bool
    is_ready: bool
    status: AccountCapabilityState
    disabled_reason: str | None


@dataclass(frozen=True, slots=True)
class DestinationPayment:
    """Platform PaymentIntent with destination charge + application fee."""

    payment_intent_id: str
    client_secret: str | None
    status: str
    amount: int
    currency: str
    application_fee_amount: int
    transfer_data_destination: str
    raw: Mapping[str, Any]


@dataclass(frozen=True, slots=True)
class ParsedWebhookEvent:
    """Verified and normalized Connect webhook event."""

    id: str
    type: WebhookEventType
    type_raw: str
    account_id: str | None
    livemode: bool
    created: int
    data: ConnectedAccount | None
    raw: Mapping[str, Any]
