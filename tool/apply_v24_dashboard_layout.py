from pathlib import Path
p=Path('lib/main_online.dart')
s=p.read_text()
start=s.index('class AdminHomeScreen extends StatefulWidget {')
end=s.index('class AdminRecordsScreen extends StatefulWidget {', start)
new=r'''class AdminHomeScreen extends StatefulWidget {
  final Map<String, dynamic> profile;
  final Future<void> Function() onLogout;
  const AdminHomeScreen({super.key, required this.profile, required this.onLogout});

  @override
  State<AdminHomeScreen> createState() => _AdminHomeScreenState();
}

class _AdminHomeScreenState extends State<AdminHomeScreen> {
  Map<String, dynamic>? ref;
  Timer? timer;
  bool running = false;
  @override
  void initState() { super.initState(); refresh(); timer = Timer.periodic(const Duration(seconds: 2), (_) => refresh()); }
  @override
  void dispose() { timer?.cancel(); super.dispose(); }
  Future<void> refresh() async {
    if (running) return; running = true;
    try { final d = await api.referenceData(); if (mounted) setState(() => ref = d); } catch (_) {} finally { running = false; }
  }

  @override
  Widget build(BuildContext context) {
    final tanks = _sortedFuelUnits(ref?['tanks']);
    final isAdmin = widget.profile['is_admin']==true;
    final isManager = widget.profile['is_manager']==true;
    void open(Widget page) => Navigator.push(context, MaterialPageRoute(builder: (_) => page));
    Widget quick(IconData icon,String title,String subtitle,VoidCallback onTap) => Card(
      margin: EdgeInsets.zero,
      child: InkWell(
        onTap:onTap,
        borderRadius:BorderRadius.circular(12),
        child:Padding(
          padding:const EdgeInsets.symmetric(horizontal:8,vertical:12),
          child:Column(mainAxisAlignment:MainAxisAlignment.center,children:[
            Icon(icon,color:_navy,size:30),
            const SizedBox(height:7),
            Text(title,textAlign:TextAlign.center,maxLines:2,overflow:TextOverflow.ellipsis,style:const TextStyle(fontWeight:FontWeight.w900,fontSize:12.5)),
            const SizedBox(height:3),
            Text(subtitle,textAlign:TextAlign.center,maxLines:2,overflow:TextOverflow.ellipsis,style:const TextStyle(fontSize:9.8,color:Colors.black54)),
          ]),
        ),
      ),
    );

    final actions=<Widget>[
      quick(Icons.local_gas_station_rounded,'Novo abastecimento','Selecionar unidade',()=>open(UnitSelectionScreen(profile:widget.profile,onLogout:widget.onLogout))),
      quick(Icons.swap_horiz_rounded,'Transferir','Entre unidades',()=>open(UnitSelectionScreen(profile:widget.profile,onLogout:widget.onLogout))),
      quick(Icons.receipt_long_rounded,'Recebimento (NF)','Entrada de combustível',()=>open(UnitSelectionScreen(profile:widget.profile,onLogout:widget.onLogout))),
      quick(Icons.assignment_outlined,'Meus registros','Operações deste login',()=>open(const MyOnlineMovementsScreen())),
      quick(Icons.manage_search_rounded,'Registros','Pesquisa e filtros',()=>open(AdminRecordsScreen(referenceData:ref!))),
      if(isAdmin||isManager) quick(Icons.folder_copy_outlined,'Relatórios','PDFs e obras',()=>open(const GeneratedReportsV23Screen())),
      quick(Icons.location_city_outlined,'Obras','Cliente e responsável',()=>open(WorksAdminScreen(profile:widget.profile))),
      if(isAdmin) quick(Icons.business_outlined,'Empresas','Clientes, locadoras e fornecedores',()=>open(const CompaniesAdminScreen())),
      quick(Icons.precision_manufacturing_outlined,'Ativos','Equipamentos próprios',()=>open(const MachinesAdminScreen())),
      quick(Icons.handyman_outlined,'Equip. terceiros','Proprietária / locadora',()=>open(const ThirdPartyAdminScreen())),
      if(isAdmin) quick(Icons.oil_barrel_outlined,'Tanques estacionários','Capacidade e saldo',()=>open(const TanksAdminScreen())),
      if(isAdmin) quick(Icons.local_shipping_rounded,'Caminhão-tanque','Função do ativo',()=>open(const TruckFunctionAdminScreen())),
      if(isAdmin) quick(Icons.manage_accounts_rounded,'Usuários','Operadores',()=>open(AdminUsersOnlineScreen(referenceData:ref!))),
      if(isAdmin) quick(Icons.admin_panel_settings_outlined,'Permissões','Supervisor e gerente',()=>open(const StaffPermissionsV23Screen())),
      if(isAdmin) quick(Icons.badge_outlined,'Dados da empresa','Empresa operadora',()=>open(const ReportCompanyAdminScreen())),
    ];

    return Scaffold(
      appBar: AppBar(
        title: const Text('R&C ABASTECIMENTO',style:TextStyle(fontWeight:FontWeight.w900)),
        actions:[
          IconButton(onPressed:()=>open(AdminCatalogScreen(profile:widget.profile)),tooltip:'Cadastros',icon:const Icon(Icons.menu_rounded)),
          IconButton(onPressed:()async{await _logoutToLogin(context,widget.onLogout);},tooltip:'Sair',icon:const Icon(Icons.logout_rounded)),
        ],
      ),
      body:ref==null?const Center(child:CircularProgressIndicator()):RefreshIndicator(
        onRefresh:refresh,
        child:ListView(
          padding:const EdgeInsets.all(16),
          children:[
            GreetingLine(name:'${widget.profile['display_name']}'),
            const SizedBox(height:6),
            Text(isAdmin?'Acesso administrativo completo.':isManager?'Acesso de gerente.':'Acesso de supervisor.',style:const TextStyle(color:Colors.black54)),
            const SizedBox(height:14),
            GridView.count(
              shrinkWrap:true,
              physics:const NeverScrollableScrollPhysics(),
              crossAxisCount:3,
              crossAxisSpacing:8,
              mainAxisSpacing:8,
              childAspectRatio:.92,
              children:actions,
            ),
            const SizedBox(height:18),
            Row(children:[const Icon(Icons.water_drop_outlined,color:_blue),const SizedBox(width:7),Text('Saldos em tempo real',style:Theme.of(context).textTheme.titleMedium?.copyWith(fontWeight:FontWeight.w900))]),
            const SizedBox(height:8),
            ...tanks.map((t)=>Padding(padding:const EdgeInsets.only(bottom:8),child:BalanceCard(tank:t))),
            const SizedBox(height:12),
            HomeActionCard(icon:Icons.dashboard_outlined,title:'Painel de combustível',subtitle:'Estoque, NFs, consumo, autonomia, custos e lucros em tempo real',onTap:()=>open(FuelDashboardV23Screen(profile:widget.profile,ref:ref!))),
          ],
        ),
      ),
    );
  }
}

'''
s=s[:start]+new+s[end:]
p.write_text(s)
print('dashboard layout staged',len(s))
