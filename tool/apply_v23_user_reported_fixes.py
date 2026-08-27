from pathlib import Path
p=Path('lib/main_online.dart')
s=p.read_text()

def replace_class(start_marker,end_marker,new_text):
    global s
    a=s.index(start_marker)
    b=s.index(end_marker,a)
    s=s[:a]+new_text.rstrip()+"\n\n"+s[b:]

transfer=r'''class TransferV23Screen extends StatefulWidget{
  final Map<String,dynamic> source,ref;
  const TransferV23Screen({super.key,required this.source,required this.ref});
  @override State<TransferV23Screen> createState()=>_TransferV23ScreenState();
}
class _TransferV23ScreenState extends State<TransferV23Screen>{
  int? dest;
  final liters=TextEditingController(),donor=TextEditingController(),receiver=TextEditingController();
  Uint8List? ds,rs;
  bool saving=false;
  String step='Concluir transferência';
  Future<Uint8List?> sign(String t)=>Navigator.push<Uint8List>(context,MaterialPageRoute(builder:(_)=>SignatureCaptureOnlineScreen(title:t),fullscreenDialog:true));
  Map<String,dynamic>? destinationOf(List<Map<String,dynamic>> a){for(final x in a){if(_intOrNull(x['id'])==dest)return x;}return null;}

  Future<void> submit(List<Map<String,dynamic>> dests) async {
    if(saving)return;
    final sourceId=_intOrNull(widget.source['id']);
    final v=_num(liters.text.replaceAll(',','.'));
    final target=destinationOf(dests);
    if(sourceId==null||dest==null||target==null||v<=0||donor.text.trim().isEmpty||receiver.text.trim().isEmpty||ds==null||rs==null){
      if(mounted)ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content:Text('Preencha os dados e as duas assinaturas.')));
      return;
    }
    final confirmed=await showDialog<bool>(context:context,builder:(ctx)=>AlertDialog(
      title:const Text('Confirmar transferência?'),
      content:Column(mainAxisSize:MainAxisSize.min,crossAxisAlignment:CrossAxisAlignment.start,children:[
        Text('Origem: ${widget.source['code']} • ${widget.source['name']}',style:const TextStyle(fontWeight:FontWeight.w700)),
        const SizedBox(height:8),
        Text('Destino: ${target['code']} • ${target['name']}',style:const TextStyle(fontWeight:FontWeight.w700)),
        const SizedBox(height:8),
        Text('Volume: ${_fmtLiters(v)}'),
        const SizedBox(height:8),
        Text('Responsável doador: ${donor.text.trim()}'),
        Text('Responsável recebedor: ${receiver.text.trim()}'),
        const SizedBox(height:10),
        const Text('Confira os dados antes de confirmar. Depois da confirmação a movimentação será registrada.'),
      ]),
      actions:[TextButton(onPressed:()=>Navigator.pop(ctx,false),child:const Text('Cancelar')),FilledButton(onPressed:()=>Navigator.pop(ctx,true),child:const Text('Confirmar transferência'))],
    ));
    if(confirmed!=true||!mounted)return;
    setState((){saving=true;step='Enviando assinaturas...';});
    try{
      final paths=await Future.wait<String>([api.uploadBytes(ds!,'transfer_doador'),api.uploadBytes(rs!,'transfer_recebedor')]);
      if(!mounted)return;
      setState(()=>step='Registrando transferência...');
      await api.transferV22(sourceTankId:sourceId,destinationTankId:dest!,liters:v,donor:donor.text.trim(),receiver:receiver.text.trim(),donorSignature:paths[0],receiverSignature:paths[1]);
      if(!mounted)return;
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content:Text('Transferência registrada com sucesso ✓')));
      Navigator.pop(context,true);
    }catch(e){
      if(mounted)ScaffoldMessenger.of(context).showSnackBar(SnackBar(content:Text('Erro ao registrar transferência: ${_friendlyError(e)}')));
    }finally{
      if(mounted)setState((){saving=false;step='Concluir transferência';});
    }
  }

  @override void dispose(){liters.dispose();donor.dispose();receiver.dispose();super.dispose();}
  @override Widget build(BuildContext c){
    final sourceId=_intOrNull(widget.source['id']);
    final dests=_rows(widget.ref['comboio_destinations']).where((x)=>_intOrNull(x['id'])!=sourceId).toList();
    return Scaffold(appBar:AppBar(title:const Text('Transferir')),body:ListView(padding:const EdgeInsets.all(18),children:[
      Text('Doador: ${widget.source['code']} • ${widget.source['name']}',style:Theme.of(c).textTheme.titleLarge?.copyWith(fontWeight:FontWeight.w900)),
      const SizedBox(height:12),
      DropdownButtonFormField<int>(value:dest,decoration:const InputDecoration(labelText:'CB recebedor *'),items:dests.map((x)=>DropdownMenuItem(value:_intOrNull(x['id']),child:Text('${x['code']} • ${x['name']}'))).toList(),onChanged:saving?null:(v)=>setState(()=>dest=v)),
      const SizedBox(height:8),TextField(controller:donor,enabled:!saving,decoration:const InputDecoration(labelText:'Responsável doador *')),
      const SizedBox(height:8),TextField(controller:receiver,enabled:!saving,decoration:const InputDecoration(labelText:'Responsável recebedor *')),
      const SizedBox(height:8),TextField(controller:liters,enabled:!saving,keyboardType:const TextInputType.numberWithOptions(decimal:true),decoration:const InputDecoration(labelText:'Volume (L) *')),
      const SizedBox(height:10),
      OutlinedButton(onPressed:saving?null:()async{final b=await sign('Assinatura responsável doador');if(b!=null)setState(()=>ds=b);},child:Text(ds==null?'Assinatura doador *':'Assinatura doador ✓')),
      OutlinedButton(onPressed:saving?null:()async{final b=await sign('Assinatura responsável recebedor');if(b!=null)setState(()=>rs=b);},child:Text(rs==null?'Assinatura recebedor *':'Assinatura recebedor ✓')),
      const SizedBox(height:12),
      FilledButton.icon(onPressed:saving?null:()=>submit(dests),icon:saving?const SizedBox(width:18,height:18,child:CircularProgressIndicator(strokeWidth:2)):const Icon(Icons.swap_horiz_rounded),label:Text(saving?step:'Concluir transferência')),
    ]));
  }
}'''
replace_class('class TransferV23Screen extends StatefulWidget','class FuelingV23Screen extends StatefulWidget',transfer)

