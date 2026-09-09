from pathlib import Path
p=Path('lib/main_online.dart')
s=p.read_text()
repls={
"rca_reference_data_v98":"rca_reference_data_v99",
"rca_record_transfer_te_v97":"rca_record_transfer_te_v99",
"rca_record_transfer_v97":"rca_record_transfer_v99",
"rca_record_fueling_v98":"rca_record_fueling_v99",
"rca_metrology_pretransfer_v97":"rca_metrology_pretransfer_v99",
"rca_metrology_fueling_check_v98":"rca_metrology_fueling_check_v99",
"rca_metrology_close_empty_v98":"rca_metrology_close_empty_v99",
"rca_metrology_audit_v98":"rca_metrology_audit_v99",
"metrologyPretransferV97":"metrologyPretransferV99",
"metrologyFuelingCheckV98":"metrologyFuelingCheckV99",
"metrologyCloseEmptyV98":"metrologyCloseEmptyV99",
"metrologyAuditV98":"metrologyAuditV99",
"Text('v98'":"Text('v99'",
}
for a,b in repls.items():
    if a not in s:
        raise SystemExit(f'missing marker: {a}')
    s=s.replace(a,b)

old="""          if (stillHasFuel != true) {
            await api.metrologyCloseEmptyV99(tankIdV87);
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
"""
new="""          if (stillHasFuel != true) {
            final closedMetrology = await api.metrologyCloseEmptyV99(tankIdV87);
            if (!offlineStore.online.value) {
              await offlineStore.markMetrologyClosedOfflineV97(tankIdV87);
            }
            if (!mounted) return;
            final ft = _map(closedMetrology['metrology_ft_event']);
            final ftCode = '${ft['code'] ?? ''}'.trim();
            final ftLiters = _num(ft['liters']);
            final ftPercent = _num(ft['percent_of_transfer']);
            final ftInvoice = '${ft['invoice_number'] ?? ''}'.trim();
            await offlineStore.recordEventV87('metrology_cb_empty_confirmed',
                tankId: tankIdV87,
                fuelingEventId: fuelingTraceIdV87,
                payload: {
                  'registered_remaining_liters': remaining,
                  'final_window_liters': window,
                  'requires_new_transfer': true,
                  if (ftCode.isNotEmpty) 'ft_code': ftCode,
                  if (ftLiters > 0) 'ft_liters': ftLiters,
                  if (ftPercent > 0) 'ft_percent': ftPercent,
                  if (ftInvoice.isNotEmpty) 'invoice_number': ftInvoice,
                });
            final ftText = ftCode.isNotEmpty && ftLiters > 0
                ? ' • $ftCode: ${_fmtLiters(ftLiters)} (${ftPercent.toStringAsFixed(2)}%)${ftInvoice.isEmpty ? '' : ' • NF $ftInvoice'}'
                : '';
            ScaffoldMessenger.of(context).showSnackBar(SnackBar(
                content: Text(
                    'CB informado como vazio$ftText. Variação negativa registrada; faça uma nova transferência antes do próximo abastecimento.')));
            return;
          }
"""
if old not in s: raise SystemExit('close flow marker missing')
s=s.replace(old,new)

old="""      final sbLiters = _num(r['metrology_surplus_liters']);
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
new="""      final sbLiters = _num(r['metrology_surplus_liters']);
      final sbCode = '${r['metrology_surplus_code'] ?? ''}'.trim();
      final sbPercent = _num(r['metrology_surplus_percent']);
      final sbInvoice = '${r['metrology_surplus_invoice_number'] ?? ''}'.trim();
      final reachedEnd = r['metrology_transfer_end_reached_now'] == true;
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(
          content: Text(r['queued'] == true
              ? 'Abastecimento salvo no aparelho ✓. Aguardando sincronização.'
              : sbLiters > 0
                  ? 'Abastecimento registrado ✓ • ${sbCode.isEmpty ? 'Sobra SB' : sbCode}: ${_fmtLiters(sbLiters)} (${sbPercent.toStringAsFixed(2)}%)${sbInvoice.isEmpty ? '' : ' • NF $sbInvoice'}.'
                  : reachedEnd
                      ? 'Abastecimento registrado ✓ • Volume transferido chegou ao fim. Cada próximo abastecimento excedente receberá um novo código SB.'
                      : 'Abastecimento registrado com sucesso ✓')));
