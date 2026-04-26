-- DeptFlow SDR minimal Supabase schema.
-- Run in Supabase SQL editor if you want cloud storage.
-- The profile also works without Supabase using local JSONL fallback.

create table if not exists public.deptflow_leads (
  id uuid primary key default gen_random_uuid(),
  client_id text,
  profile_id text,
  lead_key text unique not null,
  linkedin_url text,
  full_name text,
  headline text,
  company_name text,
  location text,
  score_total int,
  tier text,
  qualified boolean default false,
  score_json jsonb,
  message_body text,
  raw_json jsonb,
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);

create index if not exists deptflow_leads_score_idx on public.deptflow_leads(score_total desc);
create index if not exists deptflow_leads_tier_idx on public.deptflow_leads(tier);
create index if not exists deptflow_leads_qualified_idx on public.deptflow_leads(qualified);
create index if not exists deptflow_leads_client_profile_idx on public.deptflow_leads(client_id, profile_id);

create table if not exists public.deptflow_runs (
  id uuid primary key default gen_random_uuid(),
  client_id text,
  profile_id text,
  release_id text,
  started_at timestamptz,
  finished_at timestamptz,
  dry_run boolean,
  discovered int,
  qualified int,
  rejected int,
  saved int,
  messages_prepared int,
  report_path text,
  errors jsonb,
  created_at timestamptz default now()
);
