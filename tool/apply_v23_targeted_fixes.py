from pathlib import Path
p=Path('lib/main_online.dart')
s=p.read_text()

def rep(a,b,count=1):
    global s
    if a not in s:
        raise SystemExit('anchor missing: '+repr(a[:180]))
    s=s.replace(a,b,count)

# API: obra com responsavel, capacidade do ativo, terceiro sem placa e funcao caminhao-tanque.
rep("""  Future<void> saveWork({int? id, required String name, String? location, int? companyId, bool active = true}) async {
    await client.rpc('rca_save_work_v2', params: {
      'p_id': id,
      'p_name': name,
      'p_location': location,
      'p_company_id': companyId,
      'p_active': active,
    });
  }
""","""  Future<void> saveWork({int? id, required String name, String? location, String? responsible, int? companyId, bool active = true}) async {
    await client.rpc('rca_save_work_v2', params: {
      'p_id': id,
      'p_name': name,
      'p_location': location,
      'p_company_id': companyId,
      'p_active': active,
      'p_responsible': responsible,
    });
  }
""")
rep("""    bool active = true,
    double? comboioCapacityLiters,
  }) async {
""","""    bool active = true,
    double? comboioCapacityLiters,
    double? fuelTankCapacityLiters,
  }) async {
""",1)
rep("""      'p_active': active,
      'p_comboio_capacity_liters': comboioCapacityLiters,
    });
""","""      'p_active': active,
      'p_comboio_capacity_liters': comboioCapacityLiters,
      'p_fuel_tank_capacity_liters': fuelTankCapacityLiters,
    });
""",1)
rep("""  Future<void> saveThirdParty({
    int? id,
    required String plate,
""","""  Future<void> saveThirdParty({
    int? id,
    String? plate,
""")
anchor="""  Future<void> saveThirdParty({
    int? id,
    String? plate,
    String? company,
    String? description,
    String? driverName,
    bool active = true,
  }) async {
    await client.rpc('rca_save_third_party_vehicle', params: {
      'p_id': id,
      'p_plate': plate,
      'p_company_name': company,
      'p_description': description,
      'p_driver_name': driverName,
      'p_active': active,
    });
  }
"""
rep(anchor,anchor+"""

  Future<List<Map<String,dynamic>>> truckRoles() async => _rows(await client.rpc('rca_truck_roles'));
  Future<int?> saveTruckRole({int? tankId, required int machineId, required double capacityLiters, bool active=true}) async {
    final value=await client.rpc('rca_save_truck_role',params:{'p_tank_id':tankId,'p_machine_id':machineId,'p_capacity_liters':capacityLiters,'p_active':active});
    return _intOrNull(value);
  }
  Future<Map<String,dynamic>> removeTruckRole(int tankId) async => _map(await client.rpc('rca_remove_truck_role',params:{'p_tank_id':tankId}));
""")

# Selecao de unidade: caminhão-tanque nao aparece como comboio.
rep("final typeLabel = tank['tank_type'] == 'stationary' ? 'Tanque estacionário' : 'Comboio';","final typeLabel = tank['tank_type'] == 'stationary' ? 'Tanque estacionário' : tank['tank_type'] == 'truck' ? 'Caminhão-tanque' : 'Comboio';")
rep("leading: Icon(tank['tank_type'] == 'stationary' ? Icons.oil_barrel_outlined : Icons.local_shipping_outlined, color: _blue),","leading: Icon(tank['tank_type'] == 'stationary' ? Icons.oil_barrel_outlined : tank['tank_type'] == 'truck' ? Icons.local_shipping_rounded : Icons.local_shipping_outlined, color: _blue),")

# Abastecimento: exibe o responsavel da obra selecionada.
rep("final sm=selected(ms,machine),st=selected(ts,third),hasPlate=", "final sm=selected(ms,machine),st=selected(ts,third),sw=selected(ws,work),hasPlate=",1)
rep("onChanged:(v)=>setState(()=>work=v)),if(widget.source['tank_type']=='comboio')const SizedBox(height:8),", "onChanged:(v)=>setState(()=>work=v)),if(widget.source['tank_type']=='comboio'&&_hasValue(sw?['responsible']))Padding(padding:const EdgeInsets.only(top:6),child:Text('Responsável: ${sw?['responsible']}',style:const TextStyle(fontWeight:FontWeight.w700))),if(widget.source['tank_type']=='comboio')const SizedBox(height:8),",1)

