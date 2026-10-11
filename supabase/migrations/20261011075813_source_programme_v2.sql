-- Source templates are a distinct API contract, not v1 scientific approvals.
create table public.source_programme_versions (
 id text not null,
 version text not null check (version ~ '^[a-f0-9]{64}$'),
 payload jsonb not null,
 created_at timestamptz not null default now(),
 primary key (id,version),
 check ((payload->>'programme_id'=id) is true),
 check ((payload->>'programme_version'=version) is true),
 check ((payload->>'schema_version'='2') is true),
 check ((payload->>'scientific_approval'='false') is true),
 check ((payload->>'evidence_status'='SOURCE_STRUCTURED') is true),
 check ((payload->>'readiness'='REQUIRES_EXPLICIT_SETUP') is true)
);
create table public.source_programme_editions (
 id text primary key check (id ~ '^[a-f0-9]{64}$'),
 members jsonb not null check (jsonb_typeof(members)='array' and jsonb_array_length(members)>0),
 created_at timestamptz not null default now()
);
create table public.source_programme_state (
 id boolean primary key default true check (id=true),
 edition_id text not null references public.source_programme_editions(id)
);
create index source_programme_state_edition_idx on public.source_programme_state(edition_id);
alter table public.source_programme_versions enable row level security;
alter table public.source_programme_editions enable row level security;
alter table public.source_programme_state enable row level security;
revoke all on public.source_programme_versions,public.source_programme_editions,public.source_programme_state from public,anon,authenticated;
grant select on public.source_programme_versions,public.source_programme_editions,public.source_programme_state to anon,authenticated;
grant select,insert on public.source_programme_versions,public.source_programme_editions to service_role;
grant select,insert,update on public.source_programme_state to service_role;
create policy source_v2_read on public.source_programme_versions for select to anon,authenticated using (true);
create policy source_editions_read on public.source_programme_editions for select to anon,authenticated using (true);
create policy source_state_read on public.source_programme_state for select to anon,authenticated using (true);
create policy source_v2_service on public.source_programme_versions for all to service_role using (true) with check (true);
create policy source_editions_service on public.source_programme_editions for all to service_role using (true) with check (true);
create policy source_state_service on public.source_programme_state for all to service_role using (true) with check (true);
create function public.source_programme_catalog() returns jsonb
language sql stable security invoker set search_path='' as $$
 select jsonb_build_object('schema_version',2,'items',coalesce((
   select jsonb_agg(v.payload order by v.id)
   from public.source_programme_state s
   join public.source_programme_editions e on e.id=s.edition_id
   cross join lateral jsonb_array_elements(e.members) m
   join public.source_programme_versions v on v.id=m->>'id' and v.version=m->>'version'
   where s.id=true),'[]'::jsonb),
   'edition_id',(select edition_id from public.source_programme_state where id=true));
$$;
revoke all on function public.source_programme_catalog() from public;
grant execute on function public.source_programme_catalog() to anon,authenticated,service_role;
