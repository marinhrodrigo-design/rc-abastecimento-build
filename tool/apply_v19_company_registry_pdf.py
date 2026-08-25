from pathlib import Path

path = Path('lib/main_online.dart')
text = path.read_text()

old_api = r'''  Future<void> saveWork({int? id, required String name, String? location, bool active = true}) async {
    await client.rpc('rca_save_work', params: {'p_id': id, 'p_name': name, 'p_location': location, 'p_active': active});
  }
'''
new_api = r'''  Future<List<Map<String, dynamic>>> managedCompanies() async => _rows(await client.rpc('rca_managed_companies'));

  Future<void> saveManagedCompany({
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

  Future<void> saveWork({int? id, required String name, String? location, int? companyId, bool active = true}) async {
    await client.rpc('rca_save_work_v2', params: {
      'p_id': id,
      'p_name': name,
      'p_location': location,
      'p_company_id': companyId,
      'p_active': active,
    });
  }
'''
if old_api not in text:
    raise SystemExit('v19: bloco saveWork base não encontrado')
text = text.replace(old_api, new_api, 1)

old_home = r'''                  HomeActionCard(icon: Icons.inventory_2_outlined, title: 'Cadastros', subtitle: 'Obras, ativos próprios e veículos de terceiros', onTap: () async { await Navigator.push(context, MaterialPageRoute(builder: (_) => const AdminCatalogScreen())); await refresh(); }),
'''
new_home = old_home + r'''                  const SizedBox(height: 12),
                  HomeActionCard(icon: Icons.more_horiz_rounded, title: 'Mais', subtitle: 'Empresas e configurações administrativas', onTap: () async { await Navigator.push(context, MaterialPageRoute(builder: (_) => const AdminMoreScreen())); await refresh(); }),
'''
if old_home not in text:
    raise SystemExit('v19: cartão Cadastros do admin não encontrado')
text = text.replace(old_home, new_home, 1)

marker = 'class AdminCatalogScreen extends StatelessWidget {'
if marker not in text:
    raise SystemExit('v19: marcador AdminCatalogScreen não encontrado')
admin_more = r'''class AdminMoreScreen extends StatelessWidget {
  const AdminMoreScreen({super.key});

  @override
  Widget build(BuildContext context) => Scaffold(
    appBar: AppBar(title: const Text('Mais')),
    body: ListView(
      padding: const EdgeInsets.all(16),
      children: [
        HomeActionCard(
          icon: Icons.business_outlined,
          title: 'Empresas',
          subtitle: 'Cadastrar os dados das empresas que serão usados nos PDFs',
          onTap: () => Navigator.push(context, MaterialPageRoute(builder: (_) => const CompaniesAdminScreen())),
        ),
      ],
    ),
  );
}

class CompaniesAdminScreen extends StatefulWidget {
  const CompaniesAdminScreen({super.key});

  @override
  State<CompaniesAdminScreen> createState() => _CompaniesAdminScreenState();
}

class _CompaniesAdminScreenState extends State<CompaniesAdminScreen> {
  List<Map<String, dynamic>>? items;
  bool busy = false;

  @override
  void initState() {
    super.initState();
    load();
  }

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

    final ok = await showDialog<bool>(
      context: context,
      builder: (ctx) => StatefulBuilder(
        builder: (ctx, setDialogState) => AlertDialog(
          title: Text(item == null ? 'Cadastrar empresa' : 'Editar empresa'),
          content: SizedBox(
            width: 520,
            child: SingleChildScrollView(
              child: Column(mainAxisSize: MainAxisSize.min, children: [
                TextField(controller: name, decoration: const InputDecoration(labelText: 'Nome da empresa *')),
                const SizedBox(height: 9),
                TextField(controller: subtitle, decoration: const InputDecoration(labelText: 'Subtítulo / segmento', hintText: 'Ex.: Equipamentos')),
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
                SwitchListTile.adaptive(
                  contentPadding: EdgeInsets.zero,
                  title: const Text('Empresa ativa'),
                  value: active,
                  onChanged: (v) => setDialogState(() => active = v),
                ),
              ]),
            ),
          ),
          actions: [
            TextButton(onPressed: () => Navigator.pop(ctx, false), child: const Text('Cancelar')),
            FilledButton(onPressed: name.text.trim().isEmpty ? null : () => Navigator.pop(ctx, true), child: const Text('Salvar')),
          ],
        ),
      ),
    );

    if (ok == true && name.text.trim().isNotEmpty) {
      setState(() => busy = true);
      try {
        await api.saveManagedCompany(
          id: _intOrNull(item?['id']),
          name: name.text.trim(),
          subtitle: subtitle.text.trim(),
          document: document.text.trim(),
          zipCode: zip.text.trim(),
          street: street.text.trim(),
          streetNumber: number.text.trim(),
          complement: complement.text.trim(),
          neighborhood: neighborhood.text.trim(),
          city: city.text.trim(),
          state: state.text.trim(),
          active: active,
        );
        await load();
      } catch (e) {
        if (mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(_friendlyError(e))));
      } finally {
        if (mounted) setState(() => busy = false);
      }
    }

    for (final c in [name, subtitle, document, zip, street, number, complement, neighborhood, city, state]) {
      c.dispose();
    }
  }

  @override
  Widget build(BuildContext context) => Scaffold(
    appBar: AppBar(title: const Text('Empresas')),
    floatingActionButton: FloatingActionButton.extended(
      onPressed: busy ? null : () => edit(),
      icon: const Icon(Icons.add_business_outlined),
      label: const Text('Cadastrar empresa'),
    ),
    body: items == null
        ? const Center(child: CircularProgressIndicator())
        : RefreshIndicator(
            onRefresh: load,
            child: items!.isEmpty
                ? ListView(children: const [SizedBox(height: 180), Center(child: Text('Nenhuma empresa cadastrada.'))])
                : ListView.builder(
                    padding: const EdgeInsets.fromLTRB(12, 12, 12, 90),
                    itemCount: items!.length,
                    itemBuilder: (_, i) {
                      final x = items![i];
                      final address = addressOf(x);
                      return Card(child: ListTile(
                        contentPadding: const EdgeInsets.all(14),
                        leading: const CircleAvatar(child: Icon(Icons.business_rounded)),
                        title: Text('${x['name']}', style: const TextStyle(fontWeight: FontWeight.w900)),
                        subtitle: Text([
                          if (_hasValue(x['subtitle'])) '${x['subtitle']}',
                          if (_hasValue(x['document'])) 'CNPJ: ${x['document']}',
                          if (address.isNotEmpty) address,
                        ].join('\n')),
                        trailing: Column(mainAxisAlignment: MainAxisAlignment.center, children: [
                          Icon(x['active'] == true ? Icons.check_circle_rounded : Icons.pause_circle_outline_rounded, color: x['active'] == true ? Colors.green : Colors.grey),
                          const SizedBox(height: 4),
                          const Icon(Icons.edit_outlined, size: 18),
                        ]),
                        onTap: busy ? null : () => edit(x),
                      ));
                    },
                  ),
          ),
  );
}

'''
text = text.replace(marker, admin_more + marker, 1)

