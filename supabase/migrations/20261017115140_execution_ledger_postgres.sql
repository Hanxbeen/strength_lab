-- Server-only execution ledger; never expose this schema through the Data API.
CREATE SCHEMA execution_private;
REVOKE ALL ON SCHEMA execution_private FROM PUBLIC, anon;
GRANT USAGE ON SCHEMA execution_private TO authenticated;
CREATE TABLE execution_private.execution_maxes (
 owner uuid NOT NULL, id text NOT NULL, payload text NOT NULL,
 PRIMARY KEY(owner,id), CHECK(jsonb_typeof(payload::jsonb)='object'));
CREATE TABLE execution_private.execution_workouts (
 owner uuid NOT NULL, id text NOT NULL, snapshot text NOT NULL, events text NOT NULL,
 revision integer NOT NULL CHECK(revision>=0), PRIMARY KEY(owner,id),
 CHECK(jsonb_typeof(snapshot::jsonb)='object'), CHECK(jsonb_typeof(events::jsonb)='array'));
CREATE TABLE execution_private.coaching_instances (
 owner uuid NOT NULL,id text NOT NULL,payload text NOT NULL,PRIMARY KEY(owner,id),
 CHECK(jsonb_typeof(payload::jsonb)='object'));
CREATE TABLE execution_private.coaching_sessions (
 owner uuid NOT NULL,instance_id text NOT NULL,week integer NOT NULL CHECK(week>0),
 day integer NOT NULL CHECK(day>0),workout_id text NOT NULL,
 PRIMARY KEY(owner,instance_id,week,day),UNIQUE(owner,workout_id),
 FOREIGN KEY(owner,instance_id) REFERENCES execution_private.coaching_instances(owner,id),
 FOREIGN KEY(owner,workout_id) REFERENCES execution_private.execution_workouts(owner,id));
CREATE TABLE execution_private.coaching_evaluations (
 owner uuid NOT NULL,instance_id text NOT NULL,id text NOT NULL,
 revision integer NOT NULL CHECK(revision>0),fingerprint text NOT NULL,payload text NOT NULL,at text NOT NULL,
 PRIMARY KEY(owner,instance_id,id),UNIQUE(owner,instance_id,revision),
 FOREIGN KEY(owner,instance_id) REFERENCES execution_private.coaching_instances(owner,id),
 CHECK(jsonb_typeof(payload::jsonb)='object'));
DO $migration$
DECLARE t text;
BEGIN
 FOREACH t IN ARRAY ARRAY['execution_maxes','execution_workouts','coaching_instances','coaching_sessions','coaching_evaluations']
 LOOP
  EXECUTE format('ALTER TABLE execution_private.%I ENABLE ROW LEVEL SECURITY',t);
  EXECUTE format('ALTER TABLE execution_private.%I FORCE ROW LEVEL SECURITY',t);
  EXECUTE format('REVOKE ALL ON execution_private.%I FROM PUBLIC, anon, authenticated',t);
  EXECUTE format('GRANT SELECT, INSERT, UPDATE ON execution_private.%I TO authenticated',t);
  EXECUTE format('CREATE POLICY owner_read ON execution_private.%I FOR SELECT TO authenticated USING ((select auth.uid())=owner)',t);
  EXECUTE format('CREATE POLICY owner_insert ON execution_private.%I FOR INSERT TO authenticated WITH CHECK ((select auth.uid())=owner)',t);
  EXECUTE format('CREATE POLICY owner_update ON execution_private.%I FOR UPDATE TO authenticated USING ((select auth.uid())=owner) WITH CHECK ((select auth.uid())=owner)',t);
 END LOOP;
END $migration$;
