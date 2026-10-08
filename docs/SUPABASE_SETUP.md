# strength_lab Supabase connection

- Project: `strength_lab` (`gttvyfeyrnuspnnphuzk`), Seoul (`ap-northeast-2`)
- URL: `https://gttvyfeyrnuspnnphuzk.supabase.co`
- Migration: `supabase/migrations/202610090001_create_private_workout_snapshots.sql` (already applied remotely)
- `public.workout_snapshots`: owner-only RLS SELECT/INSERT/UPDATE/DELETE; security advisors returned no notices.
- Data API access requires a valid Supabase Auth session; anonymous public users cannot access records.
- Current app: local JSON + manual backup only. No automatic cloud sync or authentication yet.
- Before enabling sync: implement Apple sign-in, token/session handling, server-side compare-and-swap revision or equivalent conflict-safe writes, logout/ownership transitions, offline retry queue, cross-device conflict resolution and recovery tests. **Do not blindly upsert snapshots**: this can overwrite another device's work.
- Publishable client key is available from Supabase dashboard; never embed secret/service_role keys in mobile apps.

## Conflict-safe RPC (applied)
- `public.save_workout_snapshot(expected_revision, next_payload)` creates only when absent, otherwise updates only matching revision.
- Direct client INSERT/UPDATE/DELETE grants revoked. Owner-only SELECT RLS remains.
- `CloudTransport.swift` is a typed Swift URLSession transport (read and CAS write). It is not yet invoked by the app: auth and cross-device merge UX are prerequisites.

## iOS account connection (implemented locally, not device verified)
- `CloudAuth.swift`: native Sign in with Apple, hashed nonce and token exchange, Keychain session storage, refresh-token support.
- `CloudAccountView.swift`: explicit first upload (create-only), server snapshot preview, restore **only if local database is empty**. No automatic upload, merge or overwrite.
- Apple sign-in capability declared in `MugeMuge.entitlements`. Xcode signing must use a provisioning profile supporting this capability.
- Configure Apple provider in Supabase Auth providers and Apple Developer App ID / bundle ID (`app.mugemuge.ios`) before attempting device login.
- **Do not interpret unsigned build success as functional Apple login or Supabase roundtrip testing.** Apple Developer provisioning and iOS 26-capable Xcode remain blockers.
- Cloud login does not yet imply background sync. A multi-device merge strategy, per-account local partitioning, revision persistence and signed-in integration tests are still required before enabling ongoing synchronization.

## Manual incremental upload (development build)
- After first upload or restore, client records local account owner, last cloud revision and last local snapshot digest in UserDefaults.
- Explicit update action only appears when local data changed. The server RPC atomically compares revision before writing; any conflict leaves local data intact.
- Switching to a different signed-in account blocks upload/restore of locally bound data. **This is a guard, not full per-account local storage isolation**; local JSON is still shared by the app installation.
- This is manual revision-based upload, **not** automatic bidirectional synchronization or conflict merging. A production-grade sync journal, ownership migration and integration tests remain pending.
