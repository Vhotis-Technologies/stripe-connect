"""Hosted Account Link onboarding."""

from __future__ import annotations

from typing import TYPE_CHECKING

from stripe_connect._stripe import (
    is_stripe_error,
    normalize_onboarding_link,
    to_stripe_api_error,
)
from stripe_connect.errors import OnboardingError

if TYPE_CHECKING:
    from stripe_connect.client import ConnectClient
    from stripe_connect.types import OnboardingLink


def create_onboarding_link(
    client: ConnectClient,
    *,
    account_id: str,
    refresh_url: str,
    return_url: str,
    type: str = "account_onboarding",
) -> OnboardingLink:
    """Create a hosted Stripe Account Link for Express onboarding."""
    if not account_id or not str(account_id).strip():
        raise OnboardingError("account_id must be a non-empty string")
    if not refresh_url or not str(refresh_url).strip():
        raise OnboardingError("refresh_url must be a non-empty string")
    if not return_url or not str(return_url).strip():
        raise OnboardingError("return_url must be a non-empty string")
    if not type or not str(type).strip():
        raise OnboardingError("type must be a non-empty string")

    params = {
        "account": str(account_id).strip(),
        "refresh_url": str(refresh_url).strip(),
        "return_url": str(return_url).strip(),
        "type": str(type).strip(),
    }

    try:
        link = client.stripe.v1.account_links.create(params)
    except Exception as exc:
        if is_stripe_error(exc):
            api_error = to_stripe_api_error(exc)
            raise OnboardingError(api_error.message) from api_error
        raise OnboardingError(f"Failed to create Account Link: {exc}") from exc

    try:
        return normalize_onboarding_link(link)
    except ValueError as exc:
        raise OnboardingError(str(exc)) from exc
