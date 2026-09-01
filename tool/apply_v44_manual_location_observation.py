from pathlib import Path

p=Path('lib/main_online.dart')
s=p.read_text()

def rep(old,new,label):
    global s
    if s.count(old)!=1:
        raise SystemExit(f'v44 {label} unexpected: {s.count(old)}')
    s=s.replace(old,new,1)

# Estado de contingência e campo Observação.
rep(
"  Position? capturedPosition;\n  DateTime? locationCapturedAt;\n  double? locationAccuracyM;\n  bool locating=false,saving=false;",
"  Position? capturedPosition;\n  DateTime? locationCapturedAt;\n  double? locationAccuracyM;\n  bool manualLocationV44=false;\n  bool autoLocationAttemptedV44=false;\n  bool locating=false,saving=false;",
"location state")

rep(
"  final liters=TextEditingController(),km=TextEditingController(),hour=TextEditingController(),receiver=TextEditingController(),location=TextEditingController(),sale=TextEditingController(),thirdDescription=TextEditingController(),thirdPlate=TextEditingController();",
"  final liters=TextEditingController(),km=TextEditingController(),hour=TextEditingController(),receiver=TextEditingController(),observation=TextEditingController(),location=TextEditingController(),sale=TextEditingController(),thirdDescription=TextEditingController(),thirdPlate=TextEditingController();",
"observation controller")

# Primeira tentativa SEMPRE automática. Se falhar, libera preenchimento manual e não bloqueia a operação.
old_capture="""  Future<bool> captureLocationForSubmission() async {
    if(locating)return false;
    if(mounted)setState(()=>locating=true);
    try{
      final p=await currentPosition();
      if(p==null){if(mounted)ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content:Text('Não foi possível obter uma localização precisa (até 15 m). Ative a localização, aguarde o GPS estabilizar e tente novamente em uma área com melhor sinal.')));return false;}
      capturedPosition=p;
      locationCapturedAt=DateTime.now().toUtc();
      locationAccuracyM=p.accuracy;
      String value='';
      for(var attempt=0;attempt<2&&value.trim().isEmpty;attempt++){
        try{final places=await placemarkFromCoordinates(p.latitude,p.longitude);if(places.isNotEmpty)value=formatPlacemark(places.first);}catch(_){}
        if(value.trim().isEmpty&&attempt==0)await Future<void>.delayed(const Duration(milliseconds:700));
      }
      if(value.trim().isEmpty){if(mounted)ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content:Text('O GPS encontrou o ponto, mas não foi possível identificar o endereço. Verifique a internet e tente novamente.')));return false;}
      location.text=value;
      if(mounted)setState((){});
      return true;
    }finally{if(mounted)setState(()=>locating=false);}
  }
"""
new_capture="""  Future<bool> captureLocationForSubmission() async {
    if(locating)return false;
    // A primeira tentativa de cada abastecimento é sempre automática.
    if(manualLocationV44&&autoLocationAttemptedV44){
      if(location.text.trim().isEmpty){
        if(mounted)ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content:Text('Informe a localização do abastecimento.')));
        return false;
      }
      capturedPosition=null;
      locationCapturedAt=DateTime.now().toUtc();
      locationAccuracyM=null;
      return true;
    }
    if(mounted)setState(()=>locating=true);
    try{
      autoLocationAttemptedV44=true;
      final pos=await currentPosition();
      if(pos==null){
        capturedPosition=null;
        locationAccuracyM=null;
        manualLocationV44=true;
        location.clear();
        if(mounted){
          setState((){});
          ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content:Text('Não foi possível obter a localização automaticamente. Preencha o endereço manualmente para continuar.')));
        }
        return false;
      }
      String value='';
      for(var attempt=0;attempt<2&&value.trim().isEmpty;attempt++){
        try{final places=await placemarkFromCoordinates(pos.latitude,pos.longitude);if(places.isNotEmpty)value=formatPlacemark(places.first);}catch(_){}
        if(value.trim().isEmpty&&attempt==0)await Future<void>.delayed(const Duration(milliseconds:500));
      }
      if(value.trim().isEmpty){
        capturedPosition=null;
        locationAccuracyM=null;
        manualLocationV44=true;
        location.clear();
        if(mounted){
          setState((){});
          ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content:Text('O ponto GPS foi encontrado, mas o endereço não pôde ser identificado. Preencha a localização manualmente para continuar.')));
        }
        return false;
      }
      manualLocationV44=false;
      capturedPosition=pos;
      locationCapturedAt=DateTime.now().toUtc();
      locationAccuracyM=pos.accuracy;
      location.text=value;
      if(mounted)setState((){});
      return true;
    }finally{if(mounted)setState(()=>locating=false);}
  }
"""
rep(old_capture,new_capture,"capture contingency")

