from pathlib import Path
p=Path('lib/main_online.dart')
s=p.read_text()

def one(old,new,label):
    global s
    n=s.count(old)
    if n!=1:
        raise SystemExit(f'{label}: expected 1 occurrence, found {n}')
    s=s.replace(old,new,1)

one("child: Text('v99',", "child: Text('v100',", 'version marker')

old_api="""  Future<Map<String, dynamic>> metrologyAuditV99({int limit = 500}) async =>
      _map(await client.rpc('rca_metrology_audit_v99',
          params: {'p_limit': limit}));
"""
new_api=old_api+"""

  Future<Map<String, dynamic>> metrologyAuditV100({
    int limit = 500,
    int? tankId,
    DateTime? date,
    String? invoice,
  }) async {
    final day = date == null
        ? null
        : '${date.year.toString().padLeft(4, '0')}-${date.month.toString().padLeft(2, '0')}-${date.day.toString().padLeft(2, '0')}';
    return _map(await client.rpc('rca_metrology_audit_v100', params: {
      'p_tank_id': tankId,
      'p_date': day,
      'p_invoice': (invoice ?? '').trim().isEmpty ? null : invoice!.trim(),
      'p_limit': limit,
    }));
  }
"""
one(old_api,new_api,'api v100')

old_state="""class _MetrologyAuditV98ScreenState extends State<MetrologyAuditV98Screen> {
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
      final data = await api.metrologyAuditV99(limit: 500);
      if (mounted) setState(() => cycles = _rows(data['cycles']));
    } catch (e) {
      if (mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(_friendlyError(e))));
    } finally {
      if (mounted) setState(() => busy = false);
    }
  }
"""
new_state="""class _MetrologyAuditV98ScreenState extends State<MetrologyAuditV98Screen> {
  List<Map<String, dynamic>> cycles = [];
  List<Map<String, dynamic>> comboios = [];
  final nfFilterV100 = TextEditingController();
  int? comboioFilterV100;
  DateTime? dateFilterV100;
  bool busy = true;

  @override
  void initState() {
    super.initState();
    load();
  }

  @override
  void dispose() {
    nfFilterV100.dispose();
    super.dispose();
  }

  Future<void> load() async {
    if (mounted) setState(() => busy = true);
    try {
      final data = await api.metrologyAuditV100(
        limit: 500,
        tankId: comboioFilterV100,
        date: dateFilterV100,
        invoice: nfFilterV100.text,
      );
      if (mounted) {
        setState(() {
          cycles = _rows(data['cycles']);
          comboios = _rows(data['comboios']);
        });
      }
    } catch (e) {
      if (mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(_friendlyError(e))));
    } finally {
      if (mounted) setState(() => busy = false);
    }
  }

  Future<void> pickDateV100() async {
    final picked = await showDatePicker(
      context: context,
      initialDate: dateFilterV100 ?? DateTime.now(),
      firstDate: DateTime(2020, 1, 1),
      lastDate: DateTime.now().add(const Duration(days: 365)),
    );
    if (picked != null && mounted) setState(() => dateFilterV100 = picked);
  }

  void clearFiltersV100() {
    setState(() {
      comboioFilterV100 = null;
      dateFilterV100 = null;
      nfFilterV100.clear();
    });
    load();
  }

  String shortEventDateV100(dynamic value) {
    final raw = '${value ?? ''}'.trim();
    if (raw.isEmpty) return '—';
    final parsed = DateTime.tryParse(raw);
    if (parsed == null) return '—';
    final d = parsed.toLocal();
    String p2(int v) => v.toString().padLeft(2, '0');
    return '${p2(d.day)}/${p2(d.month)}/${p2(d.year % 100)} ${p2(d.hour)}:${p2(d.minute)}';
  }
"""
one(old_state,new_state,'screen state')