fueling=r'''class FuelingV23Screen extends StatefulWidget {
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
  bool locating=false,saving=false;
  String savingStep='Concluir abastecimento';

  bool get financial=>widget.profile['is_admin']==true||widget.profile['is_manager']==true||widget.profile['can_financial']==true;
  Future<XFile?> cam()=>ImagePicker().pickImage(source:ImageSource.camera,imageQuality:75,maxWidth:1600);
  Future<Uint8List?> sign(String t)=>Navigator.push<Uint8List>(context,MaterialPageRoute(builder:(_)=>SignatureCaptureOnlineScreen(title:t),fullscreenDialog:true));
  Map<String,dynamic>? selected(List<Map<String,dynamic>> a,int? id){if(id==null)return null;for(final x in a){if(_intOrNull(x['id'])==id)return x;}return null;}

  @override void initState(){super.initState();WidgetsBinding.instance.addPostFrameCallback((_)=>loadLocation());}

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
      try {final places=await placemarkFromCoordinates(p.latitude,p.longitude);if(places.isNotEmpty)value=formatPlacemark(places.first);} catch(_) {}
      if(value.trim().isEmpty)value='Coordenadas GPS: ${p.latitude.toStringAsFixed(6)}, ${p.longitude.toStringAsFixed(6)}';
      location.text=value;
      if(mounted)setState((){});
    } finally {if(mounted)setState(()=>locating=false);}
  }

  Future<bool> confirmFueling(double v,double k,double h) async {
    final ms=_rows(widget.ref['machines']),ts=_rows(widget.ref['third_party_vehicles']);
    final sm=selected(ms,machine),st=selected(ts,third);
    final targets=<String>[];
    if(sm!=null)targets.add('${sm['numeroAtivo']} • ${sm['modelo']??''}');
    if(st!=null)targets.add('${_hasValue(st['plate'])?st['plate']:'Sem placa'} • ${st['description']??''}');
    return await showDialog<bool>(context:context,builder:(ctx)=>AlertDialog(
      title:const Text('Confirmar abastecimento?'),
      content:SingleChildScrollView(child:Column(mainAxisSize:MainAxisSize.min,crossAxisAlignment:CrossAxisAlignment.start,children:[
        Text('Origem: ${widget.source['code']} • ${widget.source['name']}',style:const TextStyle(fontWeight:FontWeight.w700)),
        const SizedBox(height:8),Text('Ativo/equipamento: ${targets.join(' + ')}'),
        const SizedBox(height:8),Text('Combustível: $fuel'),
        Text('Volume: ${_fmtLiters(v)}'),
        Text('KM: ${k.toStringAsFixed(k.truncateToDouble()==k?0:1)}'),
        Text('Horímetro: ${h.toStringAsFixed(h.truncateToDouble()==h?0:1)}'),
        Text('Quem recebeu: ${receiver.text.trim()}'),
        const SizedBox(height:8),Text('Localização: ${location.text.trim()}'),
        const SizedBox(height:10),const Text('Confira os dados antes de confirmar. Depois da confirmação o registro será processado.'),
      ])),
      actions:[TextButton(onPressed:()=>Navigator.pop(ctx,false),child:const Text('Cancelar')),FilledButton(onPressed:()=>Navigator.pop(ctx,true),child:const Text('Confirmar abastecimento'))],
    )) ?? false;
  }

  Future<void> submit(bool hasPlate) async {
    if(saving)return;
    if(location.text.trim().isEmpty)await loadLocation();
    final v=_num(liters.text.replaceAll(',','.'));
    final k=double.tryParse(km.text.trim().replaceAll(',','.')),h=double.tryParse(hour.text.trim().replaceAll(',','.'));
    if(km.text.trim().isEmpty||hour.text.trim().isEmpty||k==null||h==null||k<0||h<0){if(mounted)ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content:Text('Preencha KM e Horímetro. Quando não se aplicar, informe 0000.')));return;}
    if(v<=0||(machine==null&&third==null)||receiver.text.trim().isEmpty||location.text.trim().isEmpty||meter==null||totalizer==null||identity==null||rs==null||os==null||(widget.source['tank_type']=='comboio'&&work==null)){if(mounted)ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content:Text('Confira os campos obrigatórios, a localização, as 3 fotos e as 2 assinaturas.')));return;}
    if(!await confirmFueling(v,k,h)||!mounted)return;
    setState((){saving=true;savingStep='Enviando evidências...';});
    try{
      Future<String> up(XFile x,String kind)async=>api.uploadBytes(await x.readAsBytes(),kind,mime:x.mimeType??'image/jpeg');
      final u=await Future.wait<String?>([up(meter!,'km_horimetro'),up(totalizer!,'totalizador'),up(identity!,'placa_identificacao'),extra==null?Future<String?>.value(null):up(extra!,'abastecimento_extra'),api.uploadBytes(rs!,'assinatura_recebedor'),api.uploadBytes(os!,'assinatura_abastecedor')]);
      if(!mounted)return;
      setState(()=>savingStep='Finalizando abastecimento...');
      final r=await api.fuelingV22(sourceTankId:_intOrNull(widget.source['id'])!,workId:work,machineId:machine,thirdId:third,liters:v,km:k,hourmeter:h,receiver:receiver.text.trim(),receiverSignature:u[4]!,operatorSignature:u[5]!,meterPhoto:u[0]!,totalizerPhoto:u[1]!,identityPhoto:u[2]!,identityKind:hasPlate?'plate':'side',extraPhoto:u[3],salePrice:financial&&sale.text.trim().isNotEmpty?_num(sale.text.replaceAll(',','.')):null,fuelType:fuel,location:location.text.trim(),latitude:capturedPosition?.latitude,longitude:capturedPosition?.longitude);
      if(!mounted)return;
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content:Text(r['queued']==true?'Abastecimento salvo no aparelho ✓. Aguardando sincronização.':'Abastecimento registrado com sucesso ✓')));
      Navigator.pop(context,true);
    }catch(e){if(mounted)ScaffoldMessenger.of(context).showSnackBar(SnackBar(content:Text('Erro ao registrar abastecimento: ${_friendlyError(e)}')));}
    finally{if(mounted)setState((){saving=false;savingStep='Concluir abastecimento';});}
  }

  @override void dispose(){for(final c in [liters,km,hour,receiver,location,sale]){c.dispose();}super.dispose();}

  @override Widget build(BuildContext c){
    final ms=_rows(widget.ref['machines']),ts=_rows(widget.ref['third_party_vehicles']),ws=_rows(widget.ref['works']);
    final sm=selected(ms,machine),st=selected(ts,third),sw=selected(ws,work),hasPlate=_hasValue(sm?['placa'])||_hasValue(st?['plate']);
    return Scaffold(appBar:AppBar(title:const Text('Novo abastecimento')),body:ListView(padding:const EdgeInsets.all(18),children:[
      if(widget.source['tank_type']=='comboio')DropdownButtonFormField<int>(value:work,decoration:const InputDecoration(labelText:'Obra *'),items:ws.map((x)=>DropdownMenuItem(value:_intOrNull(x['id']),child:Text('${x['name']}'))).toList(),onChanged:saving?null:(v)=>setState(()=>work=v)),
      if(widget.source['tank_type']=='comboio'&&_hasValue(sw?['responsible']))Padding(padding:const EdgeInsets.only(top:6),child:Text('Responsável: ${sw?['responsible']}',style:const TextStyle(fontWeight:FontWeight.w700))),
      if(widget.source['tank_type']=='comboio')const SizedBox(height:8),
      DropdownButtonFormField<int?>(value:machine,decoration:const InputDecoration(labelText:'Ativo (opcional)'),items:[const DropdownMenuItem<int?>(value:null,child:Text('Nenhum')),...ms.map((x)=>DropdownMenuItem<int?>(value:_intOrNull(x['id']),child:Text('${x['numeroAtivo']} • ${x['modelo']??''}')))],onChanged:saving?null:(v)=>setState(()=>machine=v)),
      const SizedBox(height:8),
      DropdownButtonFormField<int?>(value:third,decoration:const InputDecoration(labelText:'Equipamento de terceiros (opcional)'),items:[const DropdownMenuItem<int?>(value:null,child:Text('Nenhum')),...ts.map((x)=>DropdownMenuItem<int?>(value:_intOrNull(x['id']),child:Text('${_hasValue(x['plate'])?x['plate']:'Sem placa'} • ${x['description']??''}')))],onChanged:saving?null:(v)=>setState(()=>third=v)),
      const Padding(padding:EdgeInsets.symmetric(vertical:6),child:Text('Pelo menos Ativo ou Equipamento de terceiros é obrigatório. Os dois podem ser preenchidos.',style:TextStyle(fontSize:12,color:Colors.black54))),
      DropdownButtonFormField<String>(value:fuel,decoration:const InputDecoration(labelText:'Combustível'),items:_fuelTypes.map((x)=>DropdownMenuItem(value:x,child:Text(x))).toList(),onChanged:saving?null:(v)=>setState(()=>fuel=v??'Diesel')),
      const SizedBox(height:8),TextField(controller:liters,enabled:!saving,keyboardType:const TextInputType.numberWithOptions(decimal:true),decoration:const InputDecoration(labelText:'Quantidade (L) *')),
      if(financial)...[
        const SizedBox(height:8),TextField(controller:sale,enabled:!saving,keyboardType:const TextInputType.numberWithOptions(decimal:true),onChanged:(_)=>setState((){}),decoration:const InputDecoration(labelText:'Preço de venda/L')),
        const SizedBox(height:6),InputDecorator(decoration:const InputDecoration(labelText:'Preço total • automático e somente leitura'),child:Text(_fmtMoney(_num(liters.text.replaceAll(',','.'))*_num(sale.text.replaceAll(',','.'))),style:const TextStyle(fontWeight:FontWeight.w900)))
      ],
      const SizedBox(height:8),
      Row(children:[Expanded(child:TextField(controller:km,enabled:!saving,keyboardType:const TextInputType.numberWithOptions(decimal:true),decoration:const InputDecoration(labelText:'KM *'))),const SizedBox(width:8),Expanded(child:TextField(controller:hour,enabled:!saving,keyboardType:const TextInputType.numberWithOptions(decimal:true),decoration:const InputDecoration(labelText:'Horímetro *')))]),
      const Text('Preenchimento obrigatório. Quando não se aplicar, use 0000.',style:TextStyle(fontSize:12,color:Colors.black54)),
      const SizedBox(height:8),TextField(controller:receiver,enabled:!saving,decoration:const InputDecoration(labelText:'Quem recebeu *')),
      const SizedBox(height:8),TextField(controller:location,readOnly:true,maxLines:2,decoration:InputDecoration(labelText:'Localização automática *',prefixIcon:const Icon(Icons.location_on_outlined),suffixIcon:IconButton(onPressed:saving||locating?null:loadLocation,tooltip:'Atualizar localização',icon:locating?const SizedBox(width:18,height:18,child:CircularProgressIndicator(strokeWidth:2)):const Icon(Icons.my_location_rounded)))),
      const Padding(padding:EdgeInsets.only(top:5,bottom:10),child:Text('O app usa o endereço sempre que conseguir identificá-lo. Latitude/longitude são usadas apenas quando o GPS obtém a posição, mas não consegue converter para endereço.',style:TextStyle(fontSize:11,color:Colors.black54))),
      OutlinedButton(onPressed:saving?null:()async{final x=await cam();if(x!=null)setState(()=>meter=x);},child:Text(meter==null?'Foto KM ou Horímetro *':'KM/Horímetro registrado ✓')),
      OutlinedButton(onPressed:saving?null:()async{final x=await cam();if(x!=null)setState(()=>totalizer=x);},child:Text(totalizer==null?'Foto Totalizador *':'Totalizador registrado ✓')),
      OutlinedButton(onPressed:saving?null:()async{final x=await cam();if(x!=null)setState(()=>identity=x);},child:Text(identity==null?'Foto da placa ou identificação *':'Foto da placa ou identificação ✓')),
      OutlinedButton(onPressed:saving?null:()async{final x=await cam();if(x!=null)setState(()=>extra=x);},child:Text(extra==null?'4ª foto (opcional)':'4ª foto registrada ✓')),
      OutlinedButton(onPressed:saving?null:()async{final x=await sign('Assinatura de quem recebeu');if(x!=null)setState(()=>rs=x);},child:Text(rs==null?'Assinatura de quem recebeu *':'Assinatura de quem recebeu ✓')),
      OutlinedButton(onPressed:saving?null:()async{final x=await sign('Assinatura de quem abasteceu');if(x!=null)setState(()=>os=x);},child:Text(os==null?'Assinatura de quem abasteceu *':'Assinatura de quem abasteceu ✓')),
      const SizedBox(height:12),FilledButton.icon(onPressed:saving?null:()=>submit(hasPlate),icon:saving?const SizedBox(width:18,height:18,child:CircularProgressIndicator(strokeWidth:2)):const Icon(Icons.check_rounded),label:Text(saving?savingStep:'Concluir abastecimento')),
      if(saving)const Padding(padding:EdgeInsets.only(top:8),child:Text('Não feche esta tela. O app está concluindo o registro.',textAlign:TextAlign.center,style:TextStyle(fontSize:12,color:Colors.black54)))
    ]));
  }
}'''
replace_class('class FuelingV23Screen extends StatefulWidget','class FuelDashboardV23Screen extends StatefulWidget',fueling)

