from pathlib import Path
p=Path("lib/main_online.dart")
s=p.read_text()

def replace_once(old,new,label):
    global s
    if old not in s:
        raise SystemExit(f"anchor missing: {label}")
    s=s.replace(old,new,1)

def replace_between(start,end,new,label):
    global s
    i=s.find(start)
    if i<0: raise SystemExit(f"start missing: {label}")
    j=s.find(end,i)
    if j<0: raise SystemExit(f"end missing: {label}")
    s=s[:i]+new+s[j:]

# ---------- API ----------
old="""  Future<Map<String,dynamic>> refineryLoadV22({required int truckTankId,required double liters,required String supplier,required String invoice,required double unitCost,required String fuelType,String? batch,String? notes}) async => _map(await client.rpc('rca_record_refinery_load_v22',params:{'p_truck_tank_id':truckTankId,'p_liters':liters,'p_supplier_name':supplier,'p_invoice_number':invoice,'p_batch_number':batch,'p_unit_cost':unitCost,'p_fuel_type':fuelType,'p_photo_paths':<String>[],'p_notes':notes}));
"""
new="""  Future<Map<String,dynamic>> refineryLoadV22({
    required int truckTankId,
    required double liters,
    required String supplier,
    required String invoice,
    required double unitCost,
    required String fuelType,
    required String truckPlatePhoto,
    required String invoicePhoto,
    String? batch,
    String? notes,
  }) async => _map(await client.rpc('rca_record_refinery_load_v22',params:{
    'p_truck_tank_id':truckTankId,'p_liters':liters,'p_supplier_name':supplier,'p_invoice_number':invoice,
    'p_batch_number':batch,'p_unit_cost':unitCost,'p_fuel_type':fuelType,
    'p_photo_paths':<String>[truckPlatePhoto,invoicePhoto],'p_notes':notes,
  }));
"""
replace_once(old,new,'refinery api')

anchor="""  Future<List<Map<String,dynamic>>> compareV22(List<int> machines,List<int> thirds) async => _rows(await client.rpc('rca_compare_equipment_v22',params:{'p_machine_ids':machines,'p_third_party_ids':thirds,'p_start':null,'p_end':null}));
"""
extra=anchor+"""
  Future<List<Map<String,dynamic>>> worksCatalogV23() async => _rows(await client.rpc('rca_works_catalog_v23'));
  Future<Map<String,dynamic>> workFinalReportDataV23(int workId) async => _map(await client.rpc('rca_work_final_report_data_v23',params:{'p_work_id':workId}));
  Future<Map<String,dynamic>> finalizeWorkV23(int workId,String pdfPath) async => _map(await client.rpc('rca_finalize_work_v23',params:{'p_work_id':workId,'p_pdf_path':pdfPath}));
  Future<List<Map<String,dynamic>>> generatedReportsSearchV23({String? workName,String? responsible,DateTime? start,DateTime? end,String? asset}) async {
    String? day(DateTime? d)=>d==null?null:'${d.year.toString().padLeft(4,'0')}-${d.month.toString().padLeft(2,'0')}-${d.day.toString().padLeft(2,'0')}';
    return _rows(await client.rpc('rca_generated_reports_search_v23',params:{'p_work_name':workName,'p_responsible':responsible,'p_start':day(start),'p_end':day(end),'p_asset':asset}));
  }
  Future<Map<String,dynamic>> generatedReportDetailV23(int reportId) async => _map(await client.rpc('rca_generated_report_detail_v23',params:{'p_report_id':reportId}));
  Future<List<Map<String,dynamic>>> lotsCatalogV23() async => _rows(await client.rpc('rca_lots_catalog_v23'));
  Future<Map<String,dynamic>> traceV23(int lotId) async => _map(await client.rpc('rca_nf_trace_v23',params:{'p_lot_id':lotId}));
  Future<Map<String,dynamic>> movementTraceV23(int movementId) async => _map(await client.rpc('rca_movement_trace_v23',params:{'p_movement_id':movementId}));
  Future<Map<String,dynamic>> reportContextV23(int movementId) async => _map(await client.rpc('rca_report_context_v23',params:{'p_movement_id':movementId}));
"""
replace_once(anchor,extra,'business api methods')

replace_once("""      final ext = mime.contains('jpeg') ? 'jpg' : mime.contains('webp') ? 'webp' : 'png';
""","""      final ext = mime.contains('pdf') ? 'pdf' : mime.contains('jpeg') ? 'jpg' : mime.contains('webp') ? 'webp' : 'png';
""",'pdf extension')

