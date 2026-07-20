"""Express connected-account operations."""

from __future__ import annotations

from typing import TYPE_CHECKING, Mapping

from stripe_connect._stripe import (
    is_stripe_error,
    normalize_account,
    to_stripe_api_error,
)
from stripe_connect.errors import AccountError

if TYPE_CHECKING:
    from stripe_connect.client import ConnectClient
    from stripe_connect.types import ConnectedAccount

DEFAULT_CAPABILITIES: dict[str, dict[str, bool]] = {
    "card_payments": {"requested": True},
    "transfers": {"requested": True},
}


def create_express_account(
    client: ConnectClient,
    *,
    email: str,
    country: str,
    metadata: Mapping[str, str],
    business_type: str | None = None,
    capabilities: Mapping[str, Mapping[str, bool]] | None = None,
) -> ConnectedAccount:
    """Create a Stripe Express connected account.

    ``metadata`` is passed through unchanged. Apps should include keys such as
    ``app`` and ``entity_id``; this package does not require or validate them.
    """
    if not email or not str(email).strip():
        raise AccountError("email must be a non-empty string")
    country_code = (country or client.config.default_country or "").strip().upper()
    if len(country_code) != 2:
        raise AccountError("country must be a 2-letter ISO country code")
    if metadata is None:
        raise AccountError("metadata is required (may be an empty mapping)")

    caps = capabilities if capabilities is not None else DEFAULT_CAPABILITIES
    params: dict = {
        "type": "express",
        "country": country_code,
        "email": str(email).strip(),
        "capabilities": dict(caps),
        "metadata": {str(k): str(v) for k, v in metadata.items()},
    }
    if business_type:
        params["business_type"] = business_type

    try:
        account = client.stripe.v1.accounts.create(params)
    except Exception as exc:
        if is_stripe_error(exc):
            api_error = to_stripe_api_error(exc)
            raise AccountError(api_error.message) from api_error
        raise AccountError(f"Failed to create Express account: {exc}") from exc

    try:
        return normalize_account(account)
    except ValueError as exc:
        raise AccountError(str(exc)) from exc


def retrieve_account(client: ConnectClient, account_id: str) -> ConnectedAccount:
    """Retrieve and normalize a connected account."""
    if not account_id or not str(account_id).strip():
        raise AccountError("account_id must be a non-empty string")

    try:
        account = client.stripe.v1.accounts.retrieve(str(account_id).strip())
    except Exception as exc:
        if is_stripe_error(exc):
            api_error = to_stripe_api_error(exc)
            raise AccountError(api_error.message) from api_error
        raise AccountError(f"Failed to retrieve account: {exc}") from exc

    try:
        return normalize_account(account)
    except ValueError as exc:
        raise AccountError(str(exc)) from exc