work_start = text.find('class WorksAdminScreen extends StatefulWidget {')
work_end = text.find('class MachinesAdminScreen extends StatefulWidget {', work_start)
if work_start < 0 or work_end < 0:
    raise SystemExit('v19: WorksAdminScreen não encontrado')
new_works = r'''class WorksAdminScreen extends StatefulWidget {
  const WorksAdminScreen({super.key});
  @override
  State<WorksAdminScreen> createState() => _WorksAdminScreenState();
}

class _WorksAdminScreenState extends State<WorksAdminScreen> {
  List<Map<String, dynamic>>? items;
  List<Map<String, dynamic>> companies = const [];

  @override
  void initState() { super.initState(); load(); }

  Future<void> load() async {
    final d = await api.referenceData();
    final c = await api.managedCompanies();
    if (mounted) setState(() {
      items = _rows(d['works']);
      companies = c;
    });
  }

  String companyName(dynamic id) {
    final target = _intOrNull(id);
    for (final c in companies) {
      if (_intOrNull(c['id']) == target) return '${c['name']}';
    }
    return 'Sem empresa vinculada';
  }

  Future<void> edit([Map<String, dynamic>? item]) async {
    final name = TextEditingController(text: '${item?['name'] ?? ''}');
    final location = TextEditingController(text: '${item?['location'] ?? ''}');
    int? companyId = _intOrNull(item?['contracting_company_id']);

    final ok = await showDialog<bool>(
      context: context,
      builder: (ctx) => StatefulBuilder(
        builder: (ctx, setDialogState) => AlertDialog(
          title: Text(item == null ? 'Cadastrar obra' : 'Editar obra'),
          content: Column(mainAxisSize: MainAxisSize.min, children: [
            TextField(controller: name, decoration: const InputDecoration(labelText: 'Nome *')),
            const SizedBox(height: 10),
            DropdownButtonFormField<int>(
              value: companyId,
              isExpanded: true,
              decoration: const InputDecoration(labelText: 'Empresa *'),
              items: companies.map((c) => DropdownMenuItem<int>(value: _intOrNull(c['id']), child: Text('${c['name']}'))).toList(),
              onChanged: (v) => setDialogState(() => companyId = v),
            ),
            const SizedBox(height: 10),
            TextField(controller: location, decoration: const InputDecoration(labelText: 'Local')),
          ]),
          actions: [
            TextButton(onPressed: () => Navigator.pop(ctx, false), child: const Text('Cancelar')),
            FilledButton(onPressed: companyId == null ? null : () => Navigator.pop(ctx, true), child: const Text('Salvar')),
          ],
        ),
      ),
    );

    if (ok == true && name.text.trim().isNotEmpty && companyId != null) {
      await api.saveWork(
        id: _intOrNull(item?['id']),
        name: name.text.trim(),
        location: location.text.trim(),
        companyId: companyId,
      );
      await load();
    }
    name.dispose();
    location.dispose();
  }

  @override
  Widget build(BuildContext context) => Scaffold(
    appBar: AppBar(title: const Text('Obras')),
    floatingActionButton: FloatingActionButton(onPressed: companies.isEmpty ? null : () => edit(), child: const Icon(Icons.add)),
    body: items == null
        ? const Center(child: CircularProgressIndicator())
        : Column(children: [
            if (companies.isEmpty)
              const Padding(
                padding: EdgeInsets.all(12),
                child: Card(child: ListTile(
                  leading: Icon(Icons.info_outline_rounded),
                  title: Text('Cadastre uma empresa primeiro'),
                  subtitle: Text('Acesse Admin > Mais > Empresas. Toda obra deve ficar vinculada a uma empresa para preencher corretamente o PDF.'),
                )),
              ),
            Expanded(child: ListView.builder(
              padding: const EdgeInsets.all(12),
              itemCount: items!.length,
              itemBuilder: (_, i) {
                final x = items![i];
                return Card(child: ListTile(
                  title: Text('${x['name']}', style: const TextStyle(fontWeight: FontWeight.w900)),
                  subtitle: Text('${companyName(x['contracting_company_id'])}\n${x['location'] ?? ''}'),
                  isThreeLine: true,
                  trailing: const Icon(Icons.edit_outlined),
                  onTap: companies.isEmpty ? null : () => edit(x),
                ));
              },
            )),
          ]),
  );
}

'''
text = text[:work_start] + new_works + text[work_end:]