# ---------- truck can also fuel ----------
old="""                    HomeActionCard(icon: Icons.swap_horiz_rounded,title:'Transferir',subtitle:'Caminhão-tanque → Comboio',onTap:()=>open(TransferV23Screen(source:t,ref:ref!,profile:widget.profile))),
                  ] else if (comboio) ...[
"""
new="""                    HomeActionCard(icon: Icons.swap_horiz_rounded,title:'Transferir',subtitle:'Caminhão-tanque → Comboio',onTap:()=>open(TransferV23Screen(source:t,ref:ref!,profile:widget.profile))),
                    const SizedBox(height:12),
                    HomeActionCard(icon: Icons.local_gas_station_rounded,title:'Abastecer como comboio',subtitle:'Usar o caminhão-tanque para abastecer diretamente ativos e equipamentos',onTap:()=>open(FuelingV23Screen(source:t,ref:ref!,profile:widget.profile))),
                  ] else if (comboio) ...[
"""
replace_once(old,new,'truck fueling card')

# ---------- refinery receipt screen ----------
refinery_code=r'''class RefineryLoadV23Screen extends StatefulWidget {
  final Map<String,dynamic> truck;
  const RefineryLoadV23Screen({super.key,required this.truck});
  @override State<RefineryLoadV23Screen> createState()=>_RefineryLoadV23ScreenState();
}
class _RefineryLoadV23ScreenState extends State<RefineryLoadV23Screen> {
  final nf=TextEditingController(),supplier=TextEditingController(),liters=TextEditingController(),cost=TextEditingController(),batch=TextEditingController(),notes=TextEditingController();
  String fuel='Diesel';
  XFile? truckPlatePhoto,invoicePhoto;
  bool busy=false;
  String step='Registrar NF e carga';

  Future<XFile?> camera()=>ImagePicker().pickImage(source:ImageSource.camera,imageQuality:78,maxWidth:1800);
  void message(String value)=>ScaffoldMessenger.of(context).showSnackBar(SnackBar(content:Text(value)));

  Future<void> submit() async {
    if(busy)return;
    final volume=double.tryParse(liters.text.trim().replaceAll(',','.'));
    final unitCost=double.tryParse(cost.text.trim().replaceAll(',','.'));
    if(nf.text.trim().isEmpty){message('Preenchimento obrigatório: Número da Nota Fiscal');return;}
    if(supplier.text.trim().isEmpty){message('Preenchimento obrigatório: Fornecedor do combustível');return;}
    if(volume==null||volume<=0){message('Preenchimento obrigatório: Volume recebido');return;}
    if(unitCost==null||unitCost<0){message('Preenchimento obrigatório: Preço de compra por litro');return;}
    if(truckPlatePhoto==null){message('Foto da placa do caminhão-tanque obrigatória');return;}
    if(invoicePhoto==null){message('Foto legível da Nota Fiscal obrigatória');return;}
    final ok=await showDialog<bool>(context:context,builder:(ctx)=>AlertDialog(
      title:const Text('Confirmar recebimento da refinaria?'),
      content:Column(mainAxisSize:MainAxisSize.min,crossAxisAlignment:CrossAxisAlignment.start,children:[
        Text('Caminhão-tanque: ${widget.truck['code']} • ${widget.truck['name']}',style:const TextStyle(fontWeight:FontWeight.w700)),
        const SizedBox(height:8),Text('Nota Fiscal: ${nf.text.trim()}'),Text('Fornecedor do combustível: ${supplier.text.trim()}'),Text('Combustível: $fuel'),Text('Volume recebido: ${_fmtLiters(volume)}'),Text('Preço de compra/L: ${_fmtMoney(unitCost)}'),
        const SizedBox(height:8),const Text('A data e a hora da chegada serão registradas automaticamente pelo app.'),
      ]),
      actions:[TextButton(onPressed:()=>Navigator.pop(ctx,false),child:const Text('Cancelar')),FilledButton(onPressed:()=>Navigator.pop(ctx,true),child:const Text('Confirmar recebimento'))],
    ));
    if(ok!=true||!mounted)return;
    setState((){busy=true;step='Enviando fotos obrigatórias...';});
    try{
      Future<String> up(XFile f,String kind) async=>api.uploadBytes(await f.readAsBytes(),kind,mime:f.mimeType??'image/jpeg');
      final photos=await Future.wait<String>([up(truckPlatePhoto!,'placa_caminhao_tanque'),up(invoicePhoto!,'nota_fiscal_legivel')]);
      if(!mounted)return;
      setState(()=>step='Registrando NF e lote...');
      final r=await api.refineryLoadV22(truckTankId:_intOrNull(widget.truck['id'])!,liters:volume,supplier:supplier.text.trim(),invoice:nf.text.trim(),unitCost:unitCost,fuelType:fuel,truckPlatePhoto:photos[0],invoicePhoto:photos[1],batch:batch.text.trim(),notes:notes.text.trim());
      if(!mounted)return;
      message('NF ${r['invoice_number']} registrada com sucesso ✓ • ${_fmtLiters(r['liters'])}');
      Navigator.pop(context,true);
    }catch(e){if(mounted)message('Erro ao registrar recebimento: ${_friendlyError(e)}');}
    finally{if(mounted)setState((){busy=false;step='Registrar NF e carga';});}
  }

  @override void dispose(){for(final c in [nf,supplier,liters,cost,batch,notes]){c.dispose();}super.dispose();}
  @override Widget build(BuildContext c)=>Scaffold(
    appBar:AppBar(title:const Text('Entrada da refinaria / NF')),
    body:ListView(padding:const EdgeInsets.all(18),children:[
      Text('${widget.truck['code']} • ${widget.truck['name']}',style:Theme.of(c).textTheme.titleLarge?.copyWith(fontWeight:FontWeight.w900)),
      const SizedBox(height:5),const Text('Toda chegada da refinaria deve entrar primeiro pela Nota Fiscal. A partir dela o combustível será rastreado nas transferências e abastecimentos.'),
      const SizedBox(height:14),
      TextField(controller:nf,enabled:!busy,decoration:const InputDecoration(labelText:'Número da Nota Fiscal *')),
      const SizedBox(height:8),TextField(controller:supplier,enabled:!busy,decoration:const InputDecoration(labelText:'Fornecedor do combustível *')),
      const SizedBox(height:8),TextField(controller:batch,enabled:!busy,decoration:const InputDecoration(labelText:'Lote / remessa')),
      const SizedBox(height:8),DropdownButtonFormField<String>(value:fuel,decoration:const InputDecoration(labelText:'Combustível *'),items:_fuelTypes.map((x)=>DropdownMenuItem(value:x,child:Text(x))).toList(),onChanged:busy?null:(v)=>setState(()=>fuel=v??'Diesel')),
      const SizedBox(height:8),TextField(controller:liters,enabled:!busy,keyboardType:const TextInputType.numberWithOptions(decimal:true),decoration:const InputDecoration(labelText:'Volume recebido (L) *')),
      const SizedBox(height:8),TextField(controller:cost,enabled:!busy,keyboardType:const TextInputType.numberWithOptions(decimal:true),decoration:const InputDecoration(labelText:'Preço de compra/L *')),
      const SizedBox(height:8),TextField(controller:notes,enabled:!busy,maxLines:3,decoration:const InputDecoration(labelText:'Observações')),
      const SizedBox(height:12),
      OutlinedButton.icon(onPressed:busy?null:()async{final x=await camera();if(x!=null)setState(()=>truckPlatePhoto=x);},icon:const Icon(Icons.local_shipping_outlined),label:Text(truckPlatePhoto==null?'Foto da placa do caminhão-tanque *':'Foto da placa do caminhão-tanque ✓')),
      const SizedBox(height:6),
      OutlinedButton.icon(onPressed:busy?null:()async{final x=await camera();if(x!=null)setState(()=>invoicePhoto=x);},icon:const Icon(Icons.receipt_long_outlined),label:Text(invoicePhoto==null?'Foto legível da Nota Fiscal *':'Foto legível da Nota Fiscal ✓')),
      const SizedBox(height:8),const Card(child:ListTile(leading:Icon(Icons.schedule_rounded,color:_blue),title:Text('Data e hora da chegada'),subtitle:Text('Registradas automaticamente no momento em que a carga é confirmada.'))),
      const SizedBox(height:14),FilledButton.icon(onPressed:busy?null:submit,icon:busy?const SizedBox(width:18,height:18,child:CircularProgressIndicator(strokeWidth:2)):const Icon(Icons.check_rounded),label:Text(busy?step:'Registrar NF e carga')),
    ]),
  );
}

'''
replace_between('class RefineryLoadV23Screen','class RefineryToTeV23Screen',refinery_code,'refinery screen')

