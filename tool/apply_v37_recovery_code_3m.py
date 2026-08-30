from pathlib import Path

main=Path('lib/main_online.dart')
s=main.read_text()
start=s.index('  Future<void> recoverAdmin() async {')
end=s.index('\n\n  @override\n  Widget build', start)
new=r'''  Future<void> recoverAdmin() async {
    if(!offlineStore.online.value){
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content:Text('Conecte-se à internet para recuperar o acesso do Admin.')));
      return;
    }

    Future<Map<String,dynamic>> requestCode() async {
      final res=await Supabase.instance.client.functions.invoke('admin-recovery',body:{'action':'request_recovery'});
      final data=_map(res.data);
      if(res.status<200||res.status>=300||data['ok']!=true){
        throw Exception('${data['error']??'Não foi possível gerar o código de recuperação.'}');
      }
      return data;
    }

    Map<String,dynamic> challenge;
    setState(()=>busy=true);
    try{
      challenge=await requestCode();
    }catch(e){
      if(mounted){
        final msg=e.toString().replaceFirst('Exception: ','');
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content:Text('Não foi possível enviar o código: $msg')));
      }
      return;
    }finally{
      if(mounted)setState(()=>busy=false);
    }

    final code=TextEditingController(),next=TextEditingController(),confirm=TextEditingController();
    bool saving=false,requesting=false,hide=true;
    int challengeId=int.tryParse('${challenge['challenge_id']}')??0;
    DateTime deadline=DateTime.tryParse('${challenge['expires_at']}')?.toUtc()??DateTime.now().toUtc().add(const Duration(minutes:3));
    Timer? ticker;

    int remainingSeconds(){
      final n=deadline.difference(DateTime.now().toUtc()).inSeconds;
      if(n<0)return 0;
      if(n>180)return 180;
      return n;
    }
    String clock(){
      final total=remainingSeconds();
      final mm=(total~/60).toString().padLeft(2,'0');
      final ss=(total%60).toString().padLeft(2,'0');
      return '$mm:$ss';
    }

    try{
      await showDialog<void>(context:context,barrierDismissible:false,builder:(dialogContext)=>StatefulBuilder(builder:(ctx,setLocal){
        ticker??=Timer.periodic(const Duration(seconds:1),(_){
          if(!ctx.mounted)return;
          setLocal((){});
          if(remainingSeconds()<=0){ticker?.cancel();ticker=null;}
        });
        final expired=remainingSeconds()<=0;
        return AlertDialog(
          title:const Text('Recuperar acesso do Admin'),
          content:SizedBox(width:420,child:SingleChildScrollView(child:Column(mainAxisSize:MainAxisSize.min,crossAxisAlignment:CrossAxisAlignment.start,children:[
            const Text('Um novo código foi enviado para o e-mail de segurança. Somente o código mais recente é válido.'),
            const SizedBox(height:8),
            const Text('marinhrodrigo@gmail.com',style:TextStyle(fontWeight:FontWeight.w800)),
            const SizedBox(height:12),
            Container(
              width:double.infinity,
              padding:const EdgeInsets.symmetric(horizontal:14,vertical:12),
              decoration:BoxDecoration(borderRadius:BorderRadius.circular(12),color:expired?Colors.red.withValues(alpha:.08):_blue.withValues(alpha:.08)),
              child:Row(children:[
                Icon(expired?Icons.timer_off_outlined:Icons.timer_outlined,color:expired?Colors.red:_blue),
                const SizedBox(width:10),
                Expanded(child:Text(expired?'Código expirado':'Código expira em ${clock()}',style:TextStyle(fontWeight:FontWeight.w900,color:expired?Colors.red:_blue))),
              ]),
            ),
            const SizedBox(height:10),
            TextButton.icon(
              onPressed:requesting||saving?null:() async {
                setLocal(()=>requesting=true);
                try{
                  final fresh=await requestCode();
                  challengeId=int.tryParse('${fresh['challenge_id']}')??0;
                  deadline=DateTime.tryParse('${fresh['expires_at']}')?.toUtc()??DateTime.now().toUtc().add(const Duration(minutes:3));
                  code.clear();
                  ticker?.cancel();ticker=null;
                  if(ctx.mounted){
                    setLocal(()=>requesting=false);
                    ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content:Text('Novo código enviado. O prazo de 3 minutos foi reiniciado.')));
                  }
                }catch(e){
                  if(ctx.mounted){
                    setLocal(()=>requesting=false);
                    final msg=e.toString().replaceFirst('Exception: ','');
                    ScaffoldMessenger.of(context).showSnackBar(SnackBar(content:Text('Não foi possível gerar um novo código: $msg')));
                  }
                }
              },
              icon:requesting?const SizedBox(width:18,height:18,child:CircularProgressIndicator(strokeWidth:2)):const Icon(Icons.refresh_rounded),
              label:Text(expired?'Gerar novo código':'Gerar outro código'),
            ),
            const SizedBox(height:6),
            TextField(controller:code,keyboardType:TextInputType.number,inputFormatters:[FilteringTextInputFormatter.digitsOnly],maxLength:6,decoration:const InputDecoration(labelText:'Código de 6 dígitos *',prefixIcon:Icon(Icons.pin_outlined))),
            const SizedBox(height:8),
            TextField(controller:next,obscureText:hide,decoration:InputDecoration(labelText:'Nova senha / PIN do Admin *',prefixIcon:const Icon(Icons.lock_outline),suffixIcon:IconButton(onPressed:()=>setLocal(()=>hide=!hide),icon:Icon(hide?Icons.visibility_outlined:Icons.visibility_off_outlined)))),
            const SizedBox(height:10),
            TextField(controller:confirm,obscureText:hide,decoration:const InputDecoration(labelText:'Confirmar nova senha / PIN *',prefixIcon:Icon(Icons.lock_reset_outlined))),
          ]))),
          actions:[
            TextButton(onPressed:saving||requesting?null:()=>Navigator.pop(ctx),child:const Text('Cancelar')),
            FilledButton(onPressed:saving||requesting||expired?null:() async {
              final pin=code.text.trim(),password=next.text,again=confirm.text;
              if(pin.length!=6){ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content:Text('Informe o código de 6 dígitos recebido por e-mail.')));return;}
              if(password.length<4){ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content:Text('A nova senha/PIN deve ter pelo menos 4 caracteres.')));return;}
              if(password!=again){ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content:Text('A confirmação da nova senha não confere.')));return;}
              setLocal(()=>saving=true);
              try{
                final res=await Supabase.instance.client.functions.invoke('admin-recovery',body:{'action':'complete_recovery','challenge_id':challengeId,'code':pin,'password':password});
                final data=_map(res.data);
                if(res.status<200||res.status>=300||data['ok']!=true)throw Exception('${data['error']??'Não foi possível recuperar o Admin.'}');
                ticker?.cancel();ticker=null;
                if(ctx.mounted)Navigator.pop(ctx);
                user.text='admin';pass.clear();
                if(mounted)await showDialog<void>(context:context,builder:(okCtx)=>AlertDialog(title:const Text('Acesso recuperado ✓'),content:const Text('A senha do Admin foi redefinida com sucesso. Agora entre com o usuário admin e a nova senha escolhida.'),actions:[FilledButton(onPressed:()=>Navigator.pop(okCtx),child:const Text('OK'))]));
              }catch(e){
                final msg=e.toString().replaceFirst('Exception: ','');
                String friendly=msg;
                if(msg.contains('invalid_recovery_code'))friendly='Código inválido. Confira o e-mail e tente novamente.';
                if(msg.contains('recovery_expired'))friendly='Este código expirou. Toque em Gerar novo código.';
                if(msg.contains('recovery_locked'))friendly='Recuperação bloqueada após várias tentativas inválidas. Gere um novo código.';
                if(mounted)ScaffoldMessenger.of(context).showSnackBar(SnackBar(content:Text(friendly)));
                if(ctx.mounted)setLocal(()=>saving=false);
              }
            },child:saving?const SizedBox(width:18,height:18,child:CircularProgressIndicator(strokeWidth:2)):const Text('Redefinir senha')),
          ],
        );
      }));
    } finally {
      ticker?.cancel();
      code.dispose();next.dispose();confirm.dispose();
    }
  }
'''
s=s[:start]+new+s[end:]
main.write_text(s)
print('V37_RECOVERY_CODE_3M_PATCH_OK')
