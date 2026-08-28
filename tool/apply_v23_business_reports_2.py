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

# ---------- NF trace all lots ----------
nf_trace=r'''class NfTraceV23Screen extends StatefulWidget {
  final Map<String,dynamic> ref;
  const NfTraceV23Screen({super.key,required this.ref});
  @override State<NfTraceV23Screen> createState()=>_NfTraceV23ScreenState();
}
class _NfTraceV23ScreenState extends State<NfTraceV23Screen> {
  List<Map<String,dynamic>>? lots;
  int? id;
  Map<String,dynamic>? data;
  bool loading=false;
  final search=TextEditingController();
  @override void initState(){super.initState();loadLots();}
  @override void dispose(){search.dispose();super.dispose();}
  Future<void> loadLots() async {setState(()=>loading=true);try{final x=await api.lotsCatalogV23();if(mounted)setState(()=>lots=x);}catch(e){if(mounted)ScaffoldMessenger.of(context).showSnackBar(SnackBar(content:Text(_friendlyError(e))));}finally{if(mounted)setState(()=>loading=false);}}
  Future<void> trace(int value) async {setState(()=>loading=true);try{final x=await api.traceV23(value);if(mounted)setState((){id=value;data=x;});}catch(e){if(mounted)ScaffoldMessenger.of(context).showSnackBar(SnackBar(content:Text('Erro ao rastrear NF: ${_friendlyError(e)}')));}finally{if(mounted)setState(()=>loading=false);}}
  @override Widget build(BuildContext c){
    final q=search.text.trim().toLowerCase();
    final visible=(lots??const <Map<String,dynamic>>[]).where((x)=>q.isEmpty||'${x['invoice_number']} ${x['supplier_name']} ${x['fuel_type']}'.toLowerCase().contains(q)).toList();
    final d=data,lot=_map(d?['lot']),summary=_map(d?['summary']);
    return Scaffold(appBar:AppBar(title:const Text('Rastreabilidade por Nota Fiscal')),body:ListView(padding:const EdgeInsets.all(16),children:[
      const Card(child:ListTile(leading:Icon(Icons.route_outlined,color:_blue),title:Text('Rastreabilidade completa'),subtitle:Text('Acompanhe a NF da entrada na refinaria até transferências, estoques e abastecimentos finais. NFs já esgotadas também permanecem disponíveis.'))),
      TextField(controller:search,onChanged:(_)=>setState((){}),decoration:const InputDecoration(labelText:'Pesquisar NF, fornecedor ou combustível',prefixIcon:Icon(Icons.search_rounded))),
      const SizedBox(height:10),
      DropdownButtonFormField<int>(value:id,isExpanded:true,decoration:const InputDecoration(labelText:'Nota Fiscal / lote'),items:visible.map((x)=>DropdownMenuItem(value:_intOrNull(x['id']),child:Text('NF ${x['invoice_number']} • ${x['supplier_name']??'-'} • ${x['status']=='exhausted'?'Esgotada':_fmtLiters(x['remaining_liters'])}'))).toList(),onChanged:loading?null:(v){if(v!=null)trace(v);}),
      if(loading)const Padding(padding:EdgeInsets.only(top:10),child:LinearProgressIndicator()),
      if(d!=null)...[
        const SizedBox(height:14),Text('NF ${lot['invoice_number']}',style:Theme.of(c).textTheme.titleLarge?.copyWith(fontWeight:FontWeight.w900)),
        Card(child:Column(children:[
          ListTile(title:const Text('Fornecedor do combustível'),trailing:Flexible(child:Text('${lot['supplier_name']??'-'}',textAlign:TextAlign.right))),
          ListTile(title:const Text('Volume original'),trailing:Text(_fmtLiters(lot['total_liters']))),
          ListTile(title:const Text('Volume consumido'),trailing:Text(_fmtLiters(lot['consumed_liters']))),
          ListTile(title:const Text('Saldo atual da NF'),trailing:Text(_fmtLiters(lot['remaining_liters']))),
          ListTile(title:const Text('Recebida em'),trailing:Text(_fmtDate(lot['received_at']))),
          if(lot['exhausted_at']!=null)ListTile(title:const Text('NF esgotada em'),trailing:Text(_fmtDate(lot['exhausted_at']))),
          if(lot['unit_cost']!=null)ListTile(title:const Text('Custo de compra/L'),trailing:Text(_fmtMoney(lot['unit_cost']))),
          ListTile(title:const Text('Abastecimentos finais'),trailing:Text('${summary['final_fueling_count']??0} • ${_fmtLiters(summary['final_fueling_liters'])}')),
          if(summary['profit_total']!=null)ListTile(title:const Text('Lucro total associado'),trailing:Text(_fmtMoney(summary['profit_total']))),
        ])),
        const SizedBox(height:10),const Text('Onde ainda existe saldo',style:TextStyle(fontSize:17,fontWeight:FontWeight.w900)),
        if(_rows(d!['positions']).isEmpty)const Card(child:ListTile(title:Text('Sem saldo em estruturas'),subtitle:Text('Todo o volume desta NF já saiu do estoque ou foi consumido.'))),
        ..._rows(d!['positions']).map((p)=>Card(child:ListTile(title:Text('${p['code']} • ${p['name']}'),subtitle:Text('${p['tank_type']}'),trailing:Text(_fmtLiters(p['remaining_liters']),style:const TextStyle(fontWeight:FontWeight.w900))))),
        const SizedBox(height:10),const Text('Caminho do combustível',style:TextStyle(fontSize:17,fontWeight:FontWeight.w900)),
        ..._rows(d!['movements']).map((m){final route=[m['source'],m['destination']].where((v)=>_hasValue(v)).join(' → ');final target=m['asset_number']??m['third_party'];return Card(child:ListTile(title:Text('${_movementLabel('${m['type']}')} • ${_fmtLiters(m['liters'])}',style:const TextStyle(fontWeight:FontWeight.w900)),subtitle:Text('${_fmtDate(m['created_at'])}${route.isNotEmpty?'\n$route':''}${_hasValue(target)?'\nEquipamento: $target':''}${_hasValue(m['work'])?'\nObra: ${m['work']} • Responsável: ${m['work_responsible']??'-'}':''}${m['unit_cost']!=null?'\nCusto/L: ${_fmtMoney(m['unit_cost'])}':''}${m['sale_price_per_liter']!=null?' • Venda/L: ${_fmtMoney(m['sale_price_per_liter'])}':''}')));}),
      ],
    ]));
  }
}

'''
replace_between('class NfTraceV23Screen','String _permissionLabelV23',nf_trace,'nf trace screen')

