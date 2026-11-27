begin;
create function dmx_agent_private.create_preview_request(p_fingerprint text,p_character text)
returns uuid language plpgsql security invoker set search_path = '' as $$
declare request_id uuid;
begin
 perform 1 from dmx_agent_private.devices where fingerprint=p_fingerprint and enabled for update;
 if not found then return null; end if;
 perform dmx_agent_private.purge_expired_previews();
 if (select count(*) from dmx_agent_private.preview_requests where fingerprint=p_fingerprint) >= 2 then return null; end if;
 insert into dmx_agent_private.preview_requests(fingerprint,character) values(p_fingerprint,p_character) returning id into request_id;
 return request_id;
end;
$$;
revoke all on function dmx_agent_private.create_preview_request(text,text) from public,anon,authenticated;

create function public.dmx_initialize_preview(p_key text,p_id uuid,p_bytes integer,p_sha256 text,p_build text)
returns boolean language plpgsql security definer set search_path = '' as $$
declare r dmx_agent_private.preview_requests%rowtype;
begin
 if p_key is null or p_key !~ '^[0-9a-f]{64}$' or p_bytes is null or p_bytes not between 33 and 4194304 or p_sha256 is null or p_sha256 !~ '^[0-9a-f]{64}$' or p_build is null or length(p_build) not between 1 and 64 then return false; end if;
 select q.* into r from dmx_agent_private.preview_requests q
 join dmx_agent_private.devices d on d.fingerprint=q.fingerprint
 where q.id=p_id and d.enabled and d.fingerprint=encode(extensions.digest(p_key,'sha256'),'hex')
 and q.expires_at>now() and q.finished_at is null for update of q;
 if not found then return false; end if;
 if r.image_bytes is not null then return r.image_bytes=p_bytes and r.sha256=p_sha256 and r.build=p_build; end if;
 update dmx_agent_private.preview_requests set image_bytes=p_bytes,sha256=p_sha256,build=p_build where id=p_id;
 return true;
end;
$$;
revoke all on function public.dmx_initialize_preview(text,uuid,integer,text,text) from public,anon,authenticated;
commit;
-- Deploy only after storage and cleanup. No client grants before integration tests.
