from pathlib import Path

p=Path('lib/main_online.dart')
s=p.read_text()

# Offline optimistic bookkeeping must recognize the new RPC too.
s=s.replace("rpc == 'rca_record_fueling_v30'))", "rpc == 'rca_record_fueling_v30' || rpc == 'rca_record_fueling_v32'))", 1)

api_start=s.index('  Future<Map<String,dynamic>> fuelingV22({')
api_end=s.index('\n  Future<Map<String,dynamic>> dashboardV22()',api_start)
new_api="""  Future<Map<String,dynamic>> fuelingV22({required int sourceTankId,int? workId,int? machineId,int? thirdId,required double liters,double? km,double? hourmeter,required String receiver,required String receiverSignature,required String operatorSignature,required String meterPhoto,required String totalizerPhoto,required String identityPhoto,required String identityKind,String? extraPhoto,double? salePrice,String? notes,required String fuelType,required String location,double? latitude,double? longitude,DateTime? locationCapturedAt,double? locationAccuracyM}) async => offlineStore.executeOrQueue('rca_record_fueling_v32',{'p_source_tank_id':sourceTankId,'p_work_id':workId,'p_machine_id':machineId,'p_third_party_vehicle_id':thirdId,'p_third_party_plate':null,'p_third_party_company':null,'p_third_party_description':null,'p_liters':liters,'p_km_value':km,'p_hourmeter_value':hourmeter,'p_receiver_name':receiver,'p_receiver_company':null,'p_receiver_signature_path':receiverSignature,'p_operator_signature_path':operatorSignature,'p_meter_photo_path':meterPhoto,'p_totalizer_photo_path':totalizerPhoto,'p_identity_photo_path':identityPhoto,'p_identity_evidence_kind':identityKind,'p_extra_photo_path':extraPhoto,'p_sale_price_per_liter':salePrice,'p_notes':notes,'p_lubricated':false,'p_latitude':latitude,'p_longitude':longitude,'p_fuel_type':fuelType,'p_location_address':location,'p_location_captured_at':locationCapturedAt?.toUtc().toIso8601String(),'p_location_accuracy_m':locationAccuracyM});"""
s=s[:api_start]+new_api+s[api_end:]

