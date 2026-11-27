begin;
create function public.dmx_poll_previews(p_key text)
returns jsonb language plpgsql security definer set search_path = '' as $$
declare requests jsonb;
begin
 if p_key is null or p_key !~ '^[0-9a-f]{64}$' then return '[]'::jsonb; end if;
 select coalesce(jsonb_agg(jsonb_build_object('id',q.id,'character',q.character,'created_at',q.created_at,'expires_at',q.expires_at) order by q.created_at),'[]'::jsonb)
 into requests from (
 select r.id,r.character,r.created_at,r.expires_at
 from dmx_agent_private.preview_requests r
 join dmx_agent_private.devices d on d.fingerprint=r.fingerprint
 where d.enabled and d.fingerprint=encode(extensions.digest(p_key,'sha256'),'hex')
 and r.expires_at>now() and r.finished_at is null
 order by r.created_at limit 2
 ) q;
 return requests;
end;
$$;
revoke all on function public.dmx_poll_previews(text) from public,anon,authenticated;
commit;
-- Keep disabled until authorization tests, local opt-in and client integration pass.
