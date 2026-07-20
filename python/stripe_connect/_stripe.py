"""Internal Stripe SDK helpers (not part of the stable public surface)."""

from __future__ import annotations

from typing import Any, Mapping

import stripe
from stripe import StripeClient
from stripe._error import StripeError

from stripe_connect.config import StripeConnectConfig
from stripe_connect.errors import StripeAPIError
from stripe_connect.types import ConnectedAccount, DestinationPayment, OnboardingLink


def build_stripe_client(config: StripeConnectConfig) -> StripeClient:
    """Create a Stripe SDK client from package config."""
    kwargs: dict[str, Any] = {"api_key": config.secret_key}
    if config.api_version:
        kwargs["stripe_version"] = config.api_version
    return StripeClient(**kwargs)


def _get(obj: Any, key: str, default: Any = None) -> Any:
    if obj is None:
        return default
    if isinstance(obj, Mapping):
        return obj.get(key, default)
    return getattr(obj, key, default)


def _as_str_tuple(value: Any) -> tuple[str, ...]:
    if not value:
        return ()
    return tuple(str(item) for item in value)


def _as_str_mapping(value: Any) -> Mapping[str, str]:
    if not value:
        return {}
    if isinstance(value, Mapping):
        return {str(k): str(v) for k, v in value.items()}
    # StripeObject-like
    try:
        return {str(k): str(v) for k, v in dict(value).items()}
    except Exception:
        return {}


def _as_raw_mapping(obj: Any) -> Mapping[str, Any]:
    if isinstance(obj, Mapping):
        return dict(obj)
    to_dict = getattr(obj, "to_dict", None)
    if callable(to_dict):
        data = to_dict()
        if isinstance(data, Mapping):
            return dict(data)
    to_dict_recursive = getattr(obj, "to_dict_recursive", None)
    if callable(to_dict_recursive):
        data = to_dict_recursive()
        if isinstance(data, Mapping):
            return dict(data)
    try:
        return dict(obj)
    except Exception:
        return {"repr": repr(obj)}


def normalize_account(account: Any) -> ConnectedAccount:
    """Convert a Stripe Account object/dict into :class:`ConnectedAccount`."""
    requirements = _get(account, "requirements") or {}
    account_id = _get(account, "id")
    if not account_id:
        raise ValueError("Stripe account response missing id")

    return ConnectedAccount(
        id=str(account_id),
        email=_get(account, "email"),
        country=_get(account, "country"),
        type=str(_get(account, "type") or "express"),
        charges_enabled=bool(_get(account, "charges_enabled", False)),
        payouts_enabled=bool(_get(account, "payouts_enabled", False)),
        details_submitted=bool(_get(account, "details_submitted", False)),
        requirements_currently_due=_as_str_tuple(_get(requirements, "currently_due")),
        requirements_past_due=_as_str_tuple(_get(requirements, "past_due")),
        requirements_disabled_reason=_get(requirements, "disabled_reason"),
        metadata=_as_str_mapping(_get(account, "metadata")),
        raw=_as_raw_mapping(account),
    )


def normalize_onboarding_link(link: Any) -> OnboardingLink:
    """Convert a Stripe AccountLink object/dict into :class:`OnboardingLink`."""
    url = _get(link, "url")
    expires_at = _get(link, "expires_at")
    if not url:
        raise ValueError("Stripe AccountLink response missing url")
    if expires_at is None:
        raise ValueError("Stripe AccountLink response missing expires_at")
    return OnboardingLink(url=str(url), expires_at=int(expires_at))


def normalize_destination_payment(payment_intent: Any) -> DestinationPayment:
    """Convert a Stripe PaymentIntent into :class:`DestinationPayment`."""
    pi_id = _get(payment_intent, "id")
    if not pi_id:
        raise ValueError("Stripe PaymentIntent response missing id")

    transfer_data = _get(payment_intent, "transfer_data") or {}
    destination = _get(transfer_data, "destination")
    if not destination:
        raise ValueError("Stripe PaymentIntent missing transfer_data.destination")

    amount = _get(payment_intent, "amount")
    if amount is None:
        raise ValueError("Stripe PaymentIntent response missing amount")

    currency = _get(payment_intent, "currency")
    if not currency:
        raise ValueError("Stripe PaymentIntent response missing currency")

    fee = _get(payment_intent, "application_fee_amount")
    if fee is None:
        fee = 0

    return DestinationPayment(
        payment_intent_id=str(pi_id),
        client_secret=_get(payment_intent, "client_secret"),
        status=str(_get(payment_intent, "status") or ""),
        amount=int(amount),
        currency=str(currency).lower(),
        application_fee_amount=int(fee),
        transfer_data_destination=str(destination),
        raw=_as_raw_mapping(payment_intent),
    )


def to_stripe_api_error(exc: StripeError) -> StripeAPIError:
    """Normalize a Stripe SDK error into :class:`StripeAPIError`."""
    message = getattr(exc, "user_message", None) or str(exc) or exc.__class__.__name__
    raw: Mapping[str, Any] | None = None
    json_body = getattr(exc, "json_body", None)
    if isinstance(json_body, Mapping):
        raw = dict(json_body)
    return StripeAPIError(
        message,
        code=getattr(exc, "code", None),
        http_status=getattr(exc, "http_status", None),
        request_id=getattr(exc, "request_id", None),
        raw=raw,
    )


def is_stripe_error(exc: BaseException) -> bool:
    return isinstance(exc, StripeError)


# Re-export for typing / tests that need the SDK exception base.
stripe_error_type = StripeError
stripe_module = stripe
