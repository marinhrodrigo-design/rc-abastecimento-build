from pathlib import Path
p=Path('lib/main_online.dart')
s=p.read_text()

def replace_block(start_marker,end_marker,new,label):
    global s
    a=s.find(start_marker)
    if a<0: raise SystemExit(f'start missing: {label}')
    b=s.find(end_marker,a)
    if b<0: raise SystemExit(f'end missing: {label}')
    s=s[:a]+new+s[b:]

def insert_before(marker,text,label):
    global s
    i=s.find(marker)
    if i<0: raise SystemExit(f'marker missing: {label}')
    s=s[:i]+text+s[i:]

# ---------------- API v28 ----------------
api_marker="  Future<List<Map<String,dynamic>>> worksCatalogV23() async => _rows(await client.rpc('rca_works_catalog_v23'));\n"
api_add="""  Future<Map<String,dynamic>> dashboardKpisV28() async => _map(await client.rpc('rca_dashboard_kpis_v28'));
  Future<List<Map<String,dynamic>>> worksCatalogV28() async => _rows(await client.rpc('rca_works_catalog_v28'));
  Future<Map<String,dynamic>> workDetailV28(int workId) async => _map(await client.rpc('rca_work_detail_v28',params:{'p_work_id':workId}));
  Future<Map<String,dynamic>> restoreWorkV28(int workId) async => _map(await client.rpc('rca_restore_work_v28',params:{'p_work_id':workId}));
  Future<Map<String,dynamic>> purgeWorkV28(int workId) async => _map(await client.rpc('rca_purge_work_v28',params:{'p_work_id':workId}));
  Future<List<Map<String,dynamic>>> auditHistoryV28({String? query,int limit=200}) async => _rows(await client.rpc('rca_audit_history_v28',params:{'p_query':query,'p_limit':limit}));
  Future<Map<String,dynamic>> globalSearchV28(String query,{int limit=20}) async => _map(await client.rpc('rca_global_search_v28',params:{'p_query':query,'p_limit':limit}));
  Future<Map<String,dynamic>> generalRecordsV28({
    DateTime? start,DateTime? end,int? workId,String? asset,String? plate,String? operatorName,String? type,
    String? query,String? sourceCode,String? invoice,String? responsible,int? companyId,String? fuelType,int limit=500,
  }) async => _map(await client.rpc('rca_general_records_v28',params:{
    'p_start':start?.toUtc().toIso8601String(),'p_end':end?.toUtc().toIso8601String(),'p_work_id':workId,
    'p_asset_query':asset,'p_plate':plate,'p_operator':operatorName,'p_type':type,'p_query':query,
    'p_source_code':sourceCode,'p_invoice':invoice,'p_responsible':responsible,'p_company_id':companyId,
    'p_fuel_type':fuelType,'p_limit':limit,
  }));
"""
if 'dashboardKpisV28()' not in s:
    insert_before(api_marker,api_add,'v28 api methods')
if 'deleteWorkV25(int workId)' not in s:
    insert_before(api_marker,"  Future<Map<String,dynamic>> deleteWorkV25(int workId) async => _map(await client.rpc('rca_delete_work_v25',params:{'p_work_id':workId}));\n",'deleteWork api compat')

