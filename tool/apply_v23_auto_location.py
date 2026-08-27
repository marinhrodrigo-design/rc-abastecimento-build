from pathlib import Path
p=Path('lib/main_online.dart')
s=p.read_text()

old_api="""  Future<Map<String,dynamic>> fuelingV22({required int sourceTankId,int? workId,int? machineId,int? thirdId,required double liters,required double km,required double hourmeter,required String receiver,required String receiverSignature,required String operatorSignature,required String meterPhoto,required String totalizerPhoto,required String identityPhoto,required String identityKind,String? extraPhoto,double? salePrice,String? notes,required String fuelType,required String location}) async => _map(await client.rpc('rca_record_fueling_v22',params:{'p_source_tank_id':sourceTankId,'p_work_id':workId,'p_machine_id':machineId,'p_third_party_vehicle_id':thirdId,'p_third_party_plate':null,'p_third_party_company':null,'p_third_party_description':null,'p_liters':liters,'p_km_value':km,'p_hourmeter_value':hourmeter,'p_receiver_name':receiver,'p_receiver_company':null,'p_receiver_signature_path':receiverSignature,'p_operator_signature_path':operatorSignature,'p_meter_photo_path':meterPhoto,'p_totalizer_photo_path':totalizerPhoto,'p_identity_photo_path':identityPhoto,'p_identity_evidence_kind':identityKind,'p_extra_photo_path':extraPhoto,'p_sale_price_per_liter':salePrice,'p_notes':notes,'p_lubricated':false,'p_latitude':null,'p_longitude':null,'p_fuel_type':fuelType,'p_location_address':location}));
"""
new_api="""  Future<Map<String,dynamic>> fuelingV22({required int sourceTankId,int? workId,int? machineId,int? thirdId,required double liters,required double km,required double hourmeter,required String receiver,required String receiverSignature,required String operatorSignature,required String meterPhoto,required String totalizerPhoto,required String identityPhoto,required String identityKind,String? extraPhoto,double? salePrice,String? notes,required String fuelType,required String location,double? latitude,double? longitude}) async => _map(await client.rpc('rca_record_fueling_v22',params:{'p_source_tank_id':sourceTankId,'p_work_id':workId,'p_machine_id':machineId,'p_third_party_vehicle_id':thirdId,'p_third_party_plate':null,'p_third_party_company':null,'p_third_party_description':null,'p_liters':liters,'p_km_value':km,'p_hourmeter_value':hourmeter,'p_receiver_name':receiver,'p_receiver_company':null,'p_receiver_signature_path':receiverSignature,'p_operator_signature_path':operatorSignature,'p_meter_photo_path':meterPhoto,'p_totalizer_photo_path':totalizerPhoto,'p_identity_photo_path':identityPhoto,'p_identity_evidence_kind':identityKind,'p_extra_photo_path':extraPhoto,'p_sale_price_per_liter':salePrice,'p_notes':notes,'p_lubricated':false,'p_latitude':latitude,'p_longitude':longitude,'p_fuel_type':fuelType,'p_location_address':location}));
"""
if old_api not in s:
    raise SystemExit('fuelingV22 API anchor missing')
