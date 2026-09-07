from pathlib import Path
p=Path('lib/main_online.dart')
s=p.read_text()

api_old="""  Future<Map<String, dynamic>> traceV23(int lotId) async =>
      _map(await client.rpc('rca_nf_trace_v23', params: {'p_lot_id': lotId}));
  Future<Map<String, dynamic>> movementTraceV23(int movementId) async =>
"""
api_new="""  Future<Map<String, dynamic>> traceV23(int lotId) async =>
      _map(await client.rpc('rca_nf_trace_v23', params: {'p_lot_id': lotId}));
  Future<bool> hasPermissionV92(String key) async =>
      (await client.rpc('rca_has_permission', params: {'p_key': key})) == true;
  Future<Map<String, dynamic>> nfEditDetailV92(int lotId) async =>
      _map(await client.rpc('rca_nf_edit_detail_v92', params: {'p_lot_id': lotId}));
  Future<Map<String, dynamic>> editReceivedInvoiceV92(
          int lotId, Map<String, dynamic> changes, String reason) async =>
      _map(await client.rpc('rca_edit_received_invoice_v92', params: {
        'p_lot_id': lotId,
        'p_changes': changes,
        'p_reason': reason,
      }));
  Future<Map<String, dynamic>> movementTraceV23(int movementId) async =>
"""
if api_old not in s: raise SystemExit('api anchor missing')
s=s.replace(api_old,api_new,1)

s=s.replace("  bool loading = false;\n  final search = TextEditingController();\n", "  bool loading = false, canEdit = false;\n  final search = TextEditingController();\n",1)

load_old="""  Future<void> loadLots() async {
    setState(() => loading = true);
    try {
      final x = await api.lotsCatalogV23();
      if (mounted) setState(() => lots = x);
    } catch (e) {
      if (mounted)
        ScaffoldMessenger.of(context)
            .showSnackBar(SnackBar(content: Text(_friendlyError(e))));
    } finally {
      if (mounted) setState(() => loading = false);
    }
  }

  Future<void> trace(int value) async {
"""
load_new="""  Future<void> loadLots() async {
    setState(() => loading = true);
    try {
      final values = await Future.wait<dynamic>([
        api.lotsCatalogV23(),
        api.hasPermissionV92('nf.edit'),
      ]);
      if (mounted)
        setState(() {
          lots = (values[0] as List).cast<Map<String, dynamic>>();
          canEdit = values[1] == true;
        });
    } catch (e) {
      if (mounted)
        ScaffoldMessenger.of(context)
            .showSnackBar(SnackBar(content: Text(_friendlyError(e))));
    } finally {
      if (mounted) setState(() => loading = false);
    }
  }

  Future<void> editSelected() async {
    final lotId = id;
    if (lotId == null || !canEdit || loading) return;
    final changed = await Navigator.push<bool>(
        context,
        MaterialPageRoute(
            builder: (_) => NfEditV92Screen(lotId: lotId)));
    if (changed == true && mounted) {
      await loadLots();
      if (mounted) await trace(lotId);
    }
  }

  Future<void> trace(int value) async {
"""
if load_old not in s: raise SystemExit('load anchor missing')
s=s.replace(load_old,load_new,1)

heading_old="""            Text('NF ${lot['invoice_number']}',
                style: Theme.of(c)
                    .textTheme
                    .titleLarge
                    ?.copyWith(fontWeight: FontWeight.w900)),
            Card(
"""
heading_new="""            Row(children: [
              Expanded(
                  child: Text('NF ${lot['invoice_number']}',
                      style: Theme.of(c)
                          .textTheme
                          .titleLarge
                          ?.copyWith(fontWeight: FontWeight.w900))),
              if (canEdit)
                IconButton(
                    onPressed: loading ? null : editSelected,
                    tooltip: 'Editar/corrigir Nota Fiscal',
                    icon: const Icon(Icons.edit_outlined, color: _blue))
            ]),
            if (canEdit)
              Padding(
                  padding: const EdgeInsets.only(bottom: 8),
                  child: SizedBox(
                      width: double.infinity,
                      child: OutlinedButton.icon(
                          onPressed: loading ? null : editSelected,
                          icon: const Icon(Icons.edit_note_rounded),
                          label: const Text('Editar/corrigir Nota Fiscal')))),
            Card(
"""
if heading_old not in s: raise SystemExit('heading anchor missing')
s=s.replace(heading_old,heading_new,1)

