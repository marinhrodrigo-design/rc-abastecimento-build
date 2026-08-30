from pathlib import Path

main = Path('lib/main_online.dart')
s = main.read_text()

old_login = '''  Future<void> _login(String username,String password) async {
    setState((){loading=true;error=null;});final client=Supabase.instance.client;final normalized=username.trim().toLowerCase();final testUsername=normalized=='admin'?'adminfuel':normalized=='motorista'?'motorista1':normalized;
    try{final loginPassword=_authPasswordForLogin(password);var signedIn=false;if(normalized.contains('@')){await client.auth.signInWithPassword(email:normalized,password:loginPassword);signedIn=true;}else{try{await client.auth.signInWithPassword(email:'$testUsername@rccombustivel.app',password:loginPassword);signedIn=true;}catch(_){}if(!signedIn&&const {'adminfuel','admin','operador','motorista','motorista1','motorista2'}.contains(normalized)){final res=await client.functions.invoke('fuel-test-login',body:{'username':testUsername,'password':password});final data=_map(res.data);if(res.status>=200&&res.status<300&&data['refresh_token']!=null){await client.auth.setSession('${data['refresh_token']}');signedIn=true;}else{throw Exception('Usuário ou senha inválidos.');}}if(!signedIn){await client.auth.signInWithPassword(email:'$normalized@rcmanutencao.app',password:loginPassword);signedIn=true;}}
      final claim=await _claimSessionV34(explicitLogin:true);if(claim['ok']!=true)throw Exception('${claim['message']??'Não foi possível registrar esta sessão.'}');final p=await api.profile();offlineStore.markOnline();await offlineStore.cacheProfile(p);if(mounted)setState((){profile=p;loading=false;});_startSessionGuardV30();unawaited(offlineStore.syncPending());}
    catch(e){_sessionGuardV30?.cancel();await offlineStore.clearAppSessionIdV30();await client.auth.signOut();if(mounted)setState((){loading=false;error=_friendlyError(e);});}
  }
'''
new_login = '''  Future<void> _login(String username,String password) async {
    setState((){loading=true;error=null;});
    final client=Supabase.instance.client;
    final normalized=username.trim().toLowerCase();
    final testUsername=normalized=='motorista'?'motorista1':normalized;
    try{
      final loginPassword=_authPasswordForLogin(password);
      var signedIn=false;
      if(normalized.contains('@')){
        await client.auth.signInWithPassword(email:normalized,password:loginPassword);
        signedIn=true;
      }else if(normalized=='admin'||normalized=='adminfuel'){
        // A conta Admin pode migrar do endereço técnico antigo para o e-mail
        // proprietário sem alterar o nome digitado na tela de login.
        for(final email in const ['marinhrodrigo@gmail.com','adminfuel@rccombustivel.app']){
          try{await client.auth.signInWithPassword(email:email,password:loginPassword);signedIn=true;break;}catch(_){}
        }
        if(!signedIn)throw Exception('Usuário ou senha inválidos.');
      }else{
        try{await client.auth.signInWithPassword(email:'$testUsername@rccombustivel.app',password:loginPassword);signedIn=true;}catch(_){}
        if(!signedIn&&const {'operador','motorista','motorista1','motorista2'}.contains(normalized)){
          final res=await client.functions.invoke('fuel-test-login',body:{'username':testUsername,'password':password});
          final data=_map(res.data);
          if(res.status>=200&&res.status<300&&data['refresh_token']!=null){await client.auth.setSession('${data['refresh_token']}');signedIn=true;}else{throw Exception('Usuário ou senha inválidos.');}
        }
        if(!signedIn){await client.auth.signInWithPassword(email:'$normalized@rcmanutencao.app',password:loginPassword);signedIn=true;}
      }
      final claim=await _claimSessionV34(explicitLogin:true);
      if(claim['ok']!=true)throw Exception('${claim['message']??'Não foi possível registrar esta sessão.'}');
      final p=await api.profile();offlineStore.markOnline();await offlineStore.cacheProfile(p);
      if(mounted)setState((){profile=p;loading=false;});
      _startSessionGuardV30();unawaited(offlineStore.syncPending());
    }catch(e){
      _sessionGuardV30?.cancel();await offlineStore.clearAppSessionIdV30();await client.auth.signOut();
      if(mounted)setState((){loading=false;error=_friendlyError(e);});
    }
  }
'''
assert old_login in s
s=s.replace(old_login,new_login,1)