# ---------------- Dashboard ----------------
home_new=r'''class AdminHomeScreen extends StatefulWidget {
  final Map<String, dynamic> profile;
  final Future<void> Function() onLogout;
  const AdminHomeScreen({super.key, required this.profile, required this.onLogout});
  @override State<AdminHomeScreen> createState()=>_AdminHomeScreenState();
}
class _AdminHomeScreenState extends State<AdminHomeScreen> {
  Map<String,dynamic>? ref;
  Map<String,dynamic> kpis={};
  Timer? timer; bool running=false;
  final globalSearch=TextEditingController();
  @override void initState(){super.initState();refresh();timer=Timer.periodic(const Duration(seconds:20),(_)=>refresh());}
  @override void dispose(){timer?.cancel();globalSearch.dispose();super.dispose();}
  Future<void> refresh() async {
    if(running)return; running=true;
    try{
      final d=await api.referenceData(); Map<String,dynamic> k={};
      try{k=await api.dashboardKpisV28();}catch(_){}
      if(mounted)setState((){ref=d;kpis=k;});
    }catch(_){}finally{running=false;}
  }
  List<Map<String,dynamic>> _sources(Set<String> types)=>_sortedFuelUnits(ref?['tanks']).where((t)=>t['authorized']!=false&&types.contains('${t['tank_type']}')).toList();
  Future<Map<String,dynamic>?> _choose(String title,String subtitle,Set<String> types) async {
    final list=_sources(types);
    if(list.isEmpty){if(mounted)ScaffoldMessenger.of(context).showSnackBar(SnackBar(content:Text('Nenhuma unidade disponível para $title.')));return null;}
    if(list.length==1)return list.first;
    if(!mounted)return null;
    return showModalBottomSheet<Map<String,dynamic>>(context:context,showDragHandle:true,builder:(ctx)=>SafeArea(child:ListView(shrinkWrap:true,padding:const EdgeInsets.fromLTRB(16,0,16,20),children:[
      Text(title,style:Theme.of(ctx).textTheme.titleLarge?.copyWith(fontWeight:FontWeight.w900)),const SizedBox(height:4),Text(subtitle,style:const TextStyle(color:Colors.black54)),const SizedBox(height:10),
      ...list.map((t)=>Card(child:ListTile(leading:Icon('${t['tank_type']}'=='stationary'?Icons.oil_barrel_outlined:Icons.local_shipping_rounded,color:_blue),title:Text('${t['code']} • ${t['name']}',style:const TextStyle(fontWeight:FontWeight.w800)),subtitle:Text('Saldo: ${_fmtLiters(t['current_balance_liters'])}'),trailing:const Icon(Icons.chevron_right),onTap:()=>Navigator.pop(ctx,t))))
    ])));
  }
  Future<void> _fueling() async {if(ref==null)return;final t=await _choose('Novo abastecimento','Selecione somente a unidade de origem.',const {'stationary','comboio','truck'});if(!mounted||t==null||ref==null)return;await Navigator.push(context,MaterialPageRoute(builder:(_)=>FuelingV23Screen(source:t,ref:ref!,profile:widget.profile)));if(mounted)refresh();}
  Future<void> _transfer() async {if(ref==null)return;final t=await _choose('Transferir','Selecione a unidade doadora.',const {'comboio','truck'});if(!mounted||t==null||ref==null)return;await Navigator.push(context,MaterialPageRoute(builder:(_)=>TransferV23Screen(source:t,ref:ref!,profile:widget.profile)));if(mounted)refresh();}
  Future<void> _receipt() async {if(ref==null)return;final t=await _choose('Recebimento de combustível / NF','Selecione o caminhão-tanque que receberá a carga.',const {'truck'});if(!mounted||t==null)return;await Navigator.push(context,MaterialPageRoute(builder:(_)=>RefineryLoadV23Screen(truck:t)));if(mounted)refresh();}
  void open(Widget page)=>Navigator.push(context,MaterialPageRoute(builder:(_)=>page));
  Widget quick(IconData icon,String title,String subtitle,VoidCallback onTap)=>Card(margin:EdgeInsets.zero,child:InkWell(onTap:onTap,borderRadius:BorderRadius.circular(12),child:Padding(padding:const EdgeInsets.symmetric(horizontal:7,vertical:11),child:Column(mainAxisAlignment:MainAxisAlignment.center,children:[Icon(icon,color:_blue,size:29),const SizedBox(height:7),Text(title,textAlign:TextAlign.center,maxLines:2,overflow:TextOverflow.ellipsis,style:const TextStyle(fontWeight:FontWeight.w900,fontSize:12.2)),const SizedBox(height:3),Text(subtitle,textAlign:TextAlign.center,maxLines:2,overflow:TextOverflow.ellipsis,style:const TextStyle(fontSize:9.5,color:Colors.black54))]))));
  @override Widget build(BuildContext context){
    final tanks=_sortedFuelUnits(ref?['tanks']);final isAdmin=widget.profile['is_admin']==true;final isManager=widget.profile['is_manager']==true;
    final actions=<Widget>[
      quick(Icons.local_gas_station_rounded,'Novo abastecimento','Registrar abastecimento',_fueling),
      quick(Icons.swap_horiz_rounded,'Transferir','Registrar transferência',_transfer),
      quick(Icons.receipt_long_rounded,'Recebimento (NF)','Registrar entrada',_receipt),
      quick(Icons.today_rounded,'Registro Diário','Movimentações do dia',()=>open(const DailyRecordsV28Screen())),
      quick(Icons.manage_search_rounded,'Registro Geral','Histórico e pesquisa',()=>open(const GeneralRecordsV28Screen())),
      if(isAdmin||isManager)quick(Icons.folder_copy_outlined,'Relatórios','PDFs e obras',()=>open(const GeneratedReportsV23Screen())),
      quick(Icons.location_city_outlined,'Obras','Gestão completa',()=>open(WorksAdminScreen(profile:widget.profile))),
      if(isAdmin)quick(Icons.business_outlined,'Empresas','Clientes, locadoras e fornecedores',()=>open(const CompaniesAdminScreen())),
      quick(Icons.precision_manufacturing_outlined,'Ativos','Equipamentos próprios',()=>open(const MachinesAdminScreen())),
      quick(Icons.handyman_outlined,'Equip. terceiros','Proprietária / locadora',()=>open(const ThirdPartyAdminScreen())),
      if(isAdmin)quick(Icons.oil_barrel_outlined,'Tanques estacionários','Capacidade e saldo',()=>open(const TanksAdminScreen())),
      if(isAdmin)quick(Icons.local_shipping_rounded,'Caminhão-tanque','Função do ativo',()=>open(const TruckFunctionAdminScreen())),
      if(isAdmin)quick(Icons.manage_accounts_rounded,'Usuários','Operadores',()=>open(AdminUsersOnlineScreen(referenceData:ref!))),
      if(isAdmin)quick(Icons.admin_panel_settings_outlined,'Permissões','Supervisor e gerente',()=>open(const StaffPermissionsV23Screen())),
      if(isAdmin)quick(Icons.history_rounded,'Auditoria','Histórico de alterações',()=>open(const AuditHistoryV28Screen())),
      if(isAdmin)quick(Icons.badge_outlined,'Dados da empresa','Empresa operadora',()=>open(const ReportCompanyAdminScreen())),
    ];
    Widget kpi(IconData icon,String label,String value)=>Expanded(child:Container(padding:const EdgeInsets.all(10),decoration:BoxDecoration(color:Colors.white,borderRadius:BorderRadius.circular(12),border:Border.all(color:Colors.black12)),child:Column(children:[Icon(icon,color:_blue,size:22),const SizedBox(height:5),Text(value,maxLines:1,overflow:TextOverflow.ellipsis,style:const TextStyle(fontWeight:FontWeight.w900,fontSize:15)),Text(label,textAlign:TextAlign.center,style:const TextStyle(fontSize:9.5,color:Colors.black54))])));
    return Scaffold(appBar:AppBar(title:const Text('R&C ABASTECIMENTO',style:TextStyle(fontWeight:FontWeight.w900)),actions:[IconButton(onPressed:()=>open(GlobalSearchV28Screen(profile:widget.profile)),tooltip:'Pesquisa global',icon:const Icon(Icons.search_rounded)),IconButton(onPressed:()=>open(AdminCatalogScreen(profile:widget.profile)),tooltip:'Cadastros',icon:const Icon(Icons.menu_rounded)),IconButton(onPressed:()async{await _logoutToLogin(context,widget.onLogout);},tooltip:'Sair',icon:const Icon(Icons.logout_rounded))]),body:ref==null?const Center(child:CircularProgressIndicator()):RefreshIndicator(onRefresh:refresh,child:ListView(padding:const EdgeInsets.all(16),children:[
      GreetingLine(name:'${widget.profile['display_name']}'),const SizedBox(height:8),
      TextField(controller:globalSearch,textInputAction:TextInputAction.search,onSubmitted:(q){if(q.trim().isNotEmpty)open(GlobalSearchV28Screen(profile:widget.profile,initialQuery:q.trim()));},decoration:InputDecoration(labelText:'Pesquisar em todo o sistema',hintText:'Obra, empresa, ativo, placa, NF, CB01, Nº sequencial...',prefixIcon:const Icon(Icons.search_rounded),suffixIcon:IconButton(onPressed:(){final q=globalSearch.text.trim();if(q.isNotEmpty)open(GlobalSearchV28Screen(profile:widget.profile,initialQuery:q));},icon:const Icon(Icons.arrow_forward_rounded)))),
      const SizedBox(height:12),Row(children:[kpi(Icons.inventory_2_outlined,'Estoque atual',_fmtLiters(kpis['stock_liters'])),const SizedBox(width:7),kpi(Icons.water_drop_outlined,'Consumo hoje',_fmtLiters(kpis['fueling_liters_today']))]),const SizedBox(height:7),Row(children:[kpi(Icons.local_gas_station_outlined,'Abastecimentos hoje','${kpis['fueling_count_today']??0}'),const SizedBox(width:7),kpi(Icons.location_city_outlined,'Obras ativas','${kpis['active_works']??0}')]),
      const SizedBox(height:14),GridView.count(shrinkWrap:true,physics:const NeverScrollableScrollPhysics(),crossAxisCount:3,crossAxisSpacing:8,mainAxisSpacing:8,childAspectRatio:.92,children:actions),
      const SizedBox(height:18),Row(children:[const Icon(Icons.water_drop_outlined,color:_blue),const SizedBox(width:7),Text('Saldos em tempo real',style:Theme.of(context).textTheme.titleMedium?.copyWith(fontWeight:FontWeight.w900))]),const SizedBox(height:8),...tanks.map((t)=>Padding(padding:const EdgeInsets.only(bottom:8),child:BalanceCard(tank:t))),const SizedBox(height:12),HomeActionCard(icon:Icons.dashboard_outlined,title:'Painel de combustível',subtitle:'Estoque, NFs, consumo, autonomia, custos e lucros em tempo real',onTap:()=>open(FuelDashboardV23Screen(profile:widget.profile,ref:ref!)))
    ])));
  }
}

'''
replace_block('class AdminHomeScreen extends StatefulWidget {','class AdminRecordsScreen extends StatefulWidget {',home_new,'dashboard v28')