"""
if old not in s: raise SystemExit('sb snackbar marker missing')
s=s.replace(old,new)

old="""                  subtitle: Text('Litros • % • Valor pelo preço de compra • Valor pelo preço de venda • Tolerância de auditoria ±6%'),
"""
new="""                  subtitle: Text('SB/FT por ocorrência • Litros • % • Valor de compra • Valor de venda • Diferença • Tolerância de auditoria ±6%'),
"""
if old not in s: raise SystemExit('audit subtitle marker missing')
s=s.replace(old,new)

old="""                  final sbCode = '${x['surplus_code'] ?? ''}'.trim();
                  final sbLiters = _num(x['positive_variation_fueling_liters']);
                  final direction = '${x['variation_direction'] ?? ''}';
"""
new="""                  final sbCode = '${x['surplus_code'] ?? ''}'.trim();
                  final sbLiters = _num(x['positive_variation_fueling_liters']);
                  final variationEvents = _rows(x['variation_events']);
                  final invoice = '${x['invoice_number'] ?? ''}'.trim();
                  final direction = '${x['variation_direction'] ?? ''}';
"""
if old not in s: raise SystemExit('audit vars marker missing')
s=s.replace(old,new)

old="""                        Text('Transferido: ${_fmtLiters(transferred)} • Abastecido: ${_fmtLiters(fueled)}${physical == null ? '' : ' • Físico apurado: ${_fmtLiters(physical)}'}',
                            style: const TextStyle(fontWeight: FontWeight.w700)),
                        if (sbCode.isNotEmpty)
                          Text('Sobra: $sbCode • ${_fmtLiters(sbLiters)}',
                              style: const TextStyle(fontWeight: FontWeight.w800, color: Colors.orange)),
"""
new="""                        Text('Transferido: ${_fmtLiters(transferred)} • Abastecido: ${_fmtLiters(fueled)}${physical == null ? '' : ' • Físico apurado: ${_fmtLiters(physical)}'}',
                            style: const TextStyle(fontWeight: FontWeight.w700)),
                        if (invoice.isNotEmpty)
                          Text('NF de origem: $invoice', style: const TextStyle(fontWeight: FontWeight.w700)),
                        if (variationEvents.isNotEmpty) ...[
                          const SizedBox(height: 8),
                          const Text('SB / FT desta transferência', style: TextStyle(fontWeight: FontWeight.w900)),
                          const SizedBox(height: 4),
                          ...variationEvents.map((e) {
                            final kind = '${e['event_kind'] ?? ''}';
                            final code = '${e['code'] ?? ''}';
                            final liters = _num(e['liters']);
                            final pct = _num(e['percent_of_transfer']);
                            final cb = '${e['tank_code'] ?? x['destination_code'] ?? 'CB'}';
                            final nf = '${e['invoice_number'] ?? invoice}'.trim();
                            final color = kind == 'FT' ? Colors.redAccent : Colors.orange;
                            return Padding(
                              padding: const EdgeInsets.only(bottom: 4),
                              child: Text('$code • ${_fmtLiters(liters)} • ${pct.toStringAsFixed(2)}% • $cb${nf.isEmpty ? '' : ' • NF $nf'}',
                                style: TextStyle(fontWeight: FontWeight.w800, color: color)),
                            );
                          }),
                        ] else if (sbCode.isNotEmpty)
                          Text('Sobra anterior: $sbCode • ${_fmtLiters(sbLiters)}',
                              style: const TextStyle(fontWeight: FontWeight.w800, color: Colors.orange)),
"""
if old not in s: raise SystemExit('audit event block marker missing')
s=s.replace(old,new)

old="""                        _metrologyLineV98('Litros', closed ? signedLiters(x['variation_liters']) : 'Em andamento'),
                        _metrologyLineV98('%', closed ? signedPercent(x['variation_percent']) : '—'),
                        _metrologyLineV98('Valor pelo preço de compra', closed ? signedMoney(x['variation_purchase_value']) : '—'),
                        _metrologyLineV98('Valor pelo preço de venda', closed ? signedMoney(x['variation_sale_value']) : '—'),
"""
new="""                        _metrologyLineV98('Litros', closed ? signedLiters(x['variation_liters']) : 'Em andamento'),
                        _metrologyLineV98('%', closed ? signedPercent(x['variation_percent']) : '—'),
                        _metrologyLineV98('Valor total de compra do volume variado', closed ? _fmtMoney(_num(x['variation_purchase_value_abs']).abs()) : '—'),
                        _metrologyLineV98('Valor total de venda do volume variado', closed ? _fmtMoney(_num(x['variation_sale_value_abs']).abs()) : '—'),
                        _metrologyLineV98('Diferença venda − compra', closed ? _fmtMoney(_num(x['variation_difference_value'])) : '—'),
"""
if old not in s: raise SystemExit('audit financial marker missing')
s=s.replace(old,new)

p.write_text(s)
print('V99 patch applied')
