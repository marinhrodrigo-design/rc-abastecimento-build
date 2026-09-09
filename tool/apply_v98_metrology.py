from pathlib import Path

p=Path('lib/main_online.dart')
s=p.read_text()

def rep(old,new,label,minimum=1):
    global s
    c=s.count(old)
    if c<minimum:
        raise SystemExit(f'{label}: expected at least {minimum}, found {c}')
    s=s.replace(old,new)

rep("Text('v97'", "Text('v98'", 'version')
rep("rca_reference_data_v97", "rca_reference_data_v98", 'reference rpc')
rep("rca_record_fueling_v97", "rca_record_fueling_v98", 'fueling rpc')
rep("metrologyFuelingCheckCachedV97", "metrologyFuelingCheckCachedV98", 'cached checker')
rep("metrologyFuelingCheckV97", "metrologyFuelingCheckV98", 'online checker')
rep("rca_metrology_fueling_check_v97", "rca_metrology_fueling_check_v98", 'check rpc')
rep("metrologyCloseEmptyV97", "metrologyCloseEmptyV98", 'close id')
rep("rca_metrology_close_empty_v97", "rca_metrology_close_empty_v98", 'close rpc')
rep("metrologyAuditV97", "metrologyAuditV98", 'audit id')
rep("rca_metrology_audit_v97", "rca_metrology_audit_v98", 'audit rpc')
rep("MetrologyAuditV97", "MetrologyAuditV98", 'audit screen')
rep("_metrologyLineV97", "_metrologyLineV98", 'audit line')

start=s.index('  Map<String, dynamic> metrologyFuelingCheckCachedV98(')
end=s.index('\n  Future<void> markMetrologyClosedOfflineV97', start)
new_func=r'''  Map<String, dynamic> metrologyFuelingCheckCachedV98(
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
    final tolerance = _num(tank['metrology_audit_tolerance_percent']) > 0
        ? _num(tank['metrology_audit_tolerance_percent'])
        : 6.0;
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
    final fueledBefore = fueled + queued;
    final fueledAfter = fueledBefore + requestedLiters;
    final alertStartLiters = transfer * (100 - tolerance) / 100;
    final serverRemaining = max(0.0, transfer - fueled - other);
    final queuedExtra = max(0.0, queued - serverRemaining);
    final remaining = max(0.0, serverRemaining - queued);
    final after = max(0.0, remaining - requestedLiters);
    final cap = transfer * tolerance / 100;
    final extraUsed = baseExtra + queuedExtra;
    final extraIf = max(0.0, requestedLiters - remaining);
    final extraRemaining = max(0.0, cap - extraUsed);
    final blocked = extraIf > extraRemaining + .000001;
    return {
      'is_comboio': true,
      'has_open_cycle': true,
      'blocked': blocked,
      'block_reason': blocked
          ? 'Limite da tolerância de auditoria atingido para esta transferência.'
          : null,
      'requires_presence_answer': fueledBefore >= alertStartLiters - .000001 ||
          fueledAfter >= alertStartLiters - .000001 ||
          extraIf > .000001,
      'transfer_liters': transfer,
      'audit_tolerance_percent': tolerance,
      'alert_start_percent': 100 - tolerance,
      'alert_start_liters': alertStartLiters,
      'fueled_liters_before': fueledBefore,
      'fueled_liters_after': fueledAfter,
      'fueled_percent_before': transfer > 0 ? fueledBefore / transfer * 100 : 0,
      'fueled_percent_after': transfer > 0 ? fueledAfter / transfer * 100 : 0,
      'registered_remaining_liters': remaining,
      'registered_remaining_after_liters': after,
      'final_window_liters': transfer * tolerance / 100,
      'final_window_percent': tolerance,
      'surplus_limit_liters': cap,
      'surplus_used_liters': extraUsed,
      'surplus_remaining_liters': extraRemaining,
      'surplus_if_completed_liters': extraIf,
      'surplus_code': tank['metrology_surplus_code'],
      'transfer_end_reached': remaining <= .000001,
    };
  }
'''
s=s[:start]+new_func+s[end:]

old="""          final remaining = _num(metrologyCheck['registered_remaining_liters']);
          final window = _num(metrologyCheck['final_window_liters']);
          final extraIf = _num(metrologyCheck['surplus_if_completed_liters']);
          final stillHasFuel = await showDialog<bool>(
"""
new="""          final remaining = _num(metrologyCheck['registered_remaining_liters']);
          final window = _num(metrologyCheck['final_window_liters']);
          final extraIf = _num(metrologyCheck['surplus_if_completed_liters']);
          final transferLiters = _num(metrologyCheck['transfer_liters']);
          final tolerance = _num(metrologyCheck['audit_tolerance_percent']);
          final fueledAfter = _num(metrologyCheck['fueled_liters_after']);
          final fueledPercentAfter = _num(metrologyCheck['fueled_percent_after']);
          final stillHasFuel = await showDialog<bool>(
"""
if s.count(old)!=1: raise SystemExit('dialog vars anchor mismatch')
s=s.replace(old,new,1)

