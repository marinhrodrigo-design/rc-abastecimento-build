from pathlib import Path
p=Path('lib/main_online.dart')
s=p.read_text()

old="Future<Map<String,dynamic>> fuelingV22({required int sourceTankId,int? workId,int? machineId,int? thirdId,required double liters,required double km,required double hourmeter,required String receiver,required String receiverSignature,required String operatorSignature,required String meterPhoto,required String totalizerPhoto,required String identityPhoto,required String identityKind,String? extraPhoto,double? salePrice,String? notes,required String fuelType,required String location,double? latitude,double? longitude}) async => _map(await client.rpc('rca_record_fueling_v22',params:"
new="Future<Map<String,dynamic>> fuelingV22({required int sourceTankId,int? workId,int? machineId,int? thirdId,required double liters,required double km,required double hourmeter,required String receiver,required String receiverSignature,required String operatorSignature,required String meterPhoto,required String totalizerPhoto,required String identityPhoto,required String identityKind,String? extraPhoto,double? salePrice,String? notes,required String fuelType,required String location,double? latitude,double? longitude}) async => offlineStore.executeOrQueue('rca_record_fueling_v22',"
if old not in s: raise SystemExit('fuelingV22 anchor missing')
s=s.replace(old,new,1)
s=s.replace("}));\n  Future<Map<String,dynamic>> dashboardV22()","});\n  Future<Map<String,dynamic>> dashboardV22()",1)
s=s.replace("if ((rpc == 'rca_record_fueling' || rpc == 'rca_record_fueling_v14')) {","if ((rpc == 'rca_record_fueling' || rpc == 'rca_record_fueling_v14' || rpc == 'rca_record_fueling_v22')) {",1)
s=s.replace("fileOptions: FileOptions(contentType: mime, upsert: false),\n      );\n      offlineStore.markOnline();","fileOptions: FileOptions(contentType: mime, upsert: false),\n      ).timeout(const Duration(seconds: 45));\n      offlineStore.markOnline();",1)
s=s.replace("timer = Timer.periodic(const Duration(seconds: 2), (_) => refresh(silent: true));","timer = Timer.periodic(const Duration(seconds: 8), (_) => refresh(silent: true));",1)
old_open="""  Future<void> open(Widget page) async {
    await Navigator.push(context, MaterialPageRoute(builder: (_) => page));
    await refresh();
  }
"""
new_open="""  Future<void> open(Widget page) async {
    timer?.cancel();
    try { await Navigator.push(context, MaterialPageRoute(builder: (_) => page)); }
    finally { if (mounted) { await refresh(); timer?.cancel(); timer = Timer.periodic(const Duration(seconds: 8), (_) => refresh(silent: true)); } }
  }
"""
if old_open not in s: raise SystemExit('FieldHome open anchor missing')
s=s.replace(old_open,new_open,1)
s=s.replace("final liters=TextEditingController(),km=TextEditingController(text:'0000'),hour=TextEditingController(text:'0000'),receiver=TextEditingController(),location=TextEditingController(),sale=TextEditingController();","final liters=TextEditingController(),km=TextEditingController(),hour=TextEditingController(),receiver=TextEditingController(),location=TextEditingController(),sale=TextEditingController();",1)
s=s.replace("bool locating=false;\n\n  bool get financial","bool locating=false,saving=false;\n  String savingStep='Concluir abastecimento';\n\n  bool get financial",1)
anchor="""  @override void dispose(){
    for(final c in [liters,km,hour,receiver,location,sale]){c.dispose();}
    super.dispose();
  }
"""
helper="""  Future<void> submit(bool hasPlate) async {
    if(saving)return;
    if(location.text.trim().isEmpty)await loadLocation();
    final v=_num(liters.text.replaceAll(',','.'));
    final k=double.tryParse(km.text.trim().replaceAll(',','.')),h=double.tryParse(hour.text.trim().replaceAll(',','.'));
    if(km.text.trim().isEmpty||hour.text.trim().isEmpty||k==null||h==null||k<0||h<0){if(mounted)ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content:Text('Preencha KM e Horímetro. Quando não se aplicar, informe 0000.')));return;}
    if(v<=0||(machine==null&&third==null)||receiver.text.trim().isEmpty||location.text.trim().isEmpty||meter==null||totalizer==null||identity==null||rs==null||os==null||(widget.source['tank_type']=='comboio'&&work==null)){if(mounted)ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content:Text('Confira os campos obrigatórios, a localização, as 3 fotos e as 2 assinaturas.')));return;}
    setState((){saving=true;savingStep='Enviando evidências...';});
    try{
      Future<String> up(XFile x,String kind)async=>api.uploadBytes(await x.readAsBytes(),kind,mime:x.mimeType??'image/jpeg');
      final u=await Future.wait<String?>([up(meter!,'km_horimetro'),up(totalizer!,'totalizador'),up(identity!,'placa_identificacao'),extra==null?Future<String?>.value(null):up(extra!,'abastecimento_extra'),api.uploadBytes(rs!,'assinatura_recebedor'),api.uploadBytes(os!,'assinatura_abastecedor')]);
      if(!mounted)return; setState(()=>savingStep='Finalizando abastecimento...');
      final r=await api.fuelingV22(sourceTankId:_intOrNull(widget.source['id'])!,workId:work,machineId:machine,thirdId:third,liters:v,km:k,hourmeter:h,receiver:receiver.text.trim(),receiverSignature:u[4]!,operatorSignature:u[5]!,meterPhoto:u[0]!,totalizerPhoto:u[1]!,identityPhoto:u[2]!,identityKind:hasPlate?'plate':'side',extraPhoto:u[3],salePrice:financial&&sale.text.trim().isNotEmpty?_num(sale.text.replaceAll(',','.')):null,fuelType:fuel,location:location.text.trim(),latitude:capturedPosition?.latitude,longitude:capturedPosition?.longitude);
      if(!mounted)return; ScaffoldMessenger.of(context).showSnackBar(SnackBar(content:Text(r['queued']==true?'Abastecimento salvo no aparelho. A sincronização será automática quando houver conexão.':'Abastecimento ${r['code']??''} concluído com sucesso.'))); Navigator.pop(context,true);
    }catch(e){if(mounted)ScaffoldMessenger.of(context).showSnackBar(SnackBar(content:Text(_friendlyError(e))));}
    finally{if(mounted)setState((){saving=false;savingStep='Concluir abastecimento';});}
  }

"""+anchor
if anchor not in s: raise SystemExit('dispose anchor missing')
s=s.replace(anchor,helper,1)
s=s.replace("const Text('Quando não se aplicar, use 0000.'","const Text('Preenchimento obrigatório. Quando não se aplicar, use 0000.'",1)
s=s.replace("OutlinedButton(onPressed:()async{final x=await cam();if(x!=null)setState(()=>identity=x);},child:Text(identity==null?(hasPlate?'Foto da Placa *':'Foto lateral do equipamento *'):'Identificação registrada'))","OutlinedButton(onPressed:saving?null:()async{final x=await cam();if(x!=null)setState(()=>identity=x);},child:Text(identity==null?'Foto da placa ou identificação *':'Foto da placa ou identificação ✓'))",1)
s=s.replace("OutlinedButton(onPressed:()async{final x=await sign('Assinatura de quem recebeu');if(x!=null)setState(()=>rs=x);},child:Text(rs==null?'Assinatura de quem recebeu *':'Recebedor assinou'))","OutlinedButton(onPressed:saving?null:()async{final x=await sign('Assinatura de quem recebeu');if(x!=null)setState(()=>rs=x);},child:Text(rs==null?'Assinatura de quem recebeu *':'Assinatura de quem recebeu ✓'))",1)
s=s.replace("OutlinedButton(onPressed:()async{final x=await sign('Assinatura de quem abasteceu');if(x!=null)setState(()=>os=x);},child:Text(os==null?'Assinatura de quem abasteceu *':'Abastecedor assinou'))","OutlinedButton(onPressed:saving?null:()async{final x=await sign('Assinatura de quem abasteceu');if(x!=null)setState(()=>os=x);},child:Text(os==null?'Assinatura de quem abasteceu *':'Assinatura de quem abasteceu ✓'))",1)
bs=s.index("      FilledButton(onPressed:()async{",s.index('class _FuelingV23ScreenState'))
be=s.index("      },child:const Text('Concluir abastecimento'))",bs)+len("      },child:const Text('Concluir abastecimento'))")
newbtn="""      FilledButton.icon(onPressed:saving?null:()=>submit(hasPlate),icon:saving?const SizedBox(width:18,height:18,child:CircularProgressIndicator(strokeWidth:2)):const Icon(Icons.check_rounded),label:Text(saving?savingStep:'Concluir abastecimento')),
      if(saving)const Padding(padding:EdgeInsets.only(top:8),child:Text('Não feche esta tela. O app está concluindo o registro.',textAlign:TextAlign.center,style:TextStyle(fontSize:12,color:Colors.black54)))"""
s=s[:bs]+newbtn+s[be:]
s=s.replace("x['identity_evidence_kind']=='side'?'Foto da lateral do equipamento':'Foto da placa'","'Foto da placa ou identificação'",1)
p.write_text(s)
print('submit fix applied',len(s))
