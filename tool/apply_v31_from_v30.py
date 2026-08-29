from pathlib import Path
import re

main=Path('lib/main_online.dart')
users=Path('lib/v29_features.dart')
s=main.read_text()
u=users.read_text()

needle="part 'v30_features.dart';\n"
if "part 'v31_features.dart';" not in s:
    if needle not in s: raise SystemExit('v31: v30 part marker missing')
    s=s.replace(needle,needle+"part 'v31_features.dart';\n",1)

# Route Operacional to v31. Keep v30 class/source intact as rollback reference.
if 'OperationalHomeV31Screen(profile:' not in s:
    old="if(operational)return OperationalHomeV30Screen(profile:profile!,onLogout:_logout);"
    new="if(operational)return OperationalHomeV31Screen(profile:profile!,onLogout:_logout);"
    if old not in s: raise SystemExit('v31: operational root route missing')
    s=s.replace(old,new,1)

create_method=r'''  Future<void> createUser() async {
    final name=TextEditingController(),username=TextEditingController(),password=TextEditingController(text:'1234');
    String? role;
    final ok=await showDialog<bool>(context:context,builder:(ctx)=>StatefulBuilder(builder:(ctx,setD)=>AlertDialog(
      title:const Text('Cadastrar usuário'),
      content:SizedBox(width:520,child:SingleChildScrollView(child:Column(mainAxisSize:MainAxisSize.min,children:[
        TextField(controller:name,decoration:const InputDecoration(labelText:'Nome *')),const SizedBox(height:9),
        TextField(controller:username,decoration:const InputDecoration(labelText:'Usuário / login *')),const SizedBox(height:9),
        TextField(controller:password,obscureText:true,decoration:const InputDecoration(labelText:'Senha / PIN inicial *')),const SizedBox(height:9),
        DropdownButtonFormField<String>(value:role,decoration:const InputDecoration(labelText:'Função *'),items:const [DropdownMenuItem(value:'supervisor',child:Text('Supervisor')),DropdownMenuItem(value:'manager',child:Text('Gerente')),DropdownMenuItem(value:'operator',child:Text('Operacional'))],onChanged:(v)=>setD(()=>role=v)),
        if(role=='operator')const Padding(padding:EdgeInsets.only(top:10),child:Align(alignment:Alignment.centerLeft,child:Text('O Operacional escolherá uma unidade disponível ao iniciar o trabalho.',style:TextStyle(color:Colors.black54,fontSize:12)))),
        const SizedBox(height:10),const Align(alignment:Alignment.centerLeft,child:Text('As permissões individuais são configuradas depois em “Editar usuário”.',style:TextStyle(color:Colors.black54,fontSize:12))),
      ]))),
      actions:[TextButton(onPressed:()=>Navigator.pop(ctx,false),child:const Text('Cancelar')),FilledButton(onPressed:()=>Navigator.pop(ctx,true),child:const Text('Cadastrar'))],
    )));
    if(ok==true){
      if(name.text.trim().isEmpty||username.text.trim().isEmpty||password.text.trim().length<4||role==null){
        if(mounted)ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content:Text('Preencha os campos obrigatórios.')));
      }else{
        setState(()=>busy=true);
        try{
          if(role=='operator'){
            await api.operatorUserActionV31({'action':'create_operator','name':name.text.trim(),'username':username.text.trim(),'password':password.text});
          }else{
            await api.userActionMap({'action':'create_manager','name':name.text.trim(),'username':username.text.trim(),'password':password.text,'role':role});
          }
          await load();if(mounted)ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content:Text('Usuário cadastrado com sucesso ✓')));
        }catch(e){if(mounted)ScaffoldMessenger.of(context).showSnackBar(SnackBar(content:Text('Erro ao cadastrar: ${_friendlyError(e)}')));}
        finally{if(mounted)setState(()=>busy=false);}
      }
    }
    name.dispose();username.dispose();password.dispose();
  }

'''

