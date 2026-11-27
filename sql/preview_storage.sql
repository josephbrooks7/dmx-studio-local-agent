-- Review before deployment. No client-facing RPC or grants.
begin;
create table dmx_agent_private.preview_requests (
 id uuid primary key default gen_random_uuid(),
 fingerprint text not null references dmx_agent_private.devices(fingerprint),
 character text not null check (character in ('male','female')),
 created_at timestamptz not null default now(),
 expires_at timestamptz not null default (now() + interval '15 minutes'),
 image_bytes integer check (image_bytes between 1 and 4194304),
 sha256 text check (sha256 ~ '^[0-9a-f]{64}$'),
 build text check (length(build) <= 64),
 finished_at timestamptz,
 check (expires_at > created_at and expires_at <= created_at + interval '15 minutes')
);
create table dmx_agent_private.preview_chunks (
 request_id uuid not null references dmx_agent_private.preview_requests(id) on delete cascade,
 chunk_index integer not null check (chunk_index between 0 and 1365),
 payload bytea not null check (octet_length(payload) between 1 and 3072),
 primary key (request_id, chunk_index)
);
alter table dmx_agent_private.preview_requests enable row level security;
alter table dmx_agent_private.preview_chunks enable row level security;
revoke all on dmx_agent_private.preview_requests, dmx_agent_private.preview_chunks from public, anon, authenticated;
commit;
-- Expiry cleanup must be scheduled before enabling uploads.