needle="""                const Card(
                    child: ListTile(
                  leading: Icon(Icons.calculate_outlined, color: Colors.orange),
                  title: Text('Cálculo por transferência', style: TextStyle(fontWeight: FontWeight.w900)),
                  subtitle: Text('SB/FT por ocorrência • Litros • % • Valor de compra • Valor de venda • Diferença • Tolerância de auditoria ±6%'),
                )),
"""
filters=needle+"""                Card(
                  child: Padding(
                    padding: const EdgeInsets.all(12),
                    child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                      const Text('Filtros', style: TextStyle(fontWeight: FontWeight.w900, fontSize: 16)),
                      const SizedBox(height: 10),
                      DropdownButtonFormField<int>(
                        value: comboioFilterV100 ?? -1,
                        decoration: const InputDecoration(labelText: 'Comboio', prefixIcon: Icon(Icons.local_shipping_outlined)),
                        items: [
                          const DropdownMenuItem(value: -1, child: Text('Todos os comboios')),
                          ...comboios.map((c) => DropdownMenuItem<int>(
                            value: _intOrNull(c['id']) ?? -999999,
                            child: Text('${c['code'] ?? 'CB'}${('${c['name'] ?? ''}'.trim()).isEmpty ? '' : ' • ${c['name']}'}'),
                          )),
                        ],
                        onChanged: busy ? null : (v) => setState(() => comboioFilterV100 = v == null || v < 0 ? null : v),
                      ),
                      const SizedBox(height: 10),
                      TextField(
                        controller: nfFilterV100,
                        textInputAction: TextInputAction.search,
                        onSubmitted: (_) => load(),
                        decoration: const InputDecoration(labelText: 'NF', hintText: 'Ex.: 1234', prefixIcon: Icon(Icons.receipt_long_outlined)),
                      ),
                      const SizedBox(height: 10),
                      Row(children: [
                        Expanded(
                          child: OutlinedButton.icon(
                            onPressed: busy ? null : pickDateV100,
                            icon: const Icon(Icons.calendar_month_outlined),
                            label: Text(dateFilterV100 == null
                                ? 'Data: todas'
                                : 'Data: ${dateFilterV100!.day.toString().padLeft(2, '0')}/${dateFilterV100!.month.toString().padLeft(2, '0')}/${dateFilterV100!.year}'),
                          ),
                        ),
                        if (dateFilterV100 != null) ...[
                          const SizedBox(width: 6),
                          IconButton(
                            tooltip: 'Limpar data',
                            onPressed: busy ? null : () => setState(() => dateFilterV100 = null),
                            icon: const Icon(Icons.close),
                          ),
                        ],
                      ]),
                      const SizedBox(height: 8),
                      Row(children: [
                        Expanded(child: FilledButton.icon(onPressed: busy ? null : load, icon: const Icon(Icons.search), label: const Text('Pesquisar'))),
                        const SizedBox(width: 8),
                        Expanded(child: OutlinedButton.icon(onPressed: busy ? null : clearFiltersV100, icon: const Icon(Icons.filter_alt_off_outlined), label: const Text('Limpar'))),
                      ]),
                    ]),
                  ),
                ),
"""
one(needle,filters,'filters card')

old_event="""                            final cb = '${e['tank_code'] ?? x['destination_code'] ?? 'CB'}';
                            final nf = '${e['invoice_number'] ?? invoice}'.trim();
                            final color = kind == 'FT' ? Colors.redAccent : Colors.orange;
                            return Padding(
                              padding: const EdgeInsets.only(bottom: 4),
                              child: Text('$code • ${_fmtLiters(liters)} • ${pct.toStringAsFixed(2)}% • $cb${nf.isEmpty ? '' : ' • NF $nf'}',
                                style: TextStyle(fontWeight: FontWeight.w800, color: color)),
                            );
"""
new_event="""                            final cb = '${e['tank_code'] ?? x['destination_code'] ?? 'CB'}';
                            final nf = '${e['invoice_number'] ?? invoice}'.trim();
                            final operatorName = '${e['operator_name'] ?? 'Usuário'}'.trim();
                            final eventAt = shortEventDateV100(e['event_at'] ?? e['created_at']);
                            final purchase = _fmtMoney(_num(e['purchase_value']).abs());
                            final sale = _fmtMoney(_num(e['sale_value']).abs());
                            final difference = _fmtMoney(_num(e['difference_value']));
                            final color = kind == 'FT' ? Colors.redAccent : Colors.orange;
                            final line = '$eventAt - ${operatorName.isEmpty ? 'Usuário' : operatorName} | $cb | $code | ${_fmtLiters(liters)} | ${pct.toStringAsFixed(2)}%${nf.isEmpty ? '' : ' | NF $nf'} | Compra $purchase | Venda $sale | Diferença $difference';
                            return Padding(
                              padding: const EdgeInsets.only(bottom: 6),
                              child: SelectableText(line,
                                style: TextStyle(fontWeight: FontWeight.w800, color: color)),
                            );
"""
one(old_event,new_event,'event display')

p.write_text(s)
print('V100_APP_PATCH_OK')
