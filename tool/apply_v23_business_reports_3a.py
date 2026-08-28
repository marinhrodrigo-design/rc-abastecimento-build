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

insert_marker='class AdminHomeScreen extends StatefulWidget {'
if insert_marker not in s: raise SystemExit('admin home marker missing')
new_classes=r'''class GeneratedReportsV23Screen extends StatefulWidget {
  const GeneratedReportsV23Screen({super.key});
  @override State<GeneratedReportsV23Screen> createState()=>_GeneratedReportsV23ScreenState();
}
class _GeneratedReportsV23ScreenState extends State<GeneratedReportsV23Screen> {
  final work=TextEditingController(),responsible=TextEditingController(),asset=TextEditingController();
  DateTime? start,end;
  List<Map<String,dynamic>>? items;
  bool busy=false;
  String? error;
  @override void initState(){super.initState();search();}
  @override void dispose(){work.dispose();responsible.dispose();asset.dispose();super.dispose();}
  Future<void> choose(bool first) async {final v=await showDatePicker(context:context,firstDate:DateTime(2024),lastDate:DateTime.now().add(const Duration(days:365)),initialDate:(first?start:end)??DateTime.now());if(v!=null)setState((){if(first)start=v;else end=v;});}
  Future<void> search() async {if(busy)return;setState((){busy=true;error=null;});try{final x=await api.generatedReportsSearchV23(workName:work.text.trim(),responsible:responsible.text.trim(),start:start,end:end,asset:asset.text.trim());if(mounted)setState(()=>items=x);}catch(e){if(mounted)setState(()=>error=_friendlyError(e));}finally{if(mounted)setState(()=>busy=false);}}
  Future<void> openReport(Map<String,dynamic> r) async {final path='${r['pdf_path']??''}'.trim();if(path.isEmpty){ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content:Text('PDF armazenado não encontrado para este relatório.')));return;}setState(()=>busy=true);try{final bytes=await api.downloadMedia(path);if(bytes==null)throw Exception('Não foi possível baixar o PDF armazenado.');await Printing.sharePdf(bytes:bytes,filename:'RC-Relatorio-Final-${r['work_name']??r['id']}.pdf');}catch(e){if(mounted)ScaffoldMessenger.of(context).showSnackBar(SnackBar(content:Text(_friendlyError(e))));}finally{if(mounted)setState(()=>busy=false);}}
  @override Widget build(BuildContext c)=>Scaffold(appBar:AppBar(title:const Text('Relatórios')),body:ListView(padding:const EdgeInsets.all(16),children:[
    const Card(child:ListTile(leading:Icon(Icons.folder_copy_outlined,color:_blue),title:Text('Relatórios gerados'),subtitle:Text('Os Relatórios Finais permanecem armazenados mesmo depois da conclusão da obra.'))),
    TextField(controller:work,decoration:const InputDecoration(labelText:'Nome da obra',prefixIcon:Icon(Icons.location_city_outlined))),const SizedBox(height:8),
    TextField(controller:responsible,decoration:const InputDecoration(labelText:'Responsável da obra',prefixIcon:Icon(Icons.person_search_outlined))),const SizedBox(height:8),
    TextField(controller:asset,decoration:const InputDecoration(labelText:'Ativo / placa / identificação',prefixIcon:Icon(Icons.precision_manufacturing_outlined))),const SizedBox(height:8),
    Row(children:[Expanded(child:OutlinedButton.icon(onPressed:busy?null:()=>choose(true),icon:const Icon(Icons.calendar_today_outlined),label:Text(start==null?'Data inicial':_fmtDate(start!.toIso8601String()).split(' ').first))),const SizedBox(width:8),Expanded(child:OutlinedButton.icon(onPressed:busy?null:()=>choose(false),icon:const Icon(Icons.event_outlined),label:Text(end==null?'Data final':_fmtDate(end!.toIso8601String()).split(' ').first)))]),
    const SizedBox(height:10),SizedBox(width:double.infinity,child:FilledButton.icon(onPressed:busy?null:search,icon:const Icon(Icons.search_rounded),label:const Text('Pesquisar relatórios'))),
    if(busy)const Padding(padding:EdgeInsets.only(top:8),child:LinearProgressIndicator()),
    if(error!=null)Card(child:ListTile(leading:const Icon(Icons.error_outline_rounded),title:const Text('Não foi possível carregar os relatórios'),subtitle:Text(error!),trailing:IconButton(onPressed:busy?null:search,icon:const Icon(Icons.refresh_rounded)))),
    if(items!=null&&items!.isEmpty&&!busy&&error==null)const Padding(padding:EdgeInsets.all(30),child:Center(child:Text('Nenhum relatório encontrado.'))),
    ...?items?.map((r)=>Card(child:ListTile(leading:const CircleAvatar(child:Icon(Icons.picture_as_pdf_outlined)),title:Text('${r['title']}',style:const TextStyle(fontWeight:FontWeight.w900)),subtitle:Text('Obra: ${r['work_name']??'-'}\nResponsável: ${r['responsible']??'-'}\nGerado em: ${_fmtDate(r['report_date'])}'),isThreeLine:true,trailing:const Icon(Icons.share_outlined),onTap:busy?null:()=>openReport(r)))),
  ]));
}

class MovementTraceV23Screen extends StatefulWidget {
  final int movementId;
  const MovementTraceV23Screen({super.key,required this.movementId});
  @override State<MovementTraceV23Screen> createState()=>_MovementTraceV23ScreenState();
}
class _MovementTraceV23ScreenState extends State<MovementTraceV23Screen> {
  Map<String,dynamic>? data;String? error;
  @override void initState(){super.initState();load();}
  Future<void> load() async {try{final x=await api.movementTraceV23(widget.movementId);if(mounted)setState(()=>data=x);}catch(e){if(mounted)setState(()=>error=_friendlyError(e));}}
  @override Widget build(BuildContext c){final d=data;return Scaffold(appBar:AppBar(title:const Text('Rastreabilidade do combustível')),body:d==null?Center(child:error==null?const CircularProgressIndicator():Padding(padding:const EdgeInsets.all(24),child:Column(mainAxisSize:MainAxisSize.min,children:[Text(error!,textAlign:TextAlign.center),const SizedBox(height:10),FilledButton.icon(onPressed:load,icon:const Icon(Icons.refresh),label:const Text('Tentar novamente'))])):ListView(padding:const EdgeInsets.all(16),children:[
    const Card(child:ListTile(leading:Icon(Icons.route_rounded,color:_blue),title:Text('Origem do combustível deste registro'),subtitle:Text('Quando há mistura de NFs, o app mostra exatamente quantos litros vieram de cada lote.'))),
    const Text('NF(s) utilizadas',style:TextStyle(fontSize:17,fontWeight:FontWeight.w900)),
    ..._rows(d['allocations']).map((a)=>Card(child:ListTile(title:Text('NF ${a['invoice_number']} • ${_fmtLiters(a['liters'])}',style:const TextStyle(fontWeight:FontWeight.w900)),subtitle:Text('${a['supplier_name']??'-'} • ${a['fuel_type']??'-'}${a['unit_cost']!=null?'\nCusto/L: ${_fmtMoney(a['unit_cost'])}':''}')))),
    const SizedBox(height:10),const Text('Caminho anterior dos lotes',style:TextStyle(fontSize:17,fontWeight:FontWeight.w900)),
    ..._rows(d['lineage']).map((m)=>Card(child:ListTile(title:Text('NF ${m['invoice_number']} • ${_movementLabel('${m['type']}')}',style:const TextStyle(fontWeight:FontWeight.w900)),subtitle:Text('${_fmtDate(m['created_at'])}\n${m['source']??'Entrada'}${m['destination']!=null?' → ${m['destination']}':''} • ${_fmtLiters(m['liters'])}')))),
  ]));}
}

class WorkFinalPdf {
  static Future<Uint8List> build(Map<String,dynamic> snapshot) async {
    final doc=pw.Document();final regular=pw.Font.helvetica(),bold=pw.Font.helveticaBold();
    final navy=PdfColor.fromHex('#062A69'),royal=PdfColor.fromHex('#0E58C7'),line=PdfColor.fromHex('#D9E2EE'),text=PdfColor.fromHex('#20242B');
    final w=_map(snapshot['work']),inst=_map(w['institutional_company']),sum=_map(snapshot['summary']);
    final company=_hasValue(inst['company_name'])?'${inst['company_name']}':'Empresa não cadastrada';
    final subtitle='${inst['company_subtitle']??''}',docNo='${inst['document']??'-'}',address='${inst['address']??'-'}';
    pw.Widget header(String title)=>pw.Column(crossAxisAlignment:pw.CrossAxisAlignment.start,children:[pw.Text(company,style:pw.TextStyle(font:bold,fontSize:30,color:navy)),if(subtitle.isNotEmpty)pw.Text(subtitle,style:pw.TextStyle(font:regular,fontSize:20,color:navy)),pw.SizedBox(height:8),pw.Container(height:1.5,color:royal),pw.SizedBox(height:8),pw.Text('CNPJ: $docNo',style:pw.TextStyle(font:regular,fontSize:10,color:text)),pw.Text('Endereço: $address',style:pw.TextStyle(font:regular,fontSize:10,color:text)),pw.SizedBox(height:14),pw.Text(title,style:pw.TextStyle(font:bold,fontSize:20,color:navy)),pw.SizedBox(height:8)]);
    pw.Widget row(String label,String value)=>pw.Container(padding:const pw.EdgeInsets.symmetric(vertical:7),decoration:pw.BoxDecoration(border:pw.Border(bottom:pw.BorderSide(color:line,width:.6))),child:pw.Row(crossAxisAlignment:pw.CrossAxisAlignment.start,children:[pw.SizedBox(width:180,child:pw.Text(label,style:pw.TextStyle(font:bold,fontSize:10,color:royal))),pw.Expanded(child:pw.Text(value,style:pw.TextStyle(font:regular,fontSize:10.5,color:text)))]));
    doc.addPage(pw.Page(pageFormat:PdfPageFormat.a4,margin:const pw.EdgeInsets.all(30),theme:pw.ThemeData.withFont(base:regular,bold:bold),build:(_)=>pw.Column(crossAxisAlignment:pw.CrossAxisAlignment.start,children:[
      header('Relatório Final da Obra'),
      pw.Container(padding:const pw.EdgeInsets.all(14),decoration:pw.BoxDecoration(border:pw.Border.all(color:line),borderRadius:const pw.BorderRadius.all(pw.Radius.circular(10))),child:pw.Column(children:[
        row('Obra','${w['name']??'-'}'),row('Empresa da obra','${w['company_name']??'-'}'),row('Responsável da obra','${w['responsible']??'-'}'),row('Local','${w['location']??'-'}'),row('Início','${_fmtDate(w['created_at'])}'),row('Finalização','${_fmtDate(w['finalized_at']??snapshot['generated_at'])}'),
      ])),pw.SizedBox(height:14),
      pw.Text('Resumo geral',style:pw.TextStyle(font:bold,fontSize:15,color:navy)),row('Registros vinculados','${sum['movement_count']??0}'),row('Abastecimentos','${sum['fueling_count']??0}'),row('Volume abastecido',_fmtLiters(sum['fueling_liters'])),row('Custo do combustível utilizado',_fmtMoney(sum['purchase_cost_total'])),row('Valor de venda',_fmtMoney(sum['sale_total'])),row('Lucro total',_fmtMoney(sum['profit_total'])),
      pw.Spacer(),pw.Container(height:1.5,color:royal),pw.SizedBox(height:6),pw.Text('Documento gerado automaticamente pelo R&C Abastecimento. Os registros, evidências e rastreabilidade permanecem armazenados no sistema.',style:pw.TextStyle(font:regular,fontSize:8.5,color:text)),
    ])));
    doc.addPage(pw.MultiPage(pageFormat:PdfPageFormat.a4,margin:const pw.EdgeInsets.all(30),theme:pw.ThemeData.withFont(base:regular,bold:bold),header:(_)=>header('Detalhamento do Relatório Final'),build:(_)=>[
      pw.Text('Consumo por combustível',style:pw.TextStyle(font:bold,fontSize:14,color:navy)),..._rows(snapshot['fuel_summary']).map((f)=>row('${f['fuel_type']}','${_fmtLiters(f['liters'])} • ${f['fueling_count']} abastecimento(s)')),
      pw.SizedBox(height:14),pw.Text('Ativos e equipamentos atendidos',style:pw.TextStyle(font:bold,fontSize:14,color:navy)),..._rows(snapshot['assets']).map((a)=>row('${a['kind']=='third_party'?'Equipamento de terceiros':'Ativo próprio'} • ${a['label']??'-'}','Proprietário: ${a['owner_company']??'-'} • ${_fmtLiters(a['liters'])} • ${a['fueling_count']} registro(s)')),
      pw.SizedBox(height:14),pw.Text('Notas Fiscais utilizadas',style:pw.TextStyle(font:bold,fontSize:14,color:navy)),..._rows(snapshot['nfs']).map((n)=>row('NF ${n['invoice_number']}','Fornecedor: ${n['supplier_name']??'-'} • Usado na obra: ${_fmtLiters(n['liters_used_by_work'])} • Custo: ${_fmtMoney(n['cost_used_by_work'])}${n['exhausted_at']!=null?' • Esgotada em ${_fmtDate(n['exhausted_at'])}':''}')),
      pw.SizedBox(height:14),pw.Text('Registros da obra',style:pw.TextStyle(font:bold,fontSize:14,color:navy)),..._rows(snapshot['movements']).map((m)=>pw.Container(margin:const pw.EdgeInsets.only(bottom:7),padding:const pw.EdgeInsets.all(9),decoration:pw.BoxDecoration(border:pw.Border.all(color:line),borderRadius:const pw.BorderRadius.all(pw.Radius.circular(6))),child:pw.Column(crossAxisAlignment:pw.CrossAxisAlignment.start,children:[pw.Text('${m['code']} • ${_movementLabel('${m['type']}')} • ${_fmtLiters(m['liters'])}',style:pw.TextStyle(font:bold,fontSize:10.5,color:navy)),pw.SizedBox(height:3),pw.Text('${_fmtDate(m['created_at'])} • ${m['asset_number']??m['third_party_plate']??m['third_party_description']??'-'} • ${m['operator']??'-'}',style:pw.TextStyle(font:regular,fontSize:9.5,color:text)),if(_hasValue(m['location_address']))pw.Text('${m['location_address']}',style:pw.TextStyle(font:regular,fontSize:9,color:text))])),
      pw.SizedBox(height:14),pw.Text('Rastreabilidade dos lotes usados',style:pw.TextStyle(font:bold,fontSize:14,color:navy)),..._rows(snapshot['lineage']).map((m)=>row('NF ${m['invoice_number']} • ${m['code']}','${_movementLabel('${m['type']}')} • ${m['source']??'Entrada'}${m['destination']!=null?' → ${m['destination']}':''} • ${_fmtLiters(m['liters'])} • ${_fmtDate(m['created_at'])}')),
      if(_rows(snapshot['audit']).isNotEmpty)...[pw.SizedBox(height:14),pw.Text('Auditoria e correções',style:pw.TextStyle(font:bold,fontSize:14,color:navy)),..._rows(snapshot['audit']).map((a)=>row('${a['action']} • ${a['user_name']??'-'}','${_fmtDate(a['created_at'])} • Registro ${a['record_id']??'-'}'))],
    ]));
    return doc.save();
  }
}

'''
s=s.replace(insert_marker,new_classes+insert_marker,1)

p.write_text(s)
print("business reports part 3a applied",len(s),"chars")
