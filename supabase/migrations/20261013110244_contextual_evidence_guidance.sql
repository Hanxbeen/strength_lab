-- Reviewed evidence summaries only; no personal workout data in this public table.
CREATE TABLE public.coaching_context_versions (
  id text NOT NULL,
  version text NOT NULL,
  payload jsonb NOT NULL,
  status text NOT NULL DEFAULT 'research_preview' CHECK (status IN ('research_preview','suspended')),
  created_at timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (id, version),
  CHECK (payload @> '{"schema_version":1,"scientific_approval":false,"review_status":"extracted_pending_independent_review"}'::jsonb),
  CHECK (jsonb_typeof(payload->'sources') = 'array'),
  CHECK (payload->>'id' = id)
);
ALTER TABLE public.coaching_context_versions ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON public.coaching_context_versions FROM anon, authenticated;
GRANT SELECT ON public.coaching_context_versions TO anon, authenticated;
CREATE POLICY context_preview_read ON public.coaching_context_versions
  FOR SELECT TO anon, authenticated USING (true);
CREATE FUNCTION public.coaching_context_catalog()
RETURNS jsonb LANGUAGE sql STABLE SECURITY INVOKER SET search_path = ''
AS $$
SELECT jsonb_build_object('schema_version',1,'items',
  coalesce(jsonb_agg(jsonb_build_object('id',id,'version',version,'status',status,'definition',payload)
    ORDER BY id,version),'[]'::jsonb))
FROM public.coaching_context_versions;
$$;
REVOKE ALL ON FUNCTION public.coaching_context_catalog() FROM PUBLIC;
GRANT EXECUTE ON FUNCTION public.coaching_context_catalog() TO anon, authenticated;