replace_once("""    'comparisons.view':'Comparar equipamentos','reports.view':'Visualizar relatórios','reports.export':'Exportar relatórios',
""","""    'comparisons.view':'Comparar equipamentos','reports.view':'Visualizar relatórios','reports.export':'Exportar relatórios','works.finalize':'Finalizar obra e gerar Relatório Final',
    'fueling.create':'Registrar abastecimentos','transfer.create':'Registrar transferências','refinery.receive':'Receber carga da refinaria','refinery.unload':'Descarregar caminhão-tanque no T.E.',
""",'permission labels')

# ---------- admin home + reports card + pass profile to catalog ----------
old="""                  HomeActionCard(icon: Icons.manage_search_rounded, title: 'Registros e pesquisa', subtitle: 'Filtrar por data, obra, ativo, placa, usuário e tipo de movimentação', onTap: () => Navigator.push(context, MaterialPageRoute(builder: (_) => AdminRecordsScreen(referenceData: ref!)))),
                  const SizedBox(height: 12),
                  if(widget.profile['is_admin']==true) HomeActionCard(icon: Icons.manage_accounts_rounded, title: 'Operadores', subtitle: 'Cadastrar, editar, habilitar, desabilitar ou excluir operadores', onTap: () => Navigator.push(context, MaterialPageRoute(builder: (_) => AdminUsersOnlineScreen(referenceData: ref!)))),
"""
new="""                  HomeActionCard(icon: Icons.manage_search_rounded, title: 'Registros e pesquisa', subtitle: 'Filtrar por data, obra, ativo, placa, usuário e tipo de movimentação', onTap: () => Navigator.push(context, MaterialPageRoute(builder: (_) => AdminRecordsScreen(referenceData: ref!)))),
                  const SizedBox(height: 12),
                  if(widget.profile['is_admin']==true||widget.profile['is_manager']==true) HomeActionCard(icon: Icons.folder_copy_outlined, title: 'Relatórios', subtitle: 'Relatórios finais de obras armazenados e pesquisáveis', onTap: () => Navigator.push(context, MaterialPageRoute(builder: (_) => const GeneratedReportsV23Screen()))),
                  if(widget.profile['is_admin']==true||widget.profile['is_manager']==true) const SizedBox(height:12),
                  if(widget.profile['is_admin']==true) HomeActionCard(icon: Icons.manage_accounts_rounded, title: 'Operadores', subtitle: 'Cadastrar, editar, habilitar, desabilitar ou excluir operadores', onTap: () => Navigator.push(context, MaterialPageRoute(builder: (_) => AdminUsersOnlineScreen(referenceData: ref!)))),
"""
replace_once(old,new,'reports card')
replace_once("""                  HomeActionCard(icon: Icons.inventory_2_outlined, title: 'Cadastros', subtitle: 'Tanques estacionários, obras, ativos próprios e equipamentos alugados', onTap: () async { await Navigator.push(context, MaterialPageRoute(builder: (_) => const AdminCatalogScreen())); await refresh(); }),
""","""                  HomeActionCard(icon: Icons.inventory_2_outlined, title: 'Cadastros', subtitle: 'Tanques estacionários, obras, ativos próprios e equipamentos de terceiros', onTap: () async { await Navigator.push(context, MaterialPageRoute(builder: (_) => AdminCatalogScreen(profile:widget.profile))); await refresh(); }),
""",'catalog profile home')

# ---------- AdminMore nomenclature ----------
replace_once("""          title: 'Empresas',
          subtitle: 'Cadastrar os dados das empresas que serão usados nos PDFs',
""","""          title: 'Empresas vinculadas',
          subtitle: 'Empresas de obras e proprietárias de equipamentos de terceiros',
""",'admin more company nomenclature')
replace_once("""    appBar: AppBar(title: const Text('Empresas')),
""","""    appBar: AppBar(title: const Text('Empresas vinculadas')),
""",'company page title')

# ---------- catalog gets profile ----------
old="""class AdminCatalogScreen extends StatelessWidget {
  const AdminCatalogScreen({super.key});
"""
new="""class AdminCatalogScreen extends StatelessWidget {
  final Map<String,dynamic> profile;
  const AdminCatalogScreen({super.key,required this.profile});
"""
replace_once(old,new,'catalog constructor')
replace_once("""      HomeActionCard(icon: Icons.location_city_outlined, title: 'Obras', subtitle: 'Cadastrar e consultar obras', onTap: () => Navigator.push(context, MaterialPageRoute(builder: (_) => const WorksAdminScreen()))),
""","""      HomeActionCard(icon: Icons.location_city_outlined, title: 'Obras', subtitle: 'Cadastrar, consultar e finalizar obras', onTap: () => Navigator.push(context, MaterialPageRoute(builder: (_) => WorksAdminScreen(profile:profile)))),
""",'works profile catalog')

p.write_text(s)
print("business reports part 2 applied",len(s),"chars")
