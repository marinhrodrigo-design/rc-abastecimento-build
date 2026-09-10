from pathlib import Path

p = Path('lib/main_online.dart')
t = p.read_text()

if "Text('v105'" not in t:
    raise SystemExit('V105 marker not found')
t = t.replace("Text('v105'", "Text('v106'", 1)

old = '''  Future<void> saveThirdParty({
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
'''
new = '''  Future<int?> saveThirdPartyV106({
    int? id,
    String? plate,
    String? company,
    String? description,
    String? driverName,
    bool active = true,
    bool comboioEnabled = false,
    String? comboioCode,
    double? comboioCapacityLiters,
  }) async {
    final value = await client.rpc('rca_save_third_party_vehicle_v106', params: {
      'p_id': id,
      'p_plate': plate,
      'p_company_name': company,
      'p_description': description,
      'p_driver_name': driverName,
      'p_active': active,
      'p_comboio_enabled': comboioEnabled,
      'p_comboio_code': comboioCode,
      'p_comboio_capacity_liters': comboioCapacityLiters,
    });
    return _intOrNull(value);
  }

  Future<List<Map<String, dynamic>>> thirdPartyComboioRolesV106() async =>
      _rows(await client.rpc('rca_third_party_comboio_roles_v106'));
'''
if old not in t:
    raise SystemExit('saveThirdParty anchor not found')
t = t.replace(old, new, 1)

old_archive = '''  Future<void> archiveThirdParty(Map<String, dynamic> x) async {
    await saveThirdParty(
        id: _intOrNull(x['id']),
        plate: '${x['plate'] ?? ''}',
        company: '${x['company_name'] ?? x['company'] ?? ''}',
        description: '${x['description'] ?? ''}',
        driverName: '${x['driver_name'] ?? ''}',
        active: false);
  }
'''
new_archive = '''  Future<void> archiveThirdParty(Map<String, dynamic> x) async {
    await saveThirdPartyV106(
        id: _intOrNull(x['id']),
        plate: '${x['plate'] ?? ''}',
        company: '${x['company_name'] ?? x['company'] ?? ''}',
        description: '${x['description'] ?? ''}',
        driverName: '${x['driver_name'] ?? ''}',
        active: false,
        comboioEnabled: false);
  }
'''
if old_archive not in t:
    raise SystemExit('archiveThirdParty anchor not found')
t = t.replace(old_archive, new_archive, 1)