# ---------------- Records: Daily / General / audit / global search ----------------
records_new=r'''class AdminRecordsScreen extends StatelessWidget {
  final Map<String,dynamic> referenceData;
  const AdminRecordsScreen({super.key,required this.referenceData});
  @override Widget build(BuildContext context)=>const GeneralRecordsV28Screen();
}

class OfficialPdfPreviewV28Screen extends StatelessWidget {
  final List<Map<String,dynamic>> items; final String title;
  const OfficialPdfPreviewV28Screen({super.key,required this.items,this.title='Prévia do PDF'});
  @override Widget build(BuildContext context)=>Scaffold(appBar:AppBar(title:Text(title)),body:PdfPreview(build:(_)=>FuelPdfReport.build(items),canChangePageFormat:false,canChangeOrientation:false,canDebug:false,pdfFileName:'RC-Abastecimento-${DateTime.now().millisecondsSinceEpoch}.pdf'));
}

String _recordSequenceV28(Map<String,dynamic> x){final raw='${x['code']??''}';final m=RegExp(r'(\d+)$').firstMatch(raw);final n=int.tryParse(m?.group(1)??'');return n==null?'----':n.toString().padLeft(4,'0');}
String _recordOriginV28(Map<String,dynamic> x){final s='${x['source_tank']??''}'.trim();if(s.isNotEmpty&&s!='null')return s;final d='${x['destination_tank']??''}'.trim();if(d.isNotEmpty&&d!='null')return d;final code='${x['code']??''}';final m=RegExp(r'^(.+?)-\d+$').firstMatch(code);return m?.group(1)??'-';}

class _RecordCardV28 extends StatelessWidget {
  final Map<String,dynamic> item; final VoidCallback onOpen; final VoidCallback onPdf; final VoidCallback? onSelect; final bool selected; final bool selectionMode;
  const _RecordCardV28({required this.item,required this.onOpen,required this.onPdf,this.onSelect,this.selected=false,this.selectionMode=false});
  @override Widget build(BuildContext context){final asset=item['asset_number']??item['third_party_plate']??item['destination_tank']??item['source_tank']??'-';final fueling='${item['type']}'=='fueling';final id=_intOrNull(item['id']);return Card(child:InkWell(onTap:selectionMode?(onSelect??onOpen):onOpen,borderRadius:BorderRadius.circular(12),child:Padding(padding:const EdgeInsets.all(13),child:Column(crossAxisAlignment:CrossAxisAlignment.start,children:[
    Row(children:[Expanded(child:Text('${_movementLabelForItem(item)} • $asset',style:const TextStyle(fontWeight:FontWeight.w900,fontSize:15))),if(selectionMode)Checkbox(value:selected,onChanged:(_)=>onSelect?.call())else IconButton(onPressed:onPdf,tooltip:'Prévia / Exportar PDF',icon:const Icon(Icons.picture_as_pdf_outlined,color:_blue))]),
    Wrap(spacing:7,runSpacing:6,children:[ActionChip(avatar:const Icon(Icons.confirmation_number_outlined,size:16),label:Text('${_recordOriginV28(item)} • Nº: ${_recordSequenceV28(item)}',style:const TextStyle(fontWeight:FontWeight.w800)),onPressed:fueling&&id!=null?()=>Navigator.push(context,MaterialPageRoute(builder:(_)=>MovementTraceV23Screen(movementId:id))):onOpen),if(_hasValue(item['work']))Chip(label:Text('${item['work']}')),if(_hasValue(item['fuel_type']))Chip(label:Text('${item['fuel_type']}'))]),
    const SizedBox(height:8),Text('${_fmtDate(item['created_at'])} • ${_fmtLiters(item['liters'])}',style:const TextStyle(fontWeight:FontWeight.w700)),const SizedBox(height:3),Text('Responsável/operador: ${item['operator']??item['work_responsible']??'-'}',style:const TextStyle(color:Colors.black54)),
  ]))));}
}

class _RecordsSummaryV28 extends StatelessWidget {
  final Map<String,dynamic> summary; final DateTime? start; final DateTime? end;
  const _RecordsSummaryV28({required this.summary,this.start,this.end});
  @override Widget build(BuildContext context){final oneDay=start!=null&&end!=null&&end!.difference(start!).inDays==1;final date=oneDay?_fmtDate(start!.toIso8601String()).split(' ').first:'';Widget m(String l,String v,{bool hi=false})=>Container(padding:const EdgeInsets.all(11),decoration:BoxDecoration(color:hi?const Color(0xFFEAF2FF):Colors.white,borderRadius:BorderRadius.circular(12),border:Border.all(color:hi?_blue:Colors.black12)),child:Column(crossAxisAlignment:CrossAxisAlignment.start,children:[Text(l,style:TextStyle(fontSize:11,color:hi?_blue:Colors.black54,fontWeight:FontWeight.w700)),const SizedBox(height:3),Text(v,style:TextStyle(fontSize:hi?20:15,fontWeight:FontWeight.w900,color:hi?_blue:Colors.black87))]));return Card(child:Padding(padding:const EdgeInsets.all(15),child:Column(crossAxisAlignment:CrossAxisAlignment.stretch,children:[Text(oneDay?'Resumo do dia • $date':'Resumo dos resultados',style:const TextStyle(fontSize:17,fontWeight:FontWeight.w900)),const SizedBox(height:10),m(oneDay?'Total abastecido no dia':'Total abastecido',_fmtLiters(summary['fueling_liters']),hi:true),const SizedBox(height:8),Row(children:[Expanded(child:m('Abastecimentos','${summary['fueling_count']??0}')),const SizedBox(width:7),Expanded(child:m('Total de registros','${summary['record_count']??0}'))]),const SizedBox(height:7),Row(children:[Expanded(child:m('Transferido',_fmtLiters(summary['transfer_liters']))),const SizedBox(width:7),Expanded(child:m('Recebido por NF',_fmtLiters(summary['refinery_liters'])))]),if(summary['sale_total']!=null)...[const SizedBox(height:7),Row(children:[Expanded(child:m('Valor abastecido',_fmtMoney(summary['sale_total']))),const SizedBox(width:7),Expanded(child:m('Lucro',_fmtMoney(summary['profit_total'])))] )],if(_rows(summary['fuel_breakdown']).isNotEmpty)...[const SizedBox(height:12),const Text('Por combustível',style:TextStyle(fontWeight:FontWeight.w900)),const SizedBox(height:5),..._rows(summary['fuel_breakdown']).map((x)=>Padding(padding:const EdgeInsets.only(bottom:3),child:Row(children:[Expanded(child:Text('${x['fuel_type']}')),Text(_fmtLiters(x['liters']),style:const TextStyle(fontWeight:FontWeight.w800))])) )],const SizedBox(height:9),const Text('Transferências e recebimentos de NF ficam separados do Total abastecido para não contar o mesmo combustível mais de uma vez.',style:TextStyle(fontSize:11,color:Colors.black54))])));}
}

class DailyRecordsV28Screen extends StatefulWidget {const DailyRecordsV28Screen({super.key});@override State<DailyRecordsV28Screen> createState()=>_DailyRecordsV28ScreenState();}
class _DailyRecordsV28ScreenState extends State<DailyRecordsV28Screen>{DateTime day=DateTime.now();List<Map<String,dynamic>> items=[];Map<String,dynamic> summary={};bool busy=false;String? error;
  @override void initState(){super.initState();load();}
  DateTime get start=>DateTime(day.year,day.month,day.day);DateTime get end=>start.add(const Duration(days:1));
  Future<void> load() async {setState(()=>busy=true);try{final r=await api.generalRecordsV28(start:start,end:end,limit:1000);if(mounted)setState((){items=_rows(r['items']);summary=_map(r['summary']);error=null;});}catch(e){if(mounted)setState(()=>error=_friendlyError(e));}finally{if(mounted)setState(()=>busy=false);}}
  Future<void> choose() async {final d=await showDatePicker(context:context,firstDate:DateTime(2024),lastDate:DateTime.now().add(const Duration(days:730)),initialDate:day);if(d!=null){setState(()=>day=d);load();}}
  void preview(Map<String,dynamic> x)=>Navigator.push(context,MaterialPageRoute(builder:(_)=>OfficialPdfPreviewV28Screen(items:[x],title:'Prévia • ${x['code']??'Registro'}')));
  @override Widget build(BuildContext context)=>Scaffold(appBar:AppBar(title:const Text('Registro Diário')),body:RefreshIndicator(onRefresh:load,child:ListView(padding:const EdgeInsets.all(12),children:[Card(child:Padding(padding:const EdgeInsets.all(12),child:Column(children:[Row(children:[Expanded(child:FilledButton.tonal(onPressed:(){setState(()=>day=DateTime.now());load();},child:const Text('Hoje'))),const SizedBox(width:7),Expanded(child:OutlinedButton(onPressed:(){setState(()=>day=DateTime.now().subtract(const Duration(days:1)));load();},child:const Text('Ontem'))),const SizedBox(width:7),Expanded(child:OutlinedButton.icon(onPressed:choose,icon:const Icon(Icons.calendar_month_outlined),label:const Text('Data')))]),const SizedBox(height:8),Text('Dia selecionado: ${_fmtDate(start.toIso8601String()).split(' ').first}',style:const TextStyle(fontWeight:FontWeight.w800))]))),if(busy)const LinearProgressIndicator(minHeight:2),if(error!=null)Card(child:ListTile(leading:const Icon(Icons.error_outline),title:Text(error!),trailing:IconButton(onPressed:load,icon:const Icon(Icons.refresh)))),if(summary.isNotEmpty)_RecordsSummaryV28(summary:summary,start:start,end:end),const SizedBox(height:8),Text('${items.length} registro(s) carregado(s)',style:const TextStyle(fontWeight:FontWeight.w800)),const SizedBox(height:5),if(items.isEmpty&&!busy&&error==null)const Card(child:ListTile(title:Text('Nenhum registro neste dia.'))),...items.map((x)=>_RecordCardV28(item:x,onOpen:()=>Navigator.push(context,MaterialPageRoute(builder:(_)=>MovementDetailScreen(item:x))),onPdf:()=>preview(x))) ])));
}

class GeneralRecordsV28Screen extends StatefulWidget {
  final int? initialWorkId; final String? initialQuery; final String? initialInvoice;
  const GeneralRecordsV28Screen({super.key,this.initialWorkId,this.initialQuery,this.initialInvoice});
  @override State<GeneralRecordsV28Screen> createState()=>_GeneralRecordsV28ScreenState();
}
class _GeneralRecordsV28ScreenState extends State<GeneralRecordsV28Screen>{
  DateTime? start=DateTime.now().subtract(const Duration(days:30)); DateTime? end=DateTime.now().add(const Duration(days:1)); int? workId; String? type; String? fuelType;
  final query=TextEditingController(),asset=TextEditingController(),plate=TextEditingController(),operatorName=TextEditingController(),responsible=TextEditingController(),source=TextEditingController(),invoice=TextEditingController();
  List<Map<String,dynamic>> works=[];List<Map<String,dynamic>> items=[];Map<String,dynamic> summary={};bool busy=false;bool filters=true;String? error;final Set<String> selected=<String>{};
  @override void initState(){super.initState();workId=widget.initialWorkId;query.text=widget.initialQuery??'';invoice.text=widget.initialInvoice??'';bootstrap();}
  @override void dispose(){for(final c in [query,asset,plate,operatorName,responsible,source,invoice]){c.dispose();}super.dispose();}
  Future<void> bootstrap() async {try{works=await api.worksCatalogV28();}catch(_){}if(mounted)setState((){});await search(collapse:false);}
  String key(Map<String,dynamic>x)=>'${x['code']??x['id']}';
  Future<void> pick(bool first) async {final base=first?(start??DateTime.now().subtract(const Duration(days:30))):((end??DateTime.now().add(const Duration(days:1))).subtract(const Duration(days:1)));final d=await showDatePicker(context:context,firstDate:DateTime(2024),lastDate:DateTime.now().add(const Duration(days:730)),initialDate:base);if(d==null)return;setState((){if(first)start=DateTime(d.year,d.month,d.day);else end=DateTime(d.year,d.month,d.day).add(const Duration(days:1));});}
  Future<void> chooseWork() async {final result=await showModalBottomSheet<int>(context:context,isScrollControlled:true,showDragHandle:true,builder:(ctx)=>_WorkPickerV28(works:works,current:workId));if(!mounted||result==null)return;setState(()=>workId=result==0?null:result);}
  Future<void> search({bool collapse=true}) async {if(busy)return;setState((){busy=true;error=null;});try{final r=await api.generalRecordsV28(start:start,end:end,workId:workId,asset:asset.text.trim(),plate:plate.text.trim(),operatorName:operatorName.text.trim(),type:type,query:query.text.trim(),sourceCode:source.text.trim(),invoice:invoice.text.trim(),responsible:responsible.text.trim(),fuelType:fuelType,limit:1000).timeout(const Duration(seconds:20));if(mounted)setState((){items=_rows(r['items']);summary=_map(r['summary']);selected.clear();if(collapse)filters=false;});}catch(e){if(mounted)setState(()=>error=_friendlyError(e));}finally{if(mounted)setState(()=>busy=false);}}
  void clearFilters(){setState((){start=null;end=null;workId=null;type=null;fuelType=null;for(final c in [query,asset,plate,operatorName,responsible,source,invoice]){c.clear();}filters=true;});}
  void preview(List<Map<String,dynamic>> x){if(x.isEmpty)return;Navigator.push(context,MaterialPageRoute(builder:(_)=>OfficialPdfPreviewV28Screen(items:x,title:x.length==1?'Prévia • ${x.first['code']??'Registro'}':'Prévia • ${x.length} registros')));}
  String workLabel(){if(workId==null)return'Todas as obras';for(final w in works){if(_intOrNull(w['id'])==workId)return'${w['name']}';}return'Obra selecionada';}
  @override Widget build(BuildContext context)=>Scaffold(appBar:AppBar(title:Text(selected.isEmpty?'Registro Geral':'${selected.length} selecionado(s)'),actions:[if(selected.isNotEmpty)IconButton(onPressed:()=>preview(items.where((x)=>selected.contains(key(x))).toList()),tooltip:'Prévia / Exportar selecionados',icon:const Icon(Icons.picture_as_pdf_outlined)),if(selected.isNotEmpty)IconButton(onPressed:()=>setState(()=>selected.clear()),icon:const Icon(Icons.close))]),body:ListView(padding:const EdgeInsets.fromLTRB(12,12,12,30),children:[
    Card(child:Column(children:[ListTile(title:const Text('Pesquisa e filtros',style:TextStyle(fontWeight:FontWeight.w900)),subtitle:Text(workLabel()),trailing:Icon(filters?Icons.expand_less:Icons.expand_more),onTap:()=>setState(()=>filters=!filters)),if(filters)Padding(padding:const EdgeInsets.fromLTRB(12,0,12,12),child:Column(children:[
      TextField(controller:query,decoration:const InputDecoration(labelText:'Pesquisa geral',hintText:'Sequencial, obra, ativo, placa, NF, empresa...',prefixIcon:Icon(Icons.search_rounded))),const SizedBox(height:8),
      Row(children:[Expanded(child:OutlinedButton.icon(onPressed:()=>pick(true),icon:const Icon(Icons.calendar_today),label:Text(start==null?'Data inicial':'De ${_fmtDate(start!.toIso8601String()).split(' ').first}'))),const SizedBox(width:7),Expanded(child:OutlinedButton.icon(onPressed:()=>pick(false),icon:const Icon(Icons.event),label:Text(end==null?'Data final':'Até ${_fmtDate(end!.subtract(const Duration(days:1)).toIso8601String()).split(' ').first}')))]),const SizedBox(height:8),
      SizedBox(width:double.infinity,child:OutlinedButton.icon(onPressed:chooseWork,icon:const Icon(Icons.location_city_outlined),label:Text('Obra: ${workLabel()}'))),const SizedBox(height:8),
      TextField(controller:asset,decoration:const InputDecoration(labelText:'Ativo / equipamento',prefixIcon:Icon(Icons.precision_manufacturing_outlined))),const SizedBox(height:8),
      Row(children:[Expanded(child:TextField(controller:plate,decoration:const InputDecoration(labelText:'Placa'))),const SizedBox(width:7),Expanded(child:TextField(controller:source,decoration:const InputDecoration(labelText:'Origem / unidade',hintText:'CB01, TE01...')))]),const SizedBox(height:8),
      TextField(controller:invoice,decoration:const InputDecoration(labelText:'Nota Fiscal / lote',prefixIcon:Icon(Icons.receipt_long_outlined))),const SizedBox(height:8),
      Row(children:[Expanded(child:TextField(controller:operatorName,decoration:const InputDecoration(labelText:'Operador / recebedor'))),const SizedBox(width:7),Expanded(child:TextField(controller:responsible,decoration:const InputDecoration(labelText:'Responsável')))]),const SizedBox(height:8),
      Row(children:[Expanded(child:DropdownButtonFormField<String?>(value:type,decoration:const InputDecoration(labelText:'Tipo'),items:const [DropdownMenuItem<String?>(value:null,child:Text('Todos')),DropdownMenuItem(value:'fueling',child:Text('Abastecimento')),DropdownMenuItem(value:'tank_transfer',child:Text('Transferência')),DropdownMenuItem(value:'refinery_entry',child:Text('Recebimento/NF'))],onChanged:(v)=>setState(()=>type=v))),const SizedBox(width:7),Expanded(child:DropdownButtonFormField<String?>(value:fuelType,decoration:const InputDecoration(labelText:'Combustível'),items:[const DropdownMenuItem<String?>(value:null,child:Text('Todos')),..._fuelTypes.map((f)=>DropdownMenuItem<String?>(value:f,child:Text(f)))],onChanged:(v)=>setState(()=>fuelType=v)))]),const SizedBox(height:10),
      Row(children:[Expanded(child:OutlinedButton.icon(onPressed:busy?null:clearFilters,icon:const Icon(Icons.filter_alt_off_outlined),label:const Text('Limpar'))),const SizedBox(width:8),Expanded(flex:2,child:FilledButton.icon(onPressed:busy?null:()=>search(),icon:const Icon(Icons.search),label:const Text('Pesquisar')))])
    ]))])),if(busy)const LinearProgressIndicator(minHeight:2),if(error!=null)Card(child:ListTile(leading:const Icon(Icons.error_outline),title:Text(error!),trailing:IconButton(onPressed:()=>search(collapse:false),icon:const Icon(Icons.refresh)))),if(summary.isNotEmpty)_RecordsSummaryV28(summary:summary,start:start,end:end),const SizedBox(height:8),Row(children:[Expanded(child:Text('${summary['record_count']??items.length} resultado(s) no filtro • ${items.length} carregado(s)',style:const TextStyle(fontWeight:FontWeight.w800))),if(items.isNotEmpty)TextButton.icon(onPressed:()=>setState(()=>selected.addAll(items.map(key))),icon:const Icon(Icons.select_all),label:const Text('Selecionar carregados'))]),if(items.isEmpty&&!busy&&error==null)const Card(child:ListTile(title:Text('Nenhum registro encontrado.'))),
    ...items.map((x)=>GestureDetector(onLongPress:()=>setState(()=>selected.add(key(x))),child:_RecordCardV28(item:x,selectionMode:selected.isNotEmpty,selected:selected.contains(key(x)),onSelect:()=>setState((){final k=key(x);if(!selected.add(k))selected.remove(k);}),onOpen:()=>Navigator.push(context,MaterialPageRoute(builder:(_)=>MovementDetailScreen(item:x))),onPdf:()=>preview([x]))))
  ]));
}

class _WorkPickerV28 extends StatefulWidget {
  final List<Map<String,dynamic>> works;
  final int? current;
  const _WorkPickerV28({required this.works,this.current});
  @override State<_WorkPickerV28> createState()=>_WorkPickerV28State();
}
class _WorkPickerV28State extends State<_WorkPickerV28>{
  final q=TextEditingController();
  @override void dispose(){q.dispose();super.dispose();}
  @override Widget build(BuildContext context){
    final f=q.text.trim().toLowerCase();
    final list=widget.works.where((w)=>f.isEmpty||'${w['name']} ${w['company_name']} ${w['responsible']}'.toLowerCase().contains(f)).toList();
    return SafeArea(child:Padding(
      padding:EdgeInsets.only(left:16,right:16,bottom:MediaQuery.of(context).viewInsets.bottom+16),
      child:Column(mainAxisSize:MainAxisSize.min,children:[
        const Align(alignment:Alignment.centerLeft,child:Text('Pesquisar por obra',style:TextStyle(fontSize:19,fontWeight:FontWeight.w900))),
        const SizedBox(height:8),
        TextField(controller:q,onChanged:(_)=>setState((){}),autofocus:true,decoration:const InputDecoration(labelText:'Nome da obra, cliente ou responsável',prefixIcon:Icon(Icons.search))),
        const SizedBox(height:8),
        Flexible(child:ListView(shrinkWrap:true,children:[
          ListTile(leading:const Icon(Icons.all_inclusive),title:const Text('Todas as obras'),selected:widget.current==null,onTap:()=>Navigator.pop(context,0)),
          ...list.map((w)=>ListTile(
            leading:Icon('${w['status']}'=='finalized'?Icons.task_alt:'${w['status']}'=='deleted'?Icons.delete_outline:Icons.location_city_outlined),
            title:Text('${w['name']}',style:const TextStyle(fontWeight:FontWeight.w800)),
            subtitle:Text('${w['company_name']??'-'} • ${w['responsible']??'-'}'),
            selected:_intOrNull(w['id'])==widget.current,
            onTap:()=>Navigator.pop(context,_intOrNull(w['id'])),
          )),
        ])),
      ]),
    ));
  }
}

class AuditHistoryV28Screen extends StatefulWidget {
  const AuditHistoryV28Screen({super.key});
  @override State<AuditHistoryV28Screen> createState()=>_AuditHistoryV28ScreenState();
}
class _AuditHistoryV28ScreenState extends State<AuditHistoryV28Screen>{
  final q=TextEditingController();
  List<Map<String,dynamic>> items=[];
  bool busy=false;
  @override void initState(){super.initState();load();}
  @override void dispose(){q.dispose();super.dispose();}
  Future<void> load()async{
    setState(()=>busy=true);
    try{
      final x=await api.auditHistoryV28(query:q.text.trim(),limit:500);
      if(mounted)setState(()=>items=x);
    }catch(e){
      if(mounted)ScaffoldMessenger.of(context).showSnackBar(SnackBar(content:Text(_friendlyError(e))));
    }finally{if(mounted)setState(()=>busy=false);}
  }
  String action(String v){
    const m={'delete':'Excluiu','restore':'Restaurou','purge':'Excluiu definitivamente','finalize':'Finalizou','insert':'Cadastrou','update':'Alterou','correct':'Corrigiu'};
    return m[v]??v;
  }
  @override Widget build(BuildContext context)=>Scaffold(
    appBar:AppBar(title:const Text('Histórico de alterações')),
    body:Column(children:[
      Padding(padding:const EdgeInsets.all(12),child:TextField(
        controller:q,onSubmitted:(_)=>load(),
        decoration:InputDecoration(labelText:'Pesquisar usuário, ação ou registro',prefixIcon:const Icon(Icons.search),suffixIcon:IconButton(onPressed:load,icon:const Icon(Icons.search))),
      )),
      if(busy)const LinearProgressIndicator(minHeight:2),
      Expanded(child:RefreshIndicator(
        onRefresh:load,
        child:ListView(padding:const EdgeInsets.fromLTRB(12,4,12,30),children:[
          if(items.isEmpty&&!busy)const Card(child:ListTile(title:Text('Nenhuma alteração encontrada.'))),
          ...items.map((x)=>Card(child:ListTile(
            leading:const CircleAvatar(child:Icon(Icons.history)),
            title:Text('${action('${x['action']}')} • ${x['table_name']}',style:const TextStyle(fontWeight:FontWeight.w900)),
            subtitle:Text('${_fmtDate(x['created_at'])}\nPor: ${x['user_name']??'-'} • Registro: ${x['record_id']??'-'}'),
            isThreeLine:true,
            onTap:()=>showDialog(
              context:context,
              builder:(ctx)=>AlertDialog(
                title:const Text('Detalhes da alteração'),
                content:SingleChildScrollView(child:SelectableText(
                  'Antes:\n${const JsonEncoder.withIndent('  ').convert(x['old_data'])}\n\nDepois:\n${const JsonEncoder.withIndent('  ').convert(x['new_data'])}',
                )),
                actions:[TextButton(onPressed:()=>Navigator.pop(ctx),child:const Text('Fechar'))],
              ),
            ),
          ))),
        ]),
      )),
    ]),
  );
}

class GlobalSearchV28Screen extends StatefulWidget {final Map<String,dynamic> profile;final String? initialQuery;const GlobalSearchV28Screen({super.key,required this.profile,this.initialQuery});@override State<GlobalSearchV28Screen> createState()=>_GlobalSearchV28ScreenState();}
class _GlobalSearchV28ScreenState extends State<GlobalSearchV28Screen>{final q=TextEditingController();Map<String,dynamic> data={};bool busy=false;@override void initState(){super.initState();q.text=widget.initialQuery??'';if(q.text.trim().isNotEmpty)search();}@override void dispose(){q.dispose();super.dispose();}Future<void> search()async{if(q.text.trim().isEmpty)return;setState(()=>busy=true);try{final r=await api.globalSearchV28(q.text.trim(),limit:30);if(mounted)setState(()=>data=r);}catch(e){if(mounted)ScaffoldMessenger.of(context).showSnackBar(SnackBar(content:Text(_friendlyError(e))));}finally{if(mounted)setState(()=>busy=false);}}Widget section(String title,List<Map<String,dynamic>> list,Widget Function(Map<String,dynamic>) tile){if(list.isEmpty)return const SizedBox.shrink();return Column(crossAxisAlignment:CrossAxisAlignment.start,children:[Padding(padding:const EdgeInsets.fromLTRB(4,14,4,5),child:Text('$title (${list.length})',style:const TextStyle(fontWeight:FontWeight.w900,fontSize:16))),...list.map(tile)]);}void open(Widget w)=>Navigator.push(context,MaterialPageRoute(builder:(_)=>w));@override Widget build(BuildContext context)=>Scaffold(appBar:AppBar(title:const Text('Pesquisa global')),body:ListView(padding:const EdgeInsets.all(12),children:[TextField(controller:q,autofocus:widget.initialQuery==null,textInputAction:TextInputAction.search,onSubmitted:(_)=>search(),decoration:InputDecoration(labelText:'Pesquisar em todo o R&C',hintText:'Obra, empresa, ativo, placa, NF, CB01, Nº...',prefixIcon:const Icon(Icons.search),suffixIcon:IconButton(onPressed:search,icon:const Icon(Icons.arrow_forward)))),if(busy)const Padding(padding:EdgeInsets.only(top:8),child:LinearProgressIndicator(minHeight:2)),section('Registros',_rows(data['movements']),(x)=>Card(child:ListTile(leading:const Icon(Icons.receipt_long_outlined,color:_blue),title:Text('${x['code']} • ${_movementLabelForItem(x)}',style:const TextStyle(fontWeight:FontWeight.w900)),subtitle:Text('${x['work']??'Sem obra'} • ${x['asset']??'-'} • ${_fmtLiters(x['liters'])}'),onTap:()=>open(GeneralRecordsV28Screen(initialQuery:'${x['code']}'))))),section('Obras',_rows(data['works']),(x)=>Card(child:ListTile(leading:const Icon(Icons.location_city_outlined,color:_blue),title:Text('${x['name']}',style:const TextStyle(fontWeight:FontWeight.w900)),subtitle:Text('${x['company_name']??'-'} • ${x['responsible']??'-'}'),onTap:()=>open(WorkDetailsV28Screen(profile:widget.profile,workId:_intOrNull(x['id'])!))))),section('Empresas',_rows(data['companies']),(x)=>Card(child:ListTile(leading:const Icon(Icons.business_outlined,color:_blue),title:Text('${x['name']}'),subtitle:Text('${x['document']??''}'),onTap:widget.profile['is_admin']==true?()=>open(const CompaniesAdminScreen()):null))),section('Ativos',_rows(data['assets']),(x)=>Card(child:ListTile(leading:const Icon(Icons.precision_manufacturing_outlined,color:_blue),title:Text('${x['asset_number']} • ${x['marca']??''} ${x['modelo']??''}'),subtitle:Text('Placa: ${x['placa']??'-'}'),onTap:()=>open(const MachinesAdminScreen())))),section('Equipamentos de terceiros',_rows(data['third_party']),(x)=>Card(child:ListTile(leading:const Icon(Icons.handyman_outlined,color:_blue),title:Text('${x['plate']??'Sem placa'} • ${x['description']??''}'),subtitle:Text('${x['company_name']??'-'}'),onTap:()=>open(const ThirdPartyAdminScreen())))),section('Notas Fiscais',_rows(data['invoices']),(x)=>Card(child:ListTile(leading:const Icon(Icons.receipt_outlined,color:_blue),title:Text('NF ${x['invoice_number']}',style:const TextStyle(fontWeight:FontWeight.w900)),subtitle:Text('${x['supplier_name']??'-'} • ${_fmtLiters(x['total_liters'])}'),onTap:()=>open(GeneralRecordsV28Screen(initialInvoice:'${x['invoice_number']}'))))),if(!busy&&data.isNotEmpty&&['movements','works','companies','assets','third_party','invoices'].every((k)=>_rows(data[k]).isEmpty))const Padding(padding:EdgeInsets.all(30),child:Center(child:Text('Nenhum resultado encontrado.')))]));}

'''
replace_block('class AdminRecordsScreen extends StatefulWidget {','class MovementDetailScreen extends StatelessWidget {',records_new,'records v28')

