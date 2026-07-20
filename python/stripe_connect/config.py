"""Configuration for the Stripe Connect engine."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class StripeConnectConfig:
    """Platform credentials and Stripe API options.

    Application-specific values (URLs, fee percentages, model IDs) must not
    live here — pass them at the call site in each app adapter.
    """

    secret_key: str
    webhook_secret: str
    api_version: str | None = None
    default_country: str = "GB"

    def __post_init__(self) -> None:
        if not self.secret_key:
            raise ValueError("secret_key must be a non-empty string")
        if not self.webhook_secret:
            raise ValueError("webhook_secret must be a non-empty string")
        if not self.default_country or len(self.default_country) != 2:
            raise ValueError("default_country must be a 2-letter ISO country code")
