from pathlib import Path
p=Path('lib/main_online.dart')
s=p.read_text()

def rep(a,b,count=1):
    global s
    if a not in s:
        raise SystemExit('anchor missing: '+a[:160])
    s=s.replace(a,b,count)

# 1. Transferência: responsável doador vem do login e é somente leitura.
rep("class TransferV23Screen extends StatefulWidget{\n  final Map<String,dynamic> source,ref;\n  const TransferV23Screen({super.key,required this.source,required this.ref});",
    "class TransferV23Screen extends StatefulWidget{\n  final Map<String,dynamic> source,ref,profile;\n  const TransferV23Screen({super.key,required this.source,required this.ref,required this.profile});")
rep("  bool saving=false;\n  String step='Concluir transferência';",
    "  bool saving=false;\n  String step='Concluir transferência';\n  @override void initState(){super.initState();donor.text='${widget.profile['display_name']??''}'.trim();}")
s=s.replace("const SizedBox(height:8),TextField(controller:donor,enabled:!saving,decoration:const InputDecoration(labelText:'Responsável doador *')),", "const SizedBox(height:8),TextField(controller:donor,readOnly:true,decoration:const InputDecoration(labelText:'Responsável doador • identificado pelo login',prefixIcon:Icon(Icons.verified_user_outlined))),",1)
rep("TransferV23Screen(source:t,ref:ref!)", "TransferV23Screen(source:t,ref:ref!,profile:widget.profile)",2)

# 2. Ativo que vai operar: todos os ativos cadastrados, mantendo T.E. como opção operacional.
old="""  List<Map<String, dynamic>> get operationalUnits {
    final out = <Map<String, dynamic>>[];
    for (final m in _rows(widget.referenceData['machines'])) {
      final asset = '${m['numeroAtivo'] ?? ''}'.trim();
      if (!asset.startsWith('008')) continue;
      final mid = _intOrNull(m['id']);
      final tid = _intOrNull(m['comboio_tank_id']);
      if (mid == null || tid == null) continue;
      final model = '${m['modelo'] ?? ''}'.trim();
      final plate = '${m['placa'] ?? ''}'.trim();
      out.add({'key': 'M:$mid', 'kind': 'comboio', 'machine_id': mid, 'tank_id': tid, 'label': '$asset${model.isNotEmpty ? ' • $model' : ''}${plate.isNotEmpty ? ' • $plate' : ''}'});
    }
    for (final t in _rows(widget.referenceData['tanks'])) {
      if ('${t['tank_type']}' != 'stationary') continue;
      final tid = _intOrNull(t['id']);
      if (tid == null) continue;
      out.add({'key': 'T:$tid', 'kind': 'stationary', 'machine_id': null, 'tank_id': tid, 'label': '${t['code']} • ${t['name']}'});
    }
    out.sort((a, b) => '${a['label']}'.compareTo('${b['label']}'));
    return out;
  }
"""
new="""  List<Map<String, dynamic>> get operationalUnits {
    final out = <Map<String, dynamic>>[];
    for (final m in _rows(widget.referenceData['machines'])) {
      final mid = _intOrNull(m['id']);
      if (mid == null) continue;
      final asset = '${m['numeroAtivo'] ?? ''}'.trim();
      final model = '${m['modelo'] ?? ''}'.trim();
      final plate = '${m['placa'] ?? ''}'.trim();
      final label = '${asset.isNotEmpty ? asset : 'Ativo $mid'}${model.isNotEmpty ? ' • $model' : ''}${plate.isNotEmpty ? ' • $plate' : ''}';
      out.add({'key': 'M:$mid', 'kind': 'machine', 'machine_id': mid, 'tank_id': _intOrNull(m['comboio_tank_id']), 'label': label});
    }
    for (final t in _rows(widget.referenceData['tanks'])) {
      if ('${t['tank_type']}' != 'stationary') continue;
      final tid = _intOrNull(t['id']);
      if (tid == null) continue;
      out.add({'key': 'T:$tid', 'kind': 'stationary', 'machine_id': null, 'tank_id': tid, 'label': 'T.E. • ${t['code']} • ${t['name']}'});
    }
    out.sort((a, b) => '${a['label']}'.toLowerCase().compareTo('${b['label']}'.toLowerCase()));
    return out;
  }
"""
rep(old,new)

