from pathlib import Path

p=Path('lib/main_online.dart')
s=p.read_text()

def one(old,new,label):
    global s
    c=s.count(old)
    if c!=1:
        raise SystemExit(f'{label}: expected 1 anchor, found {c}')
    s=s.replace(old,new,1)

one("Text('v95'", "Text('v96'", 'version label')
c=s.count("rca_reference_data_v33")
if c < 1: raise SystemExit('reference rpc anchor missing')
s=s.replace("rca_reference_data_v33", "rca_reference_data_v96")

one("""  Future<Map<String, dynamic>> transfer({
    required int sourceTankId,
    required int destinationTankId,
    required double liters,
    String? notes,
  }) async {
    return offlineStore.executeOrQueue('rca_record_transfer', {
      'p_source_tank_id': sourceTankId,
      'p_destination_tank_id': destinationTankId,
      'p_liters': liters,
      'p_notes': notes,
    });
  }
""", """  Future<Map<String, dynamic>> transfer({
    required int sourceTankId,
    required int destinationTankId,
    required double liters,
    double? previousPhysicalLiters,
    String? notes,
  }) async {
    return _map(await client.rpc('rca_record_transfer_te_v96', params: {
      'p_source_tank_id': sourceTankId,
      'p_destination_tank_id': destinationTankId,
      'p_liters': liters,
      'p_previous_physical_liters': previousPhysicalLiters,
      'p_notes': notes,
    }));
  }
""", 'legacy transfer API')

one("""  Future<Map<String, dynamic>> transferV22(
          {required int sourceTankId,
          required int destinationTankId,
          required double liters,
          required String donor,
          required String receiver,
          required String donorSignature,
          required String receiverSignature,
          int? lotId,
          String? notes}) async =>
      _map(await client.rpc('rca_record_transfer_v22', params: {
        'p_source_tank_id': sourceTankId,
        'p_destination_tank_id': destinationTankId,
        'p_liters': liters,
        'p_donor_responsible': donor,
        'p_receiver_responsible': receiver,
        'p_donor_signature_path': donorSignature,
        'p_receiver_signature_path': receiverSignature,
        'p_lot_id': lotId,
        'p_notes': notes
      }));
""", """  Future<Map<String, dynamic>> transferV22(
          {required int sourceTankId,
          required int destinationTankId,
          required double liters,
          required String donor,
          required String receiver,
          required String donorSignature,
          required String receiverSignature,
          int? lotId,
          double? previousPhysicalLiters,
          String? notes}) async =>
      _map(await client.rpc('rca_record_transfer_v96', params: {
        'p_source_tank_id': sourceTankId,
        'p_destination_tank_id': destinationTankId,
        'p_liters': liters,
        'p_donor_responsible': donor,
        'p_receiver_responsible': receiver,
        'p_donor_signature_path': donorSignature,
        'p_receiver_signature_path': receiverSignature,
        'p_lot_id': lotId,
        'p_previous_physical_liters': previousPhysicalLiters,
        'p_notes': notes
      }));
""", 'signed transfer API')

one("offlineStore.executeOrQueue('rca_record_fueling_v71', {", "offlineStore.executeOrQueue('rca_record_fueling_v96', {", 'fueling rpc')

anchor="""  Future<List<Map<String, dynamic>>> offlineUnitUseConflictsV87() async =>
      _rows(await client.rpc('rca_offline_unit_use_conflicts_v87'));
"""
insert="""  Future<Map<String, dynamic>> metrologyPretransferV96(int destinationTankId) async =>
      _map(await client.rpc('rca_metrology_pretransfer_v96',
          params: {'p_destination_tank_id': destinationTankId}));

  Future<Map<String, dynamic>> metrologyConfirmExtraV96(int tankId) async =>
      _map(await client.rpc('rca_metrology_confirm_extra_v96',
          params: {'p_tank_id': tankId}));

  Future<Map<String, dynamic>> metrologyCloseEmptyV96(int tankId) async =>
      _map(await client.rpc('rca_metrology_close_empty_v96',
          params: {'p_tank_id': tankId}));

  Future<Map<String, dynamic>> metrologyAuditV96({int limit = 500}) async =>
      _map(await client.rpc('rca_metrology_audit_v96',
          params: {'p_limit': limit}));

"""+anchor
one(anchor,insert,'metrology API insertion')

