from pathlib import Path
p=Path('lib/main_online.dart')
s=p.read_text()

def one(old,new,label):
    global s
    c=s.count(old)
    if c!=1:
        raise SystemExit(f'{label}: expected 1 anchor, found {c}')
    s=s.replace(old,new,1)

def many(old,new,min_count,label):
    global s
    c=s.count(old)
    if c<min_count:
        raise SystemExit(f'{label}: expected at least {min_count}, found {c}')
    s=s.replace(old,new)

one("Text('v96'", "Text('v97'", 'visible version')
many('rca_reference_data_v96','rca_reference_data_v97',4,'reference rpc')
many('rca_record_transfer_te_v96','rca_record_transfer_te_v97',1,'legacy transfer rpc')
many('rca_record_transfer_v96','rca_record_transfer_v97',1,'signed transfer rpc')
many('rca_record_fueling_v96','rca_record_fueling_v97',1,'fueling rpc')

anchor="""  Future<Map<String, dynamic>> executeOrQueue(
      String rpc, Map<String, dynamic> params) async {
"""
insert="""  Map<String, dynamic> metrologyFuelingCheckCachedV97(
      int tankId, double requestedLiters) {
    final base = _baseReferenceDataV69;
    Map<String, dynamic>? tank;
    for (final t in _rows(base?['tanks'])) {
      if (_intOrNull(t['id']) == tankId) {
        tank = t;
        break;
      }
    }
    if (tank == null || '${tank['tank_type'] ?? ''}' != 'comboio') {
      return {'is_comboio': false, 'requires_presence_answer': false, 'blocked': false};
    }
    if (tank['metrology_has_open_cycle'] != true) {
      return {
        'is_comboio': true,
        'has_open_cycle': false,
        'blocked': true,
        'block_reason': 'Nova transferência necessária antes do próximo abastecimento.'
      };
    }
    final transfer = _num(tank['metrology_transfer_liters']);
    final fueled = _num(tank['metrology_fueling_liters']);
    final other = _num(tank['metrology_other_outflow_liters']);
    final baseExtra = _num(tank['metrology_positive_extra_liters']);
    var queued = 0.0;
    for (final q in _queue) {
      if (q['sync_rejected'] == true) continue;
      if (q['sync_blocked'] == true && q['sync_conflict'] != true) continue;
      if (!_fuelingRpc('${q['rpc'] ?? ''}')) continue;
      final qp = _map(q['params']);
      if (_intOrNull(qp['p_source_tank_id']) == tankId) {
        queued += _num(qp['p_liters']);
      }
    }
    final serverRemaining = max(0.0, transfer - fueled - other);
    final queuedExtra = max(0.0, queued - serverRemaining);
    final remaining = max(0.0, serverRemaining - queued);
    final after = max(0.0, remaining - requestedLiters);
    final window = _num(tank['metrology_final_window_liters']) > 0
        ? _num(tank['metrology_final_window_liters'])
        : transfer * .06;
    final cap = _num(tank['metrology_surplus_limit_liters']) > 0
        ? _num(tank['metrology_surplus_limit_liters'])
        : transfer * .06;
    final extraUsed = baseExtra + queuedExtra;
    final extraIf = max(0.0, requestedLiters - remaining);
    final extraRemaining = max(0.0, cap - extraUsed);
    final blocked = extraIf > extraRemaining + .000001;
    return {
      'is_comboio': true,
      'has_open_cycle': true,
      'blocked': blocked,
      'block_reason': blocked
          ? 'Limite operacional da sobra SB atingido para esta transferência.'
          : null,
      'requires_presence_answer':
          remaining <= window + .000001 || after <= window + .000001,
      'registered_remaining_liters': remaining,
      'registered_remaining_after_liters': after,
      'final_window_liters': window,
      'final_window_percent': 6,
      'surplus_limit_liters': cap,
      'surplus_used_liters': extraUsed,
      'surplus_remaining_liters': extraRemaining,
      'surplus_if_completed_liters': extraIf,
      'surplus_code': tank['metrology_surplus_code'],
      'transfer_end_reached': remaining <= .000001,
    };
  }

  Future<void> markMetrologyClosedOfflineV97(int tankId) async {
    final base = _baseReferenceDataV69;
    if (base == null) return;
    final ref = _map(jsonDecode(jsonEncode(base)));
    final tanks = _rows(ref['tanks']);
    for (final t in tanks) {
      if (_intOrNull(t['id']) != tankId) continue;
      t['metrology_has_open_cycle'] = false;
      t['metrology_registered_remaining_liters'] = 0;
      t['metrology_operational_balance_liters'] = 0;
      t['current_balance_liters'] = 0;
      t['metrology_locally_closed_v97'] = true;
    }
    ref['tanks'] = tanks;
    await cacheReferenceData(ref);
  }

"""+anchor
one(anchor,insert,'offline metrology helpers')

