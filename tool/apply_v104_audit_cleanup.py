from pathlib import Path

p = Path('lib/main_online.dart')
t = p.read_text()

if "Text('v103'" not in t:
    raise SystemExit('Expected exact V103 source marker not found')
t = t.replace("Text('v103'", "Text('v104'", 1)

anchor = """  List<Map<String, dynamic>> items = [];
  bool busy = false;"""
replacement = """  List<Map<String, dynamic>> items = [];
  bool busy = false;
  bool showTechnicalV104 = false;"""
if anchor not in t:
    raise SystemExit('Audit state anchor not found')
t = t.replace(anchor, replacement, 1)

insert_before = """  Widget _auditDetailsV103(Map<String, dynamic> x, String user,
      String detail, String table, String ref) {"""
if insert_before not in t:
    raise SystemExit('V103 detail anchor not found')
helpers = r'''  bool _isTechnicalAuditV104(Map<String, dynamic> x) {
    final type = _auditEventTypeV103(x);
    const technical = {
      'app_lifecycle',
      'app_visibility',
      'app_state',
      'app_foreground',
      'app_background',
      'app_resumed',
      'app_paused',
      'app_inactive',
      'app_hidden',
      'session_reclaimed',
      'heartbeat',
      'network_state',
      'connectivity',
      'sync',
    };
    if (technical.contains(type)) return true;
    final title = _auditEventTitleV103(x, safe(x['detail_text'])).toLowerCase();
    return title.contains('estado do aplicativo') ||
        title.contains('visibilidade do aplicativo') ||
        title.contains('sessão recuperada');
  }

  String _auditUsefulReferenceV104(Map<String, dynamic> x, String rawRef) {
    final after = _auditDataMapV103(x['new_data']);
    final before = _auditDataMapV103(x['old_data']);
    final candidates = <List<dynamic>>[
      ['Abastecimento', x['movement_code']],
      ['Abastecimento', after['movement_code']],
      ['Abastecimento', before['movement_code']],
      ['NF', after['invoice_number']],
      ['NF', after['nf']],
      ['NF', before['invoice_number']],
      ['NF', before['nf']],
      ['Comboio', after['unit_code']],
      ['Comboio', after['tank_code']],
      ['Comboio', before['unit_code']],
      ['Comboio', before['tank_code']],
    ];
    for (final pair in candidates) {
      final value = safe(pair[1]);
      if (value != '—' && !_auditLooksTechnicalReferenceV103(value)) {
        return '${pair[0]} $value';
      }
    }
    final raw = rawRef.trim();
    if (raw.isEmpty || raw == '—' || RegExp(r'^\d+$').hasMatch(raw) ||
        _auditLooksTechnicalReferenceV103(raw)) {
      return '—';
    }
    return raw;
  }

  String _auditAreaV104(Map<String, dynamic> x) {
    final type = _auditEventTypeV103(x);
    if (_isTechnicalAuditV104(x)) return 'Eventos técnicos do aplicativo';
    if (type == 'login' || type == 'logout') return 'Acesso ao aplicativo';
    if (type == 'unit_selected' || type == 'unit_released' || type == 'unit_switched') {
      return 'Comboios';
    }
    if (type == 'fueling') return 'Abastecimentos';
    final table = safe(x['table_name']).toLowerCase();
    if (table == 'registro') {
      final action = safe(x['action']).toLowerCase();
      if (action.contains('login') || action.contains('logout')) return 'Acesso ao aplicativo';
      return 'Auditoria operacional';
    }
    return _auditAreaV103(x['table_name']);
  }

  String _auditOriginV104(Map<String, dynamic> x) {
    final type = _auditEventTypeV103(x);
    if (_isTechnicalAuditV104(x)) return 'Aplicativo R&C Abastecimento';
    if (type == 'login' || type == 'logout') return 'Controle de acesso';
    if (type == 'unit_selected' || type == 'unit_released' || type == 'unit_switched') {
      return 'Uso de comboio';
    }
    if (type == 'fueling') return 'Movimentações de combustível';
    final table = safe(x['table_name']).toLowerCase();
    if (table == 'registro') {
      final action = safe(x['action']).toLowerCase();
      if (action.contains('login') || action.contains('logout')) return 'Controle de acesso';
      return 'R&C Abastecimento';
    }
    return _auditOriginV103(x);
  }

'''
t = t.replace(insert_before, helpers + insert_before, 1)