# 3. Registros de abastecimento: timeout, erro visível e tentar novamente, sem spinner infinito.
rep("  bool busy = false;\n  bool filtersExpanded = true;", "  bool busy = false;\n  String? errorMessage;\n  bool filtersExpanded = true;")
old_search="""  Future<void> search({bool collapse = true}) async {
    setState(() => busy = true);
    try {
      final x = await api.adminSearch(start: start, end: end, workId: workId, asset: asset.text.trim(), plate: plate.text.trim(), operatorName: operatorName.text.trim(), type: type);
      if (mounted) setState(() { items = x; selectedCodes.clear(); suppressNextTap = false; if (collapse) filtersExpanded = false; });
    } catch (e) {
      if (mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(_friendlyError(e))));
    } finally { if (mounted) setState(() => busy = false); }
  }
"""
new_search="""  Future<void> search({bool collapse = true}) async {
    if (busy) return;
    setState(() { busy = true; errorMessage = null; });
    try {
      final x = await api.adminSearch(start: start, end: end, workId: workId, asset: asset.text.trim(), plate: plate.text.trim(), operatorName: operatorName.text.trim(), type: type).timeout(const Duration(seconds: 12));
      if (mounted) setState(() { items = x; selectedCodes.clear(); suppressNextTap = false; errorMessage = null; if (collapse) filtersExpanded = false; });
    } catch (e) {
      final message = _friendlyError(e);
      if (mounted) setState(() { errorMessage = message; if (items == null) items = const <Map<String,dynamic>>[]; });
      if (mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Erro ao carregar registros: $message')));
    } finally { if (mounted) setState(() => busy = false); }
  }
"""
rep(old_search,new_search)
old_loading="""          if (busy) const LinearProgressIndicator(minHeight: 2),
          const SizedBox(height: 8),
          if (items == null && !busy) const Padding(padding: EdgeInsets.all(30), child: Center(child: CircularProgressIndicator())),
          if (items != null && list.isEmpty) const Padding(padding: EdgeInsets.all(30), child: Center(child: Text('Nenhum registro encontrado com estes filtros.'))),
"""
new_loading="""          if (busy) const LinearProgressIndicator(minHeight: 2),
          const SizedBox(height: 8),
          if (errorMessage != null) Card(child: Padding(padding:const EdgeInsets.all(16),child:Column(children:[const Icon(Icons.error_outline_rounded,size:34),const SizedBox(height:8),Text('Não foi possível carregar os registros.\n$errorMessage',textAlign:TextAlign.center),const SizedBox(height:10),FilledButton.icon(onPressed:busy?null:()=>search(collapse:false),icon:const Icon(Icons.refresh_rounded),label:const Text('Tentar novamente'))]))),
          if (items == null && busy) const Padding(padding: EdgeInsets.all(20), child: Center(child: Text('Carregando registros...'))),
          if (items != null && list.isEmpty && errorMessage == null && !busy) const Padding(padding: EdgeInsets.all(30), child: Center(child: Text('Nenhum registro encontrado com estes filtros.'))),
"""
rep(old_loading,new_loading)

# 4. Mais: acesso claro e permanente aos Dados da empresa.
old_more="""        HomeActionCard(
          icon: Icons.business_outlined,
          title: 'Empresas',
          subtitle: 'Cadastrar os dados das empresas que serão usados nos PDFs',
          onTap: () => Navigator.push(context, MaterialPageRoute(builder: (_) => const CompaniesAdminScreen())),
        ),
"""
new_more=old_more+"""        const SizedBox(height: 12),
        HomeActionCard(
          icon: Icons.badge_outlined,
          title: 'Dados da empresa',
          subtitle: 'Consultar e editar a identificação institucional usada nos PDFs',
          onTap: () => Navigator.push(context, MaterialPageRoute(builder: (_) => const ReportCompanyAdminScreen())),
        ),
"""
rep(old_more,new_more)

# 5. Dados da empresa: deixa explícito que carrega/salva o cadastro persistente e trata falhas.
rep("  bool busy = true;", "  bool busy = true;\n  String? errorMessage;",1)
old_load="""  Future<void> load() async {
    try {
      final d = await api.reportCompany();
      name.text = '${d['company_name'] ?? 'Hydra'}';
      subtitle.text = '${d['company_subtitle'] ?? 'Equipamentos'}';
      document.text = '${d['document'] ?? ''}';
      address.text = '${d['address'] ?? ''}';
    } catch (_) {}
    if (mounted) setState(() => busy = false);
  }
"""
new_load="""  Future<void> load() async {
    if (mounted) setState(() { busy = true; errorMessage = null; });
    try {
      final d = await api.reportCompany().timeout(const Duration(seconds: 12));
      name.text = '${d['company_name'] ?? ''}';
      subtitle.text = '${d['company_subtitle'] ?? ''}';
      document.text = '${d['document'] ?? ''}';
      address.text = '${d['address'] ?? ''}';
    } catch (e) {
      errorMessage = _friendlyError(e);
    }
    if (mounted) setState(() => busy = false);
  }
"""
rep(old_load,new_load)
rep("      await api.saveReportCompany(companyName: name.text.trim(), companySubtitle: subtitle.text.trim(), document: document.text.trim(), address: address.text.trim());\n      if (mounted) ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Dados da empresa salvos.')));",
    "      await api.saveReportCompany(companyName: name.text.trim(), companySubtitle: subtitle.text.trim(), document: document.text.trim(), address: address.text.trim()).timeout(const Duration(seconds: 12));\n      await load();\n      if (mounted) ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Dados da empresa atualizados com sucesso ✓')));")
