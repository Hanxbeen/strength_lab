create index research_catalog_last_batch_idx on public.research_catalog_state(last_batch_id);

-- Private jobs only; public clients have neither schema usage nor table grants.
create policy internal_batch_job on research_internal.batch_runs for all to service_role using (true) with check (true);
create policy internal_paper_job on research_internal.papers for all to service_role using (true) with check (true);
create policy internal_candidate_job on research_internal.protocol_candidates for all to service_role using (true) with check (true);

alter table public.research_protocol_versions add constraint nonnull_catalog_payload
check (jsonb_typeof(payload) = 'object' and jsonb_strip_nulls(payload) ?&
array['id','version','source_type','source_sha256','release_id','status','runnable','sessions','title','description']);

create function research_internal.protect_released_version() returns trigger
language plpgsql security invoker set search_path = '' as $$
begin
  if (to_jsonb(new) - 'status') is distinct from (to_jsonb(old) - 'status') then
    raise exception 'Published content is immutable; create a new reviewed version';
  end if;
  if old.status = 'REVOKED' and new.status <> old.status then
    raise exception 'A revoked version cannot be silently republished';
  end if;
  return new;
end;
$$;
revoke all on function research_internal.protect_released_version() from public, anon, authenticated;
grant execute on function research_internal.protect_released_version() to service_role;
create trigger protect_released_version before update on public.research_protocol_versions
for each row execute function research_internal.protect_released_version();
