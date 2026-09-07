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

# Sanitize dynamic values before they reach the PDF renderer. The PDF uses
# Helvetica, which does not reliably render some UI separator glyphs.
fuel_marker = 'class FuelPdfReport {'
fuel_start = s.index(fuel_marker)
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
s = s[:fuel_start] + helper + s[fuel_start:]

fuel_build = "static Future<Uint8List> build(List<Map<String, dynamic>> items) async {\n"
if s.count(fuel_build) != 1:
    raise SystemExit(f'Fuel PDF build anchor count={s.count(fuel_build)}')
s = s.replace(fuel_build, fuel_build + "    items = items.map(_pdfSafeMapV90).toList();\n", 1)

work_build = "static Future<Uint8List> build(Map<String, dynamic> snapshot) async {\n"
if s.count(work_build) != 1:
    raise SystemExit(f'Work PDF build anchor count={s.count(work_build)}')
s = s.replace(work_build, work_build + "    snapshot = _pdfSafeMapV90(snapshot);\n", 1)

# Normalize static strings inside the PDF classes as well, while leaving the
# regular Flutter UI untouched.
fuel_start = s.index('class FuelPdfReport {')
work_start = s.index('class WorkFinalPdf {', fuel_start)
work_end = s.index('class AdminSecurityV35Screen', work_start)

def pdf_safe(segment: str) -> str:
    return (segment
            .replace('•', '-')
            .replace('→', '->')
            .replace('—', '-')
            .replace('–', '-'))

s = s[:fuel_start] + pdf_safe(s[fuel_start:work_start]) + pdf_safe(s[work_start:work_end]) + s[work_end:]

required = [
    "_hasValue(st?['plate'])",
    "vehicleLike(st, thirdParty: true)",
    "identityKind: (hasPlate || manualThird) ? 'plate' : 'side'",
    "rca_record_fueling_v71",
    "_measurementTypeForPdf",
    "'Foto do KM'",
    "'Foto do Horímetro'",
    "_pdfSafeMapV90",
]
missing = [x for x in required if x not in s]
if missing:
    raise SystemExit(f'Missing v90 preserved behavior: {missing}')

fuel_start = s.index('class FuelPdfReport {')
work_start = s.index('class WorkFinalPdf {', fuel_start)
work_end = s.index('class AdminSecurityV35Screen', work_start)
pdf_region = s[fuel_start:work_end]
for bad in ('•', '→', '—', '–'):
    if bad in pdf_region:
        raise SystemExit(f'Unsupported static PDF separator still present: {bad!r}')

p.write_text(s)
print('V90_FULL_QA_FIXES_OK')
