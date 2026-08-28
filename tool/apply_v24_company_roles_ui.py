from pathlib import Path
p=Path('lib/main_online.dart')
s=p.read_text()

def rep(old,new,label):
    global s
    if old not in s:
        raise SystemExit(f'anchor missing: {label}')
    s=s.replace(old,new,1)

# API: consulta por papel e gravação v2 com papéis explícitos.
rep(
"  Future<List<Map<String, dynamic>>> managedCompanies() async => _rows(await client.rpc('rca_managed_companies'));\n\n  Future<void> saveManagedCompany({",
"  Future<List<Map<String, dynamic>>> managedCompanies() async => _rows(await client.rpc('rca_managed_companies'));\n  Future<List<Map<String, dynamic>>> companiesByRole(String role) async => _rows(await client.rpc('rca_companies_by_role', params: {'p_role': role}));\n\n  Future<void> saveManagedCompany({",
'api companiesByRole')

old_sig="""  Future<void> saveManagedCompany({
    int? id,
    required String name,
    String? subtitle,
    String? document,
    String? zipCode,
    String? street,
    String? streetNumber,
    String? complement,
    String? neighborhood,
    String? city,
    String? state,
    bool active = true,
  }) async {
    await client.rpc('rca_save_managed_company', params: {
      'p_id': id,
      'p_name': name,
      'p_subtitle': subtitle,
      'p_document': document,
      'p_zip_code': zipCode,
      'p_street': street,
      'p_street_number': streetNumber,
      'p_complement': complement,
      'p_neighborhood': neighborhood,
      'p_city': city,
      'p_state': state,
      'p_active': active,
    });
  }
"""
new_sig="""  Future<void> saveManagedCompany({
    int? id,
    required String name,
    String? subtitle,
    String? document,
    String? zipCode,
    String? street,
    String? streetNumber,
    String? complement,
    String? neighborhood,
    String? city,
    String? state,
    bool active = true,
    required bool isClient,
    required bool isEquipmentOwner,
    required bool isFuelSupplier,
  }) async {
    await client.rpc('rca_save_managed_company_v2', params: {
      'p_id': id,
      'p_name': name,
      'p_subtitle': subtitle,
      'p_document': document,
      'p_zip_code': zipCode,
      'p_street': street,
      'p_street_number': streetNumber,
      'p_complement': complement,
      'p_neighborhood': neighborhood,
      'p_city': city,
      'p_state': state,
      'p_active': active,
      'p_is_client': isClient,
      'p_is_equipment_owner': isEquipmentOwner,
      'p_is_fuel_supplier': isFuelSupplier,
    });
  }
"""
rep(old_sig,new_sig,'saveManagedCompany v2')

# Admin Mais: nomenclatura sem ambiguidade.
s=s.replace("title: 'Empresas vinculadas',\n          subtitle: 'Empresas de obras e proprietárias de equipamentos de terceiros',",
            "title: 'Empresas',\n          subtitle: 'Clientes/contratantes, proprietárias/locadoras e fornecedores de combustível',")