staff=r'''String _permissionLabelV23(String key){
  const labels=<String,String>{
    'movements.view':'Visualizar registros','movements.correct':'Corrigir registros','pdf.export':'Exportar PDF',
    'nf.view':'Visualizar Notas Fiscais','nf.create':'Cadastrar Nota Fiscal','nf.edit':'Editar/corrigir Nota Fiscal',
    'financial.view':'Visualizar financeiro','stock.view':'Visualizar estoque','autonomy.view':'Visualizar autonomia',
    'comparisons.view':'Comparar equipamentos','reports.view':'Visualizar relatórios','reports.export':'Exportar relatórios',
    'audit.view':'Visualizar auditoria','operators.manage':'Gerenciar operadores','units.manage':'Gerenciar estruturas',
    'users.create':'Cadastrar usuários','users.edit':'Editar usuários','users.enable':'Habilitar usuários',
    'users.disable':'Desabilitar usuários','users.delete':'Excluir/remover acesso','intelligence.view':'Visualizar Intelligence',
    'intelligence.manage':'Gerenciar Intelligence',
  };
  return labels[key]??key;
}

class StaffPermissionsV23Screen extends StatefulWidget{
  const StaffPermissionsV23Screen({super.key});
  @override State<StaffPermissionsV23Screen> createState()=>_StaffPermissionsV23ScreenState();
}
class _StaffPermissionsV23ScreenState extends State<StaffPermissionsV23Screen>{
  List<Map<String,dynamic>> users=[];
  List<String> keys=[];
  List<Map<String,dynamic>> defaults=[];
  bool loading=true,busy=false;
  String? error;
  @override void initState(){super.initState();load();}

  Map<String,bool> roleDefaults(String role){
    final out=<String,bool>{for(final k in keys)k:false};
    for(final d in defaults){if('${d['role']}'==role)out['${d['permission_key']}']=d['allowed']==true;}
    return out;
  }

  Future<void> load() async {
    if(mounted)setState((){loading=true;error=null;});
    try{
      final result=await Future.wait<Map<String,dynamic>>([
        api.userActionMap({'action':'list_managers'}).timeout(const Duration(seconds:15)),
        api.userActionMap({'action':'permission_catalog'}).timeout(const Duration(seconds:15)),
      ]);
      if(mounted)setState((){
        users=_rows(result[0]['users']);
        keys=(result[1]['keys'] as List? ?? []).map((e)=>'$e').toList()..sort();
        defaults=_rows(result[1]['defaults']);
        loading=false;
      });
    }catch(e){if(mounted)setState((){loading=false;error=_friendlyError(e);});}
  }

  Future<void> editUser([Map<String,dynamic>? item]) async {
    final creating=item==null;
    final name=TextEditingController(text:'${item?['name']??''}');
    final username=TextEditingController(text:'${item?['username']??''}');
    final password=TextEditingController();
    String role='${item?['role']??'supervisor'}';
    if(!['supervisor','manager'].contains(role))role='supervisor';
    bool active=item?['active']!=false;
    Map<String,bool> permissions=creating?roleDefaults(role):<String,bool>{for(final k in keys)k:_map(item?['permissions'])[k]==true};
    final ok=await showDialog<bool>(context:context,builder:(ctx)=>StatefulBuilder(builder:(ctx,setD)=>AlertDialog(
      title:Text(creating?'Cadastrar supervisor/gerente':'Editar supervisor/gerente'),
      content:SizedBox(width:560,child:SingleChildScrollView(child:Column(mainAxisSize:MainAxisSize.min,children:[
        TextField(controller:name,decoration:const InputDecoration(labelText:'Nome *')),const SizedBox(height:8),
        TextField(controller:username,decoration:const InputDecoration(labelText:'Usuário / login *')),const SizedBox(height:8),
        TextField(controller:password,obscureText:true,decoration:InputDecoration(labelText:creating?'Senha inicial *':'Nova senha (deixe em branco para manter)')),const SizedBox(height:8),
        DropdownButtonFormField<String>(value:role,decoration:const InputDecoration(labelText:'Perfil *'),items:const [DropdownMenuItem(value:'supervisor',child:Text('Supervisor')),DropdownMenuItem(value:'manager',child:Text('Gerente'))],onChanged:(v){if(v==null)return;setD((){role=v;if(creating)permissions=roleDefaults(role);});}),
        SwitchListTile(contentPadding:EdgeInsets.zero,title:const Text('Acesso ativo'),value:active,onChanged:(v)=>setD(()=>active=v)),
        const Divider(),
        Row(children:[Expanded(child:Text('Hall de permissões',style:Theme.of(ctx).textTheme.titleMedium?.copyWith(fontWeight:FontWeight.w900))),TextButton(onPressed:()=>setD(()=>permissions=roleDefaults(role)),child:const Text('Usar padrão'))]),
        ...keys.map((k)=>SwitchListTile(contentPadding:EdgeInsets.zero,title:Text(_permissionLabelV23(k)),subtitle:Text(k,style:const TextStyle(fontSize:11)),value:permissions[k]==true,onChanged:(v)=>setD(()=>permissions[k]=v))),
      ]))),
      actions:[TextButton(onPressed:()=>Navigator.pop(ctx,false),child:const Text('Cancelar')),FilledButton(onPressed:()=>Navigator.pop(ctx,true),child:const Text('Salvar'))],
    )));
    if(ok!=true){name.dispose();username.dispose();password.dispose();return;}
    if(name.text.trim().isEmpty||username.text.trim().isEmpty||(creating&&password.text.trim().length<4)){
      if(mounted)ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content:Text('Preencha nome, usuário e uma senha inicial de pelo menos 4 caracteres.')));
      name.dispose();username.dispose();password.dispose();return;
    }
    setState(()=>busy=true);
    try{
      String userId='${item?['user_id']??''}';
      if(creating){
        final r=await api.userActionMap({'action':'create_manager','name':name.text.trim(),'username':username.text.trim(),'password':password.text,'role':role});
        userId='${r['user_id']??''}';
      }else{
        await api.userActionMap({'action':'update_manager','user_id':userId,'name':name.text.trim(),'username':username.text.trim(),'password':password.text,'role':role});
      }
      if(userId.isEmpty)throw Exception('Usuário salvo sem identificador.');
      for(final k in keys){await api.userActionMap({'action':'set_permission','user_id':userId,'permission_key':k,'allowed':permissions[k]==true});}
      final oldActive=item?['active']!=false;
      if(creating&&!active || !creating&&active!=oldActive){await api.userActionMap({'action':'set_manager_active','user_id':userId,'active':active});}
      await load();
      if(mounted)ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content:Text('Usuário e permissões salvos com sucesso ✓')));
    }catch(e){if(mounted)ScaffoldMessenger.of(context).showSnackBar(SnackBar(content:Text('Erro ao salvar usuário: ${_friendlyError(e)}')));}
    finally{if(mounted)setState(()=>busy=false);name.dispose();username.dispose();password.dispose();}
  }

  Future<void> toggleActive(Map<String,dynamic> u) async {
    setState(()=>busy=true);
    try{await api.userActionMap({'action':'set_manager_active','user_id':u['user_id'],'active':u['active']!=true});await load();}
    catch(e){if(mounted)ScaffoldMessenger.of(context).showSnackBar(SnackBar(content:Text(_friendlyError(e))));}
    finally{if(mounted)setState(()=>busy=false);}
  }

  Future<void> removeUser(Map<String,dynamic> u) async {
    final ok=await showDialog<bool>(context:context,builder:(ctx)=>AlertDialog(title:Text('Remover acesso de ${u['name']}?'),content:const Text('O acesso será removido, mas os registros históricos, movimentações e assinaturas serão preservados.'),actions:[TextButton(onPressed:()=>Navigator.pop(ctx,false),child:const Text('Cancelar')),FilledButton(onPressed:()=>Navigator.pop(ctx,true),child:const Text('Remover acesso'))]));
    if(ok!=true)return;
    setState(()=>busy=true);
    try{await api.userActionMap({'action':'delete_manager','user_id':u['user_id']});await load();if(mounted)ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content:Text('Acesso removido e histórico preservado ✓')));}
    catch(e){if(mounted)ScaffoldMessenger.of(context).showSnackBar(SnackBar(content:Text(_friendlyError(e))));}
    finally{if(mounted)setState(()=>busy=false);}
  }

  @override Widget build(BuildContext c){
    final staff=users.where((u)=>u['role']!='admin').toList();
    return Scaffold(
      appBar:AppBar(title:const Text('Supervisor, gerente e permissões')),
      floatingActionButton:FloatingActionButton.extended(onPressed:busy||loading?null:()=>editUser(),icon:const Icon(Icons.person_add_alt_1_rounded),label:const Text('Cadastrar')),
      body:loading?const Center(child:CircularProgressIndicator()):error!=null?Center(child:Padding(padding:const EdgeInsets.all(24),child:Column(mainAxisSize:MainAxisSize.min,children:[const Icon(Icons.cloud_off_rounded,size:52,color:_blue),const SizedBox(height:14),Text('Não foi possível carregar os usuários.\n$error',textAlign:TextAlign.center),const SizedBox(height:14),FilledButton.icon(onPressed:load,icon:const Icon(Icons.refresh_rounded),label:const Text('Tentar novamente'))]))):RefreshIndicator(onRefresh:load,child:ListView(padding:const EdgeInsets.fromLTRB(16,16,16,90),children:[
        const Card(child:ListTile(leading:Icon(Icons.security_rounded,color:_blue),title:Text('Hall de permissões',style:TextStyle(fontWeight:FontWeight.w900)),subtitle:Text('Cadastre Supervisor ou Gerente e escolha individualmente o que cada usuário pode visualizar ou alterar.'))),
        if(staff.isEmpty)const Padding(padding:EdgeInsets.symmetric(vertical:70,horizontal:20),child:Column(children:[Icon(Icons.group_add_outlined,size:58,color:_blue),SizedBox(height:14),Text('Nenhum Supervisor ou Gerente cadastrado.',style:TextStyle(fontWeight:FontWeight.w800),textAlign:TextAlign.center),SizedBox(height:6),Text('Use o botão “Cadastrar” para criar o primeiro acesso.',textAlign:TextAlign.center)])),
        ...staff.map((u)=>Card(child:ListTile(contentPadding:const EdgeInsets.all(14),leading:CircleAvatar(child:Icon(u['role']=='manager'?Icons.manage_accounts_rounded:Icons.supervisor_account_rounded)),title:Text('${u['name']}',style:const TextStyle(fontWeight:FontWeight.w900)),subtitle:Text('${u['role']=='manager'?'Gerente':'Supervisor'} • ${u['username']??''}\n${u['active']==true?'Ativo':'Inativo'}'),isThreeLine:true,onTap:busy?null:()=>editUser(u),trailing:PopupMenuButton<String>(enabled:!busy,onSelected:(v){if(v=='edit')editUser(u);if(v=='active')toggleActive(u);if(v=='delete')removeUser(u);},itemBuilder:(_)=>[const PopupMenuItem(value:'edit',child:Text('Editar cadastro e permissões')),PopupMenuItem(value:'active',child:Text(u['active']==true?'Desabilitar acesso':'Habilitar acesso')),const PopupMenuItem(value:'delete',child:Text('Excluir / remover acesso'))])))),
      ])),
    );
  }
}'''
replace_class('class StaffPermissionsV23Screen extends StatefulWidget','class RefineryEntryScreen extends StatefulWidget',staff)

