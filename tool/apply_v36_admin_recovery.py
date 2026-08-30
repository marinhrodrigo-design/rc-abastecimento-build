from pathlib import Path

main=Path('lib/main_online.dart')
s=main.read_text()

needle="""  Future<void> submit() async {
    if (user.text.trim().isEmpty || pass.text.isEmpty) return;
    setState(() => busy = true);
    await widget.onLogin(user.text, pass.text);
    if (mounted) setState(() => busy = false);
  }

  @override
"""
insert="""  Future<void> submit() async {
    if (user.text.trim().isEmpty || pass.text.isEmpty) return;
    setState(() => busy = true);
    await widget.onLogin(user.text, pass.text);
    if (mounted) setState(() => busy = false);
  }

  Future<void> recoverAdmin() async {
    final code=TextEditingController(),next=TextEditingController(),confirm=TextEditingController();
    bool saving=false,hide=true;
    try{
      await showDialog<void>(context:context,barrierDismissible:false,builder:(dialogContext)=>StatefulBuilder(builder:(ctx,setLocal)=>AlertDialog(
        title:const Text('Recuperar acesso do Admin'),
        content:SizedBox(width:420,child:SingleChildScrollView(child:Column(mainAxisSize:MainAxisSize.min,crossAxisAlignment:CrossAxisAlignment.start,children:[
          const Text('Use o código temporário enviado para o e-mail de segurança e escolha uma nova senha para o Admin.'),
          const SizedBox(height:8),
          const Text('E-mail de segurança: marinhrodrigo@gmail.com',style:TextStyle(fontWeight:FontWeight.w800)),
          const SizedBox(height:14),
          TextField(controller:code,keyboardType:TextInputType.number,inputFormatters:[FilteringTextInputFormatter.digitsOnly],maxLength:6,decoration:const InputDecoration(labelText:'Código de 6 dígitos *',prefixIcon:Icon(Icons.pin_outlined))),
          const SizedBox(height:8),
          TextField(controller:next,obscureText:hide,decoration:InputDecoration(labelText:'Nova senha / PIN do Admin *',prefixIcon:const Icon(Icons.lock_outline),suffixIcon:IconButton(onPressed:()=>setLocal(()=>hide=!hide),icon:Icon(hide?Icons.visibility_outlined:Icons.visibility_off_outlined)))),
          const SizedBox(height:10),
          TextField(controller:confirm,obscureText:hide,decoration:const InputDecoration(labelText:'Confirmar nova senha / PIN *',prefixIcon:Icon(Icons.lock_reset_outlined))),
        ]))),
        actions:[
          TextButton(onPressed:saving?null:()=>Navigator.pop(ctx),child:const Text('Cancelar')),
          FilledButton(onPressed:saving?null:() async {
            final pin=code.text.trim(),password=next.text,again=confirm.text;
            if(pin.length!=6){ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content:Text('Informe o código de 6 dígitos recebido por e-mail.')));return;}
            if(password.length<4){ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content:Text('A nova senha/PIN deve ter pelo menos 4 caracteres.')));return;}
            if(password!=again){ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content:Text('A confirmação da nova senha não confere.')));return;}
            setLocal(()=>saving=true);
            try{
              final res=await Supabase.instance.client.functions.invoke('admin-recovery',body:{'action':'complete_recovery','code':pin,'password':password});
              final data=_map(res.data);
              if(res.status<200||res.status>=300||data['ok']!=true)throw Exception('${data['error']??'Não foi possível recuperar o Admin.'}');
              if(ctx.mounted)Navigator.pop(ctx);
              user.text='admin';pass.clear();
              if(mounted)await showDialog<void>(context:context,builder:(okCtx)=>AlertDialog(title:const Text('Acesso recuperado ✓'),content:const Text('A senha do Admin foi redefinida com sucesso. Agora entre com o usuário admin e a nova senha escolhida.'),actions:[FilledButton(onPressed:()=>Navigator.pop(okCtx),child:const Text('OK'))]));
            }catch(e){
              final msg='${e.toString().replaceFirst('Exception: ','')}';
              String friendly=msg;
              if(msg.contains('invalid_recovery_code'))friendly='Código inválido. Confira o e-mail e tente novamente.';
              if(msg.contains('recovery_expired'))friendly='Este código expirou. Solicite um novo código de recuperação.';
              if(msg.contains('recovery_locked'))friendly='Recuperação bloqueada após várias tentativas inválidas.';
              if(mounted)ScaffoldMessenger.of(context).showSnackBar(SnackBar(content:Text(friendly)));
              setLocal(()=>saving=false);
            }
          },child:saving?const SizedBox(width:18,height:18,child:CircularProgressIndicator(strokeWidth:2)):const Text('Redefinir senha')),
        ],
      )));
    } finally {code.dispose();next.dispose();confirm.dispose();}
  }

  @override
"""
assert needle in s
s=s.replace(needle,insert,1)

old="""                        SizedBox(
                          width: double.infinity,
                          height: 52,
                          child: FilledButton.icon(
                            onPressed: busy ? null : submit,
                            icon: busy ? const SizedBox.square(dimension: 20, child: CircularProgressIndicator(strokeWidth: 2)) : const Icon(Icons.login_rounded),
                            label: const Text('Entrar'),
                          ),
                        ),
"""
new=old+"""                        const SizedBox(height: 8),
                        TextButton.icon(onPressed:busy?null:recoverAdmin,icon:const Icon(Icons.admin_panel_settings_outlined),label:const Text('Recuperar acesso do Admin')),
"""
assert old in s
s=s.replace(old,new,1)

old_text="const Text('Acesso de teste: admin / 1234 • motorista / 1234', textAlign: TextAlign.center, style: TextStyle(fontWeight: FontWeight.w700, color: Color(0xFF60758D))),"
new_text="const Text('Use o usuário e a senha cadastrados pelo administrador.', textAlign: TextAlign.center, style: TextStyle(fontWeight: FontWeight.w700, color: Color(0xFF60758D))),"
assert old_text in s
s=s.replace(old_text,new_text,1)

main.write_text(s)
print('V36_ADMIN_RECOVERY_PATCH_OK')
