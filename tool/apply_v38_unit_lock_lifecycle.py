from pathlib import Path

p=Path('lib/main_online.dart')
s=p.read_text()

# ---------------- App lifecycle: minimize preserves state; close logs out/releases best effort ----------------
s=s.replace('class _AuthGateState extends State<AuthGate> {','class _AuthGateState extends State<AuthGate> with WidgetsBindingObserver {',1)
s=s.replace(
"  bool loading=true,_checkingSessionV30=false; Map<String,dynamic>? profile; String? error; Timer? _sessionGuardV30;\n  @override void initState(){super.initState();_restore();}\n  @override void dispose(){_sessionGuardV30?.cancel();super.dispose();}\n",
"  bool loading=true,_checkingSessionV30=false,_closingV38=false; Map<String,dynamic>? profile; String? error; Timer? _sessionGuardV30;\n  @override void initState(){super.initState();WidgetsBinding.instance.addObserver(this);_restore();}\n  @override void dispose(){WidgetsBinding.instance.removeObserver(this);_sessionGuardV30?.cancel();super.dispose();}\n  @override void didChangeAppLifecycleState(AppLifecycleState state){\n    if(state==AppLifecycleState.resumed){_startSessionGuardV30();unawaited(_checkSessionV30());return;}\n    // paused/inactive/hidden = minimizado: mantém tela, sessão e unidade reservada.\n    if(state==AppLifecycleState.detached){unawaited(_closeAppV38());}\n  }\n  Future<void> _closeAppV38() async {\n    if(_closingV38||profile==null)return;_closingV38=true;_sessionGuardV30?.cancel();\n    final id=offlineStore.appSessionIdV30;\n    if(id!=null&&offlineStore.online.value){try{await api.logoutV30(id).timeout(const Duration(seconds:2));}catch(_){}}\n    try{await offlineStore.clearProfile();await offlineStore.setLastTankId(null);await offlineStore.clearAppSessionIdV30();}catch(_){}\n    try{await Supabase.instance.client.auth.signOut(scope:SignOutScope.local).timeout(const Duration(seconds:1));}catch(_){}\n  }\n",
1)

