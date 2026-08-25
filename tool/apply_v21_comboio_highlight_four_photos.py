from pathlib import Path

path = Path('lib/main_online.dart')
text = path.read_text()

def one(src: str, old: str, new: str, label: str) -> str:
    if old not in src:
        raise SystemExit(f'v21: marcador não encontrado: {label}')
    return src.replace(old, new, 1)

# 1) Novo abastecimento: mantém a primeira foto existente e permite mais 3,
# totalizando até 4 fotos sem alterar as demais evidências fotográficas.
fs = text.find('class _FuelingOnlineScreenState')
fe = text.find('class SignatureCaptureOnlineScreen', fs)
if fs < 0 or fe < 0:
    raise SystemExit('v21: FuelingOnlineScreen não encontrado')
fuel = text[fs:fe]

fuel = one(
    fuel,
    '  XFile? photo;\n',
    '  XFile? photo;\n  final List<XFile> extraFuelingPhotos = <XFile>[];\n',
    'lista de fotos do abastecimento',
)

fuel = one(
    fuel,
    "      final generalPhotos = <String>[];\n      final general = await uploadX(photo, 'abastecimento');\n      if (general != null) generalPhotos.add(general);",
    "      final generalPhotos = <String>[];\n      final localFuelingPhotos = <XFile>[if (photo != null) photo!, ...extraFuelingPhotos];\n      for (var i = 0; i < localFuelingPhotos.length; i++) {\n        final general = await uploadX(localFuelingPhotos[i], 'abastecimento_${i + 1}');\n        if (general != null) generalPhotos.add(general);\n      }",
    'upload das quatro fotos',
)

fuel = one(
    fuel,
    "            photoButton('Foto do abastecimento', photo, (x) => photo = x, required: stationary || isGalao),",
    "            fuelingPhotosBlock(required: stationary || isGalao),",
    'bloco de fotos no formulário',
)

photo_methods = r'''  int get fuelingPhotoCount => (photo == null ? 0 : 1) + extraFuelingPhotos.length;

  List<XFile> get fuelingPhotoFiles => <XFile>[
    if (photo != null) photo!,
    ...extraFuelingPhotos,
  ];

  Future<void> addFuelingPhoto() async {
    if (fuelingPhotoCount >= 4) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('É possível registrar no máximo 4 fotos do abastecimento.')),
        );
      }
      return;
    }
    final x = await camera();
    if (x == null || !mounted) return;
    setState(() {
      if (photo == null) {
        photo = x;
      } else {
        extraFuelingPhotos.add(x);
      }
    });
  }

  void removeFuelingPhoto(int index) {
    final files = fuelingPhotoFiles;
    if (index < 0 || index >= files.length) return;
    files.removeAt(index);
    setState(() {
      photo = files.isEmpty ? null : files.first;
      extraFuelingPhotos
        ..clear()
        ..addAll(files.skip(1));
    });
  }

  Widget fuelingPhotosBlock({required bool required}) {
    final files = fuelingPhotoFiles;
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        OutlinedButton.icon(
          onPressed: busy || files.length >= 4 ? null : addFuelingPhoto,
          icon: const Icon(Icons.add_a_photo_outlined),
          label: Text(
            files.isEmpty
                ? 'Fotos do abastecimento${required ? ' *' : ''} (0/4)'
                : 'Adicionar foto do abastecimento (${files.length}/4)',
          ),
        ),
        if (files.isNotEmpty) ...[
          const SizedBox(height: 8),
          Wrap(
            spacing: 8,
            runSpacing: 8,
            children: List.generate(files.length, (i) => Chip(
              avatar: const Icon(Icons.photo_outlined, size: 18),
              label: Text('Foto ${i + 1} ✓'),
              onDeleted: busy ? null : () => removeFuelingPhoto(i),
            )),
          ),
        ],
        if (required && files.isEmpty) ...[
          const SizedBox(height: 6),
          const Text('Pelo menos 1 foto é obrigatória.', style: TextStyle(fontSize: 12, color: Colors.redAccent)),
        ],
      ],
    );
  }

'''
fuel = one(fuel, '  Widget photoButton(', photo_methods + '  Widget photoButton(', 'métodos das fotos')
text = text[:fs] + fuel + text[fe:]

# 2) Identificação visual centralizada para Comboio -> Comboio.
helper_marker = 'class MyOnlineMovementsScreen extends StatefulWidget'
if helper_marker not in text:
    raise SystemExit('v21: marcador de Meus registros não encontrado')
helper = r'''const Color _comboioToComboioAccent = Color(0xFFE67E22);
const Color _comboioToComboioPale = Color(0xFFFFF3E5);

bool _isComboioToComboio(Map<String, dynamic> item) {
  if (item['comboio_to_comboio'] == true) return true;
  final sourceType = '${item['source_tank_type'] ?? ''}'.toLowerCase();
  if (sourceType != 'comboio') return false;
  final type = '${item['type'] ?? ''}';
  if (type == 'tank_transfer') {
    return '${item['destination_tank_type'] ?? ''}'.toLowerCase() == 'comboio';
  }
  if (type == 'fueling') {
    return '${item['asset_number'] ?? ''}'.trim().startsWith('008');
  }
  return false;
}

'''
text = text.replace(helper_marker, helper + helper_marker, 1)

