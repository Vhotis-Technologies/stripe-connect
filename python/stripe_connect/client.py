"""ConnectClient — single entrypoint for the v0.1 Stripe Connect engine."""

from __future__ import annotations

from typing import TYPE_CHECKING, Mapping

from stripe_connect import accounts, onboarding, payments, readiness, webhooks
from stripe_connect._stripe import build_stripe_client
from stripe_connect.config import StripeConnectConfig
from stripe_connect.errors import ConfigurationError
from stripe_connect.types import (
    ConnectedAccount,
    DestinationPayment,
    OnboardingLink,
    ParsedWebhookEvent,
    Readiness,
)

if TYPE_CHECKING:
    from stripe import StripeClient


class ConnectClient:
    """Thin façade over Connect account, onboarding, payment, and webhook ops.

    Construct once per Stripe platform account (typically via DI / settings)
    and inject into app adapters. This client holds credentials only — no
    Django models, URLs, or fee tables.
    """

    def __init__(
        self,
        config: StripeConnectConfig,
        *,
        stripe_client: StripeClient | None = None,
    ) -> None:
        if not isinstance(config, StripeConnectConfig):
            raise ConfigurationError("config must be a StripeConnectConfig instance")
        self.config = config
        self._stripe = stripe_client if stripe_client is not None else build_stripe_client(config)

    @property
    def stripe(self) -> StripeClient:
        """Underlying Stripe SDK client (for internal modules and tests)."""
        return self._stripe

    # --- Accounts ---------------------------------------------------------

    def create_express_account(
        self,
        *,
        email: str,
        country: str,
        metadata: Mapping[str, str],
        business_type: str | None = None,
        capabilities: Mapping[str, Mapping[str, bool]] | None = None,
    ) -> ConnectedAccount:
        return accounts.create_express_account(
            self,
            email=email,
            country=country,
            metadata=metadata,
            business_type=business_type,
            capabilities=capabilities,
        )

    def retrieve_account(self, account_id: str) -> ConnectedAccount:
        return accounts.retrieve_account(self, account_id)

    def is_ready(self, account_id: str) -> Readiness:
        """Retrieve the account and return a readiness snapshot."""
        account = self.retrieve_account(account_id)
        return readiness.from_account(account)

    # --- Onboarding -------------------------------------------------------

    def create_onboarding_link(
        self,
        *,
        account_id: str,
        refresh_url: str,
        return_url: str,
        type: str = "account_onboarding",
    ) -> OnboardingLink:
        return onboarding.create_onboarding_link(
            self,
            account_id=account_id,
            refresh_url=refresh_url,
            return_url=return_url,
            type=type,
        )

    # --- Payments ---------------------------------------------------------

    def create_destination_payment(
        self,
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
        return payments.create_destination_payment(
            self,
            amount_cents=amount_cents,
            currency=currency,
            connected_account_id=connected_account_id,
            application_fee_cents=application_fee_cents,
            metadata=metadata,
            customer=customer,
            payment_method=payment_method,
            confirm=confirm,
            capture_method=capture_method,
            idempotency_key=idempotency_key,
            statement_descriptor_suffix=statement_descriptor_suffix,
            transfer_group=transfer_group,
        )

    # --- Webhooks ---------------------------------------------------------

    def parse_webhook(
        self,
        payload: bytes | str,
        sig_header: str,
    ) -> ParsedWebhookEvent:
        return webhooks.parse_webhook(self, payload, sig_header)


def create_client(config: StripeConnectConfig) -> ConnectClient:
    """Factory for :class:`ConnectClient`."""
    return ConnectClient(config)