start=s.index('class FuelingV23Screen extends StatefulWidget')
end=s.index('class FuelDashboardV23Screen extends StatefulWidget',start)
new_class=r'''class FuelingV23Screen extends StatefulWidget {
  final Map<String,dynamic> source,ref,profile;
  const FuelingV23Screen({super.key,required this.source,required this.ref,required this.profile});
  @override State<FuelingV23Screen> createState()=>_FuelingV23ScreenState();
}

class _FuelingV23ScreenState extends State<FuelingV23Screen> {
  int? work,machine,third;
  String fuel='Diesel';
  final liters=TextEditingController(),km=TextEditingController(),hour=TextEditingController(),receiver=TextEditingController(),location=TextEditingController(),sale=TextEditingController();
  XFile? meter,totalizer,identity,extra;
  Uint8List? rs,os;
  Position? capturedPosition;
  DateTime? locationCapturedAt;
  double? locationAccuracyM;
  bool locating=false,saving=false;
  String savingStep='Concluir abastecimento';

  bool get financial=>widget.profile['is_admin']==true||widget.profile['is_manager']==true||widget.profile['can_financial']==true;
  Future<XFile?> cam()=>ImagePicker().pickImage(source:ImageSource.camera,imageQuality:75,maxWidth:1600);
  Future<Uint8List?> sign(String t)=>Navigator.push<Uint8List>(context,MaterialPageRoute(builder:(_)=>SignatureCaptureOnlineScreen(title:t),fullscreenDialog:true));
  Map<String,dynamic>? selected(List<Map<String,dynamic>> a,int? id){if(id==null)return null;for(final x in a){if(_intOrNull(x['id'])==id)return x;}return null;}

  bool vehicleLike(Map<String,dynamic> x,{bool thirdParty=false}){
    final raw='${x['tipo']??x['type']??''} ${x['modelo']??x['model']??''} ${x['description']??''}'.toLowerCase();
    const vehicleTerms=['automóvel','automovel','caminhão','caminhao','microonibus','micro-ônibus','microônibus','ônibus','onibus','cavalo mecânico','cavalo mecanico','pickup','pick up','van','veículo','veiculo','carro'];
    if(vehicleTerms.any(raw.contains))return true;
    const machineTerms=['retroescavadeira','escavadeira','carregadeira','fresadora','rolo ','rolo compactador','motoniveladora','vibro acabadora','máquina','maquina','trator','gerador','extrusora'];
    if(machineTerms.any(raw.contains))return false;
    final plate=thirdParty?x['plate']:x['placa'];
    return _hasValue(plate);
  }

  Set<String> metricKinds(){
    final out=<String>{};
    final ms=_rows(widget.ref['machines']),ts=_rows(widget.ref['third_party_vehicles']);
    final sm=selected(ms,machine),st=selected(ts,third);
    if(sm!=null)out.add(vehicleLike(sm)?'km':'hour');
    if(st!=null)out.add(vehicleLike(st,thirdParty:true)?'km':'hour');
    return out;
  }

  String sourceTypeLabel(){switch('${widget.source['tank_type']}'){case 'stationary':return 'T.E.';case 'truck':return 'Caminhão-tanque';default:return 'Comboio';}}
  String metricPhotoLabel(Set<String> kinds){if(kinds.length>1)return 'Foto do KM/Horímetro *';if(kinds.contains('km'))return 'Foto do KM *';if(kinds.contains('hour'))return 'Foto do Horímetro *';return 'Foto do KM/Horímetro *';}

  Future<Position?> currentPosition() async {
    try{
      if(!await Geolocator.isLocationServiceEnabled())return null;
      var permission=await Geolocator.checkPermission();
      if(permission==LocationPermission.denied)permission=await Geolocator.requestPermission();
      if(permission==LocationPermission.denied||permission==LocationPermission.deniedForever)return null;
      return Geolocator.getCurrentPosition(locationSettings:const LocationSettings(accuracy:LocationAccuracy.high,timeLimit:Duration(seconds:12)));
    }catch(_){return null;}
  }

  String formatPlacemark(Placemark p){
    final street=[p.street,p.subLocality].where((v)=>v!=null&&v!.trim().isNotEmpty).map((v)=>v!.trim()).join(', ');
    final city=[p.locality,p.administrativeArea].where((v)=>v!=null&&v!.trim().isNotEmpty).map((v)=>v!.trim()).join(' - ');
    final tail=[city,p.postalCode].where((v)=>v!=null&&v!.trim().isNotEmpty).map((v)=>v!.trim()).join(', ');
    return [street,tail].where((v)=>v.trim().isNotEmpty).join(', ');
  }

  Future<bool> captureLocationForSubmission() async {
    if(locating)return false;
    if(mounted)setState(()=>locating=true);
    try{
      final p=await currentPosition();
      if(p==null){if(mounted)ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content:Text('Não foi possível obter a localização atual. Ative o GPS e tente registrar novamente.')));return false;}
      capturedPosition=p;
      locationCapturedAt=DateTime.now().toUtc();
      locationAccuracyM=p.accuracy;
      String value='';
      try{final places=await placemarkFromCoordinates(p.latitude,p.longitude);if(places.isNotEmpty)value=formatPlacemark(places.first);}catch(_){}
      if(value.trim().isEmpty)value='GPS: ${p.latitude.toStringAsFixed(6)}, ${p.longitude.toStringAsFixed(6)}';
      location.text=value;
      if(mounted)setState((){});
      return true;
    }finally{if(mounted)setState(()=>locating=false);}
  }

  String locationMeta(){
    if(locationCapturedAt==null)return 'Será capturada no momento em que o abastecimento for registrado.';
    final d=locationCapturedAt!.toLocal();final hh=d.hour.toString().padLeft(2,'0'),mm=d.minute.toString().padLeft(2,'0'),ss=d.second.toString().padLeft(2,'0');
    final accuracy=locationAccuracyM==null?'':' • precisão aproximada ±${locationAccuracyM!.round()} m';
    return 'Capturada às $hh:$mm:$ss$accuracy';
  }

  Future<bool> confirmFueling(double v,double? k,double? h) async {
    final ms=_rows(widget.ref['machines']),ts=_rows(widget.ref['third_party_vehicles']);
    final sm=selected(ms,machine),st=selected(ts,third);final targets=<String>[];
    if(sm!=null)targets.add('${sm['numeroAtivo']} • ${sm['modelo']??''}');
    if(st!=null)targets.add('${_hasValue(st['plate'])?st['plate']:'Sem placa'} • ${st['description']??''}');
    return await showDialog<bool>(context:context,builder:(ctx)=>AlertDialog(title:const Text('Confirmar abastecimento?'),content:SingleChildScrollView(child:Column(mainAxisSize:MainAxisSize.min,crossAxisAlignment:CrossAxisAlignment.start,children:[
      Text('Origem: ${widget.source['code']} • ${widget.source['name']}',style:const TextStyle(fontWeight:FontWeight.w700)),const SizedBox(height:8),Text('Ativo/equipamento: ${targets.join(' + ')}'),const SizedBox(height:8),Text('Combustível: $fuel'),Text('Volume: ${_fmtLiters(v)}'),if(k!=null)Text('KM: ${k.toStringAsFixed(k.truncateToDouble()==k?0:1)}'),if(h!=null)Text('Horímetro: ${h.toStringAsFixed(h.truncateToDouble()==h?0:1)}'),Text('Quem recebeu: ${receiver.text.trim()}'),const SizedBox(height:8),Text('Localização: ${location.text.trim()}'),Text(locationMeta(),style:const TextStyle(fontSize:12,color:Colors.black54)),const SizedBox(height:10),const Text('Confira os dados antes de confirmar. Depois da confirmação o registro será processado.')
    ])),actions:[TextButton(onPressed:()=>Navigator.pop(ctx,false),child:const Text('Cancelar')),FilledButton(onPressed:()=>Navigator.pop(ctx,true),child:const Text('Confirmar abastecimento'))]))??false;
  }

  Future<void> submit(bool hasPlate) async {
    if(saving||locating)return;
    final v=_num(liters.text.replaceAll(',','.'));final kinds=metricKinds();double? k,h;
    void requiredMessage(String field){if(mounted)ScaffoldMessenger.of(context).showSnackBar(SnackBar(content:Text('Preenchimento obrigatório: $field')));}
    if(v<=0){requiredMessage('Quantidade (L)');return;}
    final needsWork=const ['comboio','truck'].contains('${widget.source['tank_type']}');
    if(needsWork&&work==null){requiredMessage('Obra');return;}
    if(machine==null&&third==null){requiredMessage('Ativo ou Equipamento de terceiros');return;}
    if(kinds.contains('km')){k=double.tryParse(km.text.trim().replaceAll(',','.'));if(k==null||k<0){requiredMessage('KM');return;}}
    if(kinds.contains('hour')){h=double.tryParse(hour.text.trim().replaceAll(',','.'));if(h==null||h<0){requiredMessage('Horímetro');return;}}
    if(receiver.text.trim().isEmpty){requiredMessage('Quem recebeu');return;}
    if(meter==null){requiredMessage(kinds.length>1?'Foto de KM/Horímetro':kinds.contains('km')?'Foto do KM':'Foto do Horímetro');return;}
    if(totalizer==null){requiredMessage('Foto do Totalizador');return;}
    if(identity==null){requiredMessage('Foto da placa ou identificação');return;}
    if(rs==null){requiredMessage('Assinatura de quem recebeu');return;}
    if(os==null){requiredMessage('Assinatura de quem abasteceu');return;}
    if(!await captureLocationForSubmission()||!mounted)return;
    if(!await confirmFueling(v,k,h)||!mounted)return;
    setState((){saving=true;savingStep='Enviando evidências...';});
    try{
      Future<String> up(XFile x,String kind)async=>api.uploadBytes(await x.readAsBytes(),kind,mime:x.mimeType??'image/jpeg');
      final u=await Future.wait<String?>([up(meter!,'km_horimetro'),up(totalizer!,'totalizador'),up(identity!,'placa_identificacao'),extra==null?Future<String?>.value(null):up(extra!,'abastecimento_extra'),api.uploadBytes(rs!,'assinatura_recebedor'),api.uploadBytes(os!,'assinatura_abastecedor')]);
      if(!mounted)return;setState(()=>savingStep='Finalizando abastecimento...');
      final r=await api.fuelingV22(sourceTankId:_intOrNull(widget.source['id'])!,workId:work,machineId:machine,thirdId:third,liters:v,km:k,hourmeter:h,receiver:receiver.text.trim(),receiverSignature:u[4]!,operatorSignature:u[5]!,meterPhoto:u[0]!,totalizerPhoto:u[1]!,identityPhoto:u[2]!,identityKind:hasPlate?'plate':'side',extraPhoto:u[3],salePrice:financial&&sale.text.trim().isNotEmpty?_num(sale.text.replaceAll(',','.')):null,fuelType:fuel,location:location.text.trim(),latitude:capturedPosition?.latitude,longitude:capturedPosition?.longitude,locationCapturedAt:locationCapturedAt,locationAccuracyM:locationAccuracyM);
      if(!mounted)return;ScaffoldMessenger.of(context).showSnackBar(SnackBar(content:Text(r['queued']==true?'Abastecimento salvo no aparelho ✓. Aguardando sincronização.':'Abastecimento registrado com sucesso ✓')));Navigator.pop(context,true);
    }catch(e){if(mounted)ScaffoldMessenger.of(context).showSnackBar(SnackBar(content:Text('Erro ao registrar abastecimento: ${_friendlyError(e)}')));}
    finally{if(mounted)setState((){saving=false;savingStep='Concluir abastecimento';});}
  }

  @override void dispose(){for(final c in [liters,km,hour,receiver,location,sale]){c.dispose();}super.dispose();}

  @override Widget build(BuildContext c){
    final ms=_rows(widget.ref['machines']),ts=_rows(widget.ref['third_party_vehicles']),ws=_rows(widget.ref['works']);
    final sm=selected(ms,machine),st=selected(ts,third),sw=selected(ws,work),hasPlate=_hasValue(sm?['placa'])||_hasValue(st?['plate']);
    final needsWork=const ['comboio','truck'].contains('${widget.source['tank_type']}');final kinds=metricKinds(),needsKm=kinds.contains('km'),needsHour=kinds.contains('hour');
    return Scaffold(appBar:AppBar(title:Text(widget.source['tank_type']=='truck'?'Abastecer como comboio':'Novo abastecimento')),body:SafeArea(child:ListView(padding:const EdgeInsets.fromLTRB(18,18,18,36),children:[
      InputDecorator(decoration:const InputDecoration(labelText:'Origem do combustível',prefixIcon:Icon(Icons.local_gas_station_outlined)),child:Text('${widget.source['code']} • ${widget.source['name']} • ${sourceTypeLabel()}',style:const TextStyle(fontWeight:FontWeight.w800))),const SizedBox(height:10),
      if(needsWork)DropdownButtonFormField<int>(value:work,decoration:const InputDecoration(labelText:'Obra *'),items:ws.map((x)=>DropdownMenuItem(value:_intOrNull(x['id']),child:Text('${x['name']}'))).toList(),onChanged:saving?null:(v)=>setState(()=>work=v)),
      if(needsWork&&_hasValue(sw?['responsible']))Padding(padding:const EdgeInsets.only(top:6),child:Text('Responsável da obra: ${sw?['responsible']}',style:const TextStyle(fontWeight:FontWeight.w700))),if(needsWork)const SizedBox(height:12),
      Text('Destino do abastecimento *',style:Theme.of(c).textTheme.titleSmall?.copyWith(fontWeight:FontWeight.w900)),const SizedBox(height:8),
      DropdownButtonFormField<int?>(value:machine,decoration:const InputDecoration(labelText:'Ativo'),items:[const DropdownMenuItem<int?>(value:null,child:Text('Nenhum')),...ms.map((x)=>DropdownMenuItem<int?>(value:_intOrNull(x['id']),child:Text('${x['numeroAtivo']} • ${x['modelo']??''}')))],onChanged:saving?null:(v)=>setState(()=>machine=v)),const SizedBox(height:8),
      DropdownButtonFormField<int?>(value:third,decoration:const InputDecoration(labelText:'Equipamento de terceiros'),items:[const DropdownMenuItem<int?>(value:null,child:Text('Nenhum')),...ts.map((x)=>DropdownMenuItem<int?>(value:_intOrNull(x['id']),child:Text('${_hasValue(x['plate'])?x['plate']:'Sem placa'} • ${x['description']??''}')))],onChanged:saving?null:(v)=>setState(()=>third=v)),
      const Padding(padding:EdgeInsets.only(top:6,bottom:10),child:Text('Selecione pelo menos um destino.',style:TextStyle(fontSize:12,color:Colors.black54))),
      DropdownButtonFormField<String>(value:fuel,decoration:const InputDecoration(labelText:'Combustível'),items:_fuelTypes.map((x)=>DropdownMenuItem(value:x,child:Text(x))).toList(),onChanged:saving?null:(v)=>setState(()=>fuel=v??'Diesel')),const SizedBox(height:8),
      TextField(controller:liters,enabled:!saving,keyboardType:const TextInputType.numberWithOptions(decimal:true),decoration:const InputDecoration(labelText:'Quantidade (L) *')),
      if(financial)...[const SizedBox(height:8),TextField(controller:sale,enabled:!saving,keyboardType:const TextInputType.numberWithOptions(decimal:true),onChanged:(_)=>setState((){}),decoration:const InputDecoration(labelText:'Preço de venda/L')),const SizedBox(height:6),InputDecorator(decoration:const InputDecoration(labelText:'Preço total • automático e somente leitura'),child:Text(_fmtMoney(_num(liters.text.replaceAll(',','.'))*_num(sale.text.replaceAll(',','.'))),style:const TextStyle(fontWeight:FontWeight.w900)))],
      const SizedBox(height:10),
      if(needsKm&&needsHour)Row(children:[Expanded(child:TextField(controller:km,enabled:!saving,keyboardType:const TextInputType.numberWithOptions(decimal:true),decoration:const InputDecoration(labelText:'KM *'))),const SizedBox(width:8),Expanded(child:TextField(controller:hour,enabled:!saving,keyboardType:const TextInputType.numberWithOptions(decimal:true),decoration:const InputDecoration(labelText:'Horímetro *')))])
      else if(needsKm)TextField(controller:km,enabled:!saving,keyboardType:const TextInputType.numberWithOptions(decimal:true),decoration:const InputDecoration(labelText:'KM *'))
      else if(needsHour)TextField(controller:hour,enabled:!saving,keyboardType:const TextInputType.numberWithOptions(decimal:true),decoration:const InputDecoration(labelText:'Horímetro *'))
      else const Text('O campo de KM ou Horímetro será definido depois que o destino for selecionado.',style:TextStyle(fontSize:12,color:Colors.black54)),
      if(kinds.isNotEmpty)const Padding(padding:EdgeInsets.only(top:5),child:Text('O sistema solicita somente a medição aplicável ao equipamento selecionado.',style:TextStyle(fontSize:12,color:Colors.black54))),
      const SizedBox(height:10),TextField(controller:receiver,enabled:!saving,decoration:const InputDecoration(labelText:'Quem recebeu *')),const SizedBox(height:10),
      InputDecorator(decoration:const InputDecoration(labelText:'Localização do abastecimento *',prefixIcon:Icon(Icons.location_on_outlined)),child:Text(location.text.trim().isEmpty?'Será capturada ao concluir o abastecimento.':location.text.trim(),softWrap:true)),
      Padding(padding:const EdgeInsets.only(top:5,bottom:12),child:Text(locationMeta(),style:const TextStyle(fontSize:11,color:Colors.black54))),
      OutlinedButton(onPressed:saving?null:()async{final x=await cam();if(x!=null)setState(()=>meter=x);},child:Text(meter==null?metricPhotoLabel(kinds):'Medição registrada ✓')),
      OutlinedButton(onPressed:saving?null:()async{final x=await cam();if(x!=null)setState(()=>totalizer=x);},child:Text(totalizer==null?'Foto Totalizador *':'Totalizador registrado ✓')),
      OutlinedButton(onPressed:saving?null:()async{final x=await cam();if(x!=null)setState(()=>identity=x);},child:Text(identity==null?'Foto da placa ou identificação *':'Foto da placa ou identificação ✓')),
      OutlinedButton(onPressed:saving?null:()async{final x=await cam();if(x!=null)setState(()=>extra=x);},child:Text(extra==null?'4ª foto (opcional)':'4ª foto registrada ✓')),
      OutlinedButton(onPressed:saving?null:()async{final x=await sign('Assinatura de quem recebeu');if(x!=null)setState(()=>rs=x);},child:Text(rs==null?'Assinatura de quem recebeu *':'Assinatura de quem recebeu ✓')),
      OutlinedButton(onPressed:saving?null:()async{final x=await sign('Assinatura de quem abasteceu');if(x!=null)setState(()=>os=x);},child:Text(os==null?'Assinatura de quem abasteceu *':'Assinatura de quem abasteceu ✓')),
      const SizedBox(height:12),FilledButton.icon(onPressed:saving||locating?null:()=>submit(hasPlate),icon:(saving||locating)?const SizedBox(width:18,height:18,child:CircularProgressIndicator(strokeWidth:2)):const Icon(Icons.check_rounded),label:Text(locating?'Capturando localização atual...':saving?savingStep:'Concluir abastecimento')),
      if(saving)const Padding(padding:EdgeInsets.only(top:8),child:Text('Não feche esta tela. O app está concluindo o registro.',textAlign:TextAlign.center,style:TextStyle(fontSize:12,color:Colors.black54)))
    ])));
  }
}

'''
s=s[:start]+new_class+s[end:]

for marker in ['rca_record_fueling_v32','locationCapturedAt','Destino do abastecimento *','Será capturada ao concluir o abastecimento.','O sistema solicita somente a medição aplicável']:
    if marker not in s:raise SystemExit('v32 missing marker: '+marker)
section=s[start:s.index('class FuelDashboardV23Screen',start)]
for bad in ['Quando não se aplicar, use 0000','Preencha KM e Horímetro']:
    if bad in section:raise SystemExit('v32 legacy metric instruction remains: '+bad)

p.write_text(s)
print('v32 fueling/location patch applied')