# Tela Empresas inteira.
start=s.index('class CompaniesAdminScreen extends StatefulWidget {')
end=s.index('class AdminCatalogScreen extends StatelessWidget {', start)
new_companies=r'''class CompaniesAdminScreen extends StatefulWidget {
  const CompaniesAdminScreen({super.key});

  @override
  State<CompaniesAdminScreen> createState() => _CompaniesAdminScreenState();
}

class _CompaniesAdminScreenState extends State<CompaniesAdminScreen> {
  List<Map<String, dynamic>>? items;
  bool busy = false;

  @override
  void initState() { super.initState(); load(); }

  Future<void> load() async {
    try {
      final x = await api.managedCompanies();
      if (mounted) setState(() => items = x);
    } catch (e) {
      if (mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(_friendlyError(e))));
    }
  }

  String addressOf(Map<String, dynamic> x) {
    final first = [x['street'], x['street_number'], x['complement']].where((v) => _hasValue(v)).join(', ');
    final second = [x['neighborhood'], x['city']].where((v) => _hasValue(v)).join(' • ');
    final state = _hasValue(x['state']) ? ' - ${x['state']}' : '';
    final zip = _hasValue(x['zip_code']) ? ', ${x['zip_code']}' : '';
    final cityPart = second.isEmpty ? '' : '$second$state';
    return [first, cityPart].where((v) => v.isNotEmpty).join(' • ') + zip;
  }

  List<String> rolesOf(Map<String,dynamic> x) => [
    if (x['is_client'] == true) 'Cliente / Contratante',
    if (x['is_equipment_owner'] == true) 'Proprietária / Locadora',
    if (x['is_fuel_supplier'] == true) 'Fornecedor de combustível',
  ];

  Future<void> edit([Map<String, dynamic>? item]) async {
    final name = TextEditingController(text: '${item?['name'] ?? ''}');
    final subtitle = TextEditingController(text: '${item?['subtitle'] ?? ''}');
    final document = TextEditingController(text: '${item?['document'] ?? ''}');
    final zip = TextEditingController(text: '${item?['zip_code'] ?? ''}');
    final street = TextEditingController(text: '${item?['street'] ?? ''}');
    final number = TextEditingController(text: '${item?['street_number'] ?? ''}');
    final complement = TextEditingController(text: '${item?['complement'] ?? ''}');
    final neighborhood = TextEditingController(text: '${item?['neighborhood'] ?? ''}');
    final city = TextEditingController(text: '${item?['city'] ?? ''}');
    final state = TextEditingController(text: '${item?['state'] ?? ''}');
    var active = item?['active'] != false;
    var isClient = item?['is_client'] == true;
    var isEquipmentOwner = item?['is_equipment_owner'] == true;
    var isFuelSupplier = item?['is_fuel_supplier'] == true;

    final ok = await showDialog<bool>(
      context: context,
      builder: (ctx) => StatefulBuilder(
        builder: (ctx, setDialogState) => AlertDialog(
          title: Text(item == null ? 'Cadastrar empresa' : 'Editar empresa'),
          content: SizedBox(
            width: 540,
            child: SingleChildScrollView(
              child: Column(mainAxisSize: MainAxisSize.min, crossAxisAlignment: CrossAxisAlignment.stretch, children: [
                const Text('Tipo de relação', style: TextStyle(fontWeight: FontWeight.w900, color: _navy)),
                const SizedBox(height: 4),
                const Text('A mesma empresa pode exercer mais de uma função no sistema.', style: TextStyle(fontSize: 12, color: Colors.black54)),
                CheckboxListTile(contentPadding: EdgeInsets.zero, dense: true, value: isClient, onChanged: (v) => setDialogState(() => isClient = v == true), title: const Text('Cliente / Contratante'), subtitle: const Text('Empresa para quem a obra é executada e que recebe/compra o serviço ou combustível.')),
                CheckboxListTile(contentPadding: EdgeInsets.zero, dense: true, value: isEquipmentOwner, onChanged: (v) => setDialogState(() => isEquipmentOwner = v == true), title: const Text('Proprietária / Locadora de equipamento'), subtitle: const Text('Empresa externa proprietária do equipamento contratado.')),
                CheckboxListTile(contentPadding: EdgeInsets.zero, dense: true, value: isFuelSupplier, onChanged: (v) => setDialogState(() => isFuelSupplier = v == true), title: const Text('Fornecedor de combustível'), subtitle: const Text('Empresa/distribuidora que fornece combustível e emite a NF.')),
                const Divider(height: 20),
                TextField(controller: name, onChanged: (_) => setDialogState(() {}), decoration: const InputDecoration(labelText: 'Nome da empresa *')),
                const SizedBox(height: 9),
                TextField(controller: subtitle, decoration: const InputDecoration(labelText: 'Subtítulo / segmento', hintText: 'Ex.: Engenharia, Locação, Distribuidora')),
                const SizedBox(height: 9),
                TextField(controller: document, keyboardType: TextInputType.number, decoration: const InputDecoration(labelText: 'CNPJ')),
                const SizedBox(height: 9),
                TextField(controller: zip, keyboardType: TextInputType.number, decoration: const InputDecoration(labelText: 'CEP')),
                const SizedBox(height: 9),
                TextField(controller: street, decoration: const InputDecoration(labelText: 'Logradouro')),
                const SizedBox(height: 9),
                Row(children: [
                  Expanded(flex: 2, child: TextField(controller: number, decoration: const InputDecoration(labelText: 'Número'))),
                  const SizedBox(width: 9),
                  Expanded(flex: 3, child: TextField(controller: complement, decoration: const InputDecoration(labelText: 'Complemento'))),
                ]),
                const SizedBox(height: 9),
                TextField(controller: neighborhood, decoration: const InputDecoration(labelText: 'Bairro')),
                const SizedBox(height: 9),
                Row(children: [
                  Expanded(flex: 4, child: TextField(controller: city, decoration: const InputDecoration(labelText: 'Cidade'))),
                  const SizedBox(width: 9),
                  Expanded(child: TextField(controller: state, textCapitalization: TextCapitalization.characters, maxLength: 2, decoration: const InputDecoration(labelText: 'UF', counterText: ''))),
                ]),
                SwitchListTile.adaptive(contentPadding: EdgeInsets.zero, title: const Text('Empresa ativa'), value: active, onChanged: (v) => setDialogState(() => active = v)),
              ]),
            ),
          ),
          actions: [
            TextButton(onPressed: () => Navigator.pop(ctx, false), child: const Text('Cancelar')),
            FilledButton(onPressed: name.text.trim().isEmpty || !(isClient || isEquipmentOwner || isFuelSupplier) ? null : () => Navigator.pop(ctx, true), child: const Text('Salvar')),
          ],
        ),
      ),
    );

    if (ok == true && name.text.trim().isNotEmpty) {
      setState(() => busy = true);
      try {
        await api.saveManagedCompany(
          id: _intOrNull(item?['id']), name: name.text.trim(), subtitle: subtitle.text.trim(), document: document.text.trim(),
          zipCode: zip.text.trim(), street: street.text.trim(), streetNumber: number.text.trim(), complement: complement.text.trim(),
          neighborhood: neighborhood.text.trim(), city: city.text.trim(), state: state.text.trim(), active: active,
          isClient: isClient, isEquipmentOwner: isEquipmentOwner, isFuelSupplier: isFuelSupplier,
        );
        await load();
        if (mounted) ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Empresa salva com seus tipos de relação ✓')));
      } catch (e) {
        if (mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(_friendlyError(e))));
      } finally { if (mounted) setState(() => busy = false); }
    }
    for (final c in [name, subtitle, document, zip, street, number, complement, neighborhood, city, state]) { c.dispose(); }
  }

  @override
  Widget build(BuildContext context) => Scaffold(
    appBar: AppBar(title: const Text('Empresas')),
    floatingActionButton: FloatingActionButton.extended(onPressed: busy ? null : () => edit(), icon: const Icon(Icons.add_business_outlined), label: const Text('Nova empresa')),
    body: items == null ? const Center(child: CircularProgressIndicator()) : RefreshIndicator(
      onRefresh: load,
      child: ListView(
        padding: const EdgeInsets.fromLTRB(12, 12, 12, 90),
        children: [
          const Card(child: ListTile(leading: Icon(Icons.info_outline_rounded, color: _blue), title: Text('Um cadastro, vários papéis'), subtitle: Text('Cadastre cada empresa apenas uma vez e marque se ela é Cliente/Contratante, Proprietária/Locadora e/ou Fornecedor de combustível.'))),
          if (items!.isEmpty) const Padding(padding: EdgeInsets.only(top: 120), child: Center(child: Text('Nenhuma empresa cadastrada.'))),
          ...items!.map((x) {
            final roles = rolesOf(x);
            final address = addressOf(x);
            return Card(child: InkWell(onTap: busy ? null : () => edit(x), borderRadius: BorderRadius.circular(12), child: Padding(padding: const EdgeInsets.all(14), child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
              Row(children: [CircleAvatar(child: Icon(x['is_fuel_supplier']==true ? Icons.local_gas_station_rounded : x['is_equipment_owner']==true ? Icons.precision_manufacturing_outlined : Icons.business_rounded)), const SizedBox(width: 10), Expanded(child: Text('${x['name']}', style: const TextStyle(fontWeight: FontWeight.w900, fontSize: 16))), Icon(x['active']==true ? Icons.check_circle_rounded : Icons.pause_circle_outline_rounded, color: x['active']==true ? Colors.green : Colors.grey), const SizedBox(width: 6), const Icon(Icons.chevron_right_rounded)]),
              const SizedBox(height: 8),
              Wrap(spacing: 6, runSpacing: 6, children: roles.isEmpty ? [const Chip(label: Text('Sem função definida'))] : roles.map((r) => Chip(label: Text(r))).toList()),
              if (_hasValue(x['document'])) Padding(padding: const EdgeInsets.only(top: 6), child: Text('CNPJ: ${x['document']}')),
              if (address.isNotEmpty) Padding(padding: const EdgeInsets.only(top: 3), child: Text(address, style: const TextStyle(color: Colors.black54))),
            ]))));
          }),
        ],
      ),
    ),
  );
}

'''
s=s[:start]+new_companies+s[end:]