insert_anchor="""String _permissionLabelV23(String key) {
"""
edit_class=r'''class NfEditV92Screen extends StatefulWidget {
  final int lotId;
  const NfEditV92Screen({super.key, required this.lotId});
  @override
  State<NfEditV92Screen> createState() => _NfEditV92ScreenState();
}

class _NfEditV92ScreenState extends State<NfEditV92Screen> {
  final nf = TextEditingController(),
      batch = TextEditingController(),
      liters = TextEditingController(),
      cost = TextEditingController(),
      reason = TextEditingController();
  Map<String, dynamic>? detail;
  List<Map<String, dynamic>> suppliers = [];
  int? supplierId;
  String fuel = 'Diesel S10';
  bool loading = true, saving = false;

  @override
  void initState() {
    super.initState();
    load();
  }

  @override
  void dispose() {
    for (final c in [nf, batch, liters, cost, reason]) {
      c.dispose();
    }
    super.dispose();
  }

  Future<void> load() async {
    try {
      final values = await Future.wait<dynamic>([
        api.nfEditDetailV92(widget.lotId),
        api.companiesByRole('fuel_supplier'),
      ]);
      final d = _map(values[0]);
      final list = (values[1] as List).cast<Map<String, dynamic>>();
      int? selected = _intOrNull(d['supplier_company_id']);
      if (selected == null || !list.any((x) => _intOrNull(x['id']) == selected)) {
        for (final x in list) {
          if ('${x['name']}'.trim().toLowerCase() ==
              '${d['supplier_name'] ?? ''}'.trim().toLowerCase()) {
            selected = _intOrNull(x['id']);
            break;
          }
        }
      }
      nf.text = '${d['invoice_number'] ?? ''}';
      batch.text = '${d['batch_number'] ?? ''}';
      liters.text = _num(d['total_liters']).toStringAsFixed(3).replaceFirst(RegExp(r'\.?0+$'), '');
      if (d['unit_cost'] != null) {
        cost.text = _num(d['unit_cost']).toStringAsFixed(4).replaceFirst(RegExp(r'\.?0+$'), '');
      }
      final configuredFuel = '${d['fuel_type'] ?? ''}'.trim();
      fuel = configuredFuel.isEmpty ? 'Diesel S10' : configuredFuel;
      if (mounted) {
        setState(() {
          detail = d;
          suppliers = list;
          supplierId = selected;
          loading = false;
        });
      }
    } catch (e) {
      if (mounted) {
        setState(() => loading = false);
        ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(content: Text('Erro ao carregar NF: ${_friendlyError(e)}')));
      }
    }
  }

  String supplierName() {
    for (final x in suppliers) {
      if (_intOrNull(x['id']) == supplierId) return '${x['name']}'.trim();
    }
    return '';
  }

  double? parseNumber(String value) =>
      double.tryParse(value.trim().replaceAll(',', '.'));

  bool nearly(double a, double b) => (a - b).abs() < 0.000001;

  Future<void> save() async {
    final d = detail;
    if (d == null || saving) return;
    final invoice = nf.text.trim();
    final supplier = supplierName();
    final amount = parseNumber(liters.text);
    final unitCost = d['unit_cost'] == null ? null : parseNumber(cost.text);
    final why = reason.text.trim();
    if (invoice.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Informe o número da Nota Fiscal.')));
      return;
    }
    if (supplier.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Selecione o fornecedor do combustível.')));
      return;
    }
    if (amount == null || amount <= 0) {
      ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Informe um volume válido.')));
      return;
    }
    if (d['unit_cost'] != null && (unitCost == null || unitCost <= 0)) {
      ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Informe um preço de compra/L válido.')));
      return;
    }
    if (why.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Informe o motivo da correção.')));
      return;
    }

    final changes = <String, dynamic>{};
    if (invoice != '${d['invoice_number'] ?? ''}'.trim()) changes['invoice_number'] = invoice;
    final newBatch = batch.text.trim();
    if (newBatch != '${d['batch_number'] ?? ''}'.trim()) changes['batch_number'] = newBatch;
    if (supplier.toLowerCase() != '${d['supplier_name'] ?? ''}'.trim().toLowerCase()) changes['supplier_name'] = supplier;
    if (fuel != '${d['fuel_type'] ?? ''}'.trim()) changes['fuel_type'] = fuel;
    if (!nearly(amount, _num(d['total_liters']))) changes['total_liters'] = amount;
    if (unitCost != null && !nearly(unitCost, _num(d['unit_cost']))) changes['unit_cost'] = unitCost;
    if (changes.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Nenhuma informação foi alterada.')));
      return;
    }

    final ok = await showDialog<bool>(
        context: context,
        builder: (_) => AlertDialog(
              title: const Text('Confirmar correção da Nota Fiscal?'),
              content: Text(
                  'NF: $invoice\nFornecedor: $supplier\nVolume: ${amount.toStringAsFixed(3)} L\n\nMotivo: $why\n\nA correção ficará registrada na auditoria. O sequencial da entrada (ER) será preservado e não será reutilizado.'),
              actions: [
                TextButton(
                    onPressed: () => Navigator.pop(context, false),
                    child: const Text('Voltar')),
                FilledButton(
                    onPressed: () => Navigator.pop(context, true),
                    child: const Text('Confirmar correção')),
              ],
            ));
    if (ok != true || !mounted) return;
    setState(() => saving = true);
    try {
      final result = await api.editReceivedInvoiceV92(widget.lotId, changes, why);
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(
          content: Text('NF ${result['invoice_number']} corrigida com sucesso. Sequencial preservado.')));
      Navigator.pop(context, true);
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(content: Text('Erro ao corrigir NF: ${_friendlyError(e)}')));
      }
    } finally {
      if (mounted) setState(() => saving = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final d = detail;
    final hasDownstream = d?['has_downstream'] == true;
    final volumeEditable = d?['volume_editable'] == true;
    return Scaffold(
        appBar: AppBar(title: const Text('Editar Nota Fiscal recebida')),
        body: loading
            ? const Center(child: CircularProgressIndicator())
            : d == null
                ? const Center(child: Text('Não foi possível carregar a Nota Fiscal.'))
                : ListView(padding: const EdgeInsets.all(16), children: [
                    const Card(
                        child: ListTile(
                            leading: Icon(Icons.history_edu_outlined, color: _blue),
                            title: Text('Correção auditada', style: TextStyle(fontWeight: FontWeight.w900)),
                            subtitle: Text('Use esta tela apenas para corrigir informação digitada errada. O registro original fica preservado no histórico de auditoria e o número sequencial ER não retroage.'))),
                    Card(
                        child: ListTile(
                            title: Text('${d['destination_code'] ?? '-'} • ${d['destination_name'] ?? '-'}', style: const TextStyle(fontWeight: FontWeight.w900)),
                            subtitle: Text('Recebida em ${_fmtDate(d['received_at'])}'))),
                    const SizedBox(height: 8),
                    DropdownButtonFormField<int>(
                        initialValue: supplierId,
                        isExpanded: true,
                        decoration: const InputDecoration(labelText: 'Fornecedor do combustível *'),
                        items: suppliers.map((x) => DropdownMenuItem(value: _intOrNull(x['id']), child: Text('${x['name']}'))).toList(),
                        onChanged: saving ? null : (v) => setState(() => supplierId = v)),
                    const SizedBox(height: 10),
                    TextField(controller: nf, enabled: !saving, decoration: const InputDecoration(labelText: 'Número da Nota Fiscal *')),
                    const SizedBox(height: 10),
                    TextField(controller: batch, enabled: !saving, decoration: const InputDecoration(labelText: 'Lote / remessa')),
                    const SizedBox(height: 10),
                    DropdownButtonFormField<String>(
                        initialValue: fuel,
                        decoration: InputDecoration(
                            labelText: 'Combustível *',
                            helperText: hasDownstream ? 'Bloqueado porque esta NF já teve transferência ou abastecimento.' : null),
                        items: <String>{..._fuelTypes, fuel}.map((x) => DropdownMenuItem(value: x, child: Text(x))).toList(),
                        onChanged: saving || hasDownstream ? null : (v) => setState(() => fuel = v ?? fuel)),
                    const SizedBox(height: 10),
                    TextField(
                        controller: liters,
                        enabled: !saving && volumeEditable,
                        keyboardType: const TextInputType.numberWithOptions(decimal: true),
                        decoration: InputDecoration(
                            labelText: 'Volume recebido (L) *',
                            helperText: volumeEditable
                                ? 'Pode ser corrigido porque esta NF ainda não teve saída.'
                                : 'Volume bloqueado: já houve movimentação/consumo desta NF.')),
                    if (d['unit_cost'] != null) ...[
                      const SizedBox(height: 10),
                      TextField(
                          controller: cost,
                          enabled: !saving,
                          keyboardType: const TextInputType.numberWithOptions(decimal: true),
                          decoration: const InputDecoration(
                              labelText: 'Preço de compra/L *',
                              helperText: 'Ao corrigir o custo, a rastreabilidade financeira ligada a esta NF é recalculada.')),
                    ],
                    const SizedBox(height: 10),
                    TextField(
                        controller: reason,
                        enabled: !saving,
                        maxLines: 3,
                        decoration: const InputDecoration(
                            labelText: 'Motivo da correção *',
                            hintText: 'Ex.: número da NF digitado incorretamente')),
                    const SizedBox(height: 18),
                    SizedBox(
                        height: 52,
                        child: FilledButton.icon(
                            onPressed: saving ? null : save,
                            icon: saving
                                ? const SizedBox(width: 18, height: 18, child: CircularProgressIndicator(strokeWidth: 2))
                                : const Icon(Icons.save_as_outlined),
                            label: Text(saving ? 'Salvando correção...' : 'Salvar correção'))),
                  ]));
  }
}

'''
if insert_anchor not in s: raise SystemExit('insert anchor missing')
s=s.replace(insert_anchor, edit_class+insert_anchor,1)

# version badge v91 -> v92 if exact string exists from prior patch
s=s.replace("Text('v91'", "Text('v92'", 1)

p.write_text(s)
print('V92_NF_EDIT_PATCH_APPLIED')
