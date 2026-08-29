from pathlib import Path
main=Path('lib/main_online.dart');v29=Path('lib/v29_features.dart');s=main.read_text();u=v29.read_text()

needle="part 'v29_features.dart';\n"
if "part 'v30_features.dart';" not in s:
    if needle not in s: raise SystemExit('v30: v29 part marker missing')
    s=s.replace(needle,needle+"part 'v30_features.dart';\n",1)

# Cards approved without subtitles; retain parameters only for compatibility.
s=s.replace("      subtitle: Text(subtitle),\n","")
s=s.replace(",const SizedBox(height:3),Text(subtitle,textAlign:TextAlign.center,maxLines:2,overflow:TextOverflow.ellipsis,style:const TextStyle(fontSize:9.5,color:Colors.black54))","")
s=s.replace("""            const SizedBox(height:3),
            Text(subtitle,textAlign:TextAlign.center,maxLines:2,overflow:TextOverflow.ellipsis,style:const TextStyle(fontSize:9.8,color:Colors.black54)),
""","")

# Fueling writes must be validated against the server-side unit reservation.
s=s.replace("offlineStore.executeOrQueue('rca_record_fueling_v22'","offlineStore.executeOrQueue('rca_record_fueling_v30'",1)
s=s.replace("rpc == 'rca_record_fueling_v22'","rpc == 'rca_record_fueling_v22' || rpc == 'rca_record_fueling_v30'",1)

old_select="""                                await offlineStore.setLastTankId(tankId);
                                if (!context.mounted) return;
                                Navigator.pushReplacement(context, MaterialPageRoute(builder: (_) => FieldHomeScreen(profile: widget.profile, tankId: tankId, onLogout: widget.onLogout)));"""
new_select="""                                if (!offlineStore.online.value) {
                                  if (offlineStore.lastTankId != tankId) {
                                    ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Conecte-se à internet para trocar de unidade. A unidade atual continua reservada.')));
                                    return;
                                  }
                                } else {
                                  try {
                                    final claim = await api.claimUnitV30(tankId);
                                    if (claim['ok'] != true) {
                                      if (context.mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('${claim['message'] ?? 'Esta unidade já está em uso.'}')));
                                      return;
                                    }
                                  } catch (e) {
                                    if (context.mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(_friendlyError(e))));
                                    return;
                                  }
                                }
                                await offlineStore.setLastTankId(tankId);
                                if (!context.mounted) return;
                                Navigator.pushReplacement(context, MaterialPageRoute(builder: (_) => FieldHomeScreen(profile: widget.profile, tankId: tankId, onLogout: widget.onLogout)));"""
if old_select not in s: raise SystemExit('v30: UnitSelection block missing')
s=s.replace(old_select,new_select,1)

# Switching screens never releases old unit; new claim atomically releases it only after success.
s=s.replace("                await offlineStore.setLastTankId(null);\n                if (!context.mounted) return;\n                Navigator.pushReplacement(context, MaterialPageRoute(builder: (_) => UnitSelectionScreen(profile: widget.profile, onLogout: widget.onLogout)));","                if (!context.mounted) return;\n                Navigator.pushReplacement(context, MaterialPageRoute(builder: (_) => UnitSelectionScreen(profile: widget.profile, onLogout: widget.onLogout)));",1)

# Logout navigation only occurs after the server confirmed release.
a=s.index('Future<void> _logoutToLogin(');b=s.index('bool _isNetworkError',a)
s=s[:a]+"""Future<void> _logoutToLogin(BuildContext context, Future<void> Function() onLogout) async {
  try { await onLogout(); }
  catch (e) { if (context.mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(_friendlyError(e)))); return; }
  if (!context.mounted) return;
  Navigator.of(context, rootNavigator: true).pushAndRemoveUntil(MaterialPageRoute(builder: (_) => const AuthGate()), (_) => false);
}

"""+s[b:]

