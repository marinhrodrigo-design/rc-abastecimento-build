from pathlib import Path

path = Path('lib/main_online.dart')
text = path.read_text()

def one(old, new, label):
    global text
    if old not in text:
        raise SystemExit(f'v11 não aplicado: {label}')
    text = text.replace(old, new, 1)

# API de ativos: sincroniza automaticamente um ativo do tipo Comboio com a unidade interna de combustível.
start = text.index('  Future<void> saveMachine({')
end = text.index('  Future<void> saveThirdParty({', start)
text = text[:start] + r'''  Future<int?> saveMachine({
    int? id,
    required String assetNumber,
    String? model,
    String? plate,
    String? type,
    String? location,
    bool active = true,
    double? comboioCapacityLiters,
  }) async {
    final value = await client.rpc('rca_save_machine_v2', params: {
      'p_id': id,
      'p_asset_number': assetNumber,
      'p_model': model,
      'p_plate': plate,
      'p_type': type,
      'p_location': location,
      'p_active': active,
      'p_comboio_capacity_liters': comboioCapacityLiters,
    });
    return _intOrNull(value);
  }

''' + text[end:]

one("HomeActionCard(icon: Icons.inventory_2_outlined, title: 'Cadastros', subtitle: 'Comboios, tanques, obras, ativos próprios e equipamentos alugados'", "HomeActionCard(icon: Icons.inventory_2_outlined, title: 'Cadastros', subtitle: 'Tanques estacionários, obras, ativos próprios e equipamentos alugados'", 'resumo cadastros')
one("HomeActionCard(icon: Icons.oil_barrel_outlined, title: 'Comboios e tanques', subtitle: 'Cadastrar comboios e tanques estacionários e alterar capacidades', onTap: () => Navigator.push(context, MaterialPageRoute(builder: (_) => const TanksAdminScreen()))),", "HomeActionCard(icon: Icons.oil_barrel_outlined, title: 'Tanques estacionários', subtitle: 'Cadastrar tanques estacionários e alterar capacidades', onTap: () => Navigator.push(context, MaterialPageRoute(builder: (_) => const TanksAdminScreen()))),", 'card tanque')

# Gestão de usuários: substitui permissões por unidade pelo ativo que o motorista irá operar.
us = text.index('class _AdminUsersOnlineScreenState extends State<AdminUsersOnlineScreen> {')
ue = text.index('class TanksAdminScreen extends StatefulWidget {', us)
seg = text[us:ue]

s = seg.index('  String unitNames(dynamic ids) {')
e = seg.index('  Future<void> createUser() async {', s)
seg = seg[:s] + r'''  List<Map<String, dynamic>> get comboioMachines {
    final out = _rows(widget.referenceData['machines']).where((m) {
      final comboio = m['is_comboio'] == true || '${m['tipo'] ?? ''}'.toUpperCase().contains('COMBOIO');
      return comboio && _intOrNull(m['comboio_tank_id']) != null;
    }).toList();
    out.sort((a, b) => '${a['numeroAtivo'] ?? ''}'.compareTo('${b['numeroAtivo'] ?? ''}'));
    return out;
  }

  String machineLabel(int? id) {
    if (id == null) return '-';
    for (final m in comboioMachines) {
      if (_intOrNull(m['id']) != id) continue;
      final model = '${m['modelo'] ?? ''}'.trim();
      final plate = '${m['placa'] ?? ''}'.trim();
      return '${m['numeroAtivo']}${model.isNotEmpty ? ' • $model' : ''}${plate.isNotEmpty ? ' • $plate' : ''}';
    }
    return '-';
  }

''' + seg[e:]