old_company = r'''    Map<String, dynamic> company = const {};
    try {
      company = _map(await api.client.rpc('rca_report_company'));
    } catch (_) {}

    final companyName = _hasValue(company['company_name']) ? '${company['company_name']}' : 'Hydra';
    final companySubtitle = _hasValue(company['company_subtitle']) ? '${company['company_subtitle']}' : 'Equipamentos';
    final companyDocument = _hasValue(company['document']) ? '${company['document']}' : '-';
    final companyAddress = _hasValue(company['address']) ? '${company['address']}' : '-';

'''
if old_company not in text:
    raise SystemExit('v19: bloco global de empresa do PDF não encontrado')
text = text.replace(old_company, '', 1)

for_marker = '    for (final x in items) {\n'
if for_marker not in text:
    raise SystemExit('v19: loop de itens do PDF não encontrado')
company_per_item = r'''    for (final x in items) {
      Map<String, dynamic> company = const {};
      try {
        final movementId = _intOrNull(x['id']);
        if (movementId != null) {
          company = _map(await api.client.rpc('rca_report_company_for_movement', params: {'p_movement_id': movementId}));
        }
      } catch (_) {}
      final companyName = _hasValue(company['company_name']) ? '${company['company_name']}' : 'Empresa não cadastrada';
      final companySubtitle = _hasValue(company['company_subtitle']) ? '${company['company_subtitle']}' : '';
      final companyDocument = _hasValue(company['document']) ? '${company['document']}' : '-';
      final companyAddress = _hasValue(company['address']) ? '${company['address']}' : '-';
'''
text = text.replace(for_marker, company_per_item, 1)

required = [
    "title: 'Empresas'",
    "class CompaniesAdminScreen",
    "rca_save_managed_company",
    "rca_save_work_v2",
    "contracting_company_id",
    "rca_report_company_for_movement",
    "companyName = _hasValue(company['company_name'])",
]
for marker in required:
    if marker not in text:
        raise SystemExit(f'v19: marcador obrigatório ausente: {marker}')
if "api.client.rpc('rca_report_company')" in text[text.find('class FuelPdfReport'):text.find('class AdminUsersOnlineScreen')]:
    raise SystemExit('v19: PDF ainda usa empresa global fixa')

path.write_text(text)
print('v19: cadastro de empresas, vínculo Obra→Empresa e empresa dinâmica no PDF aplicados.')