# Catalogo admin.
rep("""      HomeActionCard(icon: Icons.oil_barrel_outlined, title: 'Tanques estacionários', subtitle: 'Cadastrar tanques estacionários e alterar capacidades', onTap: () => Navigator.push(context, MaterialPageRoute(builder: (_) => const TanksAdminScreen()))),
      const SizedBox(height: 10),
""","""      HomeActionCard(icon: Icons.oil_barrel_outlined, title: 'Tanques estacionários', subtitle: 'Cadastrar tanques estacionários e alterar capacidades', onTap: () => Navigator.push(context, MaterialPageRoute(builder: (_) => const TanksAdminScreen()))),
      const SizedBox(height: 10),
      HomeActionCard(icon: Icons.local_shipping_rounded, title: 'Função Caminhão-tanque', subtitle: 'Atribuir, editar ou remover a função de caminhão-tanque de um ativo', onTap: () => Navigator.push(context, MaterialPageRoute(builder: (_) => const TruckFunctionAdminScreen()))),
      const SizedBox(height: 10),
""")
rep("HomeActionCard(icon: Icons.local_shipping_outlined, title: 'Veículos de terceiros', subtitle: 'Cadastrar caminhões alugados por placa e empresa', onTap: () => Navigator.push(context, MaterialPageRoute(builder: (_) => const ThirdPartyAdminScreen()))),","HomeActionCard(icon: Icons.local_shipping_outlined, title: 'Equipamentos de terceiros', subtitle: 'Cadastrar equipamentos com placa ou identificação por descrição', onTap: () => Navigator.push(context, MaterialPageRoute(builder: (_) => const ThirdPartyAdminScreen()))),")

# Obras: responsavel obrigatorio no cadastro.
rep("""    final name = TextEditingController(text: '${item?['name'] ?? ''}');
    final location = TextEditingController(text: '${item?['location'] ?? ''}');
    int? companyId = _intOrNull(item?['contracting_company_id']);
""","""    final name = TextEditingController(text: '${item?['name'] ?? ''}');
    final location = TextEditingController(text: '${item?['location'] ?? ''}');
    final responsible = TextEditingController(text: '${item?['responsible'] ?? ''}');
    int? companyId = _intOrNull(item?['contracting_company_id']);
""")
rep("TextField(controller: name, decoration: const InputDecoration(labelText: 'Nome *')),\n            const SizedBox(height: 10),\n            DropdownButtonFormField<int>(", "TextField(controller: name, decoration: const InputDecoration(labelText: 'Nome *')),\n            const SizedBox(height: 10),\n            TextField(controller: responsible, decoration: const InputDecoration(labelText: 'Responsável *')),\n            const SizedBox(height: 10),\n            DropdownButtonFormField<int>(",1)
rep("if (ok == true && name.text.trim().isNotEmpty && companyId != null) {", "if (ok == true && name.text.trim().isNotEmpty && responsible.text.trim().isNotEmpty && companyId != null) {",1)
rep("location: location.text.trim(),\n        companyId: companyId,", "location: location.text.trim(),\n        responsible: responsible.text.trim(),\n        companyId: companyId,",1)
rep("name.dispose();\n    location.dispose();", "name.dispose();\n    location.dispose();\n    responsible.dispose();",1)
rep("${companyName(x['contracting_company_id'])}\\n${x['location'] ?? ''}", "${companyName(x['contracting_company_id'])}\\nResponsável: ${x['responsible'] ?? '-'}\\n${x['location'] ?? ''}",1)

