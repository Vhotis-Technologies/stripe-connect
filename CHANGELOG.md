# Changelog

All notable changes to this project are documented here.

This project follows **git tags** for app pins (`v0.1.0`, …). Prefer **additive** API changes; breaking changes bump the version and are called out explicitly.

## [0.1.0] — 2026-07-20

First public release of the app-agnostic Stripe Connect engine.

### Added

- `StripeConnectConfig` and `ConnectClient` / `create_client`
- Express connected accounts: `create_express_account`, `retrieve_account`
- Hosted Account Links: `create_onboarding_link`
- Readiness: `is_ready` — ready only when `charges_enabled` and `payouts_enabled`
- Destination charges: `create_destination_payment` (`transfer_data.destination` + `application_fee_amount`)
- Connect webhooks: `parse_webhook` with signature verify; normalizes `account.updated`
- Public types: `ConnectedAccount`, `OnboardingLink`, `Readiness`, `DestinationPayment`, `ParsedWebhookEvent`
- Errors: `AccountError`, `OnboardingError`, `PaymentError`, `WebhookError`, `WebhookSignatureError`, `StripeAPIError`, …

### Non-goals (by design)

- No Django models, product publish gates, fee percentages, or app URLs
- Not for platform Customer PaymentIntents (e.g. WMS/seller fees)

### Compatibility

- Python >= 3.11
- Depends on `stripe>=11.0.0` (tested with Stripe Python SDK 15.x `StripeClient`)

[0.1.0]: https://github.com/example/stripe-connect/releases/tag/v0.1.0
