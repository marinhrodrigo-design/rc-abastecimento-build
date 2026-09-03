from pathlib import Path
p=Path('lib/main_online.dart')
s=p.read_text()
old="""    if(machine!=null){
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
"""
new="""    if(machine!=null&&offlineStore.online.value){
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
      }catch(e){
        if(_isNetworkError(e)){
          offlineStore.markOffline();
        }else{
          if(mounted)ScaffoldMessenger.of(context).showSnackBar(SnackBar(content:Text(_friendlyError(e))));
          return;
        }
      }
    }
"""
assert old in s, 'Bloco de validação de KM/Horímetro não encontrado'
s=s.replace(old,new,1)
p.write_text(s)
print('VALIDACAO_PATCH_V55_OFFLINE_OK')
