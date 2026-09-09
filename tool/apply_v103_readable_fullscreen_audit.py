from pathlib import Path

p = Path('lib/main_online.dart')
t = p.read_text()

if "Text('v102'" not in t:
    raise SystemExit('Expected exact V102 source marker not found')
t = t.replace("Text('v102'", "Text('v103'", 1)

old_hidden = """    'trace_id',\n  };"""
new_hidden = """    'trace_id',\n    'online',\n    'payload_online',\n    'captured_locally',\n    'event_at',\n    'event_type',\n    'app_state',\n    'visibility_state',\n  };"""
if old_hidden not in t:
    raise SystemExit('V102 hidden-field anchor not found')
t = t.replace(old_hidden, new_hidden, 1)

start_marker = """  Widget _auditDetailsV102(Map<String, dynamic> x, String user,\n      String detail, String table, String ref) {"""
if start_marker not in t:
    raise SystemExit('V102 audit details block not found')

helpers = r'''  Map<String, dynamic> _auditDataMapV103(dynamic raw) {
    final decoded = _auditDecodeV102(raw);
    if (decoded is Map) return Map<String, dynamic>.from(decoded);
    return <String, dynamic>{};
  }

  bool _auditLooksTechnicalReferenceV103(String value) {
    final x = value.trim();
    if (x.isEmpty || x == '—') return true;
    final uuid = RegExp(
      r'^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$',
    );
    return uuid.hasMatch(x) || x.length > 48;
  }

  String _auditUsefulReferenceV103(Map<String, dynamic> x, String rawRef) {
    final after = _auditDataMapV103(x['new_data']);
    final before = _auditDataMapV103(x['old_data']);
    final candidates = <dynamic>[
      x['movement_code'],
      after['movement_code'],
      before['movement_code'],
      after['invoice_number'],
      after['nf'],
      before['invoice_number'],
      before['nf'],
      after['unit_code'],
      after['tank_code'],
      before['unit_code'],
      before['tank_code'],
    ];
    for (final raw in candidates) {
      final s = safe(raw);
      if (s != '—' && !_auditLooksTechnicalReferenceV103(s)) return s;
    }
    return _auditLooksTechnicalReferenceV103(rawRef) ? '—' : rawRef;
  }

  String _auditAreaV103(dynamic raw) {
    final x = safe(raw).toLowerCase();
    const m = {
      'operation_audit_events': 'Auditoria operacional',
      'audit_events': 'Auditoria operacional',
      'movements': 'Movimentações de combustível',
      'tanks': 'Comboios / unidades',
      'active_sessions': 'Sessões do aplicativo',
      'unit_assignments': 'Uso de comboio',
      'managers': 'Usuários de gestão',
      'drivers': 'Usuários operacionais',
      'user_permissions': 'Permissões',
      'role_default_permissions': 'Permissões padrão',
      'works': 'Obras',
      'companies': 'Empresas',
      'receipt_lots': 'Notas fiscais / lotes',
      'refinery_receipts': 'Recebimentos',
      'machines': 'Ativos',
      'third_party_vehicles': 'Equipamentos de terceiros',
    };
    return m[x] ?? area(raw);
  }

  String _auditEventTypeV103(Map<String, dynamic> x) {
    final after = _auditDataMapV103(x['new_data']);
    final before = _auditDataMapV103(x['old_data']);
    return safe(after['event_type'] ?? before['event_type']).toLowerCase();
  }

  String _auditEventTitleV103(Map<String, dynamic> x, String detail) {
    final type = _auditEventTypeV103(x);
    const byType = {
      'app_lifecycle': 'Estado do aplicativo registrado',
      'app_visibility': 'Visibilidade do aplicativo registrada',
      'login': 'Entrada no aplicativo',
      'logout': 'Saída do aplicativo',
      'fueling': 'Abastecimento registrado',
      'unit_selected': 'Comboio selecionado',
      'unit_released': 'Comboio liberado',
      'unit_switched': 'Troca de comboio',
      'session_reclaimed': 'Sessão recuperada',
    };
    if (byType.containsKey(type)) return byType[type]!;
    final lower = detail.toLowerCase().trim();
    if (lower == 'evento registrado' || lower == '—') {
      final action = safe(x['action']).toLowerCase();
      const byAction = {
        'login': 'Entrada no aplicativo',
        'logout': 'Saída do aplicativo',
        'fueling': 'Abastecimento registrado',
        'insert': 'Cadastro realizado',
        'update': 'Alteração realizada',
        'delete': 'Exclusão realizada',
      };
      if (byAction.containsKey(action)) return byAction[action]!;
      return 'Evento operacional registrado';
    }
    return detail;
  }

  String _auditOriginV103(Map<String, dynamic> x) {
    final table = safe(x['table_name']).toLowerCase();
    if (table == 'operation_audit_events' || table == 'audit_events') {
      return 'Aplicativo R&C Abastecimento';
    }
    if (table == 'movements') return 'Movimentações de combustível';
    if (table == 'active_sessions') return 'Controle de acesso do aplicativo';
    if (table == 'unit_assignments') return 'Seleção e uso de comboio';
    return _auditAreaV103(x['table_name']);
  }

  String _auditReasonV103(Map<String, dynamic> x) {
    final type = _auditEventTypeV103(x);
    const byType = {
      'app_lifecycle':
          'Registro automático para manter o histórico de abertura, minimização, retorno e encerramento do aplicativo.',
      'app_visibility':
          'Registro automático para informar quando o aplicativo ficou visível ou foi para segundo plano.',
      'login':
          'Registro de auditoria criado quando o usuário entrou no aplicativo.',
      'logout':
          'Registro de auditoria criado quando o usuário saiu do aplicativo.',
      'fueling':
          'Registro criado para manter a rastreabilidade do abastecimento realizado.',
      'unit_selected':
          'Registro criado quando o operador selecionou um comboio para trabalhar.',
      'unit_released':
          'Registro criado quando o comboio foi liberado pelo operador.',
      'unit_switched':
          'Registro criado quando o operador trocou o comboio em uso.',
      'session_reclaimed':
          'Registro automático criado quando a sessão do aplicativo foi recuperada.',
    };
    if (byType.containsKey(type)) return byType[type]!;
    final action = safe(x['action']).toLowerCase();
    if (action.contains('login')) {
      return 'Registro de auditoria criado para documentar o acesso ao aplicativo.';
    }
    if (action.contains('logout')) {
      return 'Registro de auditoria criado para documentar a saída do aplicativo.';
    }
    return 'Registro criado automaticamente para manter a rastreabilidade e explicar quando uma informação foi criada ou alterada no sistema.';
  }

  Widget _auditDetailsV103(Map<String, dynamic> x, String user,
      String detail, String table, String ref) {
    final before = _auditReadableLinesV102(x['old_data']);
    final after = _auditReadableLinesV102(x['new_data']);
    final eventTitle = _auditEventTitleV103(x, detail);
    final areaLabel = _auditAreaV103(x['table_name']);
    final usefulRef = _auditUsefulReferenceV103(x, ref);
    final sections = <Widget>[
      Text(eventTitle,
          style: const TextStyle(fontSize: 20, fontWeight: FontWeight.w900)),
      const SizedBox(height: 14),
      SelectableText(
        'Data/hora: ${_fmtDate(x['created_at'])}\n'
        'Usuário: $user\n'
        'Origem: ${_auditOriginV103(x)}\n'
        'Área: $areaLabel'
        '${usefulRef == '—' ? '' : '\nReferência operacional: $usefulRef'}',
      ),
      const SizedBox(height: 16),
      const Text('Por que este registro existe?',
          style: TextStyle(fontWeight: FontWeight.w900)),
      const SizedBox(height: 6),
      Text(_auditReasonV103(x)),
    ];
    if (before.isNotEmpty) {
      sections.add(const SizedBox(height: 18));
      sections.add(const Text('Antes da alteração',
          style: TextStyle(fontWeight: FontWeight.w900)));
      sections.add(const SizedBox(height: 6));
      sections.add(SelectableText(before.join('\n')));
    }
    if (after.isNotEmpty) {
      sections.add(const SizedBox(height: 18));
      sections.add(Text(before.isEmpty ? 'Informações operacionais' : 'Depois da alteração',
          style: const TextStyle(fontWeight: FontWeight.w900)));
      sections.add(const SizedBox(height: 6));
      sections.add(SelectableText(after.join('\n')));
    }
    if (before.isEmpty && after.isEmpty) {
      sections.add(const SizedBox(height: 18));
      sections.add(const Text(
        'Este evento não possui outros dados operacionais úteis para exibição.',
        style: TextStyle(color: Colors.black54),
      ));
    }
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: sections,
    );
  }

  void _openAuditDetailsV103(
      Map<String, dynamic> x, String user, String detail, String table, String ref) {
    Navigator.push(
      context,
      MaterialPageRoute(
        builder: (_) => Scaffold(
          appBar: AppBar(title: const Text('Detalhes do registro')),
          body: SafeArea(
            child: ListView(
              padding: const EdgeInsets.fromLTRB(16, 16, 16, 36),
              children: [
                _auditDetailsV103(x, user, detail, table, ref),
              ],
            ),
          ),
        ),
      ),
    );
  }

'''
start = t.index(start_marker)
end = t.index('\n  @override\n  Widget build', start)
t = t[:start] + helpers + t[end:]

