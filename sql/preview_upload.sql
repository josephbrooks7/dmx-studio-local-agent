-- Review and test before deployment; no client grants yet.
begin;
create function public.dmx_upload_preview_chunk(p_key text,p_id uuid,p_index integer,p_payload text)
returns boolean language plpgsql security definer set search_path = '' as $$
declare r dmx_agent_private.preview_requests%rowtype;
declare chunk bytea;
begin
 if p_key is null or p_key !~ '^[0-9a-f]{64}$' or p_index is null or p_index not between 0 and 1365 or p_payload is null or length(p_payload) not between 4 and 4096 then return false; end if;
 select q.* into r from dmx_agent_private.preview_requests q
 join dmx_agent_private.devices d on d.fingerprint=q.fingerprint
 where q.id=p_id and d.enabled and d.fingerprint=encode(extensions.digest(p_key,'sha256'),'hex')
 and q.expires_at>now() and q.finished_at is null and q.image_bytes is not null
 for update of q;
 if not found then return false; end if;
 if p_index*3072 >= r.image_bytes then return false; end if;
 begin
 chunk := decode(p_payload,'base64');
 exception when invalid_parameter_value then return false;
 end;
 if octet_length(chunk) <> least(3072,r.image_bytes-p_index*3072) then return false; end if;
 insert into dmx_agent_private.preview_chunks(request_id,chunk_index,payload)
 values(p_id,p_index,chunk) on conflict do nothing;
 return exists(select 1 from dmx_agent_private.preview_chunks c where c.request_id=p_id and c.chunk_index=p_index and c.payload=chunk);
end;
$$;
revoke all on function public.dmx_upload_preview_chunk(text,uuid,integer,text) from public,anon,authenticated;
commit;
-- Enable only after manifest initialization, finalization, quotas and authorization tests.
