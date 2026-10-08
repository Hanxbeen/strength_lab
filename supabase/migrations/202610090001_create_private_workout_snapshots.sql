-- Applied to project gttvyfeyrnuspnnphuzk (strength_lab), Seoul.
create table if not exists public.workout_snapshots (
 user_id uuid primary key references auth.users(id) on delete cascade,
 schema_version integer not null default 1 check (schema_version = 1),
 payload jsonb not null check (jsonb_typeof(payload) = 'object' and pg_column_size(payload) <= 20000000),
 revision bigint not null default 1 check (revision > 0),
 updated_at timestamptz not null default now()
);
alter table public.workout_snapshots enable row level security;
revoke all on public.workout_snapshots from anon;
grant select, insert, update, delete on public.workout_snapshots to authenticated;
create policy owner_select on public.workout_snapshots for select to authenticated using ((select auth.uid()) = user_id);
create policy owner_insert on public.workout_snapshots for insert to authenticated with check ((select auth.uid()) = user_id);
create policy owner_update on public.workout_snapshots for update to authenticated using ((select auth.uid()) = user_id) with check ((select auth.uid()) = user_id);
create policy owner_delete on public.workout_snapshots for delete to authenticated using ((select auth.uid()) = user_id);
create index workout_snapshots_updated_at_idx on public.workout_snapshots (updated_at desc);
comment on table public.workout_snapshots is 'Private per-user snapshot; conflict resolution is required before enabling sync.';
