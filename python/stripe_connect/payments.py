"""Destination charges with application fees."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Mapping

from stripe_connect._stripe import (
    is_stripe_error,
    normalize_destination_payment,
    to_stripe_api_error,
)
from stripe_connect.errors import PaymentError

if TYPE_CHECKING:
    from stripe_connect.client import ConnectClient
    from stripe_connect.types import DestinationPayment


def create_destination_payment(
    client: ConnectClient,
    *,
    amount_cents: int,
    currency: str,
    connected_account_id: str,
    application_fee_cents: int,
    metadata: Mapping[str, str] | None = None,
    customer: str | None = None,
    payment_method: str | None = None,
    confirm: bool = False,
    capture_method: str = "automatic",
    idempotency_key: str | None = None,
    statement_descriptor_suffix: str | None = None,
    transfer_group: str | None = None,
) -> DestinationPayment:
    """Create a platform PaymentIntent with destination charge + application fee.

    The application fee percentage (e.g. 2.5%) is owned by the calling app;
    this package only accepts a precomputed ``application_fee_cents``.

    This is not for platform Customer PaymentIntents (e.g. WMS/seller fees).

    Uses destination charges (``transfer_data.destination``) and does **not**
    set ``on_behalf_of``.
    """
    if not isinstance(amount_cents, int) or amount_cents <= 0:
        raise PaymentError("amount_cents must be a positive integer")
    if not isinstance(application_fee_cents, int) or application_fee_cents < 0:
        raise PaymentError("application_fee_cents must be a non-negative integer")
    if application_fee_cents >= amount_cents:
        raise PaymentError("application_fee_cents must be less than amount_cents")
    if not currency or not str(currency).strip():
        raise PaymentError("currency must be a non-empty ISO currency code")
    if not connected_account_id or not str(connected_account_id).strip():
        raise PaymentError("connected_account_id must be a non-empty string")
    if not capture_method or not str(capture_method).strip():
        raise PaymentError("capture_method must be a non-empty string")

    params: dict[str, Any] = {
        "amount": amount_cents,
        "currency": str(currency).strip().lower(),
        "application_fee_amount": application_fee_cents,
        "transfer_data": {"destination": str(connected_account_id).strip()},
        "capture_method": str(capture_method).strip(),
        "confirm": bool(confirm),
    }
    if metadata is not None:
        params["metadata"] = {str(k): str(v) for k, v in metadata.items()}
    if customer:
        params["customer"] = customer
    if payment_method:
        params["payment_method"] = payment_method
    if statement_descriptor_suffix:
        params["statement_descriptor_suffix"] = statement_descriptor_suffix
    if transfer_group:
        params["transfer_group"] = transfer_group

    options: dict[str, Any] | None = None
    if idempotency_key:
        options = {"idempotency_key": idempotency_key}

    try:
        if options is not None:
            payment_intent = client.stripe.v1.payment_intents.create(params, options)
        else:
            payment_intent = client.stripe.v1.payment_intents.create(params)
    except Exception as exc:
        if is_stripe_error(exc):
            api_error = to_stripe_api_error(exc)
            raise PaymentError(api_error.message) from api_error
        raise PaymentError(f"Failed to create destination payment: {exc}") from exc

    try:
        return normalize_destination_payment(payment_intent)
    except ValueError as exc:
        raise PaymentError(str(exc)) from exc
