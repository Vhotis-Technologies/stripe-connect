# stripe-connect

App-agnostic **Stripe Connect engine** for marketplaces and remittance products.

Create Express connected accounts, hosted Account Links, readiness checks, destination charges with application fees, and verified Connect webhooks — without Django models, product publish rules, or app-specific fee tables.

Apps (Vhotis, proptech, etc.) stay thin adapters: they store `acct_...` + status on their own merchant models, call this package, and enforce domain rules (e.g. listings go live only when Connect is ready).

**Status:** `v0.1.0` — Express accounts, Account Links, readiness, destination charges, and Connect webhook parse/verify. Pin apps to the git tag.

---

## Install (Option B — git tag pin)

Pin apps to a **git tag**, not `main`:

```toml
# pyproject.toml / requirements
stripe-connect = { git = "ssh://git@github.com/Vhotis-Technologies/stripe-connect.git", tag = "v0.1.0" }
```

```bash
pip install "stripe-connect @ git+ssh://git@github.com/Vhotis-Technologies/stripe-connect.git@v0.1.0"
```

Local development:

```bash
pip install -e ".[dev]"
pytest
```

See [CHANGELOG.md](CHANGELOG.md) for release notes.

---

## Architecture

```text
App (models, publish gate, routes, UI)
  → imports →
stripe-connect (this package)
  → Stripe API
```

| In package | Out of package (app-owned) |
|------------|----------------------------|
| Express account create/retrieve | Django / ORM models |
| Account Links (hosted) | Refresh / return URLs |
| Readiness (`charges_enabled` ∧ `payouts_enabled`) | Publish / listing gates |
| Destination PI + `application_fee_amount` | Fee % (e.g. 2.5%) and rounding |
| Webhook verify + normalize | Webhook HTTP endpoint + idempotency store |
| | WMS / seller-as-customer PaymentIntents |

---

## Defaults (v0.1)

| Decision | Choice |
|----------|--------|
| Account type | Express |
| Charge model | Destination charges + `application_fee_amount` |
| Onboarding | Hosted Account Links |
| Readiness | `charges_enabled` **and** `payouts_enabled` |
| Fee ownership | App computes `application_fee_cents` |

---

## Quickstart

```python
from stripe_connect import ConnectClient, StripeConnectConfig, create_client

config = StripeConnectConfig(
    secret_key="sk_test_...",
    webhook_secret="whsec_...",
    api_version=None,       # or pin e.g. "2025-01-27.acacia"
    default_country="GB",
)
client: ConnectClient = create_client(config)

account = client.create_express_account(
    email="seller@example.com",
    country="GB",
    metadata={"app": "vhotis", "entity_type": "seller", "entity_id": "42"},
)
link = client.create_onboarding_link(
    account_id=account.id,
    refresh_url="https://app.example.com/connect/refresh",
    return_url="https://app.example.com/connect/return",
)
readiness = client.is_ready(account.id)
# readiness.is_ready  # True only when charges_enabled and payouts_enabled

# Phase 3+
payment = client.create_destination_payment(
    amount_cents=10_000,
    currency="gbp",
    connected_account_id=account.id,
    application_fee_cents=250,  # app-computed 2.5%
    metadata={"order_id": "1001"},
    idempotency_key="order-1001",
)
event = client.parse_webhook(payload, sig_header)
```

---

## v0.1 public API

### Config / client

- `StripeConnectConfig(secret_key, webhook_secret, api_version=None, default_country="GB")`
- `create_client(config) -> ConnectClient`
- `ConnectClient` methods below

### Accounts & readiness

```python
client.create_express_account(*, email, country, metadata, business_type=None, capabilities=None)
client.retrieve_account(account_id)
client.is_ready(account_id) -> Readiness
```

**Readiness rule:** `is_ready = charges_enabled and payouts_enabled`.

`Readiness.status` is one of `pending` | `restricted` | `ready`.  
`not_started` is **app-only** (no `acct_` yet); the package never emits it.