my_records=r'''class MyOnlineMovementsScreen extends StatefulWidget {
  const MyOnlineMovementsScreen({super.key});
  @override State<MyOnlineMovementsScreen> createState() => _MyOnlineMovementsScreenState();
}

class _MyOnlineMovementsScreenState extends State<MyOnlineMovementsScreen> {
  List<Map<String, dynamic>>? items;
  Timer? timer;
  Timer? holdTimer;
  final Set<String> selectedCodes = <String>{};
  bool busy = false;
  bool loading = false;
  bool loadRunning = false;
  bool suppressNextTap = false;
  String? loadError;

  String itemKey(Map<String, dynamic> x) => '${x['code'] ?? x['id'] ?? ''}';
  bool get selectionMode => selectedCodes.isNotEmpty;
  List<Map<String, dynamic>> get selectedItems => (items ?? const <Map<String, dynamic>>[]).where((x) => selectedCodes.contains(itemKey(x))).toList();

  @override void initState() {
    super.initState();
    load();
    timer = Timer.periodic(const Duration(seconds: 15), (_) { if (!selectionMode && !busy && !loadRunning) load(silent:true); });
  }
  @override void dispose() { timer?.cancel(); holdTimer?.cancel(); super.dispose(); }

  Future<void> load({bool silent=false}) async {
    if(loadRunning)return;
    loadRunning=true;
    if(mounted&&!silent)setState((){loading=true;loadError=null;});
    try {
      final x = await api.recent(limit: 100).timeout(const Duration(seconds: 12));
      if (mounted) setState(() { items = x; loadError=null; });
    } catch (e) {
      if (mounted) setState(() => loadError='Não foi possível carregar os registros. ${_friendlyError(e)}');
    } finally {
      loadRunning=false;
      if(mounted&&!silent)setState(()=>loading=false);
    }
  }

  void toggleSelected(Map<String, dynamic> x) {final key=itemKey(x);if(key.isEmpty)return;setState(() { if (!selectedCodes.add(key)) selectedCodes.remove(key); });}
  void beginHold(Map<String, dynamic> x) {holdTimer?.cancel();suppressNextTap=false;holdTimer=Timer(const Duration(seconds: 1), () {if (!mounted) return;suppressNextTap=true;toggleSelected(x);});}
  void cancelHold() { holdTimer?.cancel(); holdTimer = null; }
  void clearSelection() => setState(() { selectedCodes.clear(); suppressNextTap = false; });
  void openOrSelect(Map<String, dynamic> x) {if (suppressNextTap) { suppressNextTap = false; return; }if (selectionMode) { toggleSelected(x); return; }Navigator.push(context, MaterialPageRoute(builder: (_) => MovementDetailScreen(item: x)));}

  Future<void> exportPdf() async {
    final targets=selectedItems;if(targets.isEmpty)return;setState(()=>busy=true);
    try {final bytes=await FuelPdfReport.build(targets);await Printing.sharePdf(bytes:bytes,filename:'RC-Abastecimento-${DateTime.now().millisecondsSinceEpoch}.pdf');if(mounted)clearSelection();}
    catch(e){if(mounted)ScaffoldMessenger.of(context).showSnackBar(SnackBar(content:Text('Falha ao gerar PDF: ${_friendlyError(e)}')));}
    finally{if(mounted)setState(()=>busy=false);}
  }

  Widget recordList(){
    final list=items??const <Map<String,dynamic>>[];
    return RefreshIndicator(onRefresh:()=>load(),child:ListView(padding:const EdgeInsets.fromLTRB(16,8,16,60),children:[
      if(loadError!=null)Card(child:ListTile(leading:const Icon(Icons.warning_amber_rounded,color:_blue),title:const Text('Não foi possível atualizar agora.'),subtitle:Text(loadError!),trailing:IconButton(onPressed:()=>load(),icon:const Icon(Icons.refresh_rounded)))),
      if(loading)const LinearProgressIndicator(minHeight:2),
      if(list.isEmpty)const Padding(padding:EdgeInsets.only(top:160),child:Center(child:Text('Nenhum registro ainda.'))),
      ...list.map((x){
        final asset=x['asset_number']??x['third_party_plate']??x['destination_tank']??x['source_tank']??'-';
        final selected=selectedCodes.contains(itemKey(x));
        final comboioToComboio=_isComboioToComboio(x);
        return GestureDetector(behavior:HitTestBehavior.opaque,onTapDown:(_)=>beginHold(x),onTapUp:(_)=>cancelHold(),onTapCancel:cancelHold,onTap:()=>openOrSelect(x),child:Card(color:comboioToComboio?_comboioToComboioPale:null,shape:RoundedRectangleBorder(borderRadius:BorderRadius.circular(18),side:BorderSide(color:selected?_blue:const Color(0xFFE2E8F0),width:selected?1.5:1)),child:Padding(padding:const EdgeInsets.all(16),child:Row(crossAxisAlignment:CrossAxisAlignment.start,children:[Expanded(child:Column(crossAxisAlignment:CrossAxisAlignment.start,children:[Text('${_movementLabelForItem(x)} • $asset',style:const TextStyle(fontSize:17,fontWeight:FontWeight.w900)),const SizedBox(height:10),Row(children:[const Icon(Icons.calendar_today_outlined,size:18,color:_blue),const SizedBox(width:10),Text(_fmtDate(x['created_at']))]),const SizedBox(height:7),Row(children:[const Icon(Icons.location_city_outlined,size:18,color:_blue),const SizedBox(width:10),Expanded(child:Text('${x['work']??'Sem obra'}'))]),const SizedBox(height:7),Row(children:[const Icon(Icons.water_drop_outlined,size:18,color:_blue),const SizedBox(width:10),Text(_fmtLiters(x['liters'])),if(_hasValue(x['fuel_type']))Text(' • ${x['fuel_type']}',style:const TextStyle(color:_ink))]),const SizedBox(height:7),Row(children:[const Icon(Icons.person_outline_rounded,size:18,color:_blue),const SizedBox(width:10),Expanded(child:Text('${x['operator']??'-'}'))])])),const SizedBox(width:8),if(selectionMode)Checkbox(value:selected,onChanged:(_)=>toggleSelected(x))else const Icon(Icons.chevron_right_rounded)]))));
      }),
    ]));
  }

  @override Widget build(BuildContext context)=>Scaffold(
    appBar:AppBar(title:Text(selectionMode?'${selectedCodes.length} selecionado(s)':'Meus registros'),actions:[if(selectionMode)IconButton(onPressed:busy?null:exportPdf,tooltip:'Exportar selecionados em PDF',icon:const Icon(Icons.picture_as_pdf_outlined)),if(selectionMode)IconButton(onPressed:busy?null:clearSelection,tooltip:'Cancelar seleção',icon:const Icon(Icons.close_rounded))]),
    body:items==null&&loading?const Center(child:CircularProgressIndicator()):items==null&&loadError!=null?Center(child:Padding(padding:const EdgeInsets.all(24),child:Column(mainAxisSize:MainAxisSize.min,children:[const Icon(Icons.cloud_off_rounded,size:56,color:_blue),const SizedBox(height:16),Text(loadError!,textAlign:TextAlign.center),const SizedBox(height:16),FilledButton.icon(onPressed:()=>load(),icon:const Icon(Icons.refresh_rounded),label:const Text('Tentar novamente'))])):recordList(),
  );
}'''
replace_class('class MyOnlineMovementsScreen extends StatefulWidget','class AdminHomeScreen extends StatefulWidget',my_records)