old_body="""    body: ListView(padding: const EdgeInsets.all(16), children: [
      TextField(controller: name, decoration: const InputDecoration(labelText: 'Empresa *')),
"""
new_body="""    body: ListView(padding: const EdgeInsets.all(16), children: [
      const Card(child:ListTile(leading:Icon(Icons.info_outline_rounded),title:Text('Cadastro institucional'),subtitle:Text('Estes dados ficam salvos no sistema e são carregados aqui sempre que você abrir esta página. Eles são usados na identificação dos PDFs e relatórios.'))),
      if(errorMessage!=null) Card(child:Padding(padding:const EdgeInsets.all(14),child:Column(children:[Text('Não foi possível carregar os dados: $errorMessage'),const SizedBox(height:8),OutlinedButton.icon(onPressed:busy?null:load,icon:const Icon(Icons.refresh),label:const Text('Tentar novamente'))]))),
      const SizedBox(height:10),
      TextField(controller: name, decoration: const InputDecoration(labelText: 'Empresa *')),
"""
rep(old_body,new_body)
rep("label: Text(busy ? 'Salvando...' : 'Salvar')", "label: Text(busy ? 'Salvando...' : 'Salvar alterações')",1)

# 6. Obras: nunca fica sem ação; oferece cadastro direto de empresa e erros claros.
rep("  @override\n  void initState() { super.initState(); load(); }\n\n  Future<void> load() async {\n    final d = await api.referenceData();\n    final c = await api.managedCompanies();\n    if (mounted) setState(() {\n      items = _rows(d['works']);\n      companies = c;\n    });\n  }",
"""  @override
  void initState() { super.initState(); load(); }

  Future<void> load() async {
    try {
      final r = await Future.wait<dynamic>([api.referenceData(), api.managedCompanies()]).timeout(const Duration(seconds:12));
      if (mounted) setState(() {
        items = _rows(_map(r[0])['works']);
        companies = _rows(r[1]);
      });
    } catch(e) {
      if(mounted){setState(()=>items ??= const <Map<String,dynamic>>[]);ScaffoldMessenger.of(context).showSnackBar(SnackBar(content:Text('Erro ao carregar obras: ${_friendlyError(e)}')));}
    }
  }

  Future<void> openCompanies() async {
    await Navigator.push(context, MaterialPageRoute(builder: (_) => const CompaniesAdminScreen()));
    if (mounted) await load();
  }""")
rep("      await api.saveWork(\n        id: _intOrNull(item?['id']),\n        name: name.text.trim(),\n        location: location.text.trim(),\n        responsible: responsible.text.trim(),\n        companyId: companyId,\n      );\n      await load();",
"""      try {
        await api.saveWork(
          id: _intOrNull(item?['id']),
          name: name.text.trim(),
          location: location.text.trim(),
          responsible: responsible.text.trim(),
          companyId: companyId,
        ).timeout(const Duration(seconds:12));
        await load();
        if(mounted)ScaffoldMessenger.of(context).showSnackBar(SnackBar(content:Text(item==null?'Obra cadastrada com sucesso ✓':'Obra atualizada com sucesso ✓')));
      } catch(e) {
        if(mounted)ScaffoldMessenger.of(context).showSnackBar(SnackBar(content:Text('Erro ao salvar obra: ${_friendlyError(e)}')));
      }""")
rep("    floatingActionButton: FloatingActionButton(onPressed: companies.isEmpty ? null : () => edit(), child: const Icon(Icons.add)),",
    "    floatingActionButton: FloatingActionButton(onPressed: () => companies.isEmpty ? openCompanies() : edit(), child: const Icon(Icons.add)),")
old_empty="""            if (companies.isEmpty)
              const Padding(
                padding: EdgeInsets.all(12),
                child: Card(child: ListTile(
                  leading: Icon(Icons.info_outline_rounded),
                  title: Text('Cadastre uma empresa primeiro'),
                  subtitle: Text('Acesse Admin > Mais > Empresas. Toda obra deve ficar vinculada a uma empresa para preencher corretamente o PDF.'),
                )),
              ),
"""
new_empty="""            if (companies.isEmpty)
              Padding(
                padding: const EdgeInsets.all(12),
                child: Card(child: Padding(padding:const EdgeInsets.all(14),child:Column(children:[
                  const ListTile(contentPadding:EdgeInsets.zero,leading:Icon(Icons.info_outline_rounded),title:Text('Cadastre uma empresa primeiro'),subtitle:Text('Toda obra precisa ficar vinculada a uma empresa. Use o botão abaixo para cadastrar e depois volte para criar ou editar a obra.')),
                  SizedBox(width:double.infinity,child:FilledButton.icon(onPressed:openCompanies,icon:const Icon(Icons.add_business_outlined),label:const Text('Cadastrar empresa'))),
                ]))),
              ),
"""
rep(old_empty,new_empty)
rep("                  onTap: companies.isEmpty ? null : () => edit(x),", "                  onTap: () => companies.isEmpty ? openCompanies() : edit(x),")

p.write_text(s)
print('follow-up patch applied', len(s), 'chars', len(s.splitlines()), 'lines')