# Meus registros: fundo laranja claro para o registro especial.
ms = text.find('class _MyOnlineMovementsScreenState')
me = text.find('class MovementDetailScreen', ms)
if ms < 0 or me < 0:
    raise SystemExit('v21: bloco Meus registros não encontrado')
my = text[ms:me]
my = one(
    my,
    '                      final selected = selectedCodes.contains(itemKey(x));\n',
    '                      final selected = selectedCodes.contains(itemKey(x));\n                      final comboioToComboio = _isComboioToComboio(x);\n',
    'flag Comboio para Comboio em Meus registros',
)
card_pos = my.find('                        child: Card(', my.find('final comboioToComboio'))
if card_pos < 0:
    raise SystemExit('v21: cartão de Meus registros não encontrado')
needle = '                        child: Card(\n'
if not my.startswith(needle, card_pos):
    raise SystemExit('v21: formato do cartão de Meus registros mudou')
my = my[:card_pos] + needle + '                          color: comboioToComboio ? _comboioToComboioPale : null,\n' + my[card_pos + len(needle):]
text = text[:ms] + my + text[me:]

# Pesquisa geral do admin: mesmo destaque visual.
admin_anchor = "            final assetText = x['asset_number'] ?? x['third_party_plate'] ?? x['destination_tank'] ?? x['source_tank'] ?? '';"
a = text.find(admin_anchor)
if a < 0:
    raise SystemExit('v21: cartão da pesquisa do admin não encontrado')
a_end = text.find('class MovementDetailScreen', a)
admin_piece = text[a:a_end]
admin_piece = one(
    admin_piece,
    '            final selected = selectedCodes.contains(itemKey(x));\n',
    '            final selected = selectedCodes.contains(itemKey(x));\n            final comboioToComboio = _isComboioToComboio(x);\n',
    'flag Comboio para Comboio na pesquisa admin',
)
admin_piece = one(
    admin_piece,
    '              child: Card(child: ListTile(',
    '              child: Card(color: comboioToComboio ? _comboioToComboioPale : null, child: ListTile(',
    'cor do cartão na pesquisa admin',
)
text = text[:a] + admin_piece + text[a_end:]

# Detalhe do registro: cartão principal recebe a mesma cor clara.
ds = text.find('class MovementDetailScreen')
de = text.find('class _RecordDetailData', ds)
if ds < 0 or de < 0:
    raise SystemExit('v21: detalhe do registro não encontrado')
detail = text[ds:de]
detail = one(
    detail,
    "    final fueling = '${item['type']}' == 'fueling';\n",
    "    final fueling = '${item['type']}' == 'fueling';\n    final comboioToComboio = _isComboioToComboio(item);\n",
    'flag no detalhe',
)
detail = one(
    detail,
    '          Card(child: Padding(',
    '          Card(color: comboioToComboio ? _comboioToComboioPale : null, child: Padding(',
    'cor no detalhe',
)
text = text[:ds] + detail + text[de:]

# 3) PDF: o layout fica igual; somente a paleta principal muda para laranja
# quando o movimento for Comboio -> Comboio.
ps = text.find('class FuelPdfReport')
pe = text.find('class AdminUsersOnlineScreen', ps)
if ps < 0 or pe < 0:
    raise SystemExit('v21: FuelPdfReport não encontrado')
pdf = text[ps:pe]
loop = '    for (final x in items) {\n'
pdf = one(
    pdf,
    loop,
    loop + "      final comboioToComboio = _isComboioToComboio(x);\n      final recordNavy = comboioToComboio ? PdfColor.fromHex('#9A4D00') : navy;\n      final recordRoyal = comboioToComboio ? PdfColor.fromHex('#E67E22') : royal;\n",
    'paleta especial do PDF',
)
loop_pos = pdf.find('    for (final x in items) {')
head = pdf[:loop_pos]
tail = pdf[loop_pos:]
tail = tail.replace('color: navy', 'color: recordNavy')
tail = tail.replace('color: royal', 'color: recordRoyal')
pdf = head + tail
text = text[:ps] + pdf + text[pe:]

# Garantias finais.
checks = [
    'extraFuelingPhotos',
    'files.length >= 4',
    "'abastecimento_${i + 1}'",
    '_isComboioToComboio',
    '_comboioToComboioAccent',
    '_comboioToComboioPale',
    'recordNavy',
    'recordRoyal',
    "signatureBox('Assinatura de quem recebeu'",
    "signatureBox('Assinatura de quem abasteceu'",
    'rca_report_company_for_movement',
    "evidence.add(MapEntry('Foto do abastecimento', p))",
]
for marker in checks:
    if marker not in text:
        raise SystemExit('v21: garantia ausente: ' + marker)

path.write_text(text)
print('v21 aplicado: destaque Comboio->Comboio e até 4 fotos no novo abastecimento.')
