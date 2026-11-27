-- Deploy only after preview_storage.sql. No public endpoint.
begin;
create function dmx_agent_private.purge_expired_previews()
returns integer
language plpgsql
security invoker
set search_path = ''
as $$
declare removed integer;
begin
  delete from dmx_agent_private.preview_requests
  where id in (
    select id from dmx_agent_private.preview_requests
    where expires_at <= now()
    order by expires_at
    limit 100
  );
  get diagnostics removed = row_count;
  return removed;
end;
$$;
revoke all on function dmx_agent_private.purge_expired_previews() from public, anon, authenticated;
create index preview_requests_expiry_idx on dmx_agent_private.preview_requests(expires_at);
commit;
-- Invoke from an authorized maintenance transaction before creating new requests.
-- Cascading foreign key removes image chunks. Expired requests must also be
-- rejected by every future upload/read endpoint, regardless of cleanup timing.
-- This is on-demand cleanup, not a guarantee of deletion at the expiry instant.
