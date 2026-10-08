# strength_lab Supabase connection

- Project: `strength_lab` (`gttvyfeyrnuspnnphuzk`), Seoul (`ap-northeast-2`)
- URL: `https://gttvyfeyrnuspnnphuzk.supabase.co`
- Migration: `supabase/migrations/202610090001_create_private_workout_snapshots.sql` (already applied remotely)
- `public.workout_snapshots`: owner-only RLS SELECT/INSERT/UPDATE/DELETE; security advisors returned no notices.
- Data API access requires a valid Supabase Auth session; anonymous public users cannot access records.
- Current app: local JSON + manual backup only. No automatic cloud sync or authentication yet.
- Before enabling sync: implement Apple sign-in, token/session handling, server-side compare-and-swap revision or equivalent conflict-safe writes, logout/ownership transitions, offline retry queue, cross-device conflict resolution and recovery tests. **Do not blindly upsert snapshots**: this can overwrite another device's work.
- Publishable client key is available from Supabase dashboard; never embed secret/service_role keys in mobile apps.