old="""    final confirmed = await showDialog<bool>(
        context: context,
        builder: (ctx) => AlertDialog(
"""
new="""    double? previousPhysicalLiters;
    try {
      final prep = await api.metrologyPretransferV96(dest!);
      if (prep['requires_physical_balance'] == true) {
        final physical = TextEditingController();
        final raw = await showDialog<String>(
            context: context,
            builder: (ctx) => AlertDialog(
                  title: const Text('Conferência física obrigatória'),
                  content: Column(mainAxisSize: MainAxisSize.min, children: [
                    Text('Antes da nova transferência, informe quanto combustível ainda resta fisicamente no ${prep['code'] ?? 'CB'}.'),
                    const SizedBox(height: 10),
                    TextField(
                        controller: physical,
                        autofocus: true,
                        keyboardType: const TextInputType.numberWithOptions(decimal: true),
                        decoration: const InputDecoration(labelText: 'Saldo físico atual do CB (L) *')),
                  ]),
                  actions: [
                    TextButton(onPressed: () => Navigator.pop(ctx), child: const Text('Cancelar')),
                    FilledButton(onPressed: () => Navigator.pop(ctx, physical.text.trim()), child: const Text('Continuar')),
                  ],
                ));
        physical.dispose();
        if (raw == null || !mounted) return;
        previousPhysicalLiters = double.tryParse(raw.replaceAll(',', '.'));
        if (previousPhysicalLiters == null || previousPhysicalLiters! < 0) {
          ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Saldo físico do CB inválido.')));
          return;
        }
      }
    } catch (e) {
      if (mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(_friendlyError(e))));
      return;
    }

    final confirmed = await showDialog<bool>(
        context: context,
        builder: (ctx) => AlertDialog(
"""
one(old,new,'signed transfer precheck')

one("""          receiverSignature: paths[1]);
""", """          receiverSignature: paths[1],
          previousPhysicalLiters: previousPhysicalLiters);
""", 'signed transfer physical param')

one("""      final result = await api.transfer(
        sourceTankId: sourceTankId,
        destinationTankId: destination!,
        liters: double.parse(liters.text.replaceAll(',', '.')),
        notes: notes.text.trim(),
      );
""", """      double? previousPhysicalLiters;
      final prep = await api.metrologyPretransferV96(destination!);
      if (prep['requires_physical_balance'] == true) {
        final physical = TextEditingController();
        final raw = await showDialog<String>(
            context: context,
            builder: (ctx) => AlertDialog(
                  title: const Text('Conferência física obrigatória'),
                  content: Column(mainAxisSize: MainAxisSize.min, children: [
                    Text('Antes da nova transferência, informe quanto combustível ainda resta fisicamente no ${prep['code'] ?? 'CB'}.'),
                    const SizedBox(height: 10),
                    TextField(
                        controller: physical,
                        autofocus: true,
                        keyboardType: const TextInputType.numberWithOptions(decimal: true),
                        decoration: const InputDecoration(labelText: 'Saldo físico atual do CB (L) *')),
                  ]),
                  actions: [
                    TextButton(onPressed: () => Navigator.pop(ctx), child: const Text('Cancelar')),
                    FilledButton(onPressed: () => Navigator.pop(ctx, physical.text.trim()), child: const Text('Continuar')),
                  ],
                ));
        physical.dispose();
        if (raw == null || !mounted) return;
        previousPhysicalLiters = double.tryParse(raw.replaceAll(',', '.'));
        if (previousPhysicalLiters == null || previousPhysicalLiters! < 0) {
          throw Exception('Saldo físico do CB inválido.');
        }
      }
      final result = await api.transfer(
        sourceTankId: sourceTankId,
        destinationTankId: destination!,
        liters: double.parse(liters.text.replaceAll(',', '.')),
        previousPhysicalLiters: previousPhysicalLiters,
        notes: notes.text.trim(),
      );
""", 'legacy transfer precheck')