# Catálogo de cadastros: inclui Empresas explicitamente e ordem mais clara.
start=s.index('class AdminCatalogScreen extends StatelessWidget {')
end=s.index('class TruckFunctionAdminScreen extends StatefulWidget {', start)
new_catalog=r'''class AdminCatalogScreen extends StatelessWidget {
  final Map<String,dynamic> profile;
  const AdminCatalogScreen({super.key,required this.profile});
  @override
  Widget build(BuildContext context) => Scaffold(
    appBar: AppBar(title: const Text('Cadastros')),
    body: ListView(padding: const EdgeInsets.all(16), children: [
      HomeActionCard(icon: Icons.badge_outlined, title: 'Dados da empresa', subtitle: 'Sua empresa operadora: identificação institucional usada nos PDFs e relatórios', onTap: () => Navigator.push(context, MaterialPageRoute(builder: (_) => const ReportCompanyAdminScreen()))),
      const SizedBox(height: 10),
      HomeActionCard(icon: Icons.business_outlined, title: 'Empresas', subtitle: 'Clientes/contratantes, proprietárias/locadoras e fornecedores de combustível', onTap: () => Navigator.push(context, MaterialPageRoute(builder: (_) => const CompaniesAdminScreen()))),
      const SizedBox(height: 10),
      HomeActionCard(icon: Icons.location_city_outlined, title: 'Obras', subtitle: 'Vincular cada obra à empresa cliente/contratante e ao responsável da obra', onTap: () => Navigator.push(context, MaterialPageRoute(builder: (_) => WorksAdminScreen(profile:profile)))),
      const SizedBox(height: 10),
      HomeActionCard(icon: Icons.precision_manufacturing_outlined, title: 'Ativos próprios', subtitle: 'Equipamentos que pertencem à sua empresa', onTap: () => Navigator.push(context, MaterialPageRoute(builder: (_) => const MachinesAdminScreen()))),
      const SizedBox(height: 10),
      HomeActionCard(icon: Icons.handyman_outlined, title: 'Equipamentos de terceiros', subtitle: 'Equipamentos contratados e sua empresa proprietária/locadora', onTap: () => Navigator.push(context, MaterialPageRoute(builder: (_) => const ThirdPartyAdminScreen()))),
      const SizedBox(height: 10),
      HomeActionCard(icon: Icons.oil_barrel_outlined, title: 'Tanques estacionários', subtitle: 'Cadastrar tanques estacionários e alterar capacidades', onTap: () => Navigator.push(context, MaterialPageRoute(builder: (_) => const TanksAdminScreen()))),
      const SizedBox(height: 10),
      HomeActionCard(icon: Icons.local_shipping_rounded, title: 'Função Caminhão-tanque', subtitle: 'Atribuir, editar ou remover a função de caminhão-tanque de um ativo', onTap: () => Navigator.push(context, MaterialPageRoute(builder: (_) => const TruckFunctionAdminScreen()))),
    ]),
  );
}

'''
s=s[:start]+new_catalog+s[end:]

