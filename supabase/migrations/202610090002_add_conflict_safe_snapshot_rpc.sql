-- Applied remotely to strength_lab. No direct authenticated write grants remain.
create or replace function public.save_workout_snapshot(expected_revision bigint, next_payload jsonb)
returns bigint language plpgsql security invoker set search_path = '' as $$
declare next_revision bigint;
begin
 if (select auth.uid()) is null then raise exception 'Authentication required' using errcode='28000'; end if;
 if next_payload is null or jsonb_typeof(next_payload) <> 'object'
    or pg_column_size(next_payload) > 20000000
    or next_payload->>'schemaVersion' <> '1' then
    raise exception 'Invalid snapshot' using errcode='22023';
 end if;
 if expected_revision is null then
   insert into public.workout_snapshots(user_id,schema_version,payload,revision,updated_at)
   values ((select auth.uid()),1,next_payload,1,now())
   on conflict (user_id) do nothing returning revision into next_revision;
 elsif expected_revision > 0 then
   update public.workout_snapshots
      set payload=next_payload, revision=revision+1, updated_at=now()
    where user_id=(select auth.uid()) and revision=expected_revision
    returning revision into next_revision;
 else
   raise exception 'Invalid revision' using errcode='22023';
 end if;
 if next_revision is null then raise exception 'Snapshot conflict; refresh before retry' using errcode='40001'; end if;
 return next_revision;
end $$;
revoke all on function public.save_workout_snapshot(bigint,jsonb) from public,anon;
grant execute on function public.save_workout_snapshot(bigint,jsonb) to authenticated;
revoke insert,update,delete on public.workout_snapshots from authenticated;
drop policy if exists owner_insert on public.workout_snapshots;
drop policy if exists owner_update on public.workout_snapshots;
drop policy if exists owner_delete on public.workout_snapshots;