old="""      if (!mounted) return;
      await offlineStore.recordEventV87(
          r['queued'] == true ? 'fueling_saved_offline' : 'fueling_registered',
"""
new="""      if (!mounted) return;
      if (r['queued'] != true && r['metrology_prompt_needed'] == true) {
        final stillHasFuel = await showDialog<bool>(
            context: context,
            barrierDismissible: false,
            builder: (ctx) => AlertDialog(
                  title: const Text('Ainda há combustível no CB?'),
                  content: const Text('O volume registrado desta transferência terminou. Informe a situação física real do CB para continuar o controle metrológico.'),
                  actions: [
                    TextButton(onPressed: () => Navigator.pop(ctx, false), child: const Text('CB vazio')),
                    FilledButton(onPressed: () => Navigator.pop(ctx, true), child: const Text('Sim, ainda há')),
                  ],
                ));
        if (stillHasFuel == true) {
          await api.metrologyConfirmExtraV96(tankIdV87);
        } else {
          await api.metrologyCloseEmptyV96(tankIdV87);
        }
      }
      if (!mounted) return;
      await offlineStore.recordEventV87(
          r['queued'] == true ? 'fueling_saved_offline' : 'fueling_registered',
"""
one(old,new,'fueling metrology prompt')

old="""          const Padding(
              padding: EdgeInsets.fromLTRB(12, 0, 12, 8),
              child: Card(
                  child: ListTile(
                leading: Icon(Icons.history_rounded, color: _blue),
                title: Text('Histórico geral em ordem cronológica',
                    style: TextStyle(fontWeight: FontWeight.w900)),
                subtitle: Text(
                    'Login, seleção/troca/liberação de comboio, abastecimentos, conflitos e decisões, logout e demais alterações ficam concentrados aqui.'),
              ))),
"""
new="""          Padding(
              padding: const EdgeInsets.fromLTRB(12, 0, 12, 8),
              child: Card(
                  child: ListTile(
                leading: const Icon(Icons.straighten_rounded, color: Colors.orange),
                title: const Text('Variação metrológica',
                    style: TextStyle(fontWeight: FontWeight.w900)),
                subtitle: const Text(
                    'Cálculo por transferência: Litros • % • Valor pelo preço de compra • Valor pelo preço de venda.'),
                trailing: const Icon(Icons.chevron_right_rounded),
                onTap: () => Navigator.push(context,
                    MaterialPageRoute(builder: (_) => const MetrologyAuditV96Screen())),
              ))),
          const Padding(
              padding: EdgeInsets.fromLTRB(12, 0, 12, 8),
              child: Card(
                  child: ListTile(
                leading: Icon(Icons.history_rounded, color: _blue),
                title: Text('Histórico geral em ordem cronológica',
                    style: TextStyle(fontWeight: FontWeight.w900)),
                subtitle: Text(
                    'Login, seleção/troca/liberação de comboio, abastecimentos, conflitos e decisões, logout e demais alterações ficam concentrados aqui.'),
              ))),
"""
one(old,new,'audit card')