# Movement detail: all record PDFs go through preview first.
old_export="""  Future<void> exportOne(BuildContext context) async {
    try {
      final bytes = await FuelPdfReport.build([item]);
      await Printing.sharePdf(bytes: bytes, filename: 'RC-Abastecimento-${item['code'] ?? DateTime.now().millisecondsSinceEpoch}.pdf');
    } catch (e) {
      if (context.mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Falha ao gerar PDF: ${_friendlyError(e)}')));
    }
  }
"""
new_export="""  Future<void> exportOne(BuildContext context) async {
    await Navigator.push(context, MaterialPageRoute(builder: (_) => OfficialPdfPreviewV28Screen(items: [item], title: 'Prévia • ${item['code'] ?? 'Registro'}')));
  }
"""
if old_export in s:s=s.replace(old_export,new_export,1)

# Meus registros: seleção abre prévia, não compartilha direto.
old_my="try {final bytes=await FuelPdfReport.build(targets);await Printing.sharePdf(bytes:bytes,filename:'RC-Abastecimento-${DateTime.now().millisecondsSinceEpoch}.pdf');if(mounted)clearSelection();}"
new_my="try {if(mounted)await Navigator.push(context,MaterialPageRoute(builder:(_)=>OfficialPdfPreviewV28Screen(items:targets,title:'Prévia • ${targets.length} registro(s)')));if(mounted)clearSelection();}"
if old_my in s:s=s.replace(old_my,new_my,1)