# Dados da empresa: explicita que é a operadora/prestadora.
s=s.replace("title:Text('Cadastro institucional'),subtitle:Text('Estes dados ficam salvos no sistema e são carregados aqui sempre que você abrir esta página. Eles são usados na identificação dos PDFs e relatórios.')",
            "title:Text('Sua empresa (Operadora)'),subtitle:Text('É a empresa que opera o R&C, presta a mão de obra, utiliza equipamentos próprios e vende/fornece combustível ao cliente da obra. Estes dados identificam os PDFs e relatórios.')")
s=s.replace("InputDecoration(labelText: 'Empresa *')", "InputDecoration(labelText: 'Nome empresarial *')", 1)
s=s.replace("InputDecoration(labelText: 'Texto abaixo do nome', hintText: 'Equipamentos')", "InputDecoration(labelText: 'Texto abaixo do nome (exibido nos documentos)', hintText: 'Engenharia')", 1)

# Obras: empresa cliente/contratante, nunca 'empresa da obra'.
s=s.replace("items:companies.where((x)=>x['active']!=false).map((c)=>DropdownMenuItem", "items:companies.where((x)=>x['active']!=false && x['is_client']==true).map((c)=>DropdownMenuItem")
s=s.replace("labelText:'Empresa da obra *'", "labelText:'Empresa cliente / contratante *'")
s=s.replace("Preenchimento obrigatório: Empresa da obra", "Preenchimento obrigatório: Empresa cliente / contratante")
s=s.replace("Empresa da obra: ${x['company_name']??companyName(x['contracting_company_id'])}", "Empresa cliente/contratante: ${x['company_name']??companyName(x['contracting_company_id'])}")
s=s.replace("title:Text('Cadastre uma empresa vinculada'),subtitle:Text('A empresa da obra é independente do cadastro institucional e continuará disponível mesmo depois da finalização da obra.')",
            "title:Text('Cadastre uma empresa cliente/contratante'),subtitle:Text('A obra deve ser vinculada à empresa para quem o serviço é executado. O responsável da obra continua sendo uma pessoa, em campo separado.')")

