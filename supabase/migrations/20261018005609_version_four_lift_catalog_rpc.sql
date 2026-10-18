-- Restore v3 adapter boundary for deployed older readers; v4 keeps the v3 envelope.
-- Add four-lift source structures; preserve legacy versions and access policy.
CREATE OR REPLACE FUNCTION public.coaching_programme_catalog_v3() RETURNS jsonb
LANGUAGE sql STABLE SECURITY INVOKER SET search_path = '' AS $$
SELECT jsonb_build_object('schema_version',3,'scientific_approval',false,
 'items',coalesce(jsonb_agg(jsonb_build_object('source_id',source_id,'version',version,
 'status',status,'definition',payload) ORDER BY source_id,version),'[]'::jsonb))
FROM public.coaching_source_versions
WHERE payload->>'adapter_version' IN
 ('helms-2018-v1','sbd-template-v1','metd-2021-v1','novice-sbd-choice-v1');
$$;
REVOKE ALL ON FUNCTION public.coaching_programme_catalog_v3() FROM PUBLIC;
GRANT EXECUTE ON FUNCTION public.coaching_programme_catalog_v3() TO anon,authenticated;

-- Add four-lift source structures; preserve legacy versions and access policy.
CREATE OR REPLACE FUNCTION public.coaching_programme_catalog_v4() RETURNS jsonb
LANGUAGE sql STABLE SECURITY INVOKER SET search_path = '' AS $$
SELECT jsonb_build_object('schema_version',3,'catalog_revision',4,'scientific_approval',false,
 'items',coalesce(jsonb_agg(jsonb_build_object('source_id',source_id,'version',version,
 'status',status,'definition',payload) ORDER BY source_id,version),'[]'::jsonb))
FROM public.coaching_source_versions
WHERE payload->>'adapter_version' IN
 ('helms-2018-v1','sbd-template-v1','metd-2021-v1','novice-sbd-choice-v1','petrizzo-2018-v1');
$$;
REVOKE ALL ON FUNCTION public.coaching_programme_catalog_v4() FROM PUBLIC;
GRANT EXECUTE ON FUNCTION public.coaching_programme_catalog_v4() TO anon,authenticated;
