"""Account Link onboarding tests with a mocked Stripe client."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from stripe._error import InvalidRequestError

from stripe_connect import ConnectClient, OnboardingError, StripeConnectConfig


def _config() -> StripeConnectConfig:
    return StripeConnectConfig(secret_key="sk_test_x", webhook_secret="whsec_x")


def test_create_onboarding_link_success() -> None:
    stripe = MagicMock()
    stripe.v1.account_links.create.return_value = {
        "url": "https://connect.stripe.com/setup/e/acct_123/token",
        "expires_at": 1_700_000_000,
    }
    client = ConnectClient(_config(), stripe_client=stripe)

    link = client.create_onboarding_link(
        account_id="acct_123",
        refresh_url="https://app.example.com/connect/refresh",
        return_url="https://app.example.com/connect/return",
    )

    assert link.url.startswith("https://connect.stripe.com/")
    assert link.expires_at == 1_700_000_000
    params = stripe.v1.account_links.create.call_args.args[0]
    assert params == {
        "account": "acct_123",
        "refresh_url": "https://app.example.com/connect/refresh",
        "return_url": "https://app.example.com/connect/return",
        "type": "account_onboarding",
    }


def test_create_onboarding_link_validation() -> None:
    client = ConnectClient(_config(), stripe_client=MagicMock())
    with pytest.raises(OnboardingError, match="account_id"):
        client.create_onboarding_link(
            account_id="",
            refresh_url="https://example.com/r",
            return_url="https://example.com/return",
        )
    with pytest.raises(OnboardingError, match="refresh_url"):
        client.create_onboarding_link(
            account_id="acct_123",
            refresh_url=" ",
            return_url="https://example.com/return",
        )
    with pytest.raises(OnboardingError, match="return_url"):
        client.create_onboarding_link(
            account_id="acct_123",
            refresh_url="https://example.com/r",
            return_url="",
        )


def test_create_onboarding_link_wraps_stripe_error() -> None:
    stripe = MagicMock()
    stripe.v1.account_links.create.side_effect = InvalidRequestError(
        message="No such account: acct_missing",
        param="account",
        code="resource_missing",
    )
    client = ConnectClient(_config(), stripe_client=stripe)

    with pytest.raises(OnboardingError, match="No such account") as exc_info:
        client.create_onboarding_link(
            account_id="acct_missing",
            refresh_url="https://example.com/r",
            return_url="https://example.com/return",
        )
    assert exc_info.value.__cause__ is not None
    assert exc_info.value.__cause__.code == "resource_missing"
