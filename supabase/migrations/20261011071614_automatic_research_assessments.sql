-- Public summaries are distinct from executable, released prescriptions.
alter table research_internal.protocol_candidates
  drop constraint protocol_candidates_status_check;
alter table research_internal.protocol_candidates add constraint protocol_candidates_status_check
  check (status in ('awaiting_human_review','source_fetch_failed','auto_blocked'));

create table public.research_assessments (
  run_id text not null,
  pmid text not null,
  payload jsonb not null,
  primary key (run_id, pmid),
  foreign key (run_id, pmid) references research_internal.protocol_candidates(run_id, pmid),
  check ((payload->>'pmid' = pmid) is true),
  check ((payload->>'runnable' = 'false') is true),
  check ((payload->>'chart_publishable' = 'false') is true),
  check ((payload->>'decision' in ('NOT_RUNNABLE','SOURCE_ERROR')) is true),
  check ((jsonb_typeof(payload->'reasons') = 'array' and jsonb_array_length(payload->'reasons') > 0) is true),
  check (payload ?& array['pmid','title','source_url','validator_version','decision','reasons','runnable','chart_publishable'])
);
alter table public.research_assessments enable row level security;
revoke all on public.research_assessments from public, anon, authenticated;
grant select on public.research_assessments to anon, authenticated;
grant select, insert on public.research_assessments to service_role;
create policy research_assessments_read on public.research_assessments
  for select to anon, authenticated using (true);
create policy research_assessments_service on public.research_assessments
  for all to service_role using (true) with check (true);

create or replace function public.research_catalog() returns jsonb
language sql stable security invoker set search_path = '' as $$
  select jsonb_build_object(
    'schema_version', 1,
    'items', coalesce((select jsonb_agg(p.payload order by p.published_at desc,p.id,p.version)
        from public.research_protocol_versions p where p.status='PUBLISHED_PROTOCOL'),'[]'::jsonb),
    'studies', coalesce((select jsonb_agg(a.payload order by a.pmid)
        from public.research_assessments a
        join public.research_catalog_state s on s.last_batch_id=a.run_id and s.id=true),'[]'::jsonb),
    'metadata', (select jsonb_build_object('last_batch_id',s.last_batch_id,
        'checked_at',s.checked_at,'requested',s.requested,'candidates',s.candidates,
        'awaiting_review',s.awaiting_review,
        'automatically_checked',(select count(*) from public.research_assessments a where a.run_id=s.last_batch_id))
        from public.research_catalog_state s where s.id=true)
  );
$$;
revoke all on function public.research_catalog() from public;
grant execute on function public.research_catalog() to anon, authenticated, service_role;
comment on table public.research_assessments is 'Automatic source and runner compatibility results, not validated prescriptions or scientific approval.';
