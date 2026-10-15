-- Keep the original Helms-only RPC compatible with existing backend deployments.
CREATE OR REPLACE FUNCTION public.coaching_source_catalog() RETURNS jsonb
LANGUAGE sql STABLE SECURITY INVOKER SET search_path = '' AS $$
SELECT jsonb_build_object('schema_version',3,'scientific_approval',false,
 'items',coalesce(jsonb_agg(jsonb_build_object('source_id',source_id,'version',version,
 'status',status,'definition',payload) ORDER BY source_id,version),'[]'::jsonb))
FROM public.coaching_source_versions WHERE payload->>'adapter_version'='helms-2018-v1';
$$;
CREATE OR REPLACE FUNCTION public.coaching_programme_catalog() RETURNS jsonb
LANGUAGE sql STABLE SECURITY INVOKER SET search_path = '' AS $$
SELECT jsonb_build_object('schema_version',3,'scientific_approval',false,
 'items',coalesce(jsonb_agg(jsonb_build_object('source_id',source_id,'version',version,
 'status',status,'definition',payload) ORDER BY source_id,version),'[]'::jsonb))
FROM public.coaching_source_versions
WHERE payload->>'adapter_version' IN ('helms-2018-v1','sbd-template-v1');
$$;
REVOKE ALL ON FUNCTION public.coaching_programme_catalog() FROM PUBLIC;
GRANT EXECUTE ON FUNCTION public.coaching_programme_catalog() TO anon,authenticated;