s=s.replace(old_api,new_api,1)

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
  final liters=TextEditingController(),km=TextEditingController(text:'0000'),hour=TextEditingController(text:'0000'),receiver=TextEditingController(),location=TextEditingController(),sale=TextEditingController();
  XFile? meter,totalizer,identity,extra;
  Uint8List? rs,os;
  Position? capturedPosition;
  bool locating=false;

  bool get financial=>widget.profile['is_admin']==true||widget.profile['is_manager']==true||widget.profile['can_financial']==true;
  Future<XFile?> cam()=>ImagePicker().pickImage(source:ImageSource.camera,imageQuality:75,maxWidth:1600);
  Future<Uint8List?> sign(String t)=>Navigator.push<Uint8List>(context,MaterialPageRoute(builder:(_)=>SignatureCaptureOnlineScreen(title:t),fullscreenDialog:true));
  Map<String,dynamic>? selected(List<Map<String,dynamic>> a,int? id){if(id==null)return null;for(final x in a){if(_intOrNull(x['id'])==id)return x;}return null;}

  @override void initState(){
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_)=>loadLocation());
  }

  Future<Position?> currentPosition() async {
    try {
      if(!await Geolocator.isLocationServiceEnabled()) return null;
      var permission=await Geolocator.checkPermission();
      if(permission==LocationPermission.denied) permission=await Geolocator.requestPermission();
      if(permission==LocationPermission.denied||permission==LocationPermission.deniedForever) return null;
      return Geolocator.getCurrentPosition(locationSettings:const LocationSettings(accuracy:LocationAccuracy.high,timeLimit:Duration(seconds:10)));
    } catch(_) { return null; }
  }

  String formatPlacemark(Placemark p){
    final street=[p.street,p.subLocality].where((v)=>v!=null&&v!.trim().isNotEmpty).map((v)=>v!.trim()).join(', ');
    final city=[p.locality,p.administrativeArea].where((v)=>v!=null&&v!.trim().isNotEmpty).map((v)=>v!.trim()).join(' - ');
    final tail=[city,p.postalCode].where((v)=>v!=null&&v!.trim().isNotEmpty).map((v)=>v!.trim()).join(', ');
    return [street,tail].where((v)=>v.trim().isNotEmpty).join(', ');
  }

  Future<void> loadLocation() async {
    if(locating) return;
    if(mounted)setState(()=>locating=true);
    try {
      final p=await currentPosition();
      if(p==null){
        if(mounted)ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content:Text('Não foi possível obter a localização. Ative o GPS e tente novamente.')));
        return;
      }
      capturedPosition=p;
      String value='';
      try {
        final places=await placemarkFromCoordinates(p.latitude,p.longitude);
        if(places.isNotEmpty)value=formatPlacemark(places.first);
      } catch(_) {}
      if(value.trim().isEmpty){
        value='Coordenadas GPS: ${p.latitude.toStringAsFixed(6)}, ${p.longitude.toStringAsFixed(6)}';
      }
      location.text=value;
      if(mounted)setState((){});
    } finally {
      if(mounted)setState(()=>locating=false);
    }
  }

  @override void dispose(){
    for(final c in [liters,km,hour,receiver,location,sale]){c.dispose();}
    super.dispose();
  }

  @override Widget build(BuildContext c){
    final ms=_rows(widget.ref['machines']),ts=_rows(widget.ref['third_party_vehicles']),ws=_rows(widget.ref['works']);
    final sm=selected(ms,machine),st=selected(ts,third),sw=selected(ws,work),hasPlate=_hasValue(sm?['placa'])||_hasValue(st?['plate']);
    return Scaffold(appBar:AppBar(title:const Text('Novo abastecimento')),body:ListView(padding:const EdgeInsets.all(18),children:[
      if(widget.source['tank_type']=='comboio')DropdownButtonFormField<int>(value:work,decoration:const InputDecoration(labelText:'Obra *'),items:ws.map((x)=>DropdownMenuItem(value:_intOrNull(x['id']),child:Text('${x['name']}'))).toList(),onChanged:(v)=>setState(()=>work=v)),
      if(widget.source['tank_type']=='comboio'&&_hasValue(sw?['responsible']))Padding(padding:const EdgeInsets.only(top:6),child:Text('Responsável: ${sw?['responsible']}',style:const TextStyle(fontWeight:FontWeight.w700))),
      if(widget.source['tank_type']=='comboio')const SizedBox(height:8),
      DropdownButtonFormField<int?>(value:machine,decoration:const InputDecoration(labelText:'Ativo (opcional)'),items:[const DropdownMenuItem<int?>(value:null,child:Text('Nenhum')),...ms.map((x)=>DropdownMenuItem<int?>(value:_intOrNull(x['id']),child:Text('${x['numeroAtivo']} • ${x['modelo']??''}')))],onChanged:(v)=>setState(()=>machine=v)),
      const SizedBox(height:8),
      DropdownButtonFormField<int?>(value:third,decoration:const InputDecoration(labelText:'Equipamento de terceiros (opcional)'),items:[const DropdownMenuItem<int?>(value:null,child:Text('Nenhum')),...ts.map((x)=>DropdownMenuItem<int?>(value:_intOrNull(x['id']),child:Text('${_hasValue(x['plate'])?x['plate']:'Sem placa'} • ${x['description']??''}')))],onChanged:(v)=>setState(()=>third=v)),
      const Padding(padding:EdgeInsets.symmetric(vertical:6),child:Text('Pelo menos Ativo ou Equipamento de terceiros é obrigatório. Os dois podem ser preenchidos.',style:TextStyle(fontSize:12,color:Colors.black54))),
      DropdownButtonFormField<String>(value:fuel,decoration:const InputDecoration(labelText:'Combustível'),items:_fuelTypes.map((x)=>DropdownMenuItem(value:x,child:Text(x))).toList(),onChanged:(v)=>setState(()=>fuel=v??'Diesel')),
      const SizedBox(height:8),
      TextField(controller:liters,keyboardType:const TextInputType.numberWithOptions(decimal:true),decoration:const InputDecoration(labelText:'Quantidade (L) *')),
      if(financial)...[
        const SizedBox(height:8),
        TextField(controller:sale,keyboardType:const TextInputType.numberWithOptions(decimal:true),onChanged:(_)=>setState((){}),decoration:const InputDecoration(labelText:'Preço de venda/L')),
        const SizedBox(height:6),
        InputDecorator(decoration:const InputDecoration(labelText:'Preço total • automático e somente leitura'),child:Text(_fmtMoney(_num(liters.text.replaceAll(',','.'))*_num(sale.text.replaceAll(',','.'))),style:const TextStyle(fontWeight:FontWeight.w900)))
      ],
      const SizedBox(height:8),
      Row(children:[Expanded(child:TextField(controller:km,keyboardType:const TextInputType.numberWithOptions(decimal:true),decoration:const InputDecoration(labelText:'KM *'))),const SizedBox(width:8),Expanded(child:TextField(controller:hour,keyboardType:const TextInputType.numberWithOptions(decimal:true),decoration:const InputDecoration(labelText:'Horímetro *')))]),
      const Text('Quando não se aplicar, use 0000.',style:TextStyle(fontSize:12,color:Colors.black54)),
      const SizedBox(height:8),
      TextField(controller:receiver,decoration:const InputDecoration(labelText:'Quem recebeu *')),
      const SizedBox(height:8),
      TextField(controller:location,readOnly:true,maxLines:2,decoration:InputDecoration(labelText:'Localização automática *',prefixIcon:const Icon(Icons.location_on_outlined),suffixIcon:IconButton(onPressed:locating?null:loadLocation,tooltip:'Atualizar localização',icon:locating?const SizedBox(width:18,height:18,child:CircularProgressIndicator(strokeWidth:2)):const Icon(Icons.my_location_rounded)))),
      const Padding(padding:EdgeInsets.only(top:5,bottom:10),child:Text('O app usa o endereço sempre que conseguir identificá-lo. Latitude/longitude são usadas apenas quando o GPS obtém a posição, mas não consegue converter para endereço.',style:TextStyle(fontSize:11,color:Colors.black54))),
      OutlinedButton(onPressed:()async{final x=await cam();if(x!=null)setState(()=>meter=x);},child:Text(meter==null?'Foto KM ou Horímetro *':'KM/Horímetro registrado')),
      OutlinedButton(onPressed:()async{final x=await cam();if(x!=null)setState(()=>totalizer=x);},child:Text(totalizer==null?'Foto Totalizador *':'Totalizador registrado')),
      OutlinedButton(onPressed:()async{final x=await cam();if(x!=null)setState(()=>identity=x);},child:Text(identity==null?(hasPlate?'Foto da Placa *':'Foto lateral do equipamento *'):'Identificação registrada')),
      OutlinedButton(onPressed:()async{final x=await cam();if(x!=null)setState(()=>extra=x);},child:Text(extra==null?'4ª foto (opcional)':'4ª foto registrada')),
      OutlinedButton(onPressed:()async{final x=await sign('Assinatura de quem recebeu');if(x!=null)setState(()=>rs=x);},child:Text(rs==null?'Assinatura de quem recebeu *':'Recebedor assinou')),
      OutlinedButton(onPressed:()async{final x=await sign('Assinatura de quem abasteceu');if(x!=null)setState(()=>os=x);},child:Text(os==null?'Assinatura de quem abasteceu *':'Abastecedor assinou')),
      const SizedBox(height:12),
      FilledButton(onPressed:()async{
        if(location.text.trim().isEmpty)await loadLocation();
        final v=_num(liters.text.replaceAll(',','.'));
        if(v<=0||(machine==null&&third==null)||receiver.text.trim().isEmpty||location.text.trim().isEmpty||meter==null||totalizer==null||identity==null||rs==null||os==null||(widget.source['tank_type']=='comboio'&&work==null)){
          ScaffoldMessenger.of(c).showSnackBar(const SnackBar(content:Text('Confira os campos, a localização, as 3 fotos e as 2 assinaturas obrigatórias.')));return;
        }
        try{
          Future<String> up(XFile x,String k)async=>api.uploadBytes(await x.readAsBytes(),k,mime:x.mimeType??'image/jpeg');
          final mp=await up(meter!,'km_horimetro'),tp=await up(totalizer!,'totalizador'),ip=await up(identity!,'placa_lateral'),ep=extra==null?null:await up(extra!,'abastecimento_extra'),rsp=await api.uploadBytes(rs!,'assinatura_recebedor'),osp=await api.uploadBytes(os!,'assinatura_abastecedor');
          await api.fuelingV22(sourceTankId:_intOrNull(widget.source['id'])!,workId:work,machineId:machine,thirdId:third,liters:v,km:_num(km.text.replaceAll(',','.')),hourmeter:_num(hour.text.replaceAll(',','.')),receiver:receiver.text.trim(),receiverSignature:rsp,operatorSignature:osp,meterPhoto:mp,totalizerPhoto:tp,identityPhoto:ip,identityKind:hasPlate?'plate':'side',extraPhoto:ep,salePrice:financial&&sale.text.trim().isNotEmpty?_num(sale.text.replaceAll(',','.')):null,fuelType:fuel,location:location.text.trim(),latitude:capturedPosition?.latitude,longitude:capturedPosition?.longitude);
          if(c.mounted)Navigator.pop(c);
        }catch(e){if(c.mounted)ScaffoldMessenger.of(c).showSnackBar(SnackBar(content:Text(_friendlyError(e))));}
      },child:const Text('Concluir abastecimento'))
    ]));
  }
}

'''
s=s[:start]+new_class+s[end:]
p.write_text(s)
print('auto location patch applied', len(s))