# Replace AuthGate with persistent logical session + Admin forced-disconnect polling.
a=s.index('class AuthGate extends StatefulWidget');b=s.index('String _friendlyError',a)
auth="""class AuthGate extends StatefulWidget {
  const AuthGate({super.key});
  @override State<AuthGate> createState()=>_AuthGateState();
}
class _AuthGateState extends State<AuthGate> {
  bool loading=true,_checkingSessionV30=false; Map<String,dynamic>? profile; String? error; Timer? _sessionGuardV30;
  @override void initState(){super.initState();_restore();}
  @override void dispose(){_sessionGuardV30?.cancel();super.dispose();}
  Future<bool> _claimSessionV30({required bool explicitLogin}) async {final id=await offlineStore.ensureAppSessionIdV30(renew:explicitLogin);return api.sessionClaimV30(id,explicitLogin:explicitLogin);}
  void _startSessionGuardV30(){_sessionGuardV30?.cancel();_sessionGuardV30=Timer.periodic(const Duration(seconds:10),(_)=>unawaited(_checkSessionV30()));}
  Future<void> _checkSessionV30() async {if(_checkingSessionV30||!offlineStore.online.value||profile==null)return;final id=offlineStore.appSessionIdV30;if(id==null)return;_checkingSessionV30=true;try{if(!await api.sessionValidV30(id))await _forcedLocalLogoutV30('Sua sessão foi desconectada pelo administrador.');}catch(e){if(!_isNetworkError(e))await _forcedLocalLogoutV30('Sua sessão não está mais ativa.');}finally{_checkingSessionV30=false;}}
  Future<void> _forcedLocalLogoutV30(String message) async {_sessionGuardV30?.cancel();await offlineStore.clearProfile();await offlineStore.setLastTankId(null);await offlineStore.clearAppSessionIdV30();try{await Supabase.instance.client.auth.signOut(scope:SignOutScope.local);}catch(_){}if(mounted)setState((){profile=null;loading=false;error=message;});}
  Future<void> _restore() async {
    final cached=offlineStore.cachedProfile;
    if(Supabase.instance.client.auth.currentSession==null){if(!offlineStore.online.value&&cached!=null){if(mounted)setState((){profile=cached;loading=false;});}else if(mounted)setState(()=>loading=false);return;}
    try{if(offlineStore.online.value){if(!await _claimSessionV30(explicitLogin:false)){await _forcedLocalLogoutV30('Sua sessão foi desconectada pelo administrador. Entre novamente para continuar.');return;}}final p=await api.profile();offlineStore.markOnline();await offlineStore.cacheProfile(p);if(mounted)setState((){profile=p;loading=false;});_startSessionGuardV30();unawaited(offlineStore.syncPending());}
    catch(e){if(_isNetworkError(e)&&cached!=null){offlineStore.markOffline();if(mounted)setState((){profile=cached;loading=false;});}else{await _forcedLocalLogoutV30(_friendlyError(e));}}
  }
  Future<void> _login(String username,String password) async {
    setState((){loading=true;error=null;});final client=Supabase.instance.client;final normalized=username.trim().toLowerCase();final testUsername=normalized=='admin'?'adminfuel':normalized=='motorista'?'motorista1':normalized;
    try{final loginPassword=_authPasswordForLogin(password);var signedIn=false;if(normalized.contains('@')){await client.auth.signInWithPassword(email:normalized,password:loginPassword);signedIn=true;}else{try{await client.auth.signInWithPassword(email:'$testUsername@rccombustivel.app',password:loginPassword);signedIn=true;}catch(_){}if(!signedIn&&const {'adminfuel','admin','operador','motorista','motorista1','motorista2'}.contains(normalized)){final res=await client.functions.invoke('fuel-test-login',body:{'username':testUsername,'password':password});final data=_map(res.data);if(res.status>=200&&res.status<300&&data['refresh_token']!=null){await client.auth.setSession('${data['refresh_token']}');signedIn=true;}else{throw Exception('Usuário ou senha inválidos.');}}if(!signedIn){await client.auth.signInWithPassword(email:'$normalized@rcmanutencao.app',password:loginPassword);signedIn=true;}}
      if(!await _claimSessionV30(explicitLogin:true))throw Exception('Não foi possível registrar esta sessão.');final p=await api.profile();offlineStore.markOnline();await offlineStore.cacheProfile(p);if(mounted)setState((){profile=p;loading=false;});_startSessionGuardV30();unawaited(offlineStore.syncPending());}
    catch(e){_sessionGuardV30?.cancel();await offlineStore.clearAppSessionIdV30();await client.auth.signOut();if(mounted)setState((){loading=false;error=_friendlyError(e);});}
  }
  Future<void> _logout() async {if(!offlineStore.online.value)throw Exception('Conecte-se à internet para sair e liberar sua unidade.');final id=offlineStore.appSessionIdV30;if(id!=null)await api.logoutV30(id);_sessionGuardV30?.cancel();if(mounted)setState(()=>profile=null);await offlineStore.clearProfile();await offlineStore.setLastTankId(null);await offlineStore.clearAppSessionIdV30();await Supabase.instance.client.auth.signOut(scope:SignOutScope.local).timeout(const Duration(seconds:2));}
  @override Widget build(BuildContext context){if(loading)return const Scaffold(body:Center(child:CircularProgressIndicator()));if(profile==null)return LoginScreen(onLogin:_login,error:error);final staff=profile!['is_admin']==true||profile!['is_manager']==true||profile!['is_supervisor']==true;if(staff)return AdminHomeScreen(profile:profile!,onLogout:_logout);final role='${profile!['role']??''}'.trim().toLowerCase();final operational=role=='fuel_driver'||role=='operator'||role=='operational';if(operational)return OperationalHomeV30Screen(profile:profile!,onLogout:_logout);final lastTankId=offlineStore.lastTankId;if(lastTankId!=null)return FieldHomeScreen(profile:profile!,tankId:lastTankId,onLogout:_logout);return UnitSelectionScreen(profile:profile!,onLogout:_logout);}
}

"""
s=s[:a]+auth+s[b:]

