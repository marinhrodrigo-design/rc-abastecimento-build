from pathlib import Path

p = Path('lib/main_online.dart')
s = p.read_text()

old_code = """  String _offlineCodeV74(int tankId, int sequence) =>
      '${_sourceCodeV74(tankId)}-${sequence.toString().padLeft(6, '0')}';"""
new_code = """  String _offlineCodeV74(int tankId, int sequence) =>
      '${_sourceCodeV74(tankId)}-AB-${sequence.toString().padLeft(6, '0')}';"""
if s.count(old_code) != 1:
    raise SystemExit(f'Expected exactly one offline-code anchor, found {s.count(old_code)}')
s = s.replace(old_code, new_code, 1)

# Remove duplicated manual-third-party plate/identifier validation while preserving
# the clearer user-facing message.
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
if s.count(dup) != 1:
    raise SystemExit(f'Expected duplicated manual-third validation once, found {s.count(dup)}')
s = s.replace(dup, clean, 1)

# Promote visible version label only. Do not touch historical migration/RPC labels.
if s.count("Text('v89'") != 1:
    raise SystemExit(f'Expected one v89 visible label, found {s.count("Text(\'v89\'") }')
s = s.replace("Text('v89'", "Text('v90'", 1)

# Regression assertions for registered third-party equipment: a saved plate must
# require plate evidence and use KM classification on the app side.
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

p.write_text(s)
print('V90_FULL_QA_FIXES_OK')
