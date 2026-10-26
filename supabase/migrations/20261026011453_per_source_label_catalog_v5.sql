-- Additive catalogue boundary: old v3/v4 readers never receive the new adapter.
CREATE OR REPLACE FUNCTION public.coaching_programme_catalog_v5() RETURNS jsonb
LANGUAGE sql STABLE SECURITY INVOKER SET search_path = '' AS $$
SELECT jsonb_build_object('schema_version',3,'catalog_revision',5,'scientific_approval',false,
 'items',coalesce(jsonb_agg(jsonb_build_object('source_id',source_id,'version',version,
 'status',status,'definition',payload) ORDER BY source_id,version),'[]'::jsonb))
FROM public.coaching_source_versions
WHERE payload->>'adapter_version' IN
 ('helms-2018-v1','sbd-template-v1','metd-2021-v1','novice-sbd-choice-v1','petrizzo-2018-v1','per-source-labels-v1');
$$;
REVOKE ALL ON FUNCTION public.coaching_programme_catalog_v5() FROM PUBLIC;
GRANT EXECUTE ON FUNCTION public.coaching_programme_catalog_v5() TO anon,authenticated;