### Onboarding

```python
client.create_onboarding_link(*, account_id, refresh_url, return_url, type="account_onboarding")
```

### Payments

```python
client.create_destination_payment(
    *,
    amount_cents,
    currency,
    connected_account_id,
    application_fee_cents,  # precomputed by the app
    metadata=None,
    customer=None,
    payment_method=None,
    confirm=False,
    capture_method="automatic",
    idempotency_key=None,
    statement_descriptor_suffix=None,
    transfer_group=None,
)
```

Creates a **platform** PaymentIntent with:

- `transfer_data={"destination": connected_account_id}`
- `application_fee_amount=application_fee_cents`

Does **not** set `on_behalf_of` (destination charges, not direct charges).

### Webhooks

```python
client.parse_webhook(payload, sig_header) -> ParsedWebhookEvent
```

v0.1 normalizes at least `account.updated`. Other types return `WebhookEventType.UNKNOWN` with `data=None` and the raw Stripe payload.

---

## Types

- `ConnectedAccount`, `OnboardingLink`, `Readiness`, `DestinationPayment`, `ParsedWebhookEvent`
- `AccountCapabilityState`, `WebhookEventType`

## Errors

- `StripeConnectError` (base)
- `ConfigurationError`, `AccountError`, `OnboardingError`, `PaymentError`
- `WebhookError`, `WebhookSignatureError`, `UnsupportedEventError`
- `StripeAPIError` (normalized SDK / API failure)

---

## Stripe Dashboard setup (per app / environment)

Do this in **each** platform Stripe account (Vhotis test, Vhotis live, proptech, …):

1. **Enable Connect** and choose **Express** connected accounts.
2. Configure Connect **branding** / platform profile as required by Stripe.
3. Create a **Connect webhook** endpoint (platform Connect events), not only account webhooks:
   - URL: your app route (e.g. `/webhooks/stripe/connect/`)
   - Events: at least `account.updated` (add more later as needed)
   - Copy the endpoint **signing secret** → `StripeConnectConfig.webhook_secret`
4. Use the platform **secret key** → `StripeConnectConfig.secret_key` (`sk_test_…` / `sk_live_…`).
5. Keep buyer/WMS PaymentIntent webhooks on a **separate** endpoint/secret if they already exist.
6. Test mode first: complete Express onboarding with test data, confirm `charges_enabled` + `payouts_enabled`, then a destination PaymentIntent.

Optional: pin `api_version` on `StripeConnectConfig` so apps do not drift with the Stripe account default.

---

## App adapter checklist (not in this package)

1. Store on seller/payee: `stripe_connect_account_id`, `stripe_connect_status`, `charges_enabled`, `payouts_enabled`, `details_submitted`, `stripe_connect_updated_at`
2. `start_onboarding` → create account if missing → Account Link with **app** URLs
3. Webhook endpoint → `parse_webhook` → update flags; readiness SoT = Stripe flags
4. Publish / listing gate → block go-live unless status `ready`
5. Checkout / rent remittance → compute fee cents → `create_destination_payment`
6. Keep existing non-Connect Customer PaymentIntents (e.g. WMS fees) separate

---

## Versioning

- Apps pin **git tags** (`v0.1.0`, …), not `main`
- Prefer **additive** API changes (new methods / optional kwargs)
- Breaking changes are called out in [CHANGELOG.md](CHANGELOG.md)

---

## Phases

| Phase | Scope |
|-------|--------|
| **1** | Repo, types, errors, config, client façade, contract/readiness tests |
| **2** | Express accounts, Account Links, retrieve, readiness via Stripe |
| **3** | Destination payments, webhook verify/parse |
| **4** (done) | Harden, changelog, tag `v0.1.0` |
| **5** | App adapters (Vhotis, then proptech) — outside this repo |

---

## Development

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
pip install -e ".[dev]"
pytest
```

Requires Python **3.11+**.