# Ativos: capacidade do tanque de combustivel.
rep("final capacity = TextEditingController(text: item?['comboio_capacity_liters'] == null ? '' : _num(item?['comboio_capacity_liters']).toStringAsFixed(0));", "final capacity = TextEditingController(text: item?['comboio_capacity_liters'] == null ? '' : _num(item?['comboio_capacity_liters']).toStringAsFixed(0));\n    final fuelCapacity = TextEditingController(text: item?['fuel_tank_capacity_liters'] == null ? '' : _num(item?['fuel_tank_capacity_liters']).toStringAsFixed(0));")
rep("""        ],
        const SizedBox(height: 8), TextField(controller: location, decoration: const InputDecoration(labelText: 'Localização')),
""","""        ],
        const SizedBox(height: 8), TextField(controller: fuelCapacity, keyboardType: const TextInputType.numberWithOptions(decimal: true), decoration: const InputDecoration(labelText: 'Capacidade do tanque de combustível do ativo (litros)')),
        const SizedBox(height: 8), TextField(controller: location, decoration: const InputDecoration(labelText: 'Localização')),
""",1)
rep("await api.saveMachine(id: _intOrNull(item?['id']), assetNumber: number.text.trim(), model: model.text.trim(), plate: plate.text.trim(), type: type.text.trim(), location: location.text.trim(), comboioCapacityLiters: isComboio ? parsed : null);", "final parsedFuel = fuelCapacity.text.trim().isEmpty ? null : double.tryParse(fuelCapacity.text.trim().replaceAll(',', '.'));\n          if (fuelCapacity.text.trim().isNotEmpty && (parsedFuel == null || parsedFuel <= 0)) throw Exception('Informe uma capacidade válida para o tanque de combustível do ativo.');\n          await api.saveMachine(id: _intOrNull(item?['id']), assetNumber: number.text.trim(), model: model.text.trim(), plate: plate.text.trim(), type: type.text.trim(), location: location.text.trim(), comboioCapacityLiters: isComboio ? parsed : null, fuelTankCapacityLiters: parsedFuel);",1)
rep("number.dispose(); model.dispose(); plate.dispose(); type.dispose(); location.dispose(); capacity.dispose();", "number.dispose(); model.dispose(); plate.dispose(); type.dispose(); location.dispose(); capacity.dispose(); fuelCapacity.dispose();",1)
rep("subtitle: Text('Placa: ${x['placa'] ?? '-'} • ${x['localizacao'] ?? ''}'),", "subtitle: Text('Placa: ${x['placa'] ?? '-'} • Tanque: ${x['fuel_tank_capacity_liters']==null?'-':_fmtLiters(x['fuel_tank_capacity_liters'])} • ${x['localizacao'] ?? ''}'),",1)

# Terceiros: placa opcional, descricao obrigatoria quando nao ha placa.
rep("decoration: const InputDecoration(labelText: 'Placa *')", "decoration: const InputDecoration(labelText: 'Placa (quando houver)')",1)
rep("TextField(controller: desc, decoration: const InputDecoration(labelText: 'Descrição'))", "TextField(controller: desc, decoration: const InputDecoration(labelText: 'Descrição / identificação *'))",1)
rep("if (ok == true && plate.text.trim().isNotEmpty) { await api.saveThirdParty(id: _intOrNull(item?['id']), plate: plate.text.trim(), company: company.text.trim(), description: desc.text.trim(), driverName: driver.text.trim()); await load(); }", "if (ok == true) { if (plate.text.trim().isEmpty && desc.text.trim().isEmpty) { if (mounted) ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Informe a placa ou uma descrição que identifique o equipamento.'))); } else { await api.saveThirdParty(id: _intOrNull(item?['id']), plate: plate.text.trim(), company: company.text.trim(), description: desc.text.trim(), driverName: driver.text.trim()); await load(); } }",1)
rep("appBar: AppBar(title: const Text('Veículos de terceiros'))", "appBar: AppBar(title: const Text('Equipamentos de terceiros'))",1)
rep("title: Text('${x['plate']} • ${x['description'] ?? ''}'", "title: Text('${_hasValue(x['plate'])?x['plate']:'Sem placa'} • ${x['description'] ?? ''}'",1)