third=r'''class ThirdPartyAdminScreen extends StatefulWidget {
  const ThirdPartyAdminScreen({super.key});
  @override State<ThirdPartyAdminScreen> createState()=>_ThirdPartyAdminScreenState();
}
class _ThirdPartyAdminScreenState extends State<ThirdPartyAdminScreen> {
  List<Map<String,dynamic>>? items;
  List<Map<String,dynamic>> companies=[];
  bool loading=false;
  @override void initState(){super.initState();load();}
  Future<void> load() async {
    if(mounted)setState(()=>loading=true);
    try{
      final r=await Future.wait<dynamic>([api.referenceData(),api.managedCompanies()]);
      final c=List<Map<String,dynamic>>.from(r[1] as List<Map<String,dynamic>>)..removeWhere((x)=>x['active']==false);
      c.sort((a,b)=>'${a['name']}'.toLowerCase().compareTo('${b['name']}'.toLowerCase()));
      if(mounted)setState((){items=_rows(_map(r[0])['third_party_vehicles']);companies=c;});
    }catch(e){if(mounted)ScaffoldMessenger.of(context).showSnackBar(SnackBar(content:Text('Erro ao carregar terceiros/empresas: ${_friendlyError(e)}')));}
    finally{if(mounted)setState(()=>loading=false);}
  }
  int? companyIdFor(String name){for(final c in companies){if('${c['name']}'.trim().toLowerCase()==name.trim().toLowerCase())return _intOrNull(c['id']);}return null;}
  String? companyNameFor(int? id){if(id==null)return null;for(final c in companies){if(_intOrNull(c['id'])==id)return '${c['name']}';}return null;}

  Future<void> edit([Map<String,dynamic>? item]) async {
    final plate=TextEditingController(text:'${item?['plate']??''}');
    final desc=TextEditingController(text:'${item?['description']??''}');
    final driver=TextEditingController(text:'${item?['driver_name']??''}');
    int? companyId=companyIdFor('${item?['company_name']??''}');
    if(companies.isEmpty){
      if(mounted)ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content:Text('Nenhuma empresa cadastrada. Cadastre uma empresa antes de vinculá-la ao equipamento.')));
    }
    final ok=await showDialog<bool>(context:context,builder:(ctx)=>StatefulBuilder(builder:(ctx,setD)=>AlertDialog(
      title:Text(item==null?'Cadastrar terceiro':'Editar terceiro'),
      content:SingleChildScrollView(child:Column(mainAxisSize:MainAxisSize.min,children:[
        TextField(controller:plate,textCapitalization:TextCapitalization.characters,decoration:const InputDecoration(labelText:'Placa (quando houver)')),const SizedBox(height:8),
        DropdownButtonFormField<int?>(value:companyId,isExpanded:true,decoration:const InputDecoration(labelText:'Empresa / locadora'),items:[const DropdownMenuItem<int?>(value:null,child:Text('Sem empresa vinculada')),...companies.map((c)=>DropdownMenuItem<int?>(value:_intOrNull(c['id']),child:Text('${c['name']}')))],onChanged:(v)=>setD(()=>companyId=v)),
        if(companies.isEmpty)const Padding(padding:EdgeInsets.only(top:6),child:Align(alignment:Alignment.centerLeft,child:Text('Nenhuma empresa cadastrada.',style:TextStyle(color:Colors.redAccent,fontSize:12)))),
        const SizedBox(height:8),TextField(controller:desc,decoration:const InputDecoration(labelText:'Descrição / identificação *')),const SizedBox(height:8),TextField(controller:driver,decoration:const InputDecoration(labelText:'Motorista')),
      ])),
      actions:[TextButton(onPressed:()=>Navigator.pop(ctx,false),child:const Text('Cancelar')),FilledButton(onPressed:()=>Navigator.pop(ctx,true),child:const Text('Salvar'))],
    )));
    if(ok==true){
      if(plate.text.trim().isEmpty&&desc.text.trim().isEmpty){if(mounted)ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content:Text('Informe a placa ou uma descrição que identifique o equipamento.')));}
      else{
        try{await api.saveThirdParty(id:_intOrNull(item?['id']),plate:plate.text.trim(),company:companyNameFor(companyId),description:desc.text.trim(),driverName:driver.text.trim());await load();if(mounted)ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content:Text('Equipamento de terceiros salvo com sucesso ✓')));}
        catch(e){if(mounted)ScaffoldMessenger.of(context).showSnackBar(SnackBar(content:Text('Erro ao salvar equipamento: ${_friendlyError(e)}')));}
      }
    }
    plate.dispose();desc.dispose();driver.dispose();
  }
  @override Widget build(BuildContext context)=>Scaffold(appBar:AppBar(title:const Text('Equipamentos de terceiros')),floatingActionButton:FloatingActionButton(onPressed:loading?null:()=>edit(),child:const Icon(Icons.add)),body:items==null?const Center(child:CircularProgressIndicator()):RefreshIndicator(onRefresh:load,child:ListView(padding:const EdgeInsets.all(12),children:[
    if(companies.isEmpty)const Card(child:ListTile(leading:Icon(Icons.business_outlined,color:_blue),title:Text('Nenhuma empresa cadastrada'),subtitle:Text('Cadastre as empresas na área “Empresas” para poder selecioná-las nos equipamentos de terceiros.'))),
    ...items!.map((x)=>Card(child:ListTile(title:Text('${_hasValue(x['plate'])?x['plate']:'Sem placa'} • ${x['description']??''}',style:const TextStyle(fontWeight:FontWeight.w900)),subtitle:Text('${x['company_name']??'Sem empresa'} • ${x['driver_name']??''}'),onTap:loading?null:()=>edit(x),trailing:const Icon(Icons.edit_outlined)))),
  ])));
}'''
idx=s.index('class ThirdPartyAdminScreen extends StatefulWidget')
s=s[:idx]+third+'\n'

p.write_text(s)
print('user reported fixes applied',len(s),len(s.splitlines()))
