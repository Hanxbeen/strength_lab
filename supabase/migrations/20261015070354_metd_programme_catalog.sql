CREATE OR REPLACE FUNCTION public.coaching_programme_catalog_v2() RETURNS jsonb
LANGUAGE sql STABLE SECURITY INVOKER SET search_path = '' AS $$
SELECT jsonb_build_object('schema_version',3,'scientific_approval',false,
 'items',coalesce(jsonb_agg(jsonb_build_object('source_id',source_id,'version',version,
 'status',status,'definition',payload) ORDER BY source_id,version),'[]'::jsonb))
FROM public.coaching_source_versions
WHERE payload->>'adapter_version' IN ('helms-2018-v1','sbd-template-v1','metd-2021-v1');
$$;
REVOKE ALL ON FUNCTION public.coaching_programme_catalog_v2() FROM PUBLIC;
GRANT EXECUTE ON FUNCTION public.coaching_programme_catalog_v2() TO anon,authenticated;
