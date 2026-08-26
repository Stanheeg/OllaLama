# Xano challenge schema

Create two Xano endpoints and map them to the environment variables in `.env.example`.

## `workflows` table
- `id` text, unique
- `vendor_name` text
- `vendor_domain` text
- `state` text
- `risk_score` integer
- `payload` json
- `updated_at` timestamp

The workflow endpoint performs an idempotent upsert by `id` and stores the current state. This is not decorative persistence: workflow resumption and the audit UI depend on it in live mode.

## `audit_events` table
- `workflow_id` text, indexed
- `event` text
- `actor` text
- `at` timestamp
- `prev_hash` text
- `event_hash` text
- `details` json

The audit endpoint rejects duplicate `event_hash` values. The chain lets a reviewer detect missing/reordered events.