old="""                    content: Text(extraIf > 0
                        ? 'O volume registrado da transferência está terminando. Este abastecimento usará ${_fmtLiters(extraIf)} além do volume transferido e essa parte será computada como sobra SB. Ainda há combustível fisicamente no CB?'
                        : 'A transferência entrou nos 6% finais (${_fmtLiters(window)}). Saldo registrado antes deste abastecimento: ${_fmtLiters(remaining)}. Esta confirmação será feita a cada abastecimento. Ainda há combustível fisicamente no CB?'),
"""
new="""                    content: Text(extraIf > 0
                        ? 'O volume abastecido ultrapassará a transferência de ${_fmtLiters(transferLiters)}. Este abastecimento levará o acumulado para ${_fmtLiters(fueledAfter)} (${fueledPercentAfter.toStringAsFixed(2)}% da transferência). A parte excedente será registrada como sobra SB. Tolerância de auditoria: ±${tolerance.toStringAsFixed(0)}%. Ainda há combustível fisicamente no CB?'
                        : 'O volume abastecido acumulado está chegando à faixa final da transferência de ${_fmtLiters(transferLiters)}. A conferência começa em ${(100 - tolerance).toStringAsFixed(0)}% abastecidos; margem de auditoria: ±${tolerance.toStringAsFixed(0)}% (${_fmtLiters(window)}). Saldo registrado antes deste abastecimento: ${_fmtLiters(remaining)}. Esta confirmação será feita a cada abastecimento. Ainda há combustível fisicamente no CB?'),
"""
if s.count(old)!=1: raise SystemExit('dialog content anchor mismatch')
s=s.replace(old,new,1)

old="""                  subtitle: Text('Litros • % • Valor pelo preço de compra • Valor pelo preço de venda'),
"""
new="""                  subtitle: Text('Litros • % • Valor pelo preço de compra • Valor pelo preço de venda • Tolerância de auditoria ±6%'),
"""
if s.count(old)!=1: raise SystemExit('audit header anchor mismatch')
s=s.replace(old,new,1)

old="""                  final direction = '${x['variation_direction'] ?? ''}';
                  return Card(
"""
new="""                  final direction = '${x['variation_direction'] ?? ''}';
                  final tolerance = _num(x['audit_tolerance_percent']) > 0
                      ? _num(x['audit_tolerance_percent'])
                      : 6.0;
                  final withinTolerance = x['audit_within_tolerance'] == true;
                  final fueled = _num(x['fueling_liters']);
                  return Card(
"""
if s.count(old)!=1: raise SystemExit('audit vars anchor mismatch')
s=s.replace(old,new,1)

old="""                        Text('Transferido: ${_fmtLiters(transferred)}${physical == null ? '' : ' • Físico apurado: ${_fmtLiters(physical)}'}',
                            style: const TextStyle(fontWeight: FontWeight.w700)),
"""
new="""                        Text('Transferido: ${_fmtLiters(transferred)} • Abastecido: ${_fmtLiters(fueled)}${physical == null ? '' : ' • Físico apurado: ${_fmtLiters(physical)}'}',
                            style: const TextStyle(fontWeight: FontWeight.w700)),
"""
if s.count(old)!=1: raise SystemExit('audit transferred anchor mismatch')
s=s.replace(old,new,1)

old="""                        if (closed && direction == 'positive')
                          const Text('Variação metrológica positiva',
                              style: TextStyle(fontWeight: FontWeight.w800, color: Colors.orange)),
                        const Divider(height: 22),
"""
new="""                        if (closed && direction == 'positive')
                          const Text('Variação metrológica positiva',
                              style: TextStyle(fontWeight: FontWeight.w800, color: Colors.orange)),
                        if (closed)
                          Text(withinTolerance
                              ? 'Dentro da tolerância de auditoria ±${tolerance.toStringAsFixed(0)}%'
                              : 'Fora da tolerância de auditoria ±${tolerance.toStringAsFixed(0)}%',
                              style: TextStyle(
                                  fontWeight: FontWeight.w900,
                                  color: withinTolerance ? Colors.green : Colors.redAccent)),
                        const Divider(height: 22),
"""
if s.count(old)!=1: raise SystemExit('audit status anchor mismatch')
s=s.replace(old,new,1)

p.write_text(s)