s = seg.index('  Future<void> createUser() async {')
e = seg.index('  Future<void> editUser(Map<String, dynamic> u) async {', s)
seg = seg[:s] + r'''  Future<void> createUser() async {
    final name = TextEditingController();
    final username = TextEditingController();
    final password = TextEditingController(text: '1234');
    int? machineId;
    final machines = comboioMachines;
    final ok = await showDialog<bool>(context: context, builder: (ctx) => StatefulBuilder(builder: (ctx, setLocal) => AlertDialog(
      title: const Text('Cadastrar usuário'),
      content: SingleChildScrollView(child: Column(mainAxisSize: MainAxisSize.min, children: [
        TextField(controller: name, decoration: const InputDecoration(labelText: 'Nome')),
        const SizedBox(height: 10),
        TextField(controller: username, decoration: const InputDecoration(labelText: 'Usuário')),
        const SizedBox(height: 10),
        TextField(controller: password, decoration: const InputDecoration(labelText: 'Senha / PIN (mínimo 4 caracteres)')),
        const SizedBox(height: 12),
        if (machines.isEmpty)
          const Align(alignment: Alignment.centerLeft, child: Text('Cadastre primeiro um ativo do tipo Comboio.', style: TextStyle(fontWeight: FontWeight.w700)))
        else
          DropdownButtonFormField<int>(
            initialValue: machineId,
            isExpanded: true,
            decoration: const InputDecoration(labelText: 'Ativo que irá operar *'),
            items: machines.map((m) => DropdownMenuItem<int>(value: _intOrNull(m['id']), child: Text(machineLabel(_intOrNull(m['id'])), overflow: TextOverflow.ellipsis))).toList(),
            onChanged: (v) => setLocal(() => machineId = v),
          ),
      ])),
      actions: [TextButton(onPressed: () => Navigator.pop(ctx, false), child: const Text('Cancelar')), FilledButton(onPressed: machines.isEmpty ? null : () => Navigator.pop(ctx, true), child: const Text('Cadastrar'))],
    )));
    if (ok == true) {
      if (machineId == null) {
        if (mounted) ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Selecione o ativo que o motorista irá operar.')));
      } else {
        setState(() => busy = true);
        try { await api.invokeUserAction({'action': 'create_driver', 'name': name.text.trim(), 'username': username.text.trim(), 'password': password.text, 'machine_id': machineId}); await load(); }
        catch (e) { if (mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(_friendlyError(e)))); }
        if (mounted) setState(() => busy = false);
      }
    }
    name.dispose(); username.dispose(); password.dispose();
  }

''' + seg[e:]

s = seg.index('  Future<void> editUser(Map<String, dynamic> u) async {')
e = seg.index('  Future<void> toggle(Map<String, dynamic> u) async {', s)
seg = seg[:s] + r'''  Future<void> editUser(Map<String, dynamic> u) async {
    final name = TextEditingController(text: '${u['name'] ?? ''}');
    final username = TextEditingController(text: '${u['username'] ?? ''}');
    final password = TextEditingController();
    int? machineId = _intOrNull(u['machine_id']);
    final machines = comboioMachines;
    final ok = await showDialog<bool>(context: context, builder: (ctx) => StatefulBuilder(builder: (ctx, setLocal) => AlertDialog(
      title: Text('Editar ${u['username']}'),
      content: SingleChildScrollView(child: Column(mainAxisSize: MainAxisSize.min, children: [
        TextField(controller: name, decoration: const InputDecoration(labelText: 'Nome')),
        const SizedBox(height: 10),
        TextField(controller: username, decoration: const InputDecoration(labelText: 'Usuário')),
        const SizedBox(height: 10),
        TextField(controller: password, decoration: const InputDecoration(labelText: 'Nova senha / PIN (opcional, mínimo 4 caracteres)')),
        const SizedBox(height: 12),
        DropdownButtonFormField<int>(
          initialValue: machines.any((m) => _intOrNull(m['id']) == machineId) ? machineId : null,
          isExpanded: true,
          decoration: const InputDecoration(labelText: 'Ativo que irá operar *'),
          items: machines.map((m) => DropdownMenuItem<int>(value: _intOrNull(m['id']), child: Text(machineLabel(_intOrNull(m['id'])), overflow: TextOverflow.ellipsis))).toList(),
          onChanged: (v) => setLocal(() => machineId = v),
        ),
      ])),
      actions: [TextButton(onPressed: () => Navigator.pop(ctx, false), child: const Text('Cancelar')), FilledButton(onPressed: machines.isEmpty ? null : () => Navigator.pop(ctx, true), child: const Text('Salvar'))],
    )));
    if (ok == true) {
      if (machineId == null) {
        if (mounted) ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Selecione o ativo que o motorista irá operar.')));
      } else {
        setState(() => busy = true);
        try { await api.invokeUserAction({'action': 'update_driver', 'user_id': u['user_id'], 'name': name.text.trim(), 'username': username.text.trim(), 'password': password.text, 'machine_id': machineId}); await load(); }
        catch (e) { if (mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(_friendlyError(e)))); }
        if (mounted) setState(() => busy = false);
      }
    }
    name.dispose(); username.dispose(); password.dispose();
  }

''' + seg[e:]

