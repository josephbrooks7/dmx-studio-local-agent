-- Run after deploying the preview schema and functions, before granting client access.
begin;
do $$
declare fp text := repeat('f',64);
declare first_id uuid;
declare second_id uuid;
begin
 if exists(select 1 from dmx_agent_private.devices where fingerprint=fp) then
   raise exception 'Test fingerprint already exists';
 end if;
 insert into dmx_agent_private.devices(fingerprint,enabled) values(fp,true);
 first_id := dmx_agent_private.create_preview_request(fp,'male');
 second_id := dmx_agent_private.create_preview_request(fp,'female');
 if first_id is null or second_id is null or dmx_agent_private.create_preview_request(fp,'male') is not null then
   raise exception 'Request quota failed';
 end if;
 if public.dmx_poll_previews(repeat('0',64)) <> '[]'::jsonb
 or public.dmx_initialize_preview(repeat('0',64),first_id,33,repeat('0',64),'test')
 or public.dmx_upload_preview_chunk(repeat('0',64),first_id,0,'AAAA')
 or public.dmx_finish_preview(repeat('0',64),first_id) then
   raise exception 'Invalid device authorization accepted';
 end if;
 if has_table_privilege('anon','dmx_agent_private.preview_chunks','SELECT')
 or has_table_privilege('anon','dmx_agent_private.preview_chunks','INSERT')
 or has_function_privilege('anon','public.dmx_upload_preview_chunk(text,uuid,integer,text)','EXECUTE') then
   raise exception 'Premature client access';
 end if;
end;
$$;
rollback;
