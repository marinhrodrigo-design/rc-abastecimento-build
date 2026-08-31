from pathlib import Path

main=Path('lib/main_online.dart')
v30=Path('lib/v30_features.dart')
s=main.read_text()
v=v30.read_text()

old="  Future<Map<String,dynamic>> _claimSessionV34({required bool explicitLogin}) async {final id=await offlineStore.ensureAppSessionIdV30(renew:false);return api.sessionClaimV34(id,explicitLogin:explicitLogin);}"
new="  Future<Map<String,dynamic>> _claimSessionV39({required bool explicitLogin}) async {final id=await offlineStore.ensureAppSessionIdV30(renew:false);final deviceId=await offlineStore.ensureDeviceIdV39();return api.sessionClaimV39(id,deviceId,explicitLogin:explicitLogin);}"
if s.count(old)!=1: raise SystemExit(f'v39: claim method count={s.count(old)}')
s=s.replace(old,new,1)
s=s.replace('_claimSessionV34(explicitLogin:', '_claimSessionV39(explicitLogin:')
if '_claimSessionV34(' in s: raise SystemExit('v39: legacy claim call remains')

needle="  Future<void> clearAppSessionIdV30() async {_state.remove('app_session_id_v30');await _persist();}\n"
insert=needle+"  String? get deviceIdV39 { final v='${_state['device_id_v39'] ?? ''}'.trim(); return v.isEmpty?null:v; }\n  Future<String> ensureDeviceIdV39() async { var id=deviceIdV39; if(id==null){final uid=Supabase.instance.client.auth.currentUser?.id??'install';id='device-$uid-${DateTime.now().microsecondsSinceEpoch}';_state['device_id_v39']=id;await _persist();}return id; }\n"
if v.count(needle)!=1: raise SystemExit('v39: offline store marker missing')
v=v.replace(needle,insert,1)

needle2="  Future<Map<String,dynamic>> sessionClaimV34(String id,{required bool explicitLogin}) async => _map(await client.rpc('rca_session_claim_v34',params:{'p_session_id':id,'p_explicit_login':explicitLogin}));\n"
insert2=needle2+"  Future<Map<String,dynamic>> sessionClaimV39(String id,String deviceId,{required bool explicitLogin}) async => _map(await client.rpc('rca_session_claim_v39',params:{'p_session_id':id,'p_device_id':deviceId,'p_explicit_login':explicitLogin}));\n"
if v.count(needle2)!=1: raise SystemExit('v39: api marker missing')
v=v.replace(needle2,insert2,1)

main.write_text(s)
v30.write_text(v)

for x in ['_claimSessionV39({required bool explicitLogin})','ensureDeviceIdV39()','sessionClaimV39(id,deviceId,explicitLogin:explicitLogin)']:
    if x not in s and x not in v: raise SystemExit('v39 missing marker: '+x)
for x in ['device_id_v39','rca_session_claim_v39','p_device_id']:
    if x not in v: raise SystemExit('v39 missing v30 marker: '+x)
print('V39_DEVICE_SESSION_PATCH_OK')