old="""      final available = _balance(tankId);
      if (liters > available + 0.000001)
        throw Exception(
            'Saldo insuficiente para abastecimento offline. Disponível: ${_fmtLiters(available)}.');
"""
new="""      final available = _balance(tankId);
      if (rpc == 'rca_record_fueling_v97') {
        final check = metrologyFuelingCheckCachedV97(tankId, liters);
        if (check['is_comboio'] == true) {
          if (check['blocked'] == true) {
            throw Exception('${check['block_reason'] ?? 'Abastecimento bloqueado pela regra metrológica.'}');
          }
          if (check['requires_presence_answer'] == true &&
              params['p_metrology_presence_confirmed'] != true) {
            throw Exception('Confirme se ainda há combustível fisicamente no CB.');
          }
        } else if (liters > available + 0.000001) {
          throw Exception(
              'Saldo insuficiente para abastecimento offline. Disponível: ${_fmtLiters(available)}.');
        }
      } else if (liters > available + 0.000001) {
        throw Exception(
            'Saldo insuficiente para abastecimento offline. Disponível: ${_fmtLiters(available)}.');
      }
"""
one(old,new,'offline balance rule')

one("""          double? locationAccuracyM,
          required DateTime occurredAt}) async =>
      offlineStore.executeOrQueue('rca_record_fueling_v97', {
""", """          double? locationAccuracyM,
          required DateTime occurredAt,
          bool? metrologyPresenceConfirmed}) async =>
      offlineStore.executeOrQueue('rca_record_fueling_v97', {
""", 'fueling signature')
one("""        'p_offline_event_id': fuelingEventId,
        'p_is_offline': false
      });
""", """        'p_offline_event_id': fuelingEventId,
        'p_is_offline': false,
        'p_metrology_presence_confirmed': metrologyPresenceConfirmed
      });
""", 'fueling metrology param')

old="""  Future<Map<String, dynamic>> metrologyPretransferV96(int destinationTankId) async =>
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
"""
new="""  Future<Map<String, dynamic>> metrologyPretransferV97(int destinationTankId) async =>
      _map(await client.rpc('rca_metrology_pretransfer_v97',
          params: {'p_destination_tank_id': destinationTankId}));

  Future<Map<String, dynamic>> metrologyFuelingCheckV97(
          int tankId, double requestedLiters) async =>
      _map(await client.rpc('rca_metrology_fueling_check_v97', params: {
        'p_tank_id': tankId,
        'p_requested_liters': requestedLiters,
      }));

  Future<Map<String, dynamic>> metrologyCloseEmptyV97(int tankId) async =>
      offlineStore.executeOrQueue('rca_metrology_close_empty_v97', {
        'p_tank_id': tankId,
      });

  Future<Map<String, dynamic>> metrologyAuditV97({int limit = 500}) async =>
      _map(await client.rpc('rca_metrology_audit_v97',
          params: {'p_limit': limit}));
"""
one(old,new,'metrology API block')
many('metrologyPretransferV96','metrologyPretransferV97',2,'pretransfer method calls')
many('metrologyAuditV96','metrologyAuditV97',1,'audit method calls')

old="""      final manualThird = machine == null && third == -1;
      final r = await api.fuelingV71(
"""
new="""      final manualThird = machine == null && third == -1;
      bool? metrologyPresenceConfirmed;
      Map<String, dynamic>? metrologyCheck;
      if ('${widget.source['tank_type'] ?? ''}' == 'comboio') {
        metrologyCheck = offlineStore.online.value
            ? await api.metrologyFuelingCheckV97(tankIdV87, v)
            : offlineStore.metrologyFuelingCheckCachedV97(tankIdV87, v);
        if (metrologyCheck['blocked'] == true) {
          throw Exception('${metrologyCheck['block_reason'] ?? 'Abastecimento bloqueado pela regra metrológica.'}');
        }
        if (metrologyCheck['requires_presence_answer'] == true) {
          final remaining = _num(metrologyCheck['registered_remaining_liters']);
          final window = _num(metrologyCheck['final_window_liters']);
          final extraIf = _num(metrologyCheck['surplus_if_completed_liters']);
          final stillHasFuel = await showDialog<bool>(
              context: context,
              barrierDismissible: false,
              builder: (ctx) => AlertDialog(
                    title: const Text('Ainda há combustível no CB?'),
                    content: Text(extraIf > 0
                        ? 'O volume registrado da transferência está terminando. Este abastecimento usará ${_fmtLiters(extraIf)} além do volume transferido e essa parte será computada como sobra SB. Ainda há combustível fisicamente no CB?'
                        : 'A transferência entrou nos 6% finais (${_fmtLiters(window)}). Saldo registrado antes deste abastecimento: ${_fmtLiters(remaining)}. Esta confirmação será feita a cada abastecimento. Ainda há combustível fisicamente no CB?'),
                    actions: [
                      TextButton(
                          onPressed: () => Navigator.pop(ctx, false),
                          child: const Text('Não • CB vazio')),
                      FilledButton(
                          onPressed: () => Navigator.pop(ctx, true),
                          child: const Text('Sim, ainda há')),
                    ],
                  ));
          if (stillHasFuel != true) {
            await api.metrologyCloseEmptyV97(tankIdV87);
            if (!offlineStore.online.value) {
              await offlineStore.markMetrologyClosedOfflineV97(tankIdV87);
            }
            if (!mounted) return;
            await offlineStore.recordEventV87('metrology_cb_empty_confirmed',
                tankId: tankIdV87,
                fuelingEventId: fuelingTraceIdV87,
                payload: {
                  'registered_remaining_liters': remaining,
                  'final_window_liters': window,
                  'requires_new_transfer': true,
                });
            ScaffoldMessenger.of(context).showSnackBar(const SnackBar(
                content: Text(
                    'CB informado como vazio. Ciclo encerrado; faça uma nova transferência antes do próximo abastecimento.')));
            return;
          }
          metrologyPresenceConfirmed = true;
          await offlineStore.recordEventV87('metrology_fuel_present_confirmed',
              tankId: tankIdV87,
              fuelingEventId: fuelingTraceIdV87,
              payload: {
                'registered_remaining_liters': remaining,
                'final_window_liters': window,
                'surplus_if_completed_liters': extraIf,
              });
        }
      }
      final r = await api.fuelingV71(
"""
one(old,new,'fueling precheck insertion')
one("""          locationAccuracyM: locationAccuracyM,
          occurredAt: occurredAt);
""", """          locationAccuracyM: locationAccuracyM,
          occurredAt: occurredAt,
          metrologyPresenceConfirmed: metrologyPresenceConfirmed);
""", 'fueling call param')

