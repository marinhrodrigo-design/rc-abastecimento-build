create or replace function public.rca_admin_edit_fueling_v47(
  p_movement_id bigint,
  p_code text,
  p_work_id bigint,
  p_machine_id bigint,
  p_third_party_vehicle_id bigint,
  p_km_value numeric,
  p_hourmeter_value numeric,
  p_receiver_name text,
  p_responsible_name text,
  p_notes text,
  p_location_address text
) returns jsonb
language plpgsql
security definer
set search_path to 'public','fuel','auth'
as $$
declare
  v_code text := upper(trim(coalesce(p_code,'')));
  v_work_name text;
  v_work_responsible text;
  v_result jsonb;
begin
  if auth.uid() is null then raise exception 'Sessão inválida'; end if;
  if not public.rca_is_admin() then raise exception 'Somente o Admin pode corrigir abastecimentos'; end if;
  if p_movement_id is null then raise exception 'Registro inválido'; end if;
  if v_code='' then raise exception 'Informe a numeração do registro'; end if;
  if p_machine_id is not null and p_third_party_vehicle_id is not null then raise exception 'Selecione somente um destino: ativo ou equipamento de terceiros'; end if;
  if p_machine_id is null and p_third_party_vehicle_id is null then raise exception 'Selecione o ativo ou equipamento de terceiros'; end if;
  if p_km_value is not null and p_km_value < 0 then raise exception 'KM inválido'; end if;
  if p_hourmeter_value is not null and p_hourmeter_value < 0 then raise exception 'Horímetro inválido'; end if;
  if exists(select 1 from fuel.movements where movement_code=v_code and id<>p_movement_id) then raise exception 'Esta numeração já está em uso'; end if;
  if not exists(select 1 from fuel.movements where id=p_movement_id and movement_type='fueling') then raise exception 'Abastecimento não encontrado'; end if;
  if p_machine_id is not null and not exists(select 1 from public.machines where id=p_machine_id) then raise exception 'Ativo não encontrado'; end if;
  if p_third_party_vehicle_id is not null and not exists(select 1 from fuel.third_party_vehicles where id=p_third_party_vehicle_id) then raise exception 'Equipamento de terceiros não encontrado'; end if;
  if p_work_id is not null then
    select w.name,w.responsible into v_work_name,v_work_responsible from fuel.works w where w.id=p_work_id;
    if v_work_name is null then raise exception 'Obra não encontrada'; end if;
  end if;
  update fuel.movements m set
    movement_code=v_code,
    work_id=p_work_id,
    work_name_snapshot=case when p_work_id is null then null else v_work_name end,
    work_responsible_snapshot=coalesce(nullif(trim(p_responsible_name),''),case when p_work_id is null then null else v_work_responsible end),
    machine_id=p_machine_id,
    third_party_vehicle_id=p_third_party_vehicle_id,
    km_value=p_km_value,
    hourmeter_value=p_hourmeter_value,
    km_hourmeter=coalesce(p_km_value,p_hourmeter_value),
    km_hourmeter_unavailable=(p_km_value is null and p_hourmeter_value is null),
    receiver_name=nullif(trim(p_receiver_name),''),
    notes=nullif(trim(p_notes),''),
    location_address=nullif(trim(p_location_address),''),
    corrected_at=now(),
    corrected_by=auth.uid()
  where m.id=p_movement_id and m.movement_type='fueling'
  returning jsonb_build_object('ok',true,'movement_id',m.id,'code',m.movement_code,'corrected_at',m.corrected_at,'protected_fields',jsonb_build_array('liters','source_tank_id','fuel_type','latitude','longitude','photos','signatures','created_at','operator')) into v_result;
  if v_result is null then raise exception 'Abastecimento não encontrado'; end if;
  return v_result;
end
$$;
revoke all on function public.rca_admin_edit_fueling_v47(bigint,text,bigint,bigint,bigint,numeric,numeric,text,text,text,text) from public, anon;
grant execute on function public.rca_admin_edit_fueling_v47(bigint,text,bigint,bigint,bigint,numeric,numeric,text,text,text,text) to authenticated;