s = seg.index('  Future<void> toggle(Map<String, dynamic> u) async {')
candidates = [x for x in (seg.find('  Future<void> deleteUser(', s), seg.find('  Future<void> removeAccess(', s)) if x >= 0]
e = min(candidates)
seg = seg[:s] + r'''  Future<void> toggle(Map<String, dynamic> u) async {
    final machineId = _intOrNull(u['machine_id']);
    if (machineId == null) {
      if (mounted) ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Edite o usuário e selecione o ativo que ele irá operar.')));
      return;
    }
    setState(() => busy = true);
    try { await api.invokeUserAction({'action': 'set_active', 'user_id': u['user_id'], 'name': u['name'], 'active': u['active'] != true, 'machine_id': machineId}); await load(); }
    catch (e) { if (mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(_friendlyError(e)))); }
    if (mounted) setState(() => busy = false);
  }

''' + seg[e:]
seg = seg.replace("Text('Unidades permitidas: ${unitNames(u['tank_ids'])}')", "Text('Ativo que irá operar: ${machineLabel(_intOrNull(u['machine_id']))}')", 1)
text = text[:us] + seg + text[ue:]

# Tela antiga de Comboios e tanques vira exclusivamente Tanques estacionários.
one("if (mounted) setState(() => items = _sortedFuelUnits(d['tanks']));", "if (mounted) setState(() => items = _sortedFuelUnits(d['tanks']).where((t) => t['tank_type'] == 'stationary').toList());", 'filtrar TE')
one("var tankType = creating ? 'comboio' : '${item?['tank_type'] ?? 'comboio'}';", "var tankType = 'stationary';", 'tipo TE fixo')
one("title: Text(creating ? 'Cadastrar unidade' : 'Editar unidade'),", "title: Text(creating ? 'Cadastrar tanque estacionário' : 'Editar tanque estacionário'),", 'título TE')
one("decoration: const InputDecoration(labelText: 'Código *', hintText: 'Ex.: CB04 ou TE02'),", "decoration: const InputDecoration(labelText: 'Código *', hintText: 'Ex.: TE02'),", 'hint TE')
old_type = r'''              if (creating)
                DropdownButtonFormField<String>(
                  initialValue: tankType,
                  decoration: const InputDecoration(labelText: 'Tipo da unidade *'),
                  items: const [
                    DropdownMenuItem(value: 'comboio', child: Text('Comboio')),
                    DropdownMenuItem(value: 'stationary', child: Text('Tanque estacionário')),
                  ],
                  onChanged: (v) { if (v != null) tankType = v; },
                )
              else
                InputDecorator(
                  decoration: const InputDecoration(labelText: 'Tipo'),
                  child: Text(tankType == 'stationary' ? 'Tanque estacionário' : 'Comboio'),
                ),
'''
one(old_type, "              const InputDecorator(decoration: InputDecoration(labelText: 'Tipo'), child: Text('Tanque estacionário')),\n", 'remover opção comboio')
one("          if (normalizedCode.startsWith('CB')) tankType = 'comboio';\n          if (normalizedCode.startsWith('TE')) tankType = 'stationary';", "          if (!normalizedCode.startsWith('TE')) throw Exception('O código do tanque estacionário deve começar com TE.');\n          tankType = 'stationary';", 'validar código TE')
one("creating ? 'Unidade cadastrada.' : 'Unidade atualizada.'", "creating ? 'Tanque estacionário cadastrado.' : 'Tanque estacionário atualizado.'", 'mensagem TE')
one("appBar: AppBar(title: const Text('Comboios e tanques')),", "appBar: AppBar(title: const Text('Tanques estacionários')),", 'appbar TE')
one("label: const Text('Nova unidade'),", "label: const Text('Novo tanque'),", 'fab TE')