start = t.index('class ThirdPartyAdminScreen extends StatefulWidget {')
new_class = r'''class ThirdPartyAdminScreen extends StatefulWidget {
  final bool canEdit;
  const ThirdPartyAdminScreen({super.key, this.canEdit = false});
  @override
  State<ThirdPartyAdminScreen> createState() => _ThirdPartyAdminScreenState();
}

class _ThirdPartyAdminScreenState extends State<ThirdPartyAdminScreen> {
  List<Map<String, dynamic>>? items;
  List<Map<String, dynamic>> companies = [];
  Map<int, Map<String, dynamic>> comboioRolesV106 = {};
  bool loading = false;
  @override
  void initState() {
    super.initState();
    load();
  }

  Future<void> load() async {
    if (mounted) setState(() => loading = true);
    try {
      final reference = await api.referenceData();
      final c = <Map<String, dynamic>>[];
      final roles = <Map<String, dynamic>>[];
      if (widget.canEdit) {
        c.addAll(await api.managedCompanies());
        c.removeWhere(
            (x) => x['active'] == false || x['is_equipment_owner'] != true);
        c.sort((a, b) => '${a['name']}'
            .toLowerCase()
            .compareTo('${b['name']}'.toLowerCase()));
        roles.addAll(await api.thirdPartyComboioRolesV106());
      }
      final roleMap = <int, Map<String, dynamic>>{};
      for (final r in roles) {
        final id = _intOrNull(r['third_party_vehicle_id']);
        if (id != null) roleMap[id] = r;
      }
      if (mounted) {
        setState(() {
          items = _rows(reference['third_party_vehicles']);
          companies = c;
          comboioRolesV106 = roleMap;
        });
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(
            content: Text(
                'Erro ao carregar equipamentos/empresas: ${_friendlyError(e)}')));
      }
    } finally {
      if (mounted) setState(() => loading = false);
    }
  }

  int? companyIdFor(String name) {
    for (final c in companies) {
      if ('${c['name']}'.trim().toLowerCase() == name.trim().toLowerCase()) {
        return _intOrNull(c['id']);
      }
    }
    return null;
  }

  String? companyNameFor(int? id) {
    if (id == null) return null;
    for (final c in companies) {
      if (_intOrNull(c['id']) == id) return '${c['name']}';
    }
    return null;
  }

  Map<String, dynamic>? comboioRoleForV106(Map<String, dynamic>? item) {
    final id = _intOrNull(item?['id']);
    return id == null ? null : comboioRolesV106[id];
  }

  String suggestedComboioCodeV106(String text) {
    final m = RegExp(r'(\d{1,3})').allMatches(text).toList();
    if (m.isEmpty) return '';
    final n = int.tryParse(m.last.group(1) ?? '');
    if (n == null) return '';
    return 'CB${n.toString().padLeft(2, '0')}';
  }

  Future<void> edit([Map<String, dynamic>? item]) async {
    if (!widget.canEdit) return;
    final plate = TextEditingController(text: '${item?['plate'] ?? ''}');
    final desc = TextEditingController(text: '${item?['description'] ?? ''}');
    final role = comboioRoleForV106(item);
    bool comboioActive = role?['active'] == true;
    final comboioCode = TextEditingController(
        text: '${role?['code'] ?? ''}'.trim().isNotEmpty
            ? '${role?['code']}'
            : suggestedComboioCodeV106('${item?['description'] ?? ''}'));
    final comboioCapacity = TextEditingController(
        text: role?['capacity_liters'] == null
            ? ''
            : _num(role?['capacity_liters']).toStringAsFixed(0));
    int? companyId = companyIdFor('${item?['company_name'] ?? ''}');

    if (companies.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(
          content: Text('Cadastre primeiro a empresa proprietária / locadora.')));
      plate.dispose();
      desc.dispose();
      comboioCode.dispose();
      comboioCapacity.dispose();
      return;
    }

    final ok = await showDialog<bool>(
        context: context,
        builder: (ctx) => StatefulBuilder(
            builder: (ctx, setD) => AlertDialog(
                    title: Text(item == null
                        ? 'Cadastrar equipamento de terceiros'
                        : 'Editar equipamento de terceiros'),
                    content: SingleChildScrollView(
                        child: Column(mainAxisSize: MainAxisSize.min, children: [
                      DropdownButtonFormField<int>(
                          initialValue: companyId,
                          isExpanded: true,
                          decoration: const InputDecoration(
                              labelText: 'Empresa proprietária / locadora *'),
                          items: companies
                              .map((c) => DropdownMenuItem(
                                  value: _intOrNull(c['id']),
                                  child: Text('${c['name']}')))
                              .toList(),
                          onChanged: (v) => setD(() => companyId = v)),
                      const SizedBox(height: 8),
                      TextField(
                          controller: plate,
                          textCapitalization: TextCapitalization.characters,
                          decoration: const InputDecoration(
                              labelText: 'Placa (quando houver)')),
                      const SizedBox(height: 8),
                      TextField(
                          controller: desc,
                          decoration: const InputDecoration(
                              labelText: 'Descrição / identificação *')),
                      const Divider(height: 24),
                      SwitchListTile(
                          contentPadding: EdgeInsets.zero,
                          title: const Text('Ativo como comboio'),
                          subtitle: const Text('Receber diesel e abastecer'),
                          value: comboioActive,
                          onChanged: (v) => setD(() {
                                comboioActive = v;
                                if (v && comboioCode.text.trim().isEmpty) {
                                  comboioCode.text =
                                      suggestedComboioCodeV106(desc.text);
                                }
                              })),
                      if (comboioActive) ...[
                        const SizedBox(height: 4),
                        TextField(
                            controller: comboioCode,
                            textCapitalization: TextCapitalization.characters,
                            decoration: const InputDecoration(
                                labelText: 'Código do comboio *',
                                hintText: 'Ex.: CB03')),
                        const SizedBox(height: 8),
                        TextField(
                            controller: comboioCapacity,
                            keyboardType: const TextInputType.numberWithOptions(
                                decimal: true),
                            decoration: const InputDecoration(
                                labelText: 'Capacidade (litros) *')),
                        if (role != null)
                          Padding(
                              padding: const EdgeInsets.only(top: 8),
                              child: Align(
                                  alignment: Alignment.centerLeft,
                                  child: Text(
                                      'Saldo: ${_fmtLiters(role['current_balance_liters'])}',
                                      style: const TextStyle(
                                          fontWeight: FontWeight.w700)))),
                      ],
                    ])),
                    actions: [
                      TextButton(
                          onPressed: () => Navigator.pop(ctx, false),
                          child: const Text('Cancelar')),
                      FilledButton(
                          onPressed: () => Navigator.pop(ctx, true),
                          child: const Text('Salvar'))
                    ])));

    if (ok == true) {
      if (companyId == null) {
        ScaffoldMessenger.of(context).showSnackBar(const SnackBar(
            content: Text('Informe a empresa proprietária / locadora.')));
      } else if (plate.text.trim().isEmpty && desc.text.trim().isEmpty) {
        ScaffoldMessenger.of(context).showSnackBar(const SnackBar(
            content: Text('Informe a placa ou identificação do equipamento.')));
      } else {
        double? comboioCap;
        final normalizedCode = comboioCode.text
            .trim()
            .toUpperCase()
            .replaceAll(RegExp(r'[^A-Z0-9]'), '');
        if (comboioActive) {
          comboioCap = double.tryParse(
              comboioCapacity.text.trim().replaceAll(',', '.'));
          if (!RegExp(r'^CB\d+').hasMatch(normalizedCode)) {
            ScaffoldMessenger.of(context).showSnackBar(const SnackBar(
                content: Text('Use um código de comboio, por exemplo CB03.')));
            comboioCap = null;
          } else if (comboioCap == null || comboioCap <= 0) {
            ScaffoldMessenger.of(context).showSnackBar(const SnackBar(
                content: Text('Informe a capacidade do comboio.')));
            comboioCap = null;
          }
          if (comboioCap == null) {
            plate.dispose();
            desc.dispose();
            comboioCode.dispose();
            comboioCapacity.dispose();
            return;
          }
        }
        try {
          await api.saveThirdPartyV106(
              id: _intOrNull(item?['id']),
              plate: plate.text.trim(),
              company: companyNameFor(companyId),
              description: desc.text.trim(),
              driverName: null,
              active: true,
              comboioEnabled: comboioActive,
              comboioCode: comboioActive ? normalizedCode : null,
              comboioCapacityLiters: comboioActive ? comboioCap : null);
          await load();
          if (mounted) {
            ScaffoldMessenger.of(context).showSnackBar(SnackBar(
                content: Text(comboioActive
                    ? 'Equipamento salvo. $normalizedCode ativo como comboio.'
                    : 'Equipamento salvo.')));
          }
        } catch (e) {
          if (mounted) {
            ScaffoldMessenger.of(context).showSnackBar(SnackBar(
                content: Text('Erro ao salvar: ${_friendlyError(e)}')));
          }
        }
      }
    }
    plate.dispose();
    desc.dispose();
    comboioCode.dispose();
    comboioCapacity.dispose();
  }

  Future<void> removeThirdParty(Map<String, dynamic> x) async {
    if (!widget.canEdit) return;
    final label = _hasValue(x['plate'])
        ? '${x['plate']}'
        : '${x['description'] ?? 'este equipamento'}';
    final role = comboioRoleForV106(x);
    final ok = await showDialog<bool>(
        context: context,
        builder: (ctx) => AlertDialog(
              title: const Text('Excluir equipamento de terceiros?'),
              content: Text(role?['active'] == true
                  ? '$label será retirado dos cadastros. A função ${role?['code']} também será desativada se estiver sem saldo. O histórico será preservado.'
                  : '$label será retirado dos cadastros ativos. O histórico será preservado.'),
              actions: [
                TextButton(
                    onPressed: () => Navigator.pop(ctx, false),
                    child: const Text('Cancelar')),
                FilledButton(
                    style: FilledButton.styleFrom(
                        backgroundColor: Colors.red.shade700),
                    onPressed: () => Navigator.pop(ctx, true),
                    child: const Text('Excluir'))
              ],
            ));
    if (ok != true) return;
    setState(() => loading = true);
    try {
      await api.archiveThirdParty(x);
      await load();
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(const SnackBar(
            content: Text('Equipamento retirado. Histórico preservado.')));
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context)
            .showSnackBar(SnackBar(content: Text(_friendlyError(e))));
      }
    } finally {
      if (mounted) setState(() => loading = false);
    }
  }

  @override
  Widget build(BuildContext context) => Scaffold(
      appBar: AppBar(title: const Text('Equipamentos de terceiros')),
      floatingActionButton: widget.canEdit
          ? FloatingActionButton(
              onPressed: loading ? null : () => edit(),
              child: const Icon(Icons.add))
          : null,
      body: items == null
          ? const Center(child: CircularProgressIndicator())
          : RefreshIndicator(
              onRefresh: load,
              child: ListView(padding: const EdgeInsets.all(12), children: [
                if (widget.canEdit && companies.isEmpty)
                  const Card(
                      child: ListTile(
                          leading: Icon(Icons.business_outlined, color: _blue),
                          title: Text('Nenhuma proprietária / locadora'),
                          subtitle: Text('Cadastre primeiro em Empresas.'))),
                ...items!.map((x) {
                  final role = comboioRoleForV106(x);
                  final roleLine = role == null
                      ? null
                      : '${role['code']} • ${role['active'] == true ? 'Comboio ativo' : 'Comboio inativo'} • ${_fmtLiters(role['capacity_liters'])}';
                  return Card(
                      child: ListTile(
                          title: Text(
                              _plateDescriptionLabel(
                                  x['plate'], x['description']),
                              style: const TextStyle(
                                  fontWeight: FontWeight.w900)),
                          subtitle: Text([
                            'Empresa / locadora: ${x['company_name'] ?? 'Não informada'}',
                            if (roleLine != null) roleLine,
                          ].join('\n')),
                          isThreeLine: roleLine != null,
                          onTap:
                              widget.canEdit && !loading ? () => edit(x) : null,
                          trailing: widget.canEdit
                              ? PopupMenuButton<String>(
                                  enabled: !loading,
                                  onSelected: (v) {
                                    if (v == 'edit') edit(x);
                                    if (v == 'delete') removeThirdParty(x);
                                  },
                                  itemBuilder: (_) => const [
                                        PopupMenuItem(
                                            value: 'edit',
                                            child: Text('Editar')),
                                        PopupMenuItem(
                                            value: 'delete',
                                            child: Text('Excluir',
                                                style: TextStyle(
                                                    color: Colors.red)))
                                      ])
                              : null));
                }),
              ])));
}
'''

t = t[:start] + new_class + '\n'
p.write_text(t)
print('V106 rented comboio patch applied')