# Tela de gerenciamento da funcao caminhão-tanque.
marker='class TanksAdminScreen extends StatefulWidget {'
if marker not in s: raise SystemExit('truck marker missing')
truck=r'''class TruckFunctionAdminScreen extends StatefulWidget {
  const TruckFunctionAdminScreen({super.key});
  @override State<TruckFunctionAdminScreen> createState()=>_TruckFunctionAdminScreenState();
}
class _TruckFunctionAdminScreenState extends State<TruckFunctionAdminScreen> {
  List<Map<String,dynamic>> trucks=[];
  List<Map<String,dynamic>> machines=[];
  bool loading=true,busy=false;
  @override void initState(){super.initState();load();}
  Future<void> load() async {
    try {
      final t=await api.truckRoles();
      final r=await api.referenceData();
      if(mounted)setState((){trucks=t;machines=_rows(r['machines']);loading=false;});
    } catch(e) {
      if(mounted){setState(()=>loading=false);ScaffoldMessenger.of(context).showSnackBar(SnackBar(content:Text(_friendlyError(e))));}
    }
  }
  Future<void> edit([Map<String,dynamic>? item]) async {
    int? machineId=_intOrNull(item?['machine_id']);
    final capacity=TextEditingController(text:item==null?'40000':_num(item['capacity_liters']).toStringAsFixed(0));
    bool active=item?['active']!=false;
    final ok=await showDialog<bool>(context:context,builder:(ctx)=>StatefulBuilder(builder:(ctx,setD)=>AlertDialog(
      title:Text(item==null?'Adicionar caminhão-tanque':'Editar função caminhão-tanque'),
      content:SingleChildScrollView(child:Column(mainAxisSize:MainAxisSize.min,children:[
        DropdownButtonFormField<int>(value:machineId,isExpanded:true,decoration:const InputDecoration(labelText:'Ativo *'),items:machines.map((m)=>DropdownMenuItem(value:_intOrNull(m['id']),child:Text('${m['numeroAtivo']} • ${m['modelo']??''}'))).toList(),onChanged:(v)=>setD(()=>machineId=v)),
        const SizedBox(height:10),
        TextField(controller:capacity,keyboardType:const TextInputType.numberWithOptions(decimal:true),decoration:const InputDecoration(labelText:'Capacidade (litros) *')),
        SwitchListTile(contentPadding:EdgeInsets.zero,title:const Text('Função ativa'),value:active,onChanged:(v)=>setD(()=>active=v)),
      ])),
      actions:[TextButton(onPressed:()=>Navigator.pop(ctx,false),child:const Text('Cancelar')),FilledButton(onPressed:()=>Navigator.pop(ctx,true),child:const Text('Salvar'))]
    )));
    if(ok==true){
      final cap=double.tryParse(capacity.text.trim().replaceAll(',','.'));
      if(machineId==null||cap==null||cap<=0){
        if(mounted)ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content:Text('Selecione o ativo e informe uma capacidade válida.')));
      }else{
        setState(()=>busy=true);
        try{await api.saveTruckRole(tankId:_intOrNull(item?['id']),machineId:machineId!,capacityLiters:cap,active:active);await load();if(mounted)ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content:Text('Função caminhão-tanque atualizada.')));}catch(e){if(mounted)ScaffoldMessenger.of(context).showSnackBar(SnackBar(content:Text(_friendlyError(e))));}finally{if(mounted)setState(()=>busy=false);}
      }
    }
    capacity.dispose();
  }
  Future<void> remove(Map<String,dynamic> item) async {
    final id=_intOrNull(item['id']); if(id==null)return;
    final ok=await showDialog<bool>(context:context,builder:(ctx)=>AlertDialog(title:Text('Remover função de ${item['machine_asset_number']??item['code']}?'),content:const Text('O ativo será preservado. Se houver histórico, a estrutura será apenas desativada para manter a rastreabilidade.'),actions:[TextButton(onPressed:()=>Navigator.pop(ctx,false),child:const Text('Cancelar')),FilledButton(onPressed:()=>Navigator.pop(ctx,true),child:const Text('Remover função'))]));
    if(ok!=true)return;
    setState(()=>busy=true);
    try{final r=await api.removeTruckRole(id);await load();if(mounted)ScaffoldMessenger.of(context).showSnackBar(SnackBar(content:Text(r['action']=='deleted'?'Função removida.':'Função desativada e histórico preservado.')));}catch(e){if(mounted)ScaffoldMessenger.of(context).showSnackBar(SnackBar(content:Text(_friendlyError(e))));}finally{if(mounted)setState(()=>busy=false);}
  }
  @override Widget build(BuildContext context)=>Scaffold(
    appBar:AppBar(title:const Text('Função Caminhão-tanque')),
    floatingActionButton:FloatingActionButton.extended(onPressed:busy?null:()=>edit(),icon:const Icon(Icons.add),label:const Text('Adicionar')),
    body:loading?const Center(child:CircularProgressIndicator()):RefreshIndicator(onRefresh:load,child:ListView(padding:const EdgeInsets.fromLTRB(12,12,12,90),children:[
      if(trucks.isEmpty)const Padding(padding:EdgeInsets.all(32),child:Text('Nenhum caminhão-tanque configurado.',textAlign:TextAlign.center)),
      ...trucks.map((x)=>Card(child:ListTile(leading:const Icon(Icons.local_shipping_rounded,color:_blue),title:Text('${x['machine_asset_number']??'Sem ativo'} • ${x['code']}',style:const TextStyle(fontWeight:FontWeight.w900)),subtitle:Text('${x['machine_model']??''}\nCapacidade: ${_fmtLiters(x['capacity_liters'])} • Saldo: ${_fmtLiters(x['current_balance_liters'])} • ${x['active']==true?'Ativo':'Inativo'}'),isThreeLine:true,onTap:busy?null:()=>edit(x),trailing:PopupMenuButton<String>(enabled:!busy,onSelected:(v){if(v=='edit')edit(x);if(v=='remove')remove(x);},itemBuilder:(_)=>const [PopupMenuItem(value:'edit',child:Text('Editar')),PopupMenuItem(value:'remove',child:Text('Remover função'))])))),
    ]))
  );
}

'''
s=s.replace(marker,truck+marker,1)

p.write_text(s)
print('targeted patch applied:',len(s),'chars')
