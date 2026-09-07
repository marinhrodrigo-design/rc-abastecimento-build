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

# Helvetica used by the PDF package does not reliably render a few UI separators.
# Normalize only the two PDF generator classes, keeping the normal app UI unchanged.
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
]
missing = [x for x in required if x not in s]
if missing:
    raise SystemExit(f'Missing v90 preserved behavior: {missing}')

# Regression gate: unsupported separators must be absent specifically in PDF code.
fuel_start = s.index('class FuelPdfReport {')
work_start = s.index('class WorkFinalPdf {', fuel_start)
work_end = s.index('class AdminSecurityV35Screen', work_start)
pdf_region = s[fuel_start:work_end]
for bad in ('•', '→', '—', '–'):
    if bad in pdf_region:
        raise SystemExit(f'Unsupported PDF separator still present: {bad!r}')

p.write_text(s)
print('V90_FULL_QA_FIXES_OK')
