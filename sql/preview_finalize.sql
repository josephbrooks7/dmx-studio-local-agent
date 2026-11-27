begin;
create function public.dmx_finish_preview(p_key text,p_id uuid)
returns boolean language plpgsql security definer set search_path = '' as $$
declare r dmx_agent_private.preview_requests%rowtype;
declare image bytea;
declare n bigint;
begin
 if p_key is null or p_key !~ '^[0-9a-f]{64}$' then return false; end if;
 select q.* into r from dmx_agent_private.preview_requests q
 join dmx_agent_private.devices d on d.fingerprint=q.fingerprint
 where q.id=p_id and d.enabled and d.fingerprint=encode(extensions.digest(p_key,'sha256'),'hex')
 and q.expires_at>now() and q.image_bytes is not null and q.sha256 is not null
 for update of q;
 if not found then return false; end if;
 if r.finished_at is not null then return true; end if;
 select count(*), string_agg(payload, ''::bytea order by chunk_index)
 into n,image from dmx_agent_private.preview_chunks where request_id=p_id;
 if n <> (r.image_bytes+3071)/3072 or image is null or octet_length(image) <> r.image_bytes
 or encode(extensions.digest(image,'sha256'),'hex') <> r.sha256
 or substring(image from 1 for 16) <> decode('89504e470d0a1a0a0000000d49484452','hex')
 then return false; end if;
 update dmx_agent_private.preview_requests set finished_at=now() where id=p_id;
 return true;
end;
$$;
revoke all on function public.dmx_finish_preview(text,uuid) from public,anon,authenticated;
commit;
-- No client grants until end-to-end authorization and quota tests pass.
