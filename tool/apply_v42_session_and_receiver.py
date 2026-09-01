from pathlib import Path

main=Path('lib/main_online.dart')
v30=Path('lib/v30_features.dart')
s=main.read_text()
v=v30.read_text()

anchor="const _blue = Color(0xFF0B4EA2);\n"
insert=anchor+"const _deviceChannelV42 = MethodChannel('rc.abastecimento/device');\n\nFuture<String> _stableDeviceIdV42() async {\n  if (Platform.isAndroid) {\n    try {\n      final raw = (await _deviceChannelV42.invokeMethod<String>('androidId'))?.trim() ?? '';\n      if (raw.isNotEmpty) return 'android-$raw';\n    } catch (_) {}\n  }\n  return offlineStore.ensureDeviceIdV39();\n}\n"
if s.count(anchor)!=1: raise SystemExit('v42 device channel anchor missing')
s=s.replace(anchor,insert,1)

old_claim="  Future<Map<String,dynamic>> _claimSessionV39({required bool explicitLogin}) async {final id=await offlineStore.ensureAppSessionIdV30(renew:false);final deviceId=await offlineStore.ensureDeviceIdV39();return api.sessionClaimV39(id,deviceId,explicitLogin:explicitLogin);}"
new_claim="  Future<Map<String,dynamic>> _claimSessionV42({required bool explicitLogin}) async {final id=await offlineStore.ensureAppSessionIdV30(renew:false);final deviceId=await _stableDeviceIdV42();return api.sessionClaimV42(id,deviceId,explicitLogin:explicitLogin);}"
if s.count(old_claim)!=1: raise SystemExit('v42 claim anchor missing')
s=s.replace(old_claim,new_claim,1)
s=s.replace('_claimSessionV39(explicitLogin:', '_claimSessionV42(explicitLogin:')
if '_claimSessionV39(' in s: raise SystemExit('v42 legacy claim call remains')

api_anchor="  Future<Map<String,dynamic>> sessionClaimV39(String id,String deviceId,{required bool explicitLogin}) async => _map(await client.rpc('rca_session_claim_v39',params:{'p_session_id':id,'p_device_id':deviceId,'p_explicit_login':explicitLogin}));\n"
api_insert=api_anchor+"  Future<Map<String,dynamic>> sessionClaimV42(String id,String deviceId,{required bool explicitLogin}) async => _map(await client.rpc('rca_session_claim_v42',params:{'p_session_id':id,'p_device_id':deviceId,'p_explicit_login':explicitLogin}));\n"
if v.count(api_anchor)!=1: raise SystemExit('v42 API anchor missing')
v=v.replace(api_anchor,api_insert,1)

old_ctrl="  final liters=TextEditingController(),km=TextEditingController(),hour=TextEditingController(),responsible=TextEditingController(),receiver=TextEditingController(),location=TextEditingController(),sale=TextEditingController(),thirdDescription=TextEditingController(),thirdPlate=TextEditingController();"
new_ctrl="  final liters=TextEditingController(),km=TextEditingController(),hour=TextEditingController(),receiver=TextEditingController(),location=TextEditingController(),sale=TextEditingController(),thirdDescription=TextEditingController(),thirdPlate=TextEditingController();"
if s.count(old_ctrl)!=1: raise SystemExit('v42 controller anchor missing')
s=s.replace(old_ctrl,new_ctrl,1)

old_dispose="  @override void dispose(){for(final c in [liters,km,hour,responsible,receiver,location,sale,thirdDescription,thirdPlate]){c.dispose();}super.dispose();}"
new_dispose="  @override void dispose(){for(final c in [liters,km,hour,receiver,location,sale,thirdDescription,thirdPlate]){c.dispose();}super.dispose();}"
if s.count(old_dispose)!=1: raise SystemExit('v42 dispose anchor missing')
s=s.replace(old_dispose,new_dispose,1)

old_work="      if(needsWork)DropdownButtonFormField<int>(value:work,decoration:const InputDecoration(labelText:'Obra *'),items:ws.map((x)=>DropdownMenuItem(value:_intOrNull(x['id']),child:Text('${x['name']}'))).toList(),onChanged:saving?null:(v){setState(()=>work=v);final w=selected(ws,v);if(responsible.text.trim().isEmpty&&_hasValue(w?['responsible']))responsible.text='${w?['responsible']}';}),\n      const SizedBox(height:8),TextField(controller:responsible,enabled:!saving,decoration:const InputDecoration(labelText:'Responsável')),const SizedBox(height:12),"
new_work="      if(needsWork)DropdownButtonFormField<int>(value:work,decoration:const InputDecoration(labelText:'Obra *'),items:ws.map((x)=>DropdownMenuItem(value:_intOrNull(x['id']),child:Text('${x['name']}'))).toList(),onChanged:saving?null:(v)=>setState(()=>work=v)),\n      const SizedBox(height:12),"
if s.count(old_work)!=1: raise SystemExit('v42 duplicate responsible field anchor missing')
s=s.replace(old_work,new_work,1)

