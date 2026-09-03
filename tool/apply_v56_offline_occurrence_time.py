from pathlib import Path
p=Path('lib/main_online.dart')
s=p.read_text()

# Include v56 in local balance handling.
s=s.replace("rpc == 'rca_record_fueling_v33')) {", "rpc == 'rca_record_fueling_v33' || rpc == 'rca_record_fueling_v56')) {", 1)

old="""  Future<Map<String,dynamic>> fuelingV22({required int sourceTankId,int? workId,int? machineId,int? thirdId,String? thirdPartyPlate,String? thirdPartyDescription,required double liters,double? km,double? hourmeter,String? responsible,required String receiver,required String receiverSignature,required String operatorSignature,String? meterPhoto,required String totalizerPhoto,required String identityPhoto,required String identityKind,String? extraPhoto,double? salePrice,String? notes,required String fuelType,required String location,double? latitude,double? longitude,DateTime? locationCapturedAt,double? locationAccuracyM}) async => offlineStore.executeOrQueue('rca_record_fueling_v41',{'p_source_tank_id':sourceTankId,'p_work_id':workId,'p_machine_id':machineId,'p_third_party_vehicle_id':thirdId,'p_third_party_plate':thirdPartyPlate,'p_third_party_company':null,'p_third_party_description':thirdPartyDescription,'p_liters':liters,'p_km_value':km,'p_hourmeter_value':hourmeter,'p_responsible_name':responsible,'p_receiver_name':receiver,'p_receiver_company':null,'p_receiver_signature_path':receiverSignature,'p_operator_signature_path':operatorSignature,'p_meter_photo_path':meterPhoto,'p_totalizer_photo_path':totalizerPhoto,'p_identity_photo_path':identityPhoto,'p_identity_evidence_kind':identityKind,'p_extra_photo_path':extraPhoto,'p_sale_price_per_liter':salePrice,'p_notes':notes,'p_lubricated':false,'p_latitude':latitude,'p_longitude':longitude,'p_fuel_type':fuelType,'p_location_address':location,'p_location_captured_at':locationCapturedAt?.toUtc().toIso8601String(),'p_location_accuracy_m':locationAccuracyM});
"""
new="""  Future<Map<String,dynamic>> fuelingV22({required int sourceTankId,int? workId,int? machineId,int? thirdId,String? thirdPartyPlate,String? thirdPartyDescription,required double liters,double? km,double? hourmeter,String? responsible,required String receiver,required String receiverSignature,required String operatorSignature,String? meterPhoto,required String totalizerPhoto,required String identityPhoto,required String identityKind,String? extraPhoto,double? salePrice,String? notes,required String fuelType,required String location,double? latitude,double? longitude,DateTime? locationCapturedAt,double? locationAccuracyM,required DateTime occurredAt}) async => offlineStore.executeOrQueue('rca_record_fueling_v56',{'p_source_tank_id':sourceTankId,'p_work_id':workId,'p_machine_id':machineId,'p_third_party_vehicle_id':thirdId,'p_third_party_plate':thirdPartyPlate,'p_third_party_company':null,'p_third_party_description':thirdPartyDescription,'p_liters':liters,'p_km_value':km,'p_hourmeter_value':hourmeter,'p_responsible_name':responsible,'p_receiver_name':receiver,'p_receiver_company':null,'p_receiver_signature_path':receiverSignature,'p_operator_signature_path':operatorSignature,'p_meter_photo_path':meterPhoto,'p_totalizer_photo_path':totalizerPhoto,'p_identity_photo_path':identityPhoto,'p_identity_evidence_kind':identityKind,'p_extra_photo_path':extraPhoto,'p_sale_price_per_liter':salePrice,'p_notes':notes,'p_lubricated':false,'p_latitude':latitude,'p_longitude':longitude,'p_fuel_type':fuelType,'p_location_address':location,'p_location_captured_at':locationCapturedAt?.toUtc().toIso8601String(),'p_location_accuracy_m':locationAccuracyM,'p_occurred_at':occurredAt.toUtc().toIso8601String()});
"""
assert old in s, 'API fuelingV22 não encontrada'
s=s.replace(old,new,1)

old="""    if(!await confirmFueling(v,k,h)||!mounted)return;
    setState((){saving=true;savingStep='Enviando evidências...';});
"""
new="""    if(!await confirmFueling(v,k,h)||!mounted)return;
    final occurredAt=DateTime.now().toUtc();
    setState((){saving=true;savingStep='Enviando evidências...';});
"""
assert old in s, 'Ponto de confirmação do abastecimento não encontrado'
s=s.replace(old,new,1)

old="""locationCapturedAt:locationCapturedAt,locationAccuracyM:locationAccuracyM);
"""
new="""locationCapturedAt:locationCapturedAt,locationAccuracyM:locationAccuracyM,occurredAt:occurredAt);
"""
assert old in s, 'Chamada fuelingV22 não encontrada'
s=s.replace(old,new,1)

# Version shown on login.
s=s.replace("child: Text('v54'", "child: Text('v56'", 1)

p.write_text(s)
print('VALIDACAO_PATCH_V56_OCCURRENCE_TIME_OK')