# ---------------- Works management ----------------
works_new=r'''class WorksAdminScreen extends StatefulWidget {final Map<String,dynamic> profile;const WorksAdminScreen({super.key,required this.profile});@override State<WorksAdminScreen> createState()=>_WorksAdminScreenState();}
class _WorksAdminScreenState extends State<WorksAdminScreen>{List<Map<String,dynamic>>? items;List<Map<String,dynamic>> companies=[];bool busy=false;bool get canEdit=>widget.profile['is_admin']==true;bool get canFinalize=>widget.profile['is_admin']==true||widget.profile['is_manager']==true;
  @override void initState(){super.initState();load();}
  Future<void> load()async{try{final w=await api.worksCatalogV28().timeout(const Duration(seconds:15));var c=<Map<String,dynamic>>[];if(canEdit){try{c=await api.managedCompanies();}catch(_){}}if(mounted)setState((){items=w;companies=c;});}catch(e){if(mounted)ScaffoldMessenger.of(context).showSnackBar(SnackBar(content:Text(_friendlyError(e))));}}
  Future<void> openCompanies()async{await Navigator.push(context,MaterialPageRoute(builder:(_)=>const CompaniesAdminScreen()));if(mounted)load();}
  Future<void> edit([Map<String,dynamic>? item])async{if(!canEdit)return;final name=TextEditingController(text:'${item?['name']??''}'),responsible=TextEditingController(text:'${item?['responsible']??''}'),location=TextEditingController(text:'${item?['location']??''}');int? companyId=_intOrNull(item?['contracting_company_id']);final clients=companies.where((x)=>x['active']!=false&&x['is_client']==true).toList();final ok=await showDialog<bool>(context:context,builder:(ctx)=>StatefulBuilder(builder:(ctx,setD)=>AlertDialog(title:Text(item==null?'Cadastrar obra':'Editar obra'),content:SingleChildScrollView(child:Column(mainAxisSize:MainAxisSize.min,children:[TextField(controller:name,decoration:const InputDecoration(labelText:'Nome da obra *')),const SizedBox(height:8),DropdownButtonFormField<int>(value:companyId,isExpanded:true,decoration:const InputDecoration(labelText:'Empresa cliente / contratante *'),items:clients.map((c)=>DropdownMenuItem(value:_intOrNull(c['id']),child:Text('${c['name']}'))).toList(),onChanged:(v)=>setD(()=>companyId=v)),const SizedBox(height:8),TextField(controller:responsible,decoration:const InputDecoration(labelText:'Responsável da obra *')),const SizedBox(height:8),TextField(controller:location,decoration:const InputDecoration(labelText:'Local'))])),actions:[TextButton(onPressed:()=>Navigator.pop(ctx,false),child:const Text('Cancelar')),FilledButton(onPressed:()=>Navigator.pop(ctx,true),child:const Text('Salvar'))])));if(ok==true){if(name.text.trim().isEmpty||responsible.text.trim().isEmpty||companyId==null){ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content:Text('Preencha Nome da obra, Empresa cliente/contratante e Responsável da obra.')));}else{setState(()=>busy=true);try{await api.saveWork(id:_intOrNull(item?['id']),name:name.text.trim(),location:location.text.trim(),responsible:responsible.text.trim(),companyId:companyId);await load();if(mounted)ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content:Text('Obra salva com sucesso ✓')));}catch(e){if(mounted)ScaffoldMessenger.of(context).showSnackBar(SnackBar(content:Text(_friendlyError(e))));}finally{if(mounted)setState(()=>busy=false);}}}name.dispose();responsible.dispose();location.dispose();}
  Future<void> finalize(Map<String,dynamic> item)async{if(!canFinalize)return;if(!offlineStore.online.value){ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content:Text('Internet obrigatória para finalizar e armazenar o Relatório Final.')));return;}final id=_intOrNull(item['id']);if(id==null)return;final count=_intOrNull(item['movement_count'])??0;final liters=_fmtLiters(item['fueling_liters']);final ok=await showDialog<bool>(context:context,builder:(ctx)=>AlertDialog(title:const Text('Finalizar obra?'),content:Text('Obra: ${item['name']}\nCliente: ${item['company_name']??'-'}\nResponsável: ${item['responsible']??'-'}\n\n$count registro(s) existentes • $liters abastecidos.\n\nA obra ficará somente para consulta e novos abastecimentos serão bloqueados. O Relatório Final será gerado e armazenado.'),actions:[TextButton(onPressed:()=>Navigator.pop(ctx,false),child:const Text('Cancelar')),FilledButton(onPressed:()=>Navigator.pop(ctx,true),child:const Text('Finalizar e gerar PDF'))]));if(ok!=true||!mounted)return;setState(()=>busy=true);try{final snapshot=await api.workFinalReportDataV23(id);final now=DateTime.now().toUtc().toIso8601String();_map(snapshot['work'])['finalized_at']=now;_map(snapshot['work'])['status']='finalized';snapshot['generated_at']=now;final bytes=await WorkFinalPdf.build(snapshot);final path=await api.uploadBytes(bytes,'relatorio_final_obra_$id',mime:'application/pdf');if(path.startsWith('local://'))throw Exception('O PDF não foi enviado ao servidor.');await api.finalizeWorkV23(id,path);await load();if(mounted)await Navigator.push(context,MaterialPageRoute(builder:(_)=>Scaffold(appBar:AppBar(title:const Text('Relatório Final')),body:PdfPreview(build:(_ )async=>bytes,canChangePageFormat:false,canChangeOrientation:false,canDebug:false))));}catch(e){if(mounted)ScaffoldMessenger.of(context).showSnackBar(SnackBar(content:Text('Não foi possível finalizar: ${_friendlyError(e)}')));}finally{if(mounted)setState(()=>busy=false);}}
  Future<void> deleteWork(Map<String,dynamic>x)async{if(!canEdit)return;final id=_intOrNull(x['id']);if(id==null)return;final mov=_intOrNull(x['movement_count'])??0,rep=_intOrNull(x['report_count'])??0;final ok=await showDialog<bool>(context:context,builder:(ctx)=>AlertDialog(title:const Text('Enviar obra para Excluídas?'),content:Text('Obra: ${x['name']}\n\nEla sairá das operações ativas, mas $mov registro(s) e $rep relatório(s) permanecerão preservados e consultáveis. Você poderá restaurá-la depois.'),actions:[TextButton(onPressed:()=>Navigator.pop(ctx,false),child:const Text('Cancelar')),FilledButton.icon(style:FilledButton.styleFrom(backgroundColor:Colors.red.shade700),onPressed:()=>Navigator.pop(ctx,true),icon:const Icon(Icons.delete_outline),label:const Text('Mover para Excluídas'))]));if(ok!=true)return;setState(()=>busy=true);try{await api.deleteWorkV25(id);await load();}catch(e){if(mounted)ScaffoldMessenger.of(context).showSnackBar(SnackBar(content:Text(_friendlyError(e))));}finally{if(mounted)setState(()=>busy=false);}}
  Future<void> restore(Map<String,dynamic>x)async{final id=_intOrNull(x['id']);if(id==null)return;final ok=await showDialog<bool>(context:context,builder:(ctx)=>AlertDialog(title:const Text('Restaurar obra?'),content:Text('A obra “${x['name']}” voltará para ${x['finalized_at']!=null?'Finalizadas':'Ativas'}.'),actions:[TextButton(onPressed:()=>Navigator.pop(ctx,false),child:const Text('Cancelar')),FilledButton(onPressed:()=>Navigator.pop(ctx,true),child:const Text('Restaurar'))]));if(ok==true){setState(()=>busy=true);try{await api.restoreWorkV28(id);await load();}catch(e){if(mounted)ScaffoldMessenger.of(context).showSnackBar(SnackBar(content:Text(_friendlyError(e))));}finally{if(mounted)setState(()=>busy=false);}}}
  Future<void> purge(Map<String,dynamic>x)async{final id=_intOrNull(x['id']);if(id==null)return;final mov=_intOrNull(x['movement_count'])??0,rep=_intOrNull(x['report_count'])??0;if(mov>0||rep>0){ScaffoldMessenger.of(context).showSnackBar(SnackBar(content:Text('Exclusão definitiva bloqueada: $mov registro(s) e $rep relatório(s) precisam ser preservados.')));return;}final ok=await showDialog<bool>(context:context,builder:(ctx)=>AlertDialog(title:const Text('Excluir definitivamente?'),content:Text('A obra “${x['name']}” não possui registros nem relatórios. Esta ação não poderá ser desfeita.'),actions:[TextButton(onPressed:()=>Navigator.pop(ctx,false),child:const Text('Cancelar')),FilledButton(style:FilledButton.styleFrom(backgroundColor:Colors.red.shade800),onPressed:()=>Navigator.pop(ctx,true),child:const Text('Excluir definitivamente'))]));if(ok==true){setState(()=>busy=true);try{await api.purgeWorkV28(id);await load();}catch(e){if(mounted)ScaffoldMessenger.of(context).showSnackBar(SnackBar(content:Text(_friendlyError(e))));}finally{if(mounted)setState(()=>busy=false);}}}
  Widget workCard(Map<String,dynamic>x){final status='${x['status']}';final deleted=status=='deleted'||x['deleted_at']!=null;final finalized=status=='finalized';return Card(child:InkWell(onTap:()=>Navigator.push(context,MaterialPageRoute(builder:(_)=>WorkDetailsV28Screen(profile:widget.profile,workId:_intOrNull(x['id'])!,onFinalize:finalize))),borderRadius:BorderRadius.circular(12),child:Padding(padding:const EdgeInsets.all(13),child:Column(crossAxisAlignment:CrossAxisAlignment.start,children:[Row(children:[CircleAvatar(child:Icon(deleted?Icons.delete_outline:finalized?Icons.task_alt_rounded:Icons.location_city_outlined)),const SizedBox(width:9),Expanded(child:Text('${x['name']}',style:const TextStyle(fontWeight:FontWeight.w900,fontSize:16))),PopupMenuButton<String>(enabled:!busy,onSelected:(v){if(v=='edit')edit(x);if(v=='finalize')finalize(x);if(v=='delete')deleteWork(x);if(v=='restore')restore(x);if(v=='purge')purge(x);},itemBuilder:(_)=>[if(!deleted&&!finalized&&canEdit)const PopupMenuItem(value:'edit',child:Text('Editar obra')),if(!deleted&&!finalized&&canFinalize)const PopupMenuItem(value:'finalize',child:Text('Finalizar obra e gerar PDF')),if(!deleted&&canEdit)const PopupMenuItem(value:'delete',child:Text('Excluir obra',style:TextStyle(color:Colors.red))),if(deleted&&canEdit)const PopupMenuItem(value:'restore',child:Text('Restaurar obra')),if(deleted&&canEdit)const PopupMenuItem(value:'purge',child:Text('Excluir definitivamente',style:TextStyle(color:Colors.red)))])]),const SizedBox(height:7),Text('Cliente: ${x['company_name']??'-'}\nResponsável: ${x['responsible']??'-'}\nLocal: ${x['location']??'-'}'),const SizedBox(height:8),Wrap(spacing:7,runSpacing:6,children:[Chip(label:Text(deleted?'EXCLUÍDA':finalized?'FINALIZADA':'ATIVA')),Chip(label:Text('Abastecido: ${_fmtLiters(x['fueling_liters'])}')),Chip(label:Text('${x['fueling_count']??0} abastecimento(s)')),Chip(label:Text('${x['own_assets_count']??0} próprios • ${x['third_assets_count']??0} terceiros'))])]))));}
  @override Widget build(BuildContext context){final all=items??const <Map<String,dynamic>>[],active=all.where((x)=>'${x['status']}'=='active'&&x['deleted_at']==null).toList(),fin=all.where((x)=>'${x['status']}'=='finalized'&&x['deleted_at']==null).toList(),del=all.where((x)=>'${x['status']}'=='deleted'||x['deleted_at']!=null).toList();Widget tab(List<Map<String,dynamic>> l,String empty)=>RefreshIndicator(onRefresh:load,child:ListView(padding:const EdgeInsets.fromLTRB(12,12,12,90),children:[if(l.isEmpty)Card(child:ListTile(title:Text(empty))),...l.map(workCard)]));return DefaultTabController(length:3,child:Scaffold(appBar:AppBar(title:const Text('Obras'),bottom:TabBar(tabs:[Tab(text:'Ativas (${active.length})'),Tab(text:'Finalizadas (${fin.length})'),Tab(text:'Excluídas (${del.length})')])),floatingActionButton:canEdit?FloatingActionButton.extended(onPressed:busy?null:()=>companies.where((x)=>x['is_client']==true&&x['active']!=false).isEmpty?openCompanies():edit(),icon:const Icon(Icons.add),label:const Text('Nova obra')):null,body:items==null?const Center(child:CircularProgressIndicator()):TabBarView(children:[tab(active,'Nenhuma obra ativa.'),tab(fin,'Nenhuma obra finalizada.'),tab(del,'Nenhuma obra excluída.')])));}
}

class WorkDetailsV28Screen extends StatefulWidget {
  final Map<String,dynamic> profile;
  final int workId;
  final Future<void> Function(Map<String,dynamic>)? onFinalize;
  const WorkDetailsV28Screen({super.key,required this.profile,required this.workId,this.onFinalize});
  @override State<WorkDetailsV28Screen> createState()=>_WorkDetailsV28ScreenState();
}
class _WorkDetailsV28ScreenState extends State<WorkDetailsV28Screen>{
  Map<String,dynamic>? data;
  bool busy=false;
  @override void initState(){super.initState();load();}
  Future<void> load()async{
    setState(()=>busy=true);
    try{
      final d=await api.workDetailV28(widget.workId);
      if(mounted)setState(()=>data=d);
    }catch(e){
      if(mounted)ScaffoldMessenger.of(context).showSnackBar(SnackBar(content:Text(_friendlyError(e))));
    }finally{if(mounted)setState(()=>busy=false);}
  }
  @override Widget build(BuildContext context){
    final w=_map(data?['work']);
    final sm=_map(data?['summary']);
    Widget metric(String l,String v)=>Expanded(child:Card(child:Padding(
      padding:const EdgeInsets.all(12),
      child:Column(crossAxisAlignment:CrossAxisAlignment.start,children:[
        Text(l,style:const TextStyle(fontSize:11,color:Colors.black54)),
        const SizedBox(height:3),
        Text(v,style:const TextStyle(fontWeight:FontWeight.w900,fontSize:17)),
      ]),
    )));
    return Scaffold(
      appBar:AppBar(title:Text(w.isEmpty?'Detalhes da obra':'${w['name']}')),
      body:data==null?const Center(child:CircularProgressIndicator()):RefreshIndicator(
        onRefresh:load,
        child:ListView(padding:const EdgeInsets.all(12),children:[
          Card(child:Padding(padding:const EdgeInsets.all(15),child:Column(crossAxisAlignment:CrossAxisAlignment.start,children:[
            Text('${w['name']}',style:const TextStyle(fontWeight:FontWeight.w900,fontSize:20)),
            const SizedBox(height:7),
            Text('Empresa cliente/contratante: ${w['company_name']??'-'}\nResponsável da obra: ${w['responsible']??'-'}\nLocal: ${w['location']??'-'}\nStatus: ${w['status']??'-'}'),
          ]))),
          Row(children:[metric('Total abastecido',_fmtLiters(sm['fueling_liters'])),metric('Abastecimentos','${sm['fueling_count']??0}')]),
          Row(children:[metric('Registros','${sm['movement_count']??0}'),if(sm['sale_total']!=null)metric('Valor',_fmtMoney(sm['sale_total']))else metric('Combustíveis','${_rows(data?['fuel_breakdown']).length}')]),
          if(_rows(data?['fuel_breakdown']).isNotEmpty)Card(child:Padding(padding:const EdgeInsets.all(14),child:Column(crossAxisAlignment:CrossAxisAlignment.start,children:[
            const Text('Consumo por combustível',style:TextStyle(fontWeight:FontWeight.w900)),
            const SizedBox(height:7),
            ..._rows(data?['fuel_breakdown']).map((x)=>ListTile(dense:true,contentPadding:EdgeInsets.zero,title:Text('${x['fuel_type']}'),trailing:Text(_fmtLiters(x['liters']),style:const TextStyle(fontWeight:FontWeight.w900)))),
          ]))),
          if(_rows(data?['own_assets']).isNotEmpty)Card(child:ExpansionTile(
            title:const Text('Equipamentos próprios',style:TextStyle(fontWeight:FontWeight.w900)),
            children:_rows(data?['own_assets']).map((x)=>ListTile(title:Text('${x['asset_number']} • ${x['model']??''}'),subtitle:Text('Placa: ${x['plate']??'-'}'),trailing:Text(_fmtLiters(x['liters'])))).toList(),
          )),
          if(_rows(data?['third_assets']).isNotEmpty)Card(child:ExpansionTile(
            title:const Text('Equipamentos de terceiros',style:TextStyle(fontWeight:FontWeight.w900)),
            children:_rows(data?['third_assets']).map((x)=>ListTile(title:Text('${x['plate']??'Sem placa'} • ${x['description']??''}'),subtitle:Text('${x['company_name']??'-'}'),trailing:Text(_fmtLiters(x['liters'])))).toList(),
          )),
          if(_rows(data?['reports']).isNotEmpty)Card(child:ExpansionTile(
            title:const Text('Relatórios',style:TextStyle(fontWeight:FontWeight.w900)),
            children:_rows(data?['reports']).map((r)=>ListTile(
              leading:const Icon(Icons.picture_as_pdf_outlined,color:_blue),
              title:Text('${r['title']}'),
              subtitle:Text(_fmtDate(r['report_date'])),
              onTap:()async{
                final b=await api.downloadMedia('${r['pdf_path']}');
                if(b!=null&&mounted){
                  await Navigator.push(context,MaterialPageRoute(builder:(_)=>Scaffold(
                    appBar:AppBar(title:Text('${r['title']}')),
                    body:PdfPreview(build:(_ )async=>b,canChangePageFormat:false,canChangeOrientation:false,canDebug:false),
                  )));
                }
              },
            )).toList(),
          )),
          const SizedBox(height:5),
          FilledButton.icon(
            onPressed:()=>Navigator.push(context,MaterialPageRoute(builder:(_)=>GeneralRecordsV28Screen(initialWorkId:widget.workId))),
            icon:const Icon(Icons.manage_search),
            label:const Text('Ver Registro Geral desta obra'),
          ),
          if('${w['status']}'=='active'&&widget.onFinalize!=null&&(widget.profile['is_admin']==true||widget.profile['is_manager']==true))...[
            const SizedBox(height:8),
            OutlinedButton.icon(
              onPressed:busy?null:()async{
                final target=Map<String,dynamic>.from(w)..addAll(sm);
                await widget.onFinalize!(target);
                if(mounted)load();
              },
              icon:const Icon(Icons.task_alt_outlined),
              label:const Text('Finalizar obra e gerar Relatório Final'),
            ),
          ],
          const SizedBox(height:40),
        ]),
      ),
    );
  }
}

'''
replace_block('class WorksAdminScreen extends StatefulWidget {','class MachinesAdminScreen extends StatefulWidget {',works_new,'works v28')

# Company role tags: simple, clear, uppercase.
s=s.replace("if (x['is_client'] == true) 'Cliente / Contratante',\n    if (x['is_equipment_owner'] == true) 'Proprietária / Locadora',\n    if (x['is_fuel_supplier'] == true) 'Fornecedor de combustível',","if (x['is_client'] == true) 'CLIENTE',\n    if (x['is_equipment_owner'] == true) 'LOCADORA',\n    if (x['is_fuel_supplier'] == true) 'FORNECEDOR',")
s=s.replace("roles.map((r) => Chip(label: Text(r))).toList()","roles.map((r) => Chip(label: Text(r, style: const TextStyle(fontWeight: FontWeight.w900)))).toList()")

p.write_text(s)
print('v28 management/records/audit staged',len(s))