a=s.index('class UnitSelectionScreen extends StatefulWidget {')
b=s.index('class FieldHomeScreen extends StatefulWidget {',a)
unit_new=r'''class UnitSelectionScreen extends StatefulWidget {
  final Map<String, dynamic> profile;
  final Future<void> Function() onLogout;
  const UnitSelectionScreen({super.key, required this.profile, required this.onLogout});

  @override
  State<UnitSelectionScreen> createState() => _UnitSelectionScreenState();
}

class _UnitSelectionScreenState extends State<UnitSelectionScreen> {
  Map<String, dynamic>? data;
  List<Map<String,dynamic>> statuses=[];
  String? error;
  Timer? timer;
  bool refreshing = false;

  @override
  void initState() {
    super.initState();
    refresh();
    timer = Timer.periodic(const Duration(seconds: 3), (_) => refresh(silent: true));
  }

  @override
  void dispose() {
    timer?.cancel();
    super.dispose();
  }

  Map<String,dynamic>? statusFor(int id){for(final x in statuses){if(_intOrNull(x['tank_id'])==id)return x;}return null;}

  Future<void> refresh({bool silent = false}) async {
    if (refreshing) return;
    refreshing = true;
    try {
      final d = await api.referenceData();
      List<Map<String,dynamic>> st=[];
      if(offlineStore.online.value){try{st=await api.unitStatusV30();}catch(_){}}
      if (mounted) setState(() { data = d; statuses=st; error = null; });
    } catch (e) {
      if (mounted && !silent) setState(() => error = _friendlyError(e));
    } finally {
      refreshing = false;
    }
  }

  @override
  Widget build(BuildContext context) {
    final tanks = _sortedFuelUnits(data?['tanks']);
    return Scaffold(
      appBar: AppBar(
        actions: [IconButton(onPressed: () async { await _logoutToLogin(context, widget.onLogout); }, tooltip: 'Sair', icon: const Icon(Icons.logout_rounded))],
      ),
      body: data == null
          ? Center(child: error == null ? const CircularProgressIndicator() : Text(error!))
          : RefreshIndicator(
              onRefresh: refresh,
              child: ListView(
                padding: const EdgeInsets.all(22),
                children: [
                  const BrandHeader(compact: true),
                  const SizedBox(height: 24),
                  SizedBox(height: 34, child: FittedBox(fit: BoxFit.scaleDown, alignment: Alignment.centerLeft, child: Text('Olá, ${widget.profile['display_name']}', maxLines: 1, softWrap: false, style: Theme.of(context).textTheme.headlineSmall?.copyWith(fontWeight: FontWeight.w900)))),
                  const SizedBox(height: 6),
                  const Text('Unidades em uso ficam bloqueadas imediatamente e só voltam a ficar disponíveis após liberação ou troca.'),
                  const SizedBox(height: 18),
                  ...tanks.map((tank) {
                    final authorized = tank['authorized'] != false;
                    final tankId=_intOrNull(tank['id']);
                    final st=tankId==null?null:statusFor(tankId);
                    final mine=st?['is_mine']==true;
                    final inUse=st?['in_use']==true;
                    final blocked=inUse&&!mine;
                    final owner='${st?['user_name']??''}'.trim();
                    final typeLabel = tank['tank_type'] == 'stationary' ? 'Tanque estacionário' : tank['tank_type'] == 'truck' ? 'Caminhão-tanque' : 'Comboio';
                    final subtitle=blocked?'$typeLabel • Em uso por ${owner.isEmpty?'outro usuário':owner}':'$typeLabel • Saldo disponível: ${_fmtLiters(tank['current_balance_liters'])}${authorized ? '' : '\nSomente visualização'}';
                    return Card(
                      child: ListTile(
                        contentPadding: const EdgeInsets.all(14),
                        leading: Icon(tank['tank_type'] == 'stationary' ? Icons.oil_barrel_outlined : tank['tank_type'] == 'truck' ? Icons.local_shipping_rounded : Icons.local_shipping_outlined, color: blocked?Colors.black38:_blue),
                        title: Text('${tank['code']} • ${tank['name']}', style: const TextStyle(fontWeight: FontWeight.w900)),
                        subtitle: Text(subtitle),
                        isThreeLine: !authorized,
                        trailing: mine?const Icon(Icons.check_circle_rounded,color:Colors.green):blocked?const Icon(Icons.lock_outline_rounded):Icon(authorized ? Icons.chevron_right_rounded : Icons.visibility_outlined),
                        onTap: blocked
                            ? () => ScaffoldMessenger.of(context).showSnackBar(SnackBar(content:Text('Esta unidade já está sendo usada por ${owner.isEmpty?'outro usuário':owner}.')))
                            : authorized
                            ? () async {
                                if (tankId == null) {
                                  ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Unidade inválida.')));
                                  return;
                                }
                                if (!offlineStore.online.value) {
                                  if (offlineStore.lastTankId != tankId) {
                                    ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Conecte-se à internet para trocar de unidade. A unidade atual continua reservada.')));
                                    return;
                                  }
                                } else {
                                  try {
                                    final claim = await api.claimUnitV31(tankId);
                                    if (claim['ok'] != true) {
                                      if (context.mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('${claim['message'] ?? 'Esta unidade já está em uso.'}')));
                                      await refresh(silent:true);
                                      return;
                                    }
                                  } catch (e) {
                                    if (context.mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(_friendlyError(e))));
                                    return;
                                  }
                                }
                                await offlineStore.setLastTankId(tankId);
                                if (!context.mounted) return;
                                Navigator.pushReplacement(context, MaterialPageRoute(builder: (_) => FieldHomeScreen(profile: widget.profile, tankId: tankId, onLogout: widget.onLogout)));
                              }
                            : () => ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Esta unidade não foi liberada para operação deste usuário.'))),
                      ),
                    );
                  }),
                  if (tanks.isEmpty) const Padding(padding: EdgeInsets.all(24), child: Text('Nenhuma unidade cadastrada no sistema.', textAlign: TextAlign.center)),
                ],
              ),
            ),
    );
  }
}

'''
s=s[:a]+unit_new+s[b:]