# Terceiros: somente empresas marcadas como proprietária/locadora.
s=s.replace("final c=List<Map<String,dynamic>>.from(r[1] as List<Map<String,dynamic>>)..removeWhere((x)=>x['active']==false);",
            "final c=List<Map<String,dynamic>>.from(r[1] as List<Map<String,dynamic>>)..removeWhere((x)=>x['active']==false || x['is_equipment_owner']!=true);")
s=s.replace("Nenhuma empresa vinculada cadastrada. Cadastre a empresa proprietária antes do equipamento.", "Nenhuma empresa Proprietária / Locadora cadastrada. Cadastre a empresa e marque esse tipo de relação antes do equipamento.")
s=s.replace("labelText:'Empresa proprietária do equipamento *'", "labelText:'Empresa proprietária / locadora *'")
s=s.replace("Preenchimento obrigatório: Empresa proprietária do equipamento", "Preenchimento obrigatório: Empresa proprietária / locadora")
s=s.replace("Empresa proprietária: ${x['company_name']??'Não informada'}", "Empresa / locadora: ${x['company_name']??'Não informada'}")
s=s.replace("title:Text('Nenhuma empresa proprietária cadastrada'),subtitle:Text('Cadastre a empresa na área “Empresas vinculadas” antes de cadastrar o equipamento de terceiros.')",
            "title:Text('Nenhuma proprietária / locadora cadastrada'),subtitle:Text('Cadastre em “Empresas” e marque o tipo de relação “Proprietária / Locadora de equipamento”.')")