# ---------- truck -> TE confirmation and explicit outcome ----------
ref_to_te=r'''class RefineryToTeV23Screen extends StatefulWidget {
  final Map<String,dynamic> truck,ref;
  const RefineryToTeV23Screen({super.key,required this.truck,required this.ref});
  @override State<RefineryToTeV23Screen> createState()=>_RefineryToTeV23ScreenState();
}
class _RefineryToTeV23ScreenState extends State<RefineryToTeV23Screen> {
  int? te,lot;
  final liters=TextEditingController();
  bool busy=false;
  @override void dispose(){liters.dispose();super.dispose();}
  @override Widget build(BuildContext c){
    final tes=_rows(widget.ref['tanks']).where((x)=>x['tank_type']=='stationary').toList(),lots=_rows(widget.ref['open_lots']);
    Map<String,dynamic>? target(){for(final x in tes){if(_intOrNull(x['id'])==te)return x;}return null;}
    Future<void> submit() async {
      final v=double.tryParse(liters.text.trim().replaceAll(',','.'));
      if(te==null){ScaffoldMessenger.of(c).showSnackBar(const SnackBar(content:Text('Preenchimento obrigatório: T.E. recebedor')));return;}
      if(v==null||v<=0){ScaffoldMessenger.of(c).showSnackBar(const SnackBar(content:Text('Preenchimento obrigatório: Volume da transferência')));return;}
      final t=target();
      final ok=await showDialog<bool>(context:c,builder:(ctx)=>AlertDialog(title:const Text('Confirmar transferência?'),content:Column(mainAxisSize:MainAxisSize.min,crossAxisAlignment:CrossAxisAlignment.start,children:[
        Text('Origem: ${widget.truck['code']} • ${widget.truck['name']}'),Text('Destino: ${t?['code']} • ${t?['name']}'),Text('Volume: ${_fmtLiters(v)}'),const SizedBox(height:8),const Text('Tipo de movimento: Transferência interna — sem venda')
      ]),actions:[TextButton(onPressed:()=>Navigator.pop(ctx,false),child:const Text('Cancelar')),FilledButton(onPressed:()=>Navigator.pop(ctx,true),child:const Text('Confirmar transferência'))]));
      if(ok!=true||!mounted)return;
      setState(()=>busy=true);
      try{await api.refineryToTeV22(truckTankId:_intOrNull(widget.truck['id'])!,teTankId:te!,lotId:lot,liters:v);if(mounted){ScaffoldMessenger.of(c).showSnackBar(const SnackBar(content:Text('Transferência registrada com sucesso ✓')));Navigator.pop(c,true);}}
      catch(e){if(mounted)ScaffoldMessenger.of(c).showSnackBar(SnackBar(content:Text('Erro ao registrar transferência: ${_friendlyError(e)}')));}
      finally{if(mounted)setState(()=>busy=false);}
    }
    return Scaffold(appBar:AppBar(title:const Text('Caminhão-tanque → T.E.')),body:ListView(padding:const EdgeInsets.all(18),children:[
      const Card(child:ListTile(leading:Icon(Icons.swap_horiz_rounded,color:_blue),title:Text('Transferência interna — sem venda'),subtitle:Text('O combustível muda de local, mas continua vinculado à mesma NF/lote.'))),
      DropdownButtonFormField<int>(value:te,decoration:const InputDecoration(labelText:'T.E. recebedor *'),items:tes.map((x)=>DropdownMenuItem(value:_intOrNull(x['id']),child:Text('${x['code']} • ${x['name']}'))).toList(),onChanged:busy?null:(v)=>setState(()=>te=v)),
      const SizedBox(height:8),DropdownButtonFormField<int?>(value:lot,decoration:const InputDecoration(labelText:'NF/lote (vazio = FIFO)'),items:[const DropdownMenuItem<int?>(value:null,child:Text('FIFO automático')),...lots.map((x)=>DropdownMenuItem<int?>(value:_intOrNull(x['id']),child:Text('NF ${x['invoice_number']} • ${_fmtLiters(x['remaining_liters'])}')))],onChanged:busy?null:(v)=>setState(()=>lot=v)),
      const SizedBox(height:8),TextField(controller:liters,enabled:!busy,keyboardType:const TextInputType.numberWithOptions(decimal:true),decoration:const InputDecoration(labelText:'Volume (L) *')),
      const SizedBox(height:16),FilledButton.icon(onPressed:busy?null:submit,icon:busy?const SizedBox(width:18,height:18,child:CircularProgressIndicator(strokeWidth:2)):const Icon(Icons.swap_horiz_rounded),label:Text(busy?'Registrando...':'Registrar descarga')),
    ]));
  }
}

'''
replace_between('class RefineryToTeV23Screen','class TransferV23Screen',ref_to_te,'refinery to TE')

