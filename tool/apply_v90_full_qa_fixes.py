from pathlib import Path

p = Path('lib/main_online.dart')
s = p.read_text()

old_code = """  String _offlineCodeV74(int tankId, int sequence) =>
      '${_sourceCodeV74(tankId)}-${sequence.toString().padLeft(6, '0')}';"""
new_code = """  String _offlineCodeV74(int tankId, int sequence) =>
      '${_sourceCodeV74(tankId)}-AB-${sequence.toString().padLeft(6, '0')}';"""
count = s.count(old_code)
if count != 1:
    raise SystemExit(f'Expected exactly one offline-code anchor, found {count}')
s = s.replace(old_code, new_code, 1)

dup = """    if (manualThird && thirdPlate.text.trim().isEmpty) {
      requiredMessage('Placa/Identificação do equipamento não cadastrado');
      return;
    }
    if (manualThird && thirdPlate.text.trim().isEmpty) {
      requiredMessage('Placa/Identificação');
      return;
    }"""
clean = """    if (manualThird && thirdPlate.text.trim().isEmpty) {
      requiredMessage('Placa/Identificação do equipamento não cadastrado');
      return;
    }"""
count = s.count(dup)
if count != 1:
    raise SystemExit(f'Expected duplicated manual-third validation once, found {count}')
s = s.replace(dup, clean, 1)

version_anchor = "Text('v89'"
count = s.count(version_anchor)
if count != 1:
    raise SystemExit(f'Expected one v89 visible label, found {count}')
s = s.replace(version_anchor, "Text('v90'", 1)

helper = r'''dynamic _pdfSafeValueV90(dynamic value) {
  if (value is String) {
    return value
        .replaceAll('•', '-')
        .replaceAll('→', '->')
        .replaceAll('—', '-')
        .replaceAll('–', '-');
  }
  if (value is Map) {
    return value.map((key, val) => MapEntry('$key', _pdfSafeValueV90(val)));
  }
  if (value is List) return value.map(_pdfSafeValueV90).toList();
  return value;
}

Map<String, dynamic> _pdfSafeMapV90(Map<String, dynamic> value) =>
    Map<String, dynamic>.from(_pdfSafeValueV90(value) as Map);

'''
fuel_marker = 'class FuelPdfReport {'
fuel_start = s.index(fuel_marker)
s = s[:fuel_start] + helper + s[fuel_start:]

fuel_build = "static Future<Uint8List> build(List<Map<String, dynamic>> items) async {\n"
if s.count(fuel_build) != 1:
    raise SystemExit(f'Fuel PDF build anchor count={s.count(fuel_build)}')
s = s.replace(fuel_build, fuel_build + "    items = items.map(_pdfSafeMapV90).toList();\n", 1)

work_build = "static Future<Uint8List> build(Map<String, dynamic> snapshot) async {\n"
if s.count(work_build) != 1:
    raise SystemExit(f'Work PDF build anchor count={s.count(work_build)}')
s = s.replace(work_build, work_build + "    snapshot = _pdfSafeMapV90(snapshot);\n", 1)

def pdf_safe(segment: str) -> str:
    return (segment
            .replace('•', '-')
            .replace('→', '->')
            .replace('—', '-')
            .replace('–', '-'))

work_start = s.index('class WorkFinalPdf {')
work_end = s.index('class AdminSecurityV35Screen', work_start)
s = s[:work_start] + pdf_safe(s[work_start:work_end]) + s[work_end:]

fuel_start = s.index('class FuelPdfReport {')
fuel_end = s.index('class AdminUsersOnlineScreen', fuel_start)
s = s[:fuel_start] + pdf_safe(s[fuel_start:fuel_end]) + s[fuel_end:]

record_start = s.index('  Future<void> recordEventV87(')
record_end = s.index('  Future<Map<String, dynamic>> syncAuditEventsV87()', record_start)
record_seg = s[record_start:record_end]
record_anchor = """  }) async {
    final uid = _activeUserKeyV78;"""
record_repl = """  }) async {
    final normalizedEventTypeV90 = eventType.trim().toLowerCase();
    if (normalizedEventTypeV90 == 'fueling_field_changed') return;
    final uid = _activeUserKeyV78;"""
if record_seg.count(record_anchor) != 1:
    raise SystemExit(f'Audit record anchor count={record_seg.count(record_anchor)}')
record_seg = record_seg.replace(record_anchor, record_repl, 1)
event_type_anchor = "'event_type': eventType.trim().toLowerCase(),"
if record_seg.count(event_type_anchor) != 1:
    raise SystemExit(f'Audit event type anchor count={record_seg.count(event_type_anchor)}')
record_seg = record_seg.replace(event_type_anchor, "'event_type': normalizedEventTypeV90,", 1)
s = s[:record_start] + record_seg + s[record_end:]

failed_anchor = """      await offlineStore.recordEventV87('fueling_submit_failed',
          tankId: _intOrNull(widget.source['id']),
          fuelingEventId: fuelingTraceIdV87,
          payload: {'error': _friendlyError(e)});"""
failed_repl = """      final failureMessageV90 = _friendlyError(e);
      await offlineStore.recordEventV87('fueling_submit_failed',
          tankId: _intOrNull(widget.source['id']),
          fuelingEventId: fuelingTraceIdV87,
          payload: {
            'error': failureMessageV90,
            'reason': failureMessageV90,
            'source_code': widget.source['code'],
            'work_id': work,
            'machine_id': machine,
            'third_party_vehicle_id': third == -1 ? null : third,
            'third_party_plate': third == -1 ? thirdPlate.text.trim() : null,
            'third_party_description':
                third == -1 ? thirdDescription.text.trim() : null,
            'fuel_type': fuel,
            'liters': v,
            'sale_price_per_liter': saleValue,
            'total_price': v * saleValue,
            'km': k,
            'hourmeter': h,
            'receiver': receiver.text.trim(),
          });
      if (offlineStore.backendReadyV81) {
        try {
          await offlineStore.syncAuditEventsV87();
        } catch (_) {}
      }"""
if s.count(failed_anchor) != 1:
    raise SystemExit(f'Fueling failure audit anchor count={s.count(failed_anchor)}')
s = s.replace(failed_anchor, failed_repl, 1)

required = [
    "_hasValue(st?['plate'])",
    "vehicleLike(st, thirdParty: true)",
    "identityKind: (hasPlate || manualThird) ? 'plate' : 'side'",
    "rca_record_fueling_v71",
    "_measurementTypeForPdf",
    "'Foto do KM'",
    "'Foto do Horímetro'",
    "_pdfSafeMapV90",
    "normalizedEventTypeV90 == 'fueling_field_changed'",
    "final failureMessageV90 = _friendlyError(e);",
]
missing = [x for x in required if x not in s]
if missing:
    raise SystemExit(f'Missing v90 preserved behavior: {missing}')

work_start = s.index('class WorkFinalPdf {')
work_end = s.index('class AdminSecurityV35Screen', work_start)
fuel_start = s.index('class FuelPdfReport {')
fuel_end = s.index('class AdminUsersOnlineScreen', fuel_start)
pdf_region = s[work_start:work_end] + s[fuel_start:fuel_end]
for bad in ('•', '→', '—', '–'):
    if bad in pdf_region:
        raise SystemExit(f'Unsupported static PDF separator still present: {bad!r}')

p.write_text(s)
print('V90_FULL_QA_FIXES_OK')
