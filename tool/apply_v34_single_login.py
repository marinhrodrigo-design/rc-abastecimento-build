from pathlib import Path

main = Path('lib/main_online.dart')
v30 = Path('lib/v30_features.dart')

s = main.read_text()
old = "  Future<bool> _claimSessionV30({required bool explicitLogin}) async {final id=await offlineStore.ensureAppSessionIdV30(renew:explicitLogin);return api.sessionClaimV30(id,explicitLogin:explicitLogin);}"
new = "  Future<Map<String,dynamic>> _claimSessionV34({required bool explicitLogin}) async {final id=await offlineStore.ensureAppSessionIdV30(renew:false);return api.sessionClaimV34(id,explicitLogin:explicitLogin);}"
assert old in s
s = s.replace(old, new, 1)

old_restore = "try{if(offlineStore.online.value){if(!await _claimSessionV30(explicitLogin:false)){await _forcedLocalLogoutV30('Sua sessão foi desconectada pelo administrador. Entre novamente para continuar.');return;}}final p=await api.profile();"
new_restore = "try{if(offlineStore.online.value){final claim=await _claimSessionV34(explicitLogin:false);if(claim['ok']!=true){await _forcedLocalLogoutV30('${claim['message']??'Sua sessão não está mais ativa. Entre novamente para continuar.'}');return;}}final p=await api.profile();"
assert old_restore in s
s = s.replace(old_restore, new_restore, 1)

old_login = "if(!await _claimSessionV30(explicitLogin:true))throw Exception('Não foi possível registrar esta sessão.');final p=await api.profile();"
new_login = "final claim=await _claimSessionV34(explicitLogin:true);if(claim['ok']!=true)throw Exception('${claim['message']??'Não foi possível registrar esta sessão.'}');final p=await api.profile();"
assert old_login in s
s = s.replace(old_login, new_login, 1)
main.write_text(s)

v = v30.read_text()
needle = "  Future<bool> sessionClaimV30(String id,{required bool explicitLogin}) async => (await client.rpc('rca_session_claim_v30',params:{'p_session_id':id,'p_explicit_login':explicitLogin}))==true;\n"
insert = needle + "  Future<Map<String,dynamic>> sessionClaimV34(String id,{required bool explicitLogin}) async => _map(await client.rpc('rca_session_claim_v34',params:{'p_session_id':id,'p_explicit_login':explicitLogin}));\n"
assert needle in v
v = v.replace(needle, insert, 1)
v30.write_text(v)

print('V34_SINGLE_LOGIN_PATCH_OK')
