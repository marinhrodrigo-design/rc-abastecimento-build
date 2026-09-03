from pathlib import Path

p=Path('lib/main_online.dart')
s=p.read_text()

old="""      if(value.trim().isEmpty){
        capturedPosition=null;
        locationAccuracyM=null;
        location.clear();
        if(locationAttemptsV52>=2)manualLocationV44=true;
        if(mounted){
          setState((){});
          final msg=locationAttemptsV52>=2
            ?'O GPS foi encontrado, mas o endereço não pôde ser identificado. Informe a localização manualmente.'
            :'O GPS foi encontrado, mas o endereço não pôde ser identificado. Toque no campo Localização para tentar novamente.';
          ScaffoldMessenger.of(context).showSnackBar(SnackBar(content:Text(msg)));
        }
        return false;
      }
"""
new="""      if(value.trim().isEmpty){
        // O GPS funcionou: preserve as coordenadas originais mesmo se o endereço
        // não puder ser resolvido sem internet. O usuário digita apenas o endereço.
        capturedPosition=pos;
        locationCapturedAt=DateTime.now().toUtc();
        locationAccuracyM=pos.accuracy;
        location.clear();
        manualLocationV44=true;
        if(mounted){
          setState((){});
          ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content:Text('GPS capturado. Informe apenas o endereço manualmente.')));
        }
        return false;
      }
"""
assert old in s, 'bloco de geocodificação não encontrado'
s=s.replace(old,new,1)

old2="""    if(manualLocationV44){
      if(location.text.trim().isEmpty){
        if(mounted)ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content:Text('Informe a localização do abastecimento.')));
        return false;
      }
      capturedPosition=null;
      locationCapturedAt=DateTime.now().toUtc();
      locationAccuracyM=null;
      return true;
    }
"""
new2="""    if(manualLocationV44){
      if(location.text.trim().isEmpty){
        if(mounted)ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content:Text('Informe a localização do abastecimento.')));
        return false;
      }
      // Se o GPS já foi capturado, mantenha coordenadas, horário e precisão.
      // Só fica 100% manual quando realmente não houve posição GPS disponível.
      if(capturedPosition==null){
        locationCapturedAt=DateTime.now().toUtc();
        locationAccuracyM=null;
      }
      return true;
    }
"""
assert old2 in s, 'bloco manual de envio não encontrado'
s=s.replace(old2,new2,1)

old3="""      if(manualLocationV44)TextField(controller:location,enabled:!saving,maxLines:2,textCapitalization:TextCapitalization.words,decoration:const InputDecoration(labelText:'Localização do abastecimento *',prefixIcon:Icon(Icons.location_on_outlined),helperText:'A busca automática falhou duas vezes. Informe o endereço manualmente.'))
"""
new3="""      if(manualLocationV44)TextField(controller:location,enabled:!saving,maxLines:2,textCapitalization:TextCapitalization.words,decoration:InputDecoration(labelText:'Localização do abastecimento *',prefixIcon:const Icon(Icons.location_on_outlined),helperText:capturedPosition!=null?'GPS capturado. Informe apenas o endereço manualmente.':'Localização automática indisponível. Informe o endereço manualmente.'))
"""
assert old3 in s, 'campo manual não encontrado'
s=s.replace(old3,new3,1)

# Nunca exponha o envelope técnico PostgrestException ao usuário.
anchor="""String _friendlyError(Object e) {
  final s = e.toString().replaceFirst('Exception: ', '');
"""
insert="""String _friendlyError(Object e) {
  var s = e.toString().replaceFirst('Exception: ', '');
  final pg=RegExp(r'PostgrestException\\(message:\\s*(.*?),\\s*code:',dotAll:true).firstMatch(s);
  if(pg!=null)s=(pg.group(1)??'').trim();
  if(s.contains('Localização GPS obrigatória no momento do abastecimento')||s.contains('Informe a localização do abastecimento')) return 'Informe a localização do abastecimento. Se o GPS não estiver disponível, preencha o endereço manualmente.';
"""
assert anchor in s, 'friendlyError não encontrado'
s=s.replace(anchor,insert,1)

s=s.replace("child: Text('v62'","child: Text('v63'",1)
p.write_text(s)
print('PATCH_V63_MANUAL_LOCATION_OK')