marker="  if (_isNetworkError(e)) return 'Sem conexão com a internet.';\n"
extra="""  if (s.contains('Sessão desconectada pelo administrador') || s.contains('Usuário desconectado pelo administrador')) return 'Sua sessão foi desconectada pelo administrador.';
  if (s.contains('Selecione esta unidade antes de registrar o abastecimento')) return 'Selecione a unidade de abastecimento antes de continuar.';
  if (s.contains('Conecte-se à internet para sair')) return 'Conecte-se à internet para sair e liberar sua unidade.';
"""
if extra.strip() not in s:s=s.replace(marker,marker+extra,1)

# Add Admin > Desconectar usuário to unified Users screen.
method="""  Future<void> disconnectUser(Map<String,dynamic> u) async {
    final ok=await showDialog<bool>(context:context,builder:(ctx)=>AlertDialog(title:const Text('Desconectar usuário?'),content:Text('O usuário ${u['name']} será desconectado e a unidade vinculada será liberada. O acesso continuará ativo e ele poderá entrar novamente depois.'),actions:[TextButton(onPressed:()=>Navigator.pop(ctx,false),child:const Text('Cancelar')),FilledButton(onPressed:()=>Navigator.pop(ctx,true),child:const Text('Desconectar'))]));
    if(ok!=true)return;setState(()=>busy=true);try{final r=await api.adminDisconnectUserV30('${u['user_id']}');await load();if(mounted)ScaffoldMessenger.of(context).showSnackBar(SnackBar(content:Text(r['released_tank_id']!=null?'Usuário desconectado. Unidade liberada ✓':'Usuário desconectado ✓')));}catch(e){if(mounted)ScaffoldMessenger.of(context).showSnackBar(SnackBar(content:Text(_friendlyError(e))));}finally{if(mounted)setState(()=>busy=false);}
  }

"""
if 'Future<void> disconnectUser(' not in u:
    p=u.index('  Future<void> deleteUser(');u=u[:p]+method+u[p:]
old="onSelected:(v){if(v=='edit')editUser(u);if(v=='active')toggleAccess(u);if(v=='delete')deleteUser(u);},itemBuilder:(_)=>[const PopupMenuItem(value:'edit',child:Text('Editar usuário e permissões')),PopupMenuItem(value:'active',child:Text(u['active']==true?'Bloquear login':'Liberar login')),const PopupMenuItem(value:'delete',child:Text('Excluir usuário'))])"
new="onSelected:(v){if(v=='edit')editUser(u);if(v=='disconnect')disconnectUser(u);if(v=='active')toggleAccess(u);if(v=='delete')deleteUser(u);},itemBuilder:(_)=>[const PopupMenuItem(value:'edit',child:Text('Editar usuário e permissões')),const PopupMenuItem(value:'disconnect',child:Text('Desconectar usuário')),PopupMenuItem(value:'active',child:Text(u['active']==true?'Bloquear login':'Liberar login')),const PopupMenuItem(value:'delete',child:Text('Excluir usuário'))])"
if old not in u:raise SystemExit('v30: users popup marker missing')
u=u.replace(old,new,1)

main.write_text(s);v29.write_text(u)
for c in ["part 'v30_features.dart';","OperationalHomeV30Screen(profile:","rca_record_fueling_v30","api.claimUnitV30(tankId)","api.logoutV30(id)","sessionValidV30"]:
    if c not in s:raise SystemExit('v30 missing main marker: '+c)
for c in ['Future<void> disconnectUser',"value:'disconnect'",'adminDisconnectUserV30']:
    if c not in u:raise SystemExit('v30 missing users marker: '+c)
if 'subtitle: Text(subtitle)' in s:raise SystemExit('v30 HomeActionCard subtitle still rendered')
if 'Text(subtitle,textAlign:TextAlign.center' in s:raise SystemExit('v30 admin quick subtitle still rendered')
print('v30 patch applied successfully')