# Cadastro de ativo: quando o tipo contém Comboio, exige/permite editar a capacidade e sincroniza a unidade interna.
ms = text.index('class _MachinesAdminScreenState extends State<MachinesAdminScreen> {')
me = text.index('  @override\n  Widget build(BuildContext context) {', ms)
seg = text[ms:me]
es = seg.index('  Future<void> edit([Map<String, dynamic>? item]) async {')
new_edit = r'''  Future<void> edit([Map<String, dynamic>? item]) async {
    final number = TextEditingController(text: '${item?['numeroAtivo'] ?? ''}');
    final model = TextEditingController(text: '${item?['modelo'] ?? ''}');
    final plate = TextEditingController(text: '${item?['placa'] ?? ''}');
    final type = TextEditingController(text: '${item?['tipo'] ?? ''}');
    final location = TextEditingController(text: '${item?['localizacao'] ?? ''}');
    final capacity = TextEditingController(text: item?['comboio_capacity_liters'] == null ? '' : _num(item?['comboio_capacity_liters']).toStringAsFixed(0));
    final ok = await showDialog<bool>(context: context, builder: (ctx) => StatefulBuilder(builder: (ctx, setLocal) {
      final isComboio = type.text.trim().toUpperCase().contains('COMBOIO');
      return AlertDialog(title: Text(item == null ? 'Cadastrar ativo' : 'Editar ativo'), content: SingleChildScrollView(child: Column(mainAxisSize: MainAxisSize.min, children: [
        TextField(controller: number, decoration: const InputDecoration(labelText: 'Número do ativo *')),
        const SizedBox(height: 8), TextField(controller: model, decoration: const InputDecoration(labelText: 'Modelo')),
        const SizedBox(height: 8), TextField(controller: plate, decoration: const InputDecoration(labelText: 'Placa')),
        const SizedBox(height: 8), TextField(controller: type, onChanged: (_) => setLocal(() {}), decoration: const InputDecoration(labelText: 'Tipo', hintText: 'Ex.: CAMINHÃO COMBOIO')),
        if (isComboio) ...[
          const SizedBox(height: 8),
          TextField(controller: capacity, keyboardType: const TextInputType.numberWithOptions(decimal: true), decoration: const InputDecoration(labelText: 'Capacidade do comboio (litros) *')),
          if (_hasValue(item?['comboio_code'])) Padding(padding: const EdgeInsets.only(top: 8), child: Align(alignment: Alignment.centerLeft, child: Text('Unidade: ${item?['comboio_code']} • Saldo: ${_fmtLiters(item?['comboio_balance_liters'])}', style: const TextStyle(fontWeight: FontWeight.w700)))),
        ],
        const SizedBox(height: 8), TextField(controller: location, decoration: const InputDecoration(labelText: 'Localização')),
      ])), actions: [TextButton(onPressed: () => Navigator.pop(ctx, false), child: const Text('Cancelar')), FilledButton(onPressed: () => Navigator.pop(ctx, true), child: const Text('Salvar'))]);
    }));
    if (ok == true && number.text.trim().isNotEmpty) {
      final isComboio = type.text.trim().toUpperCase().contains('COMBOIO');
      final parsed = double.tryParse(capacity.text.trim().replaceAll(',', '.'));
      if (isComboio && (parsed == null || parsed <= 0)) {
        if (mounted) ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Informe a capacidade do comboio.')));
      } else {
        try {
          await api.saveMachine(id: _intOrNull(item?['id']), assetNumber: number.text.trim(), model: model.text.trim(), plate: plate.text.trim(), type: type.text.trim(), location: location.text.trim(), comboioCapacityLiters: isComboio ? parsed : null);
          await load();
          if (mounted && isComboio) ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Ativo e comboio sincronizados.')));
        } catch (e) { if (mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(_friendlyError(e)))); }
      }
    }
    number.dispose(); model.dispose(); plate.dispose(); type.dispose(); location.dispose(); capacity.dispose();
  }
'''
seg = seg[:es] + new_edit
text = text[:ms] + seg + text[me:]

for marker in ["rca_save_machine_v2", "Ativo que irá operar", "Capacidade do comboio (litros)", "title: 'Tanques estacionários'"]:
    if marker not in text: raise SystemExit(f'v11 validação falhou: {marker}')
path.write_text(text)
print('v11 aplicado: comboio nasce do ativo; motorista escolhe ativo; cadastro separado de comboio removido; TE mantido.')