marker='class AdminHomeScreen extends StatefulWidget {'
assert marker in s
security_class=r'''class AdminSecurityV35Screen extends StatefulWidget {
  const AdminSecurityV35Screen({super.key});
  @override State<AdminSecurityV35Screen> createState()=>_AdminSecurityV35ScreenState();
}

class _AdminSecurityV35ScreenState extends State<AdminSecurityV35Screen>{
  final pin=TextEditingController(),password=TextEditingController(),confirm=TextEditingController();
  bool sending=false,saving=false,pinSent=false,hidePassword=true;
  static const ownerEmail='marinhrodrigo@gmail.com';
  @override void dispose(){pin.dispose();password.dispose();confirm.dispose();super.dispose();}

  Future<void> sendPin() async {
    if(!offlineStore.online.value){ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content:Text('Conecte-se à internet para enviar o PIN de segurança.')));return;}
    setState(()=>sending=true);
    try{
      final client=Supabase.instance.client;
      final res=await client.functions.invoke('admin-security',body:{'action':'prepare_password_change'});
      final data=_map(res.data);
      if(res.status<200||res.status>=300||data['ok']!=true)throw Exception('${data['error']??'Não foi possível preparar a verificação.'}');
      try{await client.auth.refreshSession();}catch(_){}
      await client.auth.reauthenticate();
      if(mounted){setState(()=>pinSent=true);ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content:Text('PIN enviado para marinhrodrigo@gmail.com.')));}
    }catch(e){if(mounted)ScaffoldMessenger.of(context).showSnackBar(SnackBar(content:Text('Não foi possível enviar o PIN: ${_friendlyError(e)}')));}
    finally{if(mounted)setState(()=>sending=false);}
  }

  Future<void> changePassword() async {
    if(!pinSent){ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content:Text('Envie o PIN para o seu e-mail primeiro.')));return;}
    final code=pin.text.trim(),next=password.text,again=confirm.text;
    if(code.isEmpty){ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content:Text('Informe o PIN recebido por e-mail.')));return;}
    if(next.length<4){ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content:Text('A nova senha/PIN deve ter pelo menos 4 caracteres.')));return;}
    if(next!=again){ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content:Text('A confirmação da nova senha não confere.')));return;}
    if(!offlineStore.online.value){ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content:Text('Conecte-se à internet para alterar a senha do Admin.')));return;}
    setState(()=>saving=true);
    try{
      final client=Supabase.instance.client;
      await client.auth.updateUser(UserAttributes(password:_authPasswordForLogin(next),nonce:code));
      try{await client.auth.signOut(scope:SignOutScope.others);}catch(_){}
      final sessionId=offlineStore.appSessionIdV30;
      final res=await client.functions.invoke('admin-security',body:{'action':'complete_password_change','session_id':sessionId});
      final data=_map(res.data);
      if(res.status<200||res.status>=300||data['ok']!=true)throw Exception('${data['error']??'Senha alterada, mas houve falha ao registrar a segurança.'}');
      pin.clear();password.clear();confirm.clear();
      if(mounted){setState(()=>pinSent=false);await showDialog<void>(context:context,builder:(ctx)=>AlertDialog(title:const Text('Senha alterada ✓'),content:const Text('A senha do Admin foi alterada. Outras sessões foram encerradas e a alteração foi registrada na Auditoria.'),actions:[FilledButton(onPressed:()=>Navigator.pop(ctx),child:const Text('OK'))]));}
    }catch(e){if(mounted)ScaffoldMessenger.of(context).showSnackBar(SnackBar(content:Text('Não foi possível alterar a senha: ${_friendlyError(e)}')));}
    finally{if(mounted)setState(()=>saving=false);}
  }

  @override Widget build(BuildContext context)=>Scaffold(
    appBar:AppBar(title:const Text('Segurança do Admin')),
    body:ListView(padding:const EdgeInsets.all(16),children:[
      Card(child:Padding(padding:const EdgeInsets.all(16),child:Column(crossAxisAlignment:CrossAxisAlignment.start,children:[
        const Row(children:[Icon(Icons.verified_user_outlined,color:_blue),SizedBox(width:8),Expanded(child:Text('Proteção da senha do Admin',style:TextStyle(fontSize:17,fontWeight:FontWeight.w900)))]),
        const SizedBox(height:10),
        const Text('Para alterar a senha do Admin, será obrigatório confirmar um PIN enviado para o e-mail do proprietário.'),
        const SizedBox(height:8),
        const Text(ownerEmail,style:TextStyle(fontWeight:FontWeight.w900)),
        const SizedBox(height:12),
        FilledButton.icon(onPressed:sending||saving?null:sendPin,icon:sending?const SizedBox(width:18,height:18,child:CircularProgressIndicator(strokeWidth:2)):const Icon(Icons.email_outlined),label:Text(pinSent?'Reenviar PIN':'Enviar PIN para o e-mail')),
      ]))),
      if(pinSent)...[
        const SizedBox(height:12),
        Card(child:Padding(padding:const EdgeInsets.all(16),child:Column(children:[
          TextField(controller:pin,keyboardType:TextInputType.number,inputFormatters:[FilteringTextInputFormatter.digitsOnly],decoration:const InputDecoration(labelText:'PIN recebido por e-mail *',prefixIcon:Icon(Icons.pin_outlined))),
          const SizedBox(height:10),
          TextField(controller:password,obscureText:hidePassword,decoration:InputDecoration(labelText:'Nova senha / PIN do Admin *',prefixIcon:const Icon(Icons.lock_outline),suffixIcon:IconButton(onPressed:()=>setState(()=>hidePassword=!hidePassword),icon:Icon(hidePassword?Icons.visibility_outlined:Icons.visibility_off_outlined)))),
          const SizedBox(height:10),
          TextField(controller:confirm,obscureText:hidePassword,decoration:const InputDecoration(labelText:'Confirmar nova senha / PIN *',prefixIcon:Icon(Icons.lock_reset_outlined))),
          const SizedBox(height:14),
          SizedBox(width:double.infinity,child:FilledButton.icon(onPressed:saving?null:changePassword,icon:saving?const SizedBox(width:18,height:18,child:CircularProgressIndicator(strokeWidth:2)):const Icon(Icons.security_rounded),label:const Text('Confirmar PIN e alterar senha'))),
        ]))),
      ],
      const SizedBox(height:12),
      const Card(child:ListTile(leading:Icon(Icons.info_outline,color:_blue),title:Text('Regra de segurança'),subtitle:Text('A troca de senha funciona somente online. O código enviado por e-mail é temporário e a alteração fica registrada na Auditoria.'))),
    ]),
  );
}

'''
s=s.replace(marker,security_class+marker,1)

old_actions="      if(isAdmin)quick(Icons.badge_outlined,'Dados da empresa','Empresa operadora',()=>open(const ReportCompanyAdminScreen())),\n"
new_actions=old_actions+"      if(isAdmin)quick(Icons.shield_outlined,'Segurança','Senha e proteção do Admin',()=>open(const AdminSecurityV35Screen())),\n"
assert old_actions in s
s=s.replace(old_actions,new_actions,1)

# Friendly errors for the new security flow.
needle="  if (s.contains('managed_account_use_current_username_and_password')) return 'Use o usuário e a senha/PIN definidos pelo administrador.';\n"
replacement=needle+"  if (s.contains('recovery_email_in_use')) return 'O e-mail de segurança já está vinculado a outra conta.';\n  if (s.contains('admin_only')) return 'Somente o Admin pode alterar esta configuração.';\n  if (s.contains('otp') || s.contains('nonce') || s.contains('reauth')) return 'PIN inválido ou expirado. Solicite um novo código e tente novamente.';\n"
assert needle in s
s=s.replace(needle,replacement,1)

main.write_text(s)
print('V35_ADMIN_EMAIL_PIN_PATCH_OK')
