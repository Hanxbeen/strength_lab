-- Evidence candidates stay private. Research previews are not approved prescriptions.
CREATE TABLE research_internal.coaching_search_runs (
 id text PRIMARY KEY, payload jsonb NOT NULL, created_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE research_internal.coaching_report_versions (
 report_id text NOT NULL, version text NOT NULL, payload jsonb NOT NULL,
 PRIMARY KEY(report_id,version)
);
ALTER TABLE research_internal.coaching_search_runs ENABLE ROW LEVEL SECURITY;
ALTER TABLE research_internal.coaching_report_versions ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON research_internal.coaching_search_runs, research_internal.coaching_report_versions FROM anon, authenticated;
CREATE TABLE public.coaching_source_versions (
 source_id text NOT NULL, version text NOT NULL, payload jsonb NOT NULL,
 status text NOT NULL DEFAULT 'research_preview' CHECK(status IN ('research_preview','suspended')),
 PRIMARY KEY(source_id,version),
 CHECK(payload->>'review_status' = 'source_extracted'),
 CHECK(payload->'scientific_approval' = 'false'::jsonb)
);
ALTER TABLE public.coaching_source_versions ENABLE ROW LEVEL SECURITY;
GRANT SELECT ON public.coaching_source_versions TO anon, authenticated;
REVOKE INSERT, UPDATE, DELETE ON public.coaching_source_versions FROM anon, authenticated;
CREATE POLICY coaching_preview_read ON public.coaching_source_versions FOR SELECT TO anon, authenticated USING (true);
CREATE FUNCTION public.coaching_source_catalog() RETURNS jsonb
LANGUAGE sql STABLE SECURITY INVOKER SET search_path = ''
AS $$
 SELECT jsonb_build_object('schema_version',3,'scientific_approval',false,
   'items',coalesce(jsonb_agg(jsonb_build_object('source_id',source_id,'version',version,
                   'status',status,'definition',payload) ORDER BY source_id,version),'[]'::jsonb))
 FROM public.coaching_source_versions;
$$;
REVOKE ALL ON FUNCTION public.coaching_source_catalog() FROM PUBLIC;
GRANT EXECUTE ON FUNCTION public.coaching_source_catalog() TO anon, authenticated;