# Recebimento de combustível/NF: fornecedor selecionado do cadastro Empresas.
start=s.index('class RefineryLoadV23Screen extends StatefulWidget {')
end=s.index('class RefineryToTeV23Screen extends StatefulWidget {', start)
new_refinery=r'''class RefineryLoadV23Screen extends StatefulWidget {
  final Map<String,dynamic> truck;
  const RefineryLoadV23Screen({super.key,required this.truck});
  @override State<RefineryLoadV23Screen> createState()=>_RefineryLoadV23ScreenState();
}
class _RefineryLoadV23ScreenState extends State<RefineryLoadV23Screen> {
  final nf=TextEditingController(),liters=TextEditingController(),cost=TextEditingController(),batch=TextEditingController(),notes=TextEditingController();
  String fuel='Diesel';
  XFile? truckPlatePhoto,invoicePhoto;
  List<Map<String,dynamic>> suppliers=[];
  Map<String,dynamic> buyerCompany={};
  int? supplierId;
  bool busy=false,loadingRefs=true;
  String step='Salvar recebimento';

  @override void initState(){super.initState();loadRefs();}
  Future<void> loadRefs() async {
    try {
      final r=await Future.wait<dynamic>([api.companiesByRole('fuel_supplier'),api.reportCompany()]);
      if(mounted)setState((){suppliers=List<Map<String,dynamic>>.from(r[0] as List<Map<String,dynamic>>);buyerCompany=_map(r[1]);supplierId=suppliers.length==1?_intOrNull(suppliers.first['id']):null;loadingRefs=false;});
    } catch(e) {
      if(mounted){setState(()=>loadingRefs=false);ScaffoldMessenger.of(context).showSnackBar(SnackBar(content:Text('Erro ao carregar empresas: ${_friendlyError(e)}')));}
    }
  }
  String supplierName(){for(final x in suppliers){if(_intOrNull(x['id'])==supplierId)return '${x['name']}';}return '';}
  Future<XFile?> camera()=>ImagePicker().pickImage(source:ImageSource.camera,imageQuality:78,maxWidth:1800);
  void message(String value)=>ScaffoldMessenger.of(context).showSnackBar(SnackBar(content:Text(value)));

  Future<void> submit() async {
    if(busy)return;
    final volume=double.tryParse(liters.text.trim().replaceAll(',','.'));
    final unitCost=double.tryParse(cost.text.trim().replaceAll(',','.'));
    final supplier=supplierName();
    if(nf.text.trim().isEmpty){message('Preenchimento obrigatório: Número da Nota Fiscal');return;}
    if(supplierId==null||supplier.isEmpty){message('Preenchimento obrigatório: Fornecedor do combustível');return;}
    if(volume==null||volume<=0){message('Preenchimento obrigatório: Volume recebido');return;}
    if(unitCost==null||unitCost<0){message('Preenchimento obrigatório: Preço de compra por litro');return;}
    if(truckPlatePhoto==null){message('Foto da placa do caminhão-tanque obrigatória');return;}
    if(invoicePhoto==null){message('Foto legível da Nota Fiscal obrigatória');return;}
    final ok=await showDialog<bool>(context:context,builder:(ctx)=>AlertDialog(
      title:const Text('Confirmar recebimento de combustível?'),
      content:Column(mainAxisSize:MainAxisSize.min,crossAxisAlignment:CrossAxisAlignment.start,children:[
        Text('Empresa compradora: ${buyerCompany['company_name']??'-'}',style:const TextStyle(fontWeight:FontWeight.w700)),
        Text('Fornecedor do combustível: $supplier'),
        const SizedBox(height:8),Text('Caminhão-tanque: ${widget.truck['code']} • ${widget.truck['name']}'),Text('Nota Fiscal: ${nf.text.trim()}'),Text('Combustível: $fuel'),Text('Volume recebido: ${_fmtLiters(volume)}'),Text('Preço de compra/L: ${_fmtMoney(unitCost)}'),
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
      final r=await api.refineryLoadV22(truckTankId:_intOrNull(widget.truck['id'])!,liters:volume,supplier:supplier,invoice:nf.text.trim(),unitCost:unitCost,fuelType:fuel,truckPlatePhoto:photos[0],invoicePhoto:photos[1],batch:batch.text.trim(),notes:notes.text.trim());
      if(!mounted)return;
      message('NF ${r['invoice_number']} registrada com sucesso ✓ • ${_fmtLiters(r['liters'])}');
      Navigator.pop(context,true);
    }catch(e){if(mounted)message('Erro ao registrar recebimento: ${_friendlyError(e)}');}
    finally{if(mounted)setState((){busy=false;step='Salvar recebimento';});}
  }

  @override void dispose(){for(final c in [nf,liters,cost,batch,notes]){c.dispose();}super.dispose();}
  @override Widget build(BuildContext c)=>Scaffold(
    appBar:AppBar(title:const Text('Recebimento de combustível / NF')),
    body:loadingRefs?const Center(child:CircularProgressIndicator()):ListView(padding:const EdgeInsets.all(18),children:[
      Card(child:ListTile(leading:const Icon(Icons.business_rounded,color:_blue),title:const Text('Empresa compradora'),subtitle:Text('${buyerCompany['company_name']??'-'}\nSua empresa operadora recebe o combustível e o incorpora ao estoque.'))),
      const SizedBox(height:8),
      Text('${widget.truck['code']} • ${widget.truck['name']}',style:Theme.of(c).textTheme.titleLarge?.copyWith(fontWeight:FontWeight.w900)),
      const SizedBox(height:5),const Text('Toda chegada entra primeiro pela Nota Fiscal. O fornecedor é selecionado do cadastro “Empresas” e deve estar marcado como “Fornecedor de combustível”.'),
      const SizedBox(height:14),
      DropdownButtonFormField<int>(value:supplierId,isExpanded:true,decoration:const InputDecoration(labelText:'Fornecedor do combustível *'),items:suppliers.map((x)=>DropdownMenuItem(value:_intOrNull(x['id']),child:Text('${x['name']}'))).toList(),onChanged:busy?null:(v)=>setState(()=>supplierId=v)),
      if(suppliers.isEmpty) const Padding(padding:EdgeInsets.only(top:8),child:Card(child:ListTile(leading:Icon(Icons.warning_amber_rounded,color:Colors.orange),title:Text('Nenhum fornecedor cadastrado'),subtitle:Text('O Admin deve abrir Cadastros > Empresas e marcar uma empresa como “Fornecedor de combustível”.')))),
      const SizedBox(height:8),TextField(controller:nf,enabled:!busy,decoration:const InputDecoration(labelText:'Número da Nota Fiscal *')),
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
      const SizedBox(height:14),FilledButton.icon(onPressed:busy||suppliers.isEmpty?null:submit,icon:busy?const SizedBox(width:18,height:18,child:CircularProgressIndicator(strokeWidth:2)):const Icon(Icons.check_rounded),label:Text(busy?step:'Salvar recebimento')),
    ]),
  );
}

'''
s=s[:start]+new_refinery+s[end:]

# Home: descrição dos cadastros alinhada ao novo modelo.
s=s.replace("title: 'Cadastros', subtitle: 'Tanques estacionários, obras, ativos próprios e equipamentos de terceiros'",
            "title: 'Cadastros', subtitle: 'Empresa operadora, empresas externas, obras, ativos, terceiros e unidades de combustível'")

p.write_text(s)
print('company roles ui staged',len(s))