edit_method=r'''  Future<void> editUser(Map<String,dynamic> u) async {
    final name=TextEditingController(text:'${u['name']??''}'),username=TextEditingController(text:'${u['username']??''}'),password=TextEditingController();
    final role='${u['role']}';bool active=u['active']==true;
    Map<String,bool> permissions=<String,bool>{for(final k in keys)k:_map(u['permissions'])[k]==true};
    final ok=await showDialog<bool>(context:context,builder:(ctx)=>StatefulBuilder(builder:(ctx,setD)=>AlertDialog(
      title:const Text('Editar usuário'),
      content:SizedBox(width:560,child:SingleChildScrollView(child:Column(mainAxisSize:MainAxisSize.min,children:[
        TextField(controller:name,decoration:const InputDecoration(labelText:'Nome *')),const SizedBox(height:8),
        TextField(controller:username,decoration:const InputDecoration(labelText:'Usuário / login *')),const SizedBox(height:8),
        TextField(controller:password,obscureText:true,decoration:const InputDecoration(labelText:'Nova senha / PIN (deixe em branco para manter)')),const SizedBox(height:8),
        ListTile(contentPadding:EdgeInsets.zero,leading:const Icon(Icons.badge_outlined,color:_blue),title:const Text('Função'),subtitle:Text(roleLabel(role))),
        if(role=='operator')const Align(alignment:Alignment.centerLeft,child:Padding(padding:EdgeInsets.only(bottom:8),child:Text('A unidade de abastecimento é escolhida pelo próprio Operacional durante o trabalho.',style:TextStyle(color:Colors.black54,fontSize:12)))),
        SwitchListTile(contentPadding:EdgeInsets.zero,title:const Text('Acesso ativo',style:TextStyle(fontWeight:FontWeight.w800)),subtitle:Text(active?'Pode fazer login normalmente':'Continua cadastrado, mas não pode acessar o sistema'),value:active,onChanged:(v)=>setD(()=>active=v)),
        const Divider(height:24),
        Row(children:[Expanded(child:Text('Permissões',style:Theme.of(ctx).textTheme.titleMedium?.copyWith(fontWeight:FontWeight.w900))),TextButton(onPressed:()=>setD(()=>permissions=roleDefaults(role)),child:const Text('Usar padrão'))]),
        ...keys.map((k)=>SwitchListTile(contentPadding:EdgeInsets.zero,title:Text(_permissionLabelV23(k)),value:permissions[k]==true,onChanged:(v)=>setD(()=>permissions[k]=v))),
      ]))),
      actions:[TextButton(onPressed:()=>Navigator.pop(ctx,false),child:const Text('Cancelar')),FilledButton(onPressed:()=>Navigator.pop(ctx,true),child:const Text('Salvar'))],
    )));
    if(ok==true){
      if(name.text.trim().isEmpty||username.text.trim().isEmpty||(password.text.isNotEmpty&&password.text.length<4)){
        if(mounted)ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content:Text('Confira os campos obrigatórios.')));
      }else{
        setState(()=>busy=true);
        try{
          final userId='${u['user_id']}';
          if(role=='operator'){
            await api.operatorUserActionV31({'action':'update_operator','user_id':userId,'name':name.text.trim(),'username':username.text.trim(),'password':password.text});
            if(active!=(u['active']==true))await api.operatorUserActionV31({'action':'set_operator_active','user_id':userId,'active':active});
          }else{
            await api.userActionMap({'action':'update_manager','user_id':userId,'name':name.text.trim(),'username':username.text.trim(),'password':password.text,'role':role});
            if(active!=(u['active']==true))await api.userActionMap({'action':'set_manager_active','user_id':userId,'active':active});
          }
          for(final k in keys){await api.adminSetUserPermissionV29(userId,k,permissions[k]==true);}
          await load();if(mounted)ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content:Text('Usuário atualizado com sucesso ✓')));
        }catch(e){if(mounted)ScaffoldMessenger.of(context).showSnackBar(SnackBar(content:Text('Erro ao salvar: ${_friendlyError(e)}')));}
        finally{if(mounted)setState(()=>busy=false);}
      }
    }
    name.dispose();username.dispose();password.dispose();
  }

'''

toggle_method=r'''  Future<void> toggleAccess(Map<String,dynamic> u) async {
    setState(()=>busy=true);
    try{
      final role='${u['role']}',active=u['active']!=true,userId='${u['user_id']}';
      if(role=='operator'){
        await api.operatorUserActionV31({'action':'set_operator_active','user_id':userId,'active':active});
      }else{
        await api.userActionMap({'action':'set_manager_active','user_id':userId,'active':active});
      }
      await load();
    }catch(e){if(mounted)ScaffoldMessenger.of(context).showSnackBar(SnackBar(content:Text(_friendlyError(e))));}
    finally{if(mounted)setState(()=>busy=false);}
  }

'''

def replace_between(text,start_marker,end_marker,replacement,label):
    a=text.find(start_marker)
    if a<0: raise SystemExit(f'v31: {label} start missing')
    b=text.find(end_marker,a)
    if b<0: raise SystemExit(f'v31: {label} end missing')
    return text[:a]+replacement+text[b:]

u=replace_between(u,'  Future<void> createUser() async {','  Future<void> editUser(',create_method,'createUser')
u=replace_between(u,'  Future<void> editUser(Map<String,dynamic> u) async {','  Future<void> toggleAccess(',edit_method,'editUser')
end_toggle='  Future<void> disconnectUser(' if '  Future<void> disconnectUser(' in u else '  Future<void> deleteUser('
u=replace_between(u,'  Future<void> toggleAccess(Map<String,dynamic> u) async {',end_toggle,toggle_method,'toggleAccess')

# Admin list no longer displays a legacy static unit as if it were the user's permanent assignment.
u=u.replace("${u['active']==true?'Acesso ativo':'Acesso bloqueado'}${role=='operator'?' • ${assignmentLabel(u)}':''}","${u['active']==true?'Acesso ativo':'Acesso bloqueado'}")
u=u.replace("Cadastre Supervisor, Gerente ou Operacional. As permissões individuais ficam em Editar usuário.","Cadastre Supervisor, Gerente ou Operacional. O Operacional escolhe uma unidade disponível durante o trabalho.")

main.write_text(s)
users.write_text(u)

checks_main=["part 'v31_features.dart';","OperationalHomeV31Screen(profile:","rca_record_fueling_v30"]
for x in checks_main:
    if x not in s: raise SystemExit('v31 missing main marker: '+x)
checks_users=["action':'create_operator'","action':'update_operator'","action':'set_operator_active'","Desconectar usuário"]
for x in checks_users:
    if x not in u: raise SystemExit('v31 missing users marker: '+x)
for bad in ["labelText:'Unidade que irá operar *'","role=='operator'&&selected==null","assignmentPayload(selected!)"]:
    if bad in u: raise SystemExit('v31 legacy assignment remains: '+bad)
print('v31 patch applied successfully')