old="""      if (r['queued'] != true && r['metrology_prompt_needed'] == true) {
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
"""
one(old,'','remove old post fueling prompt')

old="""      ScaffoldMessenger.of(context).showSnackBar(SnackBar(
          content: Text(r['queued'] == true
              ? 'Abastecimento salvo no aparelho ✓. Aguardando sincronização.'
              : 'Abastecimento registrado com sucesso ✓')));
"""
new="""      final sbLiters = _num(r['metrology_surplus_liters']);
      final sbCode = '${r['metrology_surplus_code'] ?? ''}'.trim();
      final reachedEnd = r['metrology_transfer_end_reached_now'] == true;
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(
          content: Text(r['queued'] == true
              ? 'Abastecimento salvo no aparelho ✓. Aguardando sincronização.'
              : sbLiters > 0
                  ? 'Abastecimento registrado ✓ • ${sbCode.isEmpty ? 'Sobra SB' : sbCode}: +${_fmtLiters(sbLiters)}.'
                  : reachedEnd
                      ? 'Abastecimento registrado ✓ • Volume transferido chegou ao fim. Próximos litros serão sobra SB.'
                      : 'Abastecimento registrado com sucesso ✓')));
"""
one(old,new,'success SB message')

many('MetrologyAuditV96Screen','MetrologyAuditV97Screen',7,'audit screen class')
many('_metrologyLineV96','_metrologyLineV97',5,'audit line helper')
one("""                  return Card(
                    child: Padding(
                      padding: const EdgeInsets.all(14),
                      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                        Text('$transfer • $route', style: const TextStyle(fontWeight: FontWeight.w900, fontSize: 16)),
                        const SizedBox(height: 3),
                        Text(_fmtDate(x['opened_at']), style: const TextStyle(color: Colors.black54)),
                        const Divider(height: 22),
                        _metrologyLineV97('Litros', closed ? signedLiters(x['variation_liters']) : 'Em andamento'),
""", """                  final transferred = _num(x['transfer_liters']);
                  final physical = x['physical_effective_liters'] == null
                      ? null
                      : _num(x['physical_effective_liters']);
                  final sbCode = '${x['surplus_code'] ?? ''}'.trim();
                  final sbLiters = _num(x['positive_variation_fueling_liters']);
                  final direction = '${x['variation_direction'] ?? ''}';
                  return Card(
                    child: Padding(
                      padding: const EdgeInsets.all(14),
                      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                        Text('$transfer • $route', style: const TextStyle(fontWeight: FontWeight.w900, fontSize: 16)),
                        const SizedBox(height: 3),
                        Text(_fmtDate(x['opened_at']), style: const TextStyle(color: Colors.black54)),
                        const SizedBox(height: 8),
                        Text('Transferido: ${_fmtLiters(transferred)}${physical == null ? '' : ' • Físico apurado: ${_fmtLiters(physical)}'}',
                            style: const TextStyle(fontWeight: FontWeight.w700)),
                        if (sbCode.isNotEmpty)
                          Text('Sobra: $sbCode • ${_fmtLiters(sbLiters)}',
                              style: const TextStyle(fontWeight: FontWeight.w800, color: Colors.orange)),
                        if (closed && direction == 'negative')
                          const Text('Variação metrológica negativa',
                              style: TextStyle(fontWeight: FontWeight.w800, color: Colors.redAccent)),
                        if (closed && direction == 'positive')
                          const Text('Variação metrológica positiva',
                              style: TextStyle(fontWeight: FontWeight.w800, color: Colors.orange)),
                        const Divider(height: 22),
                        _metrologyLineV97('Litros', closed ? signedLiters(x['variation_liters']) : 'Em andamento'),
""", 'audit traceability')

p.write_text(s)
print('V97_APP_PATCH_PASS')