a=s.index('class _AdminHomeScreenState extends State<AdminHomeScreen> {')
b=s.index('class AdminRecordsScreen extends StatelessWidget {',a)
admin_new=r'''class _AdminHomeScreenState extends State<AdminHomeScreen> {
  Map<String,dynamic>? ref;
  Map<String,dynamic> kpis={};
  Map<String,dynamic> currentUnit={};
  List<Map<String,dynamic>> statuses=[];
  Timer? timer; bool running=false;
  final globalSearch=TextEditingController();
  @override void initState(){super.initState();refresh();timer=Timer.periodic(const Duration(seconds:20),(_)=>refresh());}
  @override void dispose(){timer?.cancel();globalSearch.dispose();super.dispose();}
  Future<void> refresh() async {
    if(running)return; running=true;
    try{
      final d=await api.referenceData(); Map<String,dynamic> k={};Map<String,dynamic> mine={};List<Map<String,dynamic>> st=[];
      try{k=await api.dashboardKpisV28();}catch(_){}
      try{mine=await api.myUnitV30();}catch(_){}
      try{st=await api.unitStatusV30();}catch(_){}
      final tid=_intOrNull(mine['tank_id']);await offlineStore.setLastTankId(tid);
      if(mounted)setState((){ref=d;kpis=k;currentUnit=mine;statuses=st;});
    }catch(_){}finally{running=false;}
  }
  List<Map<String,dynamic>> _sources(Set<String> types)=>_sortedFuelUnits(ref?['tanks']).where((t)=>t['authorized']!=false&&types.contains('${t['tank_type']}')).toList();
  Map<String,dynamic>? _statusFor(int id){for(final x in statuses){if(_intOrNull(x['tank_id'])==id)return x;}return null;}
  Map<String,dynamic>? _tankFor(int? id){if(id==null)return null;for(final t in _sortedFuelUnits(ref?['tanks'])){if(_intOrNull(t['id'])==id)return t;}return null;}

  Future<bool> _claim(Map<String,dynamic> t) async {
    final id=_intOrNull(t['id']);if(id==null)return false;
    if(!offlineStore.online.value){ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content:Text('Conecte-se à internet para selecionar ou trocar de unidade.')));return false;}
    try{
      final x=await api.claimUnitV31(id);
      if(x['ok']!=true){if(mounted)ScaffoldMessenger.of(context).showSnackBar(SnackBar(content:Text('${x['message']??'Esta unidade já está em uso.'}')));await refresh();return false;}
      await offlineStore.setLastTankId(id);
      if(mounted)setState(()=>currentUnit={'tank_id':id,'unit_code':t['code'],'unit_name':t['name'],'tank_type':t['tank_type'],'user_name':widget.profile['display_name']});
      return true;
    }catch(e){if(mounted)ScaffoldMessenger.of(context).showSnackBar(SnackBar(content:Text(_friendlyError(e))));return false;}
  }

  Future<Map<String,dynamic>?> _choose(String title,String subtitle,Set<String> types,{bool excludeCurrent=false}) async {
    if(!offlineStore.online.value){ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content:Text('Conecte-se à internet para selecionar ou trocar de unidade.')));return null;}
    try{statuses=await api.unitStatusV30();}catch(_){}
    final currentId=_intOrNull(currentUnit['tank_id']);
    final list=_sources(types).where((t)=>!excludeCurrent||_intOrNull(t['id'])!=currentId).toList();
    if(list.isEmpty){if(mounted)ScaffoldMessenger.of(context).showSnackBar(SnackBar(content:Text('Nenhuma unidade disponível para $title.')));return null;}
    if(list.length==1){
      final t=list.first,id=_intOrNull(t['id']),st=id==null?null:_statusFor(id);final blocked=st?['in_use']==true&&st?['is_mine']!=true;
      if(blocked){final owner='${st?['user_name']??''}'.trim();if(mounted)ScaffoldMessenger.of(context).showSnackBar(SnackBar(content:Text('Esta unidade já está sendo usada por ${owner.isEmpty?'outro usuário':owner}.')));return null;}
      return await _claim(t)?t:null;
    }
    if(!mounted)return null;
    final selected=await showModalBottomSheet<Map<String,dynamic>>(context:context,showDragHandle:true,isScrollControlled:true,builder:(ctx)=>SafeArea(child:ConstrainedBox(constraints:BoxConstraints(maxHeight:MediaQuery.of(ctx).size.height*.75),child:ListView(shrinkWrap:true,padding:const EdgeInsets.fromLTRB(16,0,16,20),children:[
      Text(title,style:Theme.of(ctx).textTheme.titleLarge?.copyWith(fontWeight:FontWeight.w900)),const SizedBox(height:4),Text(subtitle,style:const TextStyle(color:Colors.black54)),const SizedBox(height:10),
      ...list.map((t){final id=_intOrNull(t['id']),st=id==null?null:_statusFor(id);final mine=st?['is_mine']==true,inUse=st?['in_use']==true,blocked=inUse&&!mine,owner='${st?['user_name']??''}'.trim();return Card(child:ListTile(leading:Icon('${t['tank_type']}'=='stationary'?Icons.oil_barrel_outlined:Icons.local_shipping_rounded,color:blocked?Colors.black38:_blue),title:Text('${t['code']} • ${t['name']}',style:const TextStyle(fontWeight:FontWeight.w800)),subtitle:Text(blocked?'Em uso por ${owner.isEmpty?'outro usuário':owner}':'Saldo: ${_fmtLiters(t['current_balance_liters'])}'),trailing:mine?const Icon(Icons.check_circle_rounded,color:Colors.green):blocked?const Icon(Icons.lock_outline_rounded):const Icon(Icons.chevron_right),onTap:blocked?(){ScaffoldMessenger.of(ctx).showSnackBar(SnackBar(content:Text('Esta unidade já está sendo usada por ${owner.isEmpty?'outro usuário':owner}.')));}:()=>Navigator.pop(ctx,t)));})
    ]))));
    if(selected==null||!mounted)return null;
    return await _claim(selected)?selected:null;
  }

  Future<void> _switchUnit() async {
    final selected=await _choose('Trocar unidade','Selecione uma unidade disponível. A unidade atual será liberada automaticamente.',const {'stationary','comboio','truck'},excludeCurrent:true);
    if(selected!=null&&mounted){await refresh();ScaffoldMessenger.of(context).showSnackBar(SnackBar(content:Text('Unidade alterada para ${selected['code']} ✓')));}
  }
  Future<void> _releaseUnit() async {
    final id=_intOrNull(currentUnit['tank_id']);if(id==null)return;
    final code='${currentUnit['unit_code']??''}';
    final ok=await showDialog<bool>(context:context,builder:(ctx)=>AlertDialog(title:const Text('Liberar unidade?'),content:Text(code.isEmpty?'A unidade ficará disponível para outro usuário.':'A unidade $code ficará disponível para outro usuário.'),actions:[TextButton(onPressed:()=>Navigator.pop(ctx,false),child:const Text('Cancelar')),FilledButton(onPressed:()=>Navigator.pop(ctx,true),child:const Text('Liberar'))]));
    if(ok!=true)return;
    try{await api.releaseMyUnitV31();await offlineStore.setLastTankId(null);if(mounted)setState(()=>currentUnit={});await refresh();if(mounted)ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content:Text('Unidade liberada ✓')));}catch(e){if(mounted)ScaffoldMessenger.of(context).showSnackBar(SnackBar(content:Text(_friendlyError(e))));}
  }
  Future<Map<String,dynamic>?> _operationUnit(Set<String> types,String title,String subtitle) async {
    final currentId=_intOrNull(currentUnit['tank_id']);final current=_tankFor(currentId);
    if(current!=null&&types.contains('${current['tank_type']}'))return current;
    return _choose(title,subtitle,types,excludeCurrent:currentId!=null);
  }
  Future<void> _fueling() async {if(ref==null)return;final t=await _operationUnit(const {'stationary','comboio','truck'},'Novo abastecimento','Selecione a unidade de origem.');if(!mounted||t==null||ref==null)return;await Navigator.push(context,MaterialPageRoute(builder:(_)=>FuelingV23Screen(source:t,ref:ref!,profile:widget.profile)));if(mounted)refresh();}
  Future<void> _transfer() async {if(ref==null)return;final t=await _operationUnit(const {'comboio','truck'},'Transferir','Selecione a unidade doadora.');if(!mounted||t==null||ref==null)return;await Navigator.push(context,MaterialPageRoute(builder:(_)=>TransferV23Screen(source:t,ref:ref!,profile:widget.profile)));if(mounted)refresh();}
  Future<void> _receipt() async {if(ref==null)return;final t=await _operationUnit(const {'truck'},'Recebimento de combustível / NF','Selecione o caminhão-tanque que receberá a carga.');if(!mounted||t==null)return;await Navigator.push(context,MaterialPageRoute(builder:(_)=>RefineryLoadV23Screen(truck:t)));if(mounted)refresh();}
  void open(Widget page)=>Navigator.push(context,MaterialPageRoute(builder:(_)=>page));
  Widget quick(IconData icon,String title,String subtitle,VoidCallback onTap)=>Card(margin:EdgeInsets.zero,child:InkWell(onTap:onTap,borderRadius:BorderRadius.circular(12),child:Padding(padding:const EdgeInsets.symmetric(horizontal:7,vertical:11),child:Column(mainAxisAlignment:MainAxisAlignment.center,children:[Icon(icon,color:_blue,size:29),const SizedBox(height:7),Text(title,textAlign:TextAlign.center,maxLines:2,overflow:TextOverflow.ellipsis,style:const TextStyle(fontWeight:FontWeight.w900,fontSize:12.2))]))));
  @override Widget build(BuildContext context){
    final tanks=_sortedFuelUnits(ref?['tanks']);final isAdmin=widget.profile['is_admin']==true;final isManager=widget.profile['is_manager']==true;
    final currentCode='${currentUnit['unit_code']??''}'.trim(),currentName='${currentUnit['unit_name']??''}'.trim();
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
      if(isAdmin)quick(Icons.manage_accounts_rounded,'Usuários','Supervisor, Gerente e Operacional',()=>open(UnifiedUsersV29Screen(referenceData:ref!))),
      if(isAdmin)quick(Icons.history_rounded,'Auditoria','Histórico de alterações',()=>open(const AuditHistoryV28Screen())),
      if(isAdmin)quick(Icons.badge_outlined,'Dados da empresa','Empresa operadora',()=>open(const ReportCompanyAdminScreen())),
      if(isAdmin)quick(Icons.shield_outlined,'Segurança','Senha e proteção do Admin',()=>open(const AdminSecurityV35Screen())),
    ];
    Widget kpi(IconData icon,String label,String value)=>Expanded(child:Container(padding:const EdgeInsets.all(10),decoration:BoxDecoration(color:Colors.white,borderRadius:BorderRadius.circular(12),border:Border.all(color:Colors.black12)),child:Column(children:[Icon(icon,color:_blue,size:22),const SizedBox(height:5),Text(value,maxLines:1,overflow:TextOverflow.ellipsis,style:const TextStyle(fontWeight:FontWeight.w900,fontSize:15)),Text(label,textAlign:TextAlign.center,style:const TextStyle(fontSize:9.5,color:Colors.black54))])));
    return Scaffold(appBar:AppBar(title:const Text('R&C ABASTECIMENTO',style:TextStyle(fontWeight:FontWeight.w900)),actions:[IconButton(onPressed:()=>open(GlobalSearchV28Screen(profile:widget.profile)),tooltip:'Pesquisa global',icon:const Icon(Icons.search_rounded)),IconButton(onPressed:()=>open(AdminCatalogScreen(profile:widget.profile)),tooltip:'Cadastros',icon:const Icon(Icons.menu_rounded)),IconButton(onPressed:()async{await _logoutToLogin(context,widget.onLogout);},tooltip:'Sair',icon:const Icon(Icons.logout_rounded))]),body:ref==null?const Center(child:CircularProgressIndicator()):RefreshIndicator(onRefresh:refresh,child:ListView(padding:const EdgeInsets.all(16),children:[
      GreetingLine(name:'${widget.profile['display_name']}'),
      if(currentCode.isNotEmpty)...[const SizedBox(height:10),Card(child:Padding(padding:const EdgeInsets.all(14),child:Column(crossAxisAlignment:CrossAxisAlignment.stretch,children:[Row(children:[const Icon(Icons.lock_clock_outlined,size:19,color:_blue),const SizedBox(width:7),Expanded(child:Text('Unidade em uso: $currentCode${currentName.isNotEmpty?' • $currentName':''}',style:const TextStyle(fontWeight:FontWeight.w900)))]),const SizedBox(height:10),Row(children:[Expanded(child:OutlinedButton.icon(onPressed:_switchUnit,icon:const Icon(Icons.swap_horiz_rounded),label:const Text('Trocar unidade'))),const SizedBox(width:8),Expanded(child:OutlinedButton.icon(onPressed:_releaseUnit,icon:const Icon(Icons.lock_open_rounded),label:const Text('Liberar unidade')))])]))),],
      const SizedBox(height:8),
      TextField(controller:globalSearch,textInputAction:TextInputAction.search,onSubmitted:(q){if(q.trim().isNotEmpty)open(GlobalSearchV28Screen(profile:widget.profile,initialQuery:q.trim()));},decoration:InputDecoration(labelText:'Pesquisar em todo o sistema',hintText:'Obra, empresa, ativo, placa, NF, CB01, Nº sequencial...',prefixIcon:const Icon(Icons.search_rounded),suffixIcon:IconButton(onPressed:(){final q=globalSearch.text.trim();if(q.isNotEmpty)open(GlobalSearchV28Screen(profile:widget.profile,initialQuery:q));},icon:const Icon(Icons.arrow_forward_rounded)))),
      const SizedBox(height:12),Row(children:[kpi(Icons.inventory_2_outlined,'Estoque atual',_fmtLiters(kpis['stock_liters'])),const SizedBox(width:7),kpi(Icons.water_drop_outlined,'Consumo hoje',_fmtLiters(kpis['fueling_liters_today']))]),const SizedBox(height:7),Row(children:[kpi(Icons.local_gas_station_outlined,'Abastecimentos hoje','${kpis['fueling_count_today']??0}'),const SizedBox(width:7),kpi(Icons.location_city_outlined,'Obras ativas','${kpis['active_works']??0}')]),
      const SizedBox(height:14),GridView.count(shrinkWrap:true,physics:const NeverScrollableScrollPhysics(),crossAxisCount:3,crossAxisSpacing:8,mainAxisSpacing:8,childAspectRatio:.92,children:actions),
      const SizedBox(height:18),Row(children:[const Icon(Icons.water_drop_outlined,color:_blue),const SizedBox(width:7),Text('Saldos em tempo real',style:Theme.of(context).textTheme.titleMedium?.copyWith(fontWeight:FontWeight.w900))]),const SizedBox(height:8),...tanks.map((t)=>Padding(padding:const EdgeInsets.only(bottom:8),child:BalanceCard(tank:t))),const SizedBox(height:12),HomeActionCard(icon:Icons.dashboard_outlined,title:'Painel de combustível',subtitle:'Estoque, NFs, consumo, autonomia, custos e lucros em tempo real',onTap:()=>open(FuelDashboardV23Screen(profile:widget.profile,ref:ref!)))
    ])));
  }
}

'''
s=s[:a]+admin_new+s[b:]

for marker in [
    'with WidgetsBindingObserver',
    'AppLifecycleState.detached',
    "api.claimUnitV31(tankId)",
    'Unidades em uso ficam bloqueadas imediatamente',
    'Map<String,dynamic> currentUnit={};',
    'await api.claimUnitV31(id)',
    'Liberar unidade',
    'Trocar unidade',
    'Preço de venda/L',
    'Preço total • automático e somente leitura',
    "equipment.replaceAll('\\u2022', '-')",
]:
    if marker not in s: raise SystemExit('v38 missing marker: '+marker)

p.write_text(s)
print('V38_UNIT_LOCK_LIFECYCLE_OK')
