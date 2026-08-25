from pathlib import Path

path = Path('lib/main_online.dart')
text = path.read_text()

old = "      for (final p in _rowsFromPaths(x['photo_paths'])) { evidence.add(MapEntry('Foto do abastecimento', p)); }"
new = r'''      final fuelingPhotoPaths = <String>[];
      final rawFuelingPhotos = x['photo_paths'];
      if (rawFuelingPhotos is List) {
        for (final value in rawFuelingPhotos) {
          final p = '${value ?? ''}'.trim();
          if (p.isNotEmpty && p != 'null') fuelingPhotoPaths.add(p);
        }
      } else if (_hasValue(rawFuelingPhotos)) {
        final raw = '$rawFuelingPhotos'.trim();
        try {
          final decoded = jsonDecode(raw);
          if (decoded is List) {
            for (final value in decoded) {
              final p = '${value ?? ''}'.trim();
              if (p.isNotEmpty && p != 'null') fuelingPhotoPaths.add(p);
            }
          } else if (raw.isNotEmpty) {
            fuelingPhotoPaths.add(raw);
          }
        } catch (_) {
          if (raw.isNotEmpty) fuelingPhotoPaths.add(raw);
        }
      }
      for (final p in fuelingPhotoPaths) {
        evidence.add(MapEntry('Foto do abastecimento', p));
      }'''

if old not in text:
    raise SystemExit('v20: linha de foto do abastecimento no PDF não encontrada')

text = text.replace(old, new, 1)

# Validação: esta versão altera somente a leitura das fotos do abastecimento no PDF.
pdf_start = text.find('class FuelPdfReport {')
pdf_end = text.find('class AdminUsersOnlineScreen', pdf_start)
if pdf_start < 0 or pdf_end < 0:
    raise SystemExit('v20: classe FuelPdfReport não encontrada')
pdf = text[pdf_start:pdf_end]

required = [
    "final fuelingPhotoPaths = <String>[];",
    "final rawFuelingPhotos = x['photo_paths'];",
    "evidence.add(MapEntry('Foto do abastecimento', p));",
    "signatureBox('Assinatura de quem recebeu'",
    "signatureBox('Assinatura de quem abasteceu'",
    "rca_report_company_for_movement",
    "halfRow(Icons.location_on_outlined, 'Localização', location)",
    "halfRow(Icons.water_drop_outlined, 'Combustível', fuel)",
    "fullRow(Icons.local_gas_station_rounded, _movementLabelForItem(x), liters)",
]
for marker in required:
    if marker not in pdf:
        raise SystemExit(f'v20: marcador preservado ausente: {marker}')

if "for (final p in _rowsFromPaths(x['photo_paths']))" in pdf:
    raise SystemExit('v20: leitura antiga de photo_paths ainda presente')

path.write_text(text)
print('v20: somente a leitura da foto do abastecimento no PDF foi corrigida; demais recursos preservados.')