old_card = """                    final detail = safe(x['detail_text']);
                    final user = safe(x['user_name']);
                    final ref = safe(x['record_id']);
                    final table = area(x['table_name']);
                    return Card(
                        child: ListTile(
                      leading: const CircleAvatar(
                          child: Icon(Icons.receipt_long_outlined)),
                      title: Text(detail,
                          style: const TextStyle(fontWeight: FontWeight.w900)),
                      subtitle: Text(
                          '${_fmtDate(x['created_at'])}\\nUsuário: $user\\nÁrea: $table${ref == '—' ? '' : ' • Referência: $ref'}'),
                      isThreeLine: false,
                      onTap: () => showDialog(
                        context: context,
                        builder: (ctx) => AlertDialog(
                          title: const Text('Detalhes do registro'),
                          content: SingleChildScrollView(
                            child: _auditDetailsV102(x, user, detail, table, ref),
                          ),
                          actions: [
                            TextButton(
                                onPressed: () => Navigator.pop(ctx),
                                child: const Text('Fechar'))
                          ],
                        ),
                      ),
                    ));"""
new_card = """                    final detail = safe(x['detail_text']);
                    final user = safe(x['user_name']);
                    final ref = safe(x['record_id']);
                    final table = _auditAreaV103(x['table_name']);
                    final eventTitle = _auditEventTitleV103(x, detail);
                    final usefulRef = _auditUsefulReferenceV103(x, ref);
                    return Card(
                        child: ListTile(
                      leading: const CircleAvatar(
                          child: Icon(Icons.receipt_long_outlined)),
                      title: Text(eventTitle,
                          style: const TextStyle(fontWeight: FontWeight.w900)),
                      subtitle: Text(
                          '${_fmtDate(x['created_at'])}\\nUsuário: $user\\nOrigem: ${_auditOriginV103(x)}\\nÁrea: $table${usefulRef == '—' ? '' : ' • Ref.: $usefulRef'}'),
                      isThreeLine: false,
                      trailing: const Icon(Icons.chevron_right_rounded),
                      onTap: () =>
                          _openAuditDetailsV103(x, user, detail, table, ref),
                    ));"""
if old_card not in t:
    raise SystemExit('V102 audit card/dialog block not found')
t = t.replace(old_card, new_card, 1)

p.write_text(t)
print('V103 audit readability/fullscreen patch applied')
