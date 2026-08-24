from pathlib import Path

path = Path('lib/main_online.dart')
text = path.read_text()

old_class = '''class FuelPdfReport {
  static Future<Uint8List> build(List<Map<String, dynamic>> items) async {'''
new_class = '''class FuelPdfReport {
  static Future<Uint8List> _materialIconPng(IconData icon, Color color) async {
    const canvasSize = 64.0;
    const glyphSize = 48.0;
    final recorder = ui.PictureRecorder();
    final canvas = ui.Canvas(recorder);
    final painter = TextPainter(
      text: TextSpan(
        text: String.fromCharCode(icon.codePoint),
        style: TextStyle(
          fontFamily: icon.fontFamily,
          package: icon.fontPackage,
          fontSize: glyphSize,
          color: color,
        ),
      ),
      textDirection: ui.TextDirection.ltr,
      textAlign: TextAlign.center,
    );
    painter.layout();
    painter.paint(
      canvas,
      ui.Offset((canvasSize - painter.width) / 2, (canvasSize - painter.height) / 2),
    );
    final picture = recorder.endRecording();
    final image = await picture.toImage(canvasSize.toInt(), canvasSize.toInt());
    final data = await image.toByteData(format: ui.ImageByteFormat.png);
    image.dispose();
    picture.dispose();
    if (data == null) throw StateError('Falha ao preparar ícone para o PDF.');
    return data.buffer.asUint8List();
  }

  static Future<Uint8List> build(List<Map<String, dynamic>> items) async {'''
if old_class not in text:
    raise SystemExit('v16: início do FuelPdfReport não encontrado')
text = text.replace(old_class, new_class, 1)

old_font = '''    pw.Font? iconFont;
    try { iconFont = pw.Font.ttf(await rootBundle.load('assets/MaterialIcons-Regular.otf')); } catch (_) {}
'''
if old_font not in text:
    raise SystemExit('v16: carregamento antigo da fonte de ícones não encontrado')
text = text.replace(old_font, '', 1)

marker = '''    final lineColor = PdfColor.fromHex('#DCE5F0');

'''
insert = '''    final lineColor = PdfColor.fromHex('#DCE5F0');

    final materialIcons = <IconData>[
      Icons.location_city_outlined,
      Icons.location_on_outlined,
      Icons.water_drop_outlined,
      Icons.person_outline_rounded,
      Icons.speed_outlined,
      Icons.storage_outlined,
    ];
    final blueIconImages = <int, pw.MemoryImage>{};
    for (final icon in materialIcons) {
      blueIconImages[icon.codePoint] = pw.MemoryImage(await _materialIconPng(icon, _blue));
    }
    final headerIconImage = pw.MemoryImage(
      await _materialIconPng(Icons.local_gas_station_rounded, Colors.white),
    );

'''
if marker not in text:
    raise SystemExit('v16: marcador de cores do PDF não encontrado')
text = text.replace(marker, insert, 1)

old_material = '''    pw.Widget materialIcon(IconData icon, {double size = 18}) {
      if (iconFont == null) return pw.Container(width: size, height: size, decoration: pw.BoxDecoration(shape: pw.BoxShape.circle, color: blue));
      return pw.Icon(pw.IconData(icon.codePoint), font: iconFont, size: size, color: blue);
    }
'''
new_material = '''    pw.Widget materialIcon(IconData icon, {double size = 18}) {
      final image = blueIconImages[icon.codePoint];
      if (image == null) {
        return pw.Container(
          width: size,
          height: size,
          decoration: pw.BoxDecoration(shape: pw.BoxShape.circle, color: blue),
        );
      }
      return pw.SizedBox(
        width: size,
        height: size,
        child: pw.Image(image, fit: pw.BoxFit.contain),
      );
    }
'''
if old_material not in text:
    raise SystemExit('v16: materialIcon da v15 não encontrado')
text = text.replace(old_material, new_material, 1)

old_header = "pw.Container(width: 42, height: 42, decoration: pw.BoxDecoration(color: blue, shape: pw.BoxShape.circle), child: pw.Center(child: iconFont == null ? pw.Text('R&C', style: pw.TextStyle(font: bold, fontSize: 8, color: PdfColors.white)) : pw.Icon(pw.IconData(Icons.local_gas_station_rounded.codePoint), font: iconFont, size: 22, color: PdfColors.white))),"
new_header = "pw.Container(width: 42, height: 42, decoration: pw.BoxDecoration(color: blue, shape: pw.BoxShape.circle), child: pw.Center(child: pw.Image(headerIconImage, width: 22, height: 22, fit: pw.BoxFit.contain))),"
if old_header not in text:
    raise SystemExit('v16: ícone de cabeçalho da v15 não encontrado')
text = text.replace(old_header, new_header, 1)

pdf = text[text.index('class FuelPdfReport'):]
if 'pw.Icon(' in pdf:
    raise SystemExit('v16: ainda existe pw.Icon dentro do gerador de PDF')
if "pw.Font.ttf(await rootBundle.load('assets/MaterialIcons-Regular.otf'))" in pdf:
    raise SystemExit('v16: o PDF ainda tenta usar Material Icons como fonte textual')
if 'pw.Image(headerIconImage' not in pdf or 'blueIconImages' not in pdf:
    raise SystemExit('v16: rasterização dos ícones não foi aplicada')

path.write_text(text)
print('v16: ícones Material rasterizados pelo Flutter e incorporados ao PDF como PNG transparente.')
