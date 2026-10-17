-- Preserve all existing RPCs. Product prototypes are not relabeled source extracts.
ALTER TABLE public.coaching_source_versions
  DROP CONSTRAINT coaching_source_versions_payload_check;
ALTER TABLE public.coaching_source_versions
  ADD CONSTRAINT coaching_source_versions_payload_check CHECK (coalesce(
    payload->>'review_status' = 'source_extracted' OR (
      source_id = 'novice-sbd-choice-v1'
      AND payload->>'id' = source_id
      AND payload->>'adapter_version' = 'novice-sbd-choice-v1'
      AND payload->>'review_status' = 'internal_product_prototype'
      AND payload->>'publication_status' = 'internal_preview'
      AND payload->'scientific_approval' = 'false'::jsonb
    ), false));

CREATE FUNCTION public.coaching_programme_catalog_v3() RETURNS jsonb
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
