from pathlib import Path
p=Path('lib/main_online.dart')
s=p.read_text()

def rep(old,new,label):
    global s
    if old not in s: raise SystemExit(f'{label}: marker not found')
    s=s.replace(old,new,1)

marker="""  Future<Map<String, dynamic>> adminEditFuelingV47({
    required int movementId, required String code, int? workId, int? machineId, int? thirdPartyVehicleId,
    double? kmValue, double? hourmeterValue, String? receiverName, String? responsibleName, String? notes, String? locationAddress,
  }) async => _map(await client.rpc('rca_admin_edit_fueling_v47', params: {
    'p_movement_id': movementId, 'p_code': code, 'p_work_id': workId, 'p_machine_id': machineId,
    'p_third_party_vehicle_id': thirdPartyVehicleId, 'p_km_value': kmValue, 'p_hourmeter_value': hourmeterValue,
    'p_receiver_name': receiverName, 'p_responsible_name': responsibleName, 'p_notes': notes, 'p_location_address': locationAddress,
  }));
"""
apiadd=marker+"""

  Future<Map<String,dynamic>> meterStatusV48(int machineId) async => _map(await client.rpc('rca_meter_status_v48',params:{'p_machine_id':machineId}));
  Future<Map<String,dynamic>> meterCheckV48(int machineId,{double? km,double? hourmeter}) async => _map(await client.rpc('rca_meter_check_v48',params:{'p_machine_id':machineId,'p_km':km,'p_hourmeter':hourmeter}));
  Future<Map<String,dynamic>> replaceHourmeterV48({required int machineId,required double brokenReading,double newInitialReading=0,required String reason,String? oldPhotoPath,String? newPhotoPath,DateTime? replacedAt}) async => _map(await client.rpc('rca_admin_replace_hourmeter_v48',params:{
    'p_machine_id':machineId,'p_broken_reading':brokenReading,'p_new_initial_reading':newInitialReading,'p_reason':reason,
    'p_old_photo_path':oldPhotoPath,'p_new_photo_path':newPhotoPath,'p_replaced_at':(replacedAt??DateTime.now().toUtc()).toIso8601String(),
  }));
  Future<Map<String,dynamic>> adminEditFuelingV48({
    required int movementId,required String code,required int sourceTankId,int? workId,int? machineId,int? thirdPartyVehicleId,required double liters,required String fuelType,
    double? kmValue,double? hourmeterValue,String? receiverName,String? receiverCompany,String? responsibleName,String? operatorName,String? notes,String? locationAddress,
    double? latitude,double? longitude,DateTime? locationCapturedAt,double? locationAccuracyM,double? salePrice,bool lubricated=false,
    String? meterPhotoPath,String? totalizerPhotoPath,String? identityPhotoPath,String? identityKind,String? extraPhotoPath,String? receiverSignaturePath,String? operatorSignaturePath,
    DateTime? occurredAt,required String reason,
  }) async => _map(await client.rpc('rca_admin_edit_fueling_v48',params:{
    'p_movement_id':movementId,'p_code':code,'p_source_tank_id':sourceTankId,'p_work_id':workId,'p_machine_id':machineId,'p_third_party_vehicle_id':thirdPartyVehicleId,
    'p_liters':liters,'p_fuel_type':fuelType,'p_km_value':kmValue,'p_hourmeter_value':hourmeterValue,'p_receiver_name':receiverName,'p_receiver_company':receiverCompany,
    'p_responsible_name':responsibleName,'p_operator_name':operatorName,'p_notes':notes,'p_location_address':locationAddress,'p_latitude':latitude,'p_longitude':longitude,
    'p_location_captured_at':locationCapturedAt?.toUtc().toIso8601String(),'p_location_accuracy_m':locationAccuracyM,'p_sale_price_per_liter':salePrice,'p_lubricated':lubricated,
    'p_meter_photo_path':meterPhotoPath,'p_totalizer_photo_path':totalizerPhotoPath,'p_identity_photo_path':identityPhotoPath,'p_identity_evidence_kind':identityKind,
    'p_extra_photo_path':extraPhotoPath,'p_receiver_signature_path':receiverSignaturePath,'p_operator_signature_path':operatorSignaturePath,
    'p_occurred_at':occurredAt?.toUtc().toIso8601String(),'p_reason':reason,
  }));
"""
rep(marker,apiadd,'api methods')
rep("onChanged:saving?null:(v)=>setState(()=>machine=v)","onChanged:(saving||third!=null||manualThird)?null:(v)=>setState((){machine=v;if(v!=null){third=null;thirdPlate.clear();thirdDescription.clear();}})",'machine destination')
rep("onChanged:saving?null:(v){setState(()=>third=v);final t=selected(ts,v);if(t!=null){thirdPlate.text='${t['plate']??''}';thirdDescription.text='${t['description']??''}';}else{thirdPlate.clear();thirdDescription.clear();}})","onChanged:(saving||machine!=null)?null:(v){setState((){third=v;if(v!=null)machine=null;});final t=selected(ts,v);if(t!=null){thirdPlate.text='${t['plate']??''}';thirdDescription.text='${t['description']??''}';}else{thirdPlate.clear();thirdDescription.clear();}})",'third destination')
rep("TextField(controller:thirdDescription,enabled:!saving&&third==null", "TextField(controller:thirdDescription,enabled:!saving&&third==null&&machine==null", 'manual third description')
rep("TextField(controller:thirdPlate,enabled:!saving&&third==null", "TextField(controller:thirdPlate,enabled:!saving&&third==null&&machine==null", 'manual third plate')
old="""    if(os==null){requiredMessage('Assinatura de quem abasteceu');return;}
    if(!await captureLocationForSubmission()||!mounted)return;
"""
new="""    if(os==null){requiredMessage('Assinatura de quem abasteceu');return;}
    if(machine!=null){
      try{
        final check=await api.meterCheckV48(machine!,km:k,hourmeter:h);
        if(check['regression']==true){
          final msg='${check['message']??'Valor inferior ao último registro.'}';
          if(mounted)await showDialog<void>(context:context,builder:(ctx)=>AlertDialog(title:const Text('KM/Horímetro inválido'),content:Text(msg),actions:[FilledButton(onPressed:()=>Navigator.pop(ctx),child:const Text('Corrigir valor'))]));
          return;
        }
        if(check['large_jump']==true&&mounted){
          final lastK=check['last_km'],lastH=check['last_hourmeter'];
          final ok=await showDialog<bool>(context:context,builder:(ctx)=>AlertDialog(title:const Text('Valor muito acima do último registro'),content:Text('Último KM: ${lastK??'-'}\\nÚltimo horímetro: ${lastH??'-'}\\n\\nO valor informado teve um aumento fora do normal. Confirme somente se conferiu a leitura no equipamento.'),actions:[TextButton(onPressed:()=>Navigator.pop(ctx,false),child:const Text('Voltar')),FilledButton(onPressed:()=>Navigator.pop(ctx,true),child:const Text('Valor conferido'))]))??false;
          if(!ok)return;
        }
      }catch(e){if(mounted)ScaffoldMessenger.of(context).showSnackBar(SnackBar(content:Text(_friendlyError(e))));return;}
    }
    if(!await captureLocationForSubmission()||!mounted)return;
"""
rep(old,new,'meter check submit')
s=s.replace("AdminEditFuelingV47Screen(item:item)","AdminEditFuelingV48Screen(item:item)",1)
start=s.index("class AdminEditFuelingV47Screen extends StatefulWidget")
end=s.index("class _RecordDetailData {",start)
editor=Path('../tool/v48_editor_fragment.tmp').read_text() if Path('../tool/v48_editor_fragment.tmp').exists() else None
if editor is None:
    raise SystemExit('v48 editor fragment missing')
s=s[:start]+editor+s[end:]
more="""        HomeActionCard(
          icon: Icons.badge_outlined,
          title: 'Dados da empresa',
          subtitle: 'Consultar e editar a identificação institucional usada nos PDFs',
          onTap: () => Navigator.push(context, MaterialPageRoute(builder: (_) => const ReportCompanyAdminScreen())),
        ),
"""
rep(more,more+"""        const SizedBox(height: 12),
        HomeActionCard(
          icon: Icons.av_timer_outlined,
          title: 'Substituição de horímetro',
          subtitle: 'Registrar horímetro danificado e iniciar um novo ciclo sem perder o total acumulado',
          onTap: () => Navigator.push(context, MaterialPageRoute(builder: (_) => const HourmeterReplacementV48Screen())),
        ),
""",'admin more card')
ins=s.index("class CompaniesAdminScreen extends StatefulWidget")
hour=Path('../tool/v48_hourmeter_fragment.tmp').read_text() if Path('../tool/v48_hourmeter_fragment.tmp').exists() else None
if hour is None: raise SystemExit('v48 hourmeter fragment missing')
s=s[:ins]+hour+s[ins:]
p.write_text(s)
print('V48_PATCH_OK')