# Confirmação: endereço automático ou manual, com indicação clara da origem.
rep(
"Text('Responsável pelo recebimento do abastecimento: ${receiver.text.trim()}'),const SizedBox(height:8),Text('Endereço do abastecimento: ${location.text.trim()}',style:const TextStyle(fontWeight:FontWeight.w700)),if(capturedPosition!=null)Text('Coordenadas: ${capturedPosition!.latitude.toStringAsFixed(6)}, ${capturedPosition!.longitude.toStringAsFixed(6)}',style:const TextStyle(fontSize:12,color:Colors.black54)),Text(locationMeta(),style:const TextStyle(fontSize:12,color:Colors.black54))",
"Text('Responsável pelo recebimento do abastecimento: ${receiver.text.trim()}'),if(observation.text.trim().isNotEmpty)Text('Observação: ${observation.text.trim()}'),const SizedBox(height:8),Text('Endereço do abastecimento: ${location.text.trim()}',style:const TextStyle(fontWeight:FontWeight.w700)),Text(manualLocationV44?'Localização informada manualmente':'Localização obtida automaticamente',style:const TextStyle(fontSize:12,color:Colors.black54)),if(capturedPosition!=null)Text('Coordenadas: ${capturedPosition!.latitude.toStringAsFixed(6)}, ${capturedPosition!.longitude.toStringAsFixed(6)}',style:const TextStyle(fontSize:12,color:Colors.black54)),if(capturedPosition!=null)Text(locationMeta(),style:const TextStyle(fontSize:12,color:Colors.black54))",
"confirmation")

# Salva Observação em p_notes, que já existe no backend.
rep(
"extraPhoto:u[3],salePrice:sale.text.trim().isNotEmpty?_num(sale.text.replaceAll(',','.')):null,fuelType:fuel,location:location.text.trim()",
"extraPhoto:u[3],salePrice:sale.text.trim().isNotEmpty?_num(sale.text.replaceAll(',','.')):null,notes:observation.text.trim().isEmpty?null:observation.text.trim(),fuelType:fuel,location:location.text.trim()",
"notes save")

# UI: Observação + localização somente leitura até a tentativa automática falhar; depois fica digitável.
old_location="""      const SizedBox(height:10),TextField(controller:receiver,enabled:!saving,decoration:const InputDecoration(labelText:'Responsável pelo recebimento do abastecimento *')),const SizedBox(height:10),
      InputDecorator(decoration:const InputDecoration(labelText:'Localização do abastecimento *',prefixIcon:Icon(Icons.location_on_outlined)),child:Text(location.text.trim().isEmpty?'Será capturada ao concluir o abastecimento.':location.text.trim(),softWrap:true)),
      const SizedBox(height:12),
"""
new_location="""      const SizedBox(height:10),TextField(controller:receiver,enabled:!saving,decoration:const InputDecoration(labelText:'Responsável pelo recebimento do abastecimento *')),
      const SizedBox(height:10),TextField(controller:observation,enabled:!saving,maxLines:3,textCapitalization:TextCapitalization.sentences,decoration:const InputDecoration(labelText:'Observação')),
      const SizedBox(height:10),
      if(manualLocationV44)TextField(controller:location,enabled:!saving,maxLines:2,textCapitalization:TextCapitalization.words,decoration:const InputDecoration(labelText:'Localização do abastecimento *',prefixIcon:Icon(Icons.location_on_outlined),helperText:'Preencha manualmente porque a captura automática não foi possível.'))
      else InputDecorator(decoration:const InputDecoration(labelText:'Localização do abastecimento',prefixIcon:Icon(Icons.location_on_outlined)),child:Text(location.text.trim().isEmpty?'Será buscada automaticamente ao concluir o abastecimento.':location.text.trim(),softWrap:true)),
      const SizedBox(height:12),
"""
rep(old_location,new_location,"location field")

rep(
"  @override void dispose(){for(final c in [liters,km,hour,receiver,location,sale,thirdDescription,thirdPlate]){c.dispose();}super.dispose();}",
"  @override void dispose(){for(final c in [liters,km,hour,receiver,observation,location,sale,thirdDescription,thirdPlate]){c.dispose();}super.dispose();}",
"dispose")

# PDF: o backend já entrega notes; exibe como Observação no abastecimento.
if "'Observações', '${x['notes']}'" in s:
    s=s.replace("'Observações', '${x['notes']}'","'Observação', '${x['notes']}'",1)

p.write_text(s)

checks=[
    "bool manualLocationV44=false",
    "bool autoLocationAttemptedV44=false",
    "A primeira tentativa de cada abastecimento é sempre automática.",
    "Preencha o endereço manualmente para continuar.",
    "labelText:'Observação'",
    "notes:observation.text.trim().isEmpty?null:observation.text.trim()",
    "Localização informada manualmente",
    "Localização obtida automaticamente",
    "helperText:'Preencha manualmente porque a captura automática não foi possível.'",
]
for x in checks:
    if x not in s: raise SystemExit('v44 missing marker: '+x)
print('V44_MANUAL_LOCATION_OBSERVATION_OK')