t = t.replace("final areaLabel = _auditAreaV103(x['table_name']);\n    final usefulRef = _auditUsefulReferenceV103(x, ref);",
              "final areaLabel = _auditAreaV104(x);\n    final usefulRef = _auditUsefulReferenceV104(x, ref);", 1)
t = t.replace("'Origem: ${_auditOriginV103(x)}\\n'", "'Origem: ${_auditOriginV104(x)}\\n'", 1)

start = t.index("  @override\n  Widget build(BuildContext context) => Scaffold(\n        appBar: AppBar(title: const Text('Auditoria • Registros')),")
end = t.index("\n}\n\nclass MetrologyAuditV98Screen", start)
new_build = r'''  @override
  Widget build(BuildContext context) {
    final visibleItems = items
        .where((x) => showTechnicalV104
            ? _isTechnicalAuditV104(x)
            : !_isTechnicalAuditV104(x))
        .toList();
    return Scaffold(
      appBar: AppBar(title: const Text('Auditoria • Registros')),
      body: RefreshIndicator(
        onRefresh: load,
        child: ListView(
          physics: const AlwaysScrollableScrollPhysics(),
          padding: const EdgeInsets.fromLTRB(12, 12, 12, 30),
          children: [
            TextField(
              controller: q,
              onSubmitted: (_) => load(),
              decoration: InputDecoration(
                labelText: 'Pesquisar',
                hintText: 'NF, comboio, abastecimento...',
                prefixIcon: const Icon(Icons.search),
                suffixIcon: IconButton(onPressed: load, icon: const Icon(Icons.search)),
              ),
            ),
            const SizedBox(height: 10),
            Card(
              child: ListTile(
                leading: const Icon(Icons.straighten_rounded, color: Colors.orange),
                title: const Text('Variação metrológica',
                    style: TextStyle(fontWeight: FontWeight.w900)),
                subtitle: const Text('SB/FT • Litros • % • Compra • Venda'),
                trailing: const Icon(Icons.chevron_right_rounded),
                onTap: () => Navigator.push(context,
                    MaterialPageRoute(builder: (_) => const MetrologyAuditV98Screen())),
              ),
            ),
            const SizedBox(height: 4),
            Wrap(
              spacing: 8,
              runSpacing: 8,
              children: [
                ChoiceChip(
                  label: const Text('Histórico geral'),
                  selected: !showTechnicalV104,
                  onSelected: (_) => setState(() => showTechnicalV104 = false),
                ),
                ChoiceChip(
                  label: const Text('Eventos técnicos do aplicativo'),
                  selected: showTechnicalV104,
                  onSelected: (_) => setState(() => showTechnicalV104 = true),
                ),
              ],
            ),
            const SizedBox(height: 8),
            if (busy) const LinearProgressIndicator(minHeight: 2),
            if (visibleItems.isEmpty && !busy)
              Card(
                child: ListTile(
                  title: Text(showTechnicalV104
                      ? 'Nenhum evento técnico encontrado.'
                      : 'Nenhum registro encontrado.'),
                ),
              ),
            ...visibleItems.map((x) {
              final detail = safe(x['detail_text']);
              final user = safe(x['user_name']);
              final ref = safe(x['record_id']);
              final table = _auditAreaV104(x);
              final eventTitle = _auditEventTitleV103(x, detail);
              final usefulRef = _auditUsefulReferenceV104(x, ref);
              final origin = _auditOriginV104(x);
              return Card(
                child: ListTile(
                  leading: CircleAvatar(
                    child: Icon(showTechnicalV104
                        ? Icons.settings_outlined
                        : Icons.receipt_long_outlined),
                  ),
                  title: Text(eventTitle,
                      style: const TextStyle(fontWeight: FontWeight.w900)),
                  subtitle: Text(
                    '${_fmtDate(x['created_at'])} • $user\n'
                    '$origin${usefulRef == '—' ? '' : ' • $usefulRef'}',
                  ),
                  trailing: const Icon(Icons.chevron_right_rounded),
                  onTap: () =>
                      _openAuditDetailsV103(x, user, detail, table, ref),
                ),
              );
            }),
          ],
        ),
      ),
    );
  }
'''
t = t[:start] + new_build + t[end:]

t = t.replace(
    "'Histórico geral e acesso à Variação metrológica com SB/FT e filtros'",
    "'Histórico e variação metrológica'",
    1,
)

p.write_text(t)
print('V104 audit cleanup patch applied')