old_confirm="const SizedBox(height:8),if(responsible.text.trim().isNotEmpty)Text('Responsável: ${responsible.text.trim()}'),Text('Combustível: $fuel')"
new_confirm="const SizedBox(height:8),Text('Combustível: $fuel')"
if s.count(old_confirm)!=1: raise SystemExit('v42 confirm responsible anchor missing')
s=s.replace(old_confirm,new_confirm,1)
s=s.replace("Text('Quem recebeu: ${receiver.text.trim()}')","Text('Responsável pelo recebimento do abastecimento: ${receiver.text.trim()}')",1)

old_required="    if(receiver.text.trim().isEmpty){requiredMessage('Quem recebeu');return;}"
new_required="    if(receiver.text.trim().isEmpty){requiredMessage('Responsável pelo recebimento do abastecimento');return;}"
if s.count(old_required)!=1: raise SystemExit('v42 receiver required anchor missing')
s=s.replace(old_required,new_required,1)

old_call="responsible:responsible.text.trim(),receiver:receiver.text.trim()"
new_call="responsible:null,receiver:receiver.text.trim()"
if s.count(old_call)!=1: raise SystemExit('v42 responsible API call anchor missing')
s=s.replace(old_call,new_call,1)

old_field="TextField(controller:receiver,enabled:!saving,decoration:const InputDecoration(labelText:'Quem recebeu *'))"
new_field="TextField(controller:receiver,enabled:!saving,decoration:const InputDecoration(labelText:'Responsável pelo recebimento do abastecimento *'))"
if s.count(old_field)!=1: raise SystemExit('v42 receiver field anchor missing')
s=s.replace(old_field,new_field,1)

s=s.replace("sign('Assinatura de quem recebeu')","sign('Assinatura do responsável pelo recebimento')",1)
s=s.replace("rs==null?'Assinatura de quem recebeu *':'Assinatura de quem recebeu ✓'","rs==null?'Assinatura do responsável pelo recebimento *':'Assinatura do responsável pelo recebimento ✓'",1)

old_legacy="TextFormField(controller: receiver, decoration: const InputDecoration(labelText: 'Quem recebeu o combustível *'), validator: (v) => v == null || v.trim().isEmpty ? 'Informe quem recebeu.' : null)"
new_legacy="TextFormField(controller: receiver, decoration: const InputDecoration(labelText: 'Responsável pelo recebimento do abastecimento *'), validator: (v) => v == null || v.trim().isEmpty ? 'Informe o responsável pelo recebimento do abastecimento.' : null)"
if s.count(old_legacy)!=1: raise SystemExit('v42 legacy receiver field anchor missing')
s=s.replace(old_legacy,new_legacy,1)

old_pdf="row(Icons.person_outline_rounded, 'Quem recebeu', receiver, navy)"
new_pdf="row(Icons.person_outline_rounded, 'Responsável pelo recebimento do abastecimento', receiver, navy)"
if s.count(old_pdf)!=1: raise SystemExit('v42 PDF receiver label anchor missing')
s=s.replace(old_pdf,new_pdf,1)

main.write_text(s)
v30.write_text(v)

checks=[
    "_deviceChannelV42",
    "_stableDeviceIdV42()",
    "_claimSessionV42({required bool explicitLogin})",
    "sessionClaimV42(id,deviceId,explicitLogin:explicitLogin)",
    "labelText:'Responsável pelo recebimento do abastecimento *'",
    "responsible:null,receiver:receiver.text.trim()",
    "'Responsável pelo recebimento do abastecimento', receiver, navy",
    "labelText:'Equipamento de terceiros'",
    "labelText:'Placa/Identificação'",
]
for x in checks:
    if x not in s and x not in v: raise SystemExit('v42 missing marker: '+x)
if "TextField(controller:responsible,enabled:!saving,decoration:const InputDecoration(labelText:'Responsável'))" in s: raise SystemExit('v42 duplicate fueling responsible input remains')
if "[liters,km,hour,responsible,receiver,location,sale,thirdDescription,thirdPlate]" in s: raise SystemExit('v42 removed controller still referenced in fueling dispose')
print('V42_SESSION_RECEIVER_PATCH_OK')