anchor="""class GlobalSearchV28Screen extends StatefulWidget {
"""
metrology="""class MetrologyAuditV96Screen extends StatefulWidget {
  const MetrologyAuditV96Screen({super.key});
  @override
  State<MetrologyAuditV96Screen> createState() => _MetrologyAuditV96ScreenState();
}

class _MetrologyAuditV96ScreenState extends State<MetrologyAuditV96Screen> {
  List<Map<String, dynamic>> cycles = [];
  bool busy = true;

  @override
  void initState() {
    super.initState();
    load();
  }

  Future<void> load() async {
    if (mounted) setState(() => busy = true);
    try {
      final data = await api.metrologyAuditV96(limit: 500);
      if (mounted) setState(() => cycles = _rows(data['cycles']));
    } catch (e) {
      if (mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(_friendlyError(e))));
    } finally {
      if (mounted) setState(() => busy = false);
    }
  }

  String signedLiters(dynamic value) {
    final n = _num(value);
    final sign = n > 0 ? '+' : n < 0 ? '-' : '';
    return '$sign${_fmtLiters(n.abs())}';
  }

  String signedPercent(dynamic value) {
    final n = _num(value);
    final sign = n > 0 ? '+' : n < 0 ? '-' : '';
    return '$sign${n.abs().toStringAsFixed(2)}%';
  }

  String signedMoney(dynamic value) {
    final n = _num(value);
    final sign = n > 0 ? '+ ' : n < 0 ? '- ' : '';
    return '$sign${_fmtMoney(n.abs())}';
  }

  @override
  Widget build(BuildContext context) => Scaffold(
        appBar: AppBar(title: const Text('Variação metrológica')),
        body: Column(children: [
          if (busy) const LinearProgressIndicator(minHeight: 2),
          Expanded(
              child: RefreshIndicator(
            onRefresh: load,
            child: ListView(
              padding: const EdgeInsets.fromLTRB(12, 12, 12, 30),
              children: [
                const Card(
                    child: ListTile(
                  leading: Icon(Icons.calculate_outlined, color: Colors.orange),
                  title: Text('Cálculo por transferência', style: TextStyle(fontWeight: FontWeight.w900)),
                  subtitle: Text('Litros • % • Valor pelo preço de compra • Valor pelo preço de venda'),
                )),
                if (cycles.isEmpty && !busy)
                  const Card(child: ListTile(title: Text('Nenhuma transferência metrológica registrada ainda.'))),
                ...cycles.map((x) {
                  final closed = '${x['status']}' == 'closed';
                  final transfer = '${x['transfer_code'] ?? '—'}';
                  final route = '${x['source_code'] ?? 'T.E.'} → ${x['destination_code'] ?? 'CB'}';
                  return Card(
                    child: Padding(
                      padding: const EdgeInsets.all(14),
                      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                        Text('$transfer • $route', style: const TextStyle(fontWeight: FontWeight.w900, fontSize: 16)),
                        const SizedBox(height: 3),
                        Text(_fmtDate(x['opened_at']), style: const TextStyle(color: Colors.black54)),
                        const Divider(height: 22),
                        _metrologyLineV96('Litros', closed ? signedLiters(x['variation_liters']) : 'Em andamento'),
                        _metrologyLineV96('%', closed ? signedPercent(x['variation_percent']) : '—'),
                        _metrologyLineV96('Valor pelo preço de compra', closed ? signedMoney(x['variation_purchase_value']) : '—'),
                        _metrologyLineV96('Valor pelo preço de venda', closed ? signedMoney(x['variation_sale_value']) : '—'),
                      ]),
                    ),
                  );
                }),
              ],
            ),
          )),
        ]),
      );
}

Widget _metrologyLineV96(String label, String value) => Padding(
      padding: const EdgeInsets.symmetric(vertical: 5),
      child: Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
        Expanded(child: Text(label, style: const TextStyle(fontWeight: FontWeight.w700))),
        const SizedBox(width: 12),
        Text(value, textAlign: TextAlign.right, style: const TextStyle(fontWeight: FontWeight.w900)),
      ]),
    );

"""+anchor
one(anchor,metrology,'metrology screen insertion')

if '±6%' in s or 'tolerance_percent' in s or 'metrology_tolerance_percent' in s:
    raise SystemExit('V96 must not expose or reference a ±6% tolerance')

p.write_text(s)
print('V96_METROLOGY_V2_PATCH_PASS')