# ---------- fueling: truck requires work + precise local validation ----------
replace_once("""    if(v<=0||(machine==null&&third==null)||receiver.text.trim().isEmpty||location.text.trim().isEmpty||meter==null||totalizer==null||identity==null||rs==null||os==null||(widget.source['tank_type']=='comboio'&&work==null)){if(mounted)ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content:Text('Confira os campos obrigatórios, a localização, as 3 fotos e as 2 assinaturas.')));return;}
""","""    final needsWork=const ['comboio','truck'].contains('${widget.source['tank_type']}');
    void requiredMessage(String field){if(mounted)ScaffoldMessenger.of(context).showSnackBar(SnackBar(content:Text('Preenchimento obrigatório: $field')));}
    if(v<=0){requiredMessage('Quantidade (L)');return;}
    if(needsWork&&work==null){requiredMessage('Obra');return;}
    if(machine==null&&third==null){requiredMessage('Ativo ou Equipamento de terceiros');return;}
    if(receiver.text.trim().isEmpty){requiredMessage('Quem recebeu');return;}
    if(location.text.trim().isEmpty){requiredMessage('Localização');return;}
    if(meter==null){requiredMessage('Foto de KM/Horímetro');return;}
    if(totalizer==null){requiredMessage('Foto do Totalizador');return;}
    if(identity==null){requiredMessage('Foto da placa ou identificação');return;}
    if(rs==null){requiredMessage('Assinatura de quem recebeu');return;}
    if(os==null){requiredMessage('Assinatura de quem abasteceu');return;}
""",'fueling validation')
replace_once("""    final ms=_rows(widget.ref['machines']),ts=_rows(widget.ref['third_party_vehicles']),ws=_rows(widget.ref['works']);
    final sm=selected(ms,machine),st=selected(ts,third),sw=selected(ws,work),hasPlate=_hasValue(sm?['placa'])||_hasValue(st?['plate']);
    return Scaffold(appBar:AppBar(title:const Text('Novo abastecimento')),body:ListView(padding:const EdgeInsets.all(18),children:[
      if(widget.source['tank_type']=='comboio')DropdownButtonFormField<int>(value:work,decoration:const InputDecoration(labelText:'Obra *'),items:ws.map((x)=>DropdownMenuItem(value:_intOrNull(x['id']),child:Text('${x['name']}'))).toList(),onChanged:saving?null:(v)=>setState(()=>work=v)),
      if(widget.source['tank_type']=='comboio'&&_hasValue(sw?['responsible']))Padding(padding:const EdgeInsets.only(top:6),child:Text('Responsável: ${sw?['responsible']}',style:const TextStyle(fontWeight:FontWeight.w700))),
      if(widget.source['tank_type']=='comboio')const SizedBox(height:8),
""","""    final ms=_rows(widget.ref['machines']),ts=_rows(widget.ref['third_party_vehicles']),ws=_rows(widget.ref['works']);
    final sm=selected(ms,machine),st=selected(ts,third),sw=selected(ws,work),hasPlate=_hasValue(sm?['placa'])||_hasValue(st?['plate']);
    final needsWork=const ['comboio','truck'].contains('${widget.source['tank_type']}');
    return Scaffold(appBar:AppBar(title:Text(widget.source['tank_type']=='truck'?'Abastecer como comboio':'Novo abastecimento')),body:ListView(padding:const EdgeInsets.all(18),children:[
      if(needsWork)DropdownButtonFormField<int>(value:work,decoration:const InputDecoration(labelText:'Obra *'),items:ws.map((x)=>DropdownMenuItem(value:_intOrNull(x['id']),child:Text('${x['name']}'))).toList(),onChanged:saving?null:(v)=>setState(()=>work=v)),
      if(needsWork&&_hasValue(sw?['responsible']))Padding(padding:const EdgeInsets.only(top:6),child:Text('Responsável da obra: ${sw?['responsible']}',style:const TextStyle(fontWeight:FontWeight.w700))),
      if(needsWork)const SizedBox(height:8),
""",'fueling work condition')

p.write_text(s)
print("business reports part 1 applied",len(s),"chars")
