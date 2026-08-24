from pathlib import Path

path = Path('lib/main_online.dart')
text = path.read_text()
start = text.find('class FuelPdfReport {')
end = text.find('class AdminUsersOnlineScreen', start)
if start < 0 or end < 0:
    raise SystemExit('v17: classe FuelPdfReport ou marcador seguinte não encontrado')

new_class = r'''class FuelPdfReport {
  static const Color _iconBlue = Color(0xFF08367C);

  static Future<Uint8List> _materialIconPng(IconData icon, Color color) async {
    const canvasSize = 72.0;
    const glyphSize = 52.0;
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

  static String _brNumber(dynamic value, {bool liters = false}) {
    final n = _num(value);
    final fixed = n.toStringAsFixed(1);
    final parts = fixed.split('.');
    final raw = parts.first;
    final chars = raw.split('').reversed.toList();
    final grouped = <String>[];
    for (var i = 0; i < chars.length; i++) {
      if (i > 0 && i % 3 == 0) grouped.add('.');
      grouped.add(chars[i]);
    }
    final integer = grouped.reversed.join();
    final result = '$integer,${parts.length > 1 ? parts[1] : '0'}';
    return liters ? '$result L' : result;
  }

  static String _meter(dynamic value) {
    if (value == null) return '-';
    final n = _num(value);
    if (n == n.roundToDouble()) {
      final raw = n.round().toString();
      final chars = raw.split('').reversed.toList();
      final grouped = <String>[];
      for (var i = 0; i < chars.length; i++) {
        if (i > 0 && i % 3 == 0) grouped.add('.');
        grouped.add(chars[i]);
      }
      return grouped.reversed.join();
    }
    return _brNumber(n);
  }

  static Future<Uint8List> build(List<Map<String, dynamic>> items) async {
    final doc = pw.Document();
    Map<String, dynamic> company = const {};
    try {
      company = _map(await api.client.rpc('rca_report_company'));
    } catch (_) {}

    final companyName = _hasValue(company['company_name']) ? '${company['company_name']}' : 'Hydra';
    final companySubtitle = _hasValue(company['company_subtitle']) ? '${company['company_subtitle']}' : 'Equipamentos';
    final companyDocument = _hasValue(company['document']) ? '${company['document']}' : '-';
    final companyAddress = _hasValue(company['address']) ? '${company['address']}' : '-';

    final regular = pw.Font.helvetica();
    final bold = pw.Font.helveticaBold();
    final navy = PdfColor.fromHex('#062A69');
    final royal = PdfColor.fromHex('#0E58C7');
    final pale = PdfColor.fromHex('#EEF5FF');
    final lineColor = PdfColor.fromHex('#D9E2EE');
    final textColor = PdfColor.fromHex('#20242B');

    final icons = <IconData>[
      Icons.local_gas_station_rounded,
      Icons.location_city_outlined,
      Icons.water_drop_outlined,
      Icons.location_on_outlined,
      Icons.person_outline_rounded,
      Icons.speed_outlined,
      Icons.storage_outlined,
      Icons.assignment_outlined,
      Icons.draw_outlined,
    ];
    final blueIcons = <int, pw.MemoryImage>{};
    final whiteIcons = <int, pw.MemoryImage>{};
    for (final icon in icons) {
      blueIcons[icon.codePoint] = pw.MemoryImage(await _materialIconPng(icon, _iconBlue));
    }
    whiteIcons[Icons.local_gas_station_rounded.codePoint] = pw.MemoryImage(
      await _materialIconPng(Icons.local_gas_station_rounded, Colors.white),
    );

    pw.Widget icon(IconData data, {double size = 25, bool white = false}) {
      final image = (white ? whiteIcons : blueIcons)[data.codePoint];
      if (image == null) return pw.SizedBox(width: size, height: size);
      return pw.Image(image, width: size, height: size, fit: pw.BoxFit.contain);
    }

    pw.Widget rule() => pw.Container(height: 0.7, color: lineColor);

    pw.Widget fullRow(IconData data, String label, String value, {double height = 55}) {
      return pw.Container(
        height: height,
        child: pw.Row(crossAxisAlignment: pw.CrossAxisAlignment.center, children: [
          pw.SizedBox(width: 42, child: pw.Center(child: icon(data, size: 25))),
          pw.SizedBox(width: 10),
          pw.Expanded(child: pw.Column(
            mainAxisAlignment: pw.MainAxisAlignment.center,
            crossAxisAlignment: pw.CrossAxisAlignment.start,
            children: [
              pw.Text(label, style: pw.TextStyle(font: bold, fontSize: 11.5, color: royal)),
              pw.SizedBox(height: 4),
              pw.Text(value, style: pw.TextStyle(font: regular, fontSize: 13.5, color: textColor)),
            ],
          )),
        ]),
      );
    }

    pw.Widget halfRow(IconData data, String label, String value) {
      return pw.Expanded(child: pw.Padding(
        padding: const pw.EdgeInsets.symmetric(vertical: 10, horizontal: 6),
        child: pw.Row(crossAxisAlignment: pw.CrossAxisAlignment.center, children: [
          pw.SizedBox(width: 38, child: pw.Center(child: icon(data, size: 24))),
          pw.SizedBox(width: 8),
          pw.Expanded(child: pw.Column(
            mainAxisAlignment: pw.MainAxisAlignment.center,
            crossAxisAlignment: pw.CrossAxisAlignment.start,
            children: [
              pw.Text(label, style: pw.TextStyle(font: bold, fontSize: 10.7, color: royal)),
              pw.SizedBox(height: 4),
              pw.Text(value, style: pw.TextStyle(font: regular, fontSize: 13, color: textColor)),
            ],
          )),
        ]),
      ));
    }

    pw.Widget signatureBox(String title, String name, Uint8List? bytes) {
      return pw.Expanded(child: pw.Container(
        height: 94,
        padding: const pw.EdgeInsets.fromLTRB(10, 8, 10, 7),
        decoration: pw.BoxDecoration(
          border: pw.Border.all(color: lineColor, width: 0.8),
          borderRadius: const pw.BorderRadius.all(pw.Radius.circular(7)),
        ),
        child: pw.Column(crossAxisAlignment: pw.CrossAxisAlignment.start, children: [
          pw.Row(children: [
            icon(Icons.draw_outlined, size: 17),
            pw.SizedBox(width: 5),
            pw.Text(title, style: pw.TextStyle(font: bold, fontSize: 9.5, color: royal)),
          ]),
          pw.SizedBox(height: 5),
          pw.Expanded(child: pw.Center(
            child: bytes == null
              ? pw.Text('Assinatura não disponível', style: pw.TextStyle(font: regular, fontSize: 8, color: PdfColors.grey600))
              : pw.Image(pw.MemoryImage(bytes), fit: pw.BoxFit.contain),
          )),
          pw.Container(height: 0.6, color: lineColor),
          pw.SizedBox(height: 3),
          pw.Text(name, maxLines: 1, style: pw.TextStyle(font: regular, fontSize: 8.5, color: textColor)),
        ]),
      ));
    }

    for (final x in items) {
      final asset = _hasValue(x['asset_number'])
          ? '${x['asset_number']}'
          : _hasValue(x['third_party_plate'])
              ? '${x['third_party_plate']}'
              : _hasValue(x['destination_tank'])
                  ? '${x['destination_tank']}'
                  : _hasValue(x['source_tank'])
                      ? '${x['source_tank']}'
                      : '-';
      final title = '${_movementLabelForItem(x)} • $asset';
      final liters = _brNumber(x['liters'], liters: true);
      final work = _hasValue(x['work']) ? '${x['work']}' : '-';
      final fuel = _hasValue(x['fuel_type']) ? '${x['fuel_type']}' : '-';
      final location = _hasValue(x['location_address'])
          ? '${x['location_address']}'
          : (x['latitude'] != null && x['longitude'] != null)
              ? '${x['latitude']}, ${x['longitude']}'
              : '-';
      final receiver = _hasValue(x['receiver']) ? '${x['receiver']}' : '-';
      final operator = _hasValue(x['operator']) ? '${x['operator']}' : '-';
      final km = x['km_unavailable'] == true ? 'Indisponível' : _meter(x['km_hourmeter']);
      final source = _hasValue(x['source_tank']) ? '${x['source_tank']}' : 'origem';
      final stockBefore = x['source_balance_before'] == null ? '-' : _brNumber(x['source_balance_before'], liters: true);
      final stockAfter = x['source_balance_after'] == null ? '-' : _brNumber(x['source_balance_after'], liters: true);
      final notes = _hasValue(x['notes']) ? '${x['notes']}' : 'Sem observações.';

      final receiverSig = await api.downloadMedia(_hasValue(x['receiver_signature_path']) ? '${x['receiver_signature_path']}' : null);
      final operatorSig = await api.downloadMedia(_hasValue(x['operator_signature_path']) ? '${x['operator_signature_path']}' : null);

      doc.addPage(pw.Page(
        pageFormat: PdfPageFormat.a4,
        margin: const pw.EdgeInsets.fromLTRB(30, 28, 30, 22),
        theme: pw.ThemeData.withFont(base: regular, bold: bold),
        build: (_) => pw.Column(crossAxisAlignment: pw.CrossAxisAlignment.start, children: [
          pw.Text(companyName, style: pw.TextStyle(font: bold, fontSize: 35, color: navy, lineSpacing: 0)),
          pw.Text(companySubtitle, style: pw.TextStyle(font: regular, fontSize: 25, color: navy, lineSpacing: 0)),
          pw.SizedBox(height: 9),
          pw.Container(height: 1.5, width: double.infinity, color: royal),
          pw.SizedBox(height: 11),
          pw.Text('CNPJ: $companyDocument', style: pw.TextStyle(font: regular, fontSize: 11.5, color: textColor)),
          pw.SizedBox(height: 4),
          pw.Text('Endereço: $companyAddress', style: pw.TextStyle(font: regular, fontSize: 11.5, color: textColor)),
          pw.SizedBox(height: 16),
          pw.Expanded(child: pw.Container(
            width: double.infinity,
            padding: const pw.EdgeInsets.fromLTRB(18, 16, 18, 15),
            decoration: pw.BoxDecoration(
              border: pw.Border.all(color: lineColor, width: 0.9),
              borderRadius: const pw.BorderRadius.all(pw.Radius.circular(12)),
            ),
            child: pw.Column(crossAxisAlignment: pw.CrossAxisAlignment.start, children: [
              pw.Row(crossAxisAlignment: pw.CrossAxisAlignment.center, children: [
                pw.Container(
                  width: 55,
                  height: 55,
                  decoration: pw.BoxDecoration(color: navy, shape: pw.BoxShape.circle),
                  child: pw.Center(child: icon(Icons.local_gas_station_rounded, size: 28, white: true)),
                ),
                pw.SizedBox(width: 14),
                pw.Expanded(child: pw.Column(crossAxisAlignment: pw.CrossAxisAlignment.start, children: [
                  pw.Text(title, style: pw.TextStyle(font: bold, fontSize: 17.5, color: navy)),
                  pw.SizedBox(height: 5),
                  pw.Text('${_fmtDate(x['created_at'])}  •  $liters', style: pw.TextStyle(font: regular, fontSize: 13, color: textColor)),
                ])),
              ]),
              pw.SizedBox(height: 13),
              pw.Container(height: 0.8, color: royal),
              pw.Row(children: [
                halfRow(Icons.location_city_outlined, 'Obra', work),
                pw.Container(width: 0.7, height: 50, color: lineColor),
                halfRow(Icons.water_drop_outlined, 'Combustível', fuel),
              ]),
              rule(),
              fullRow(Icons.location_on_outlined, 'Localização', location, height: 62),
              rule(),
              fullRow(Icons.person_outline_rounded, 'Recebedor', receiver),
              rule(),
              fullRow(Icons.person_outline_rounded, 'Quem abasteceu', operator),
              rule(),
              fullRow(Icons.speed_outlined, 'KM / horímetro', km),
              rule(),
              pw.Row(children: [
                halfRow(Icons.storage_outlined, 'Estoque do $source antes', stockBefore),
                pw.Container(width: 0.7, height: 52, color: lineColor),
                halfRow(Icons.storage_outlined, 'Estoque do $source depois', stockAfter),
              ]),
              pw.SizedBox(height: 10),
              pw.Container(
                width: double.infinity,
                padding: const pw.EdgeInsets.fromLTRB(10, 9, 10, 9),
                decoration: pw.BoxDecoration(
                  border: pw.Border.all(color: lineColor, width: 0.8),
                  borderRadius: const pw.BorderRadius.all(pw.Radius.circular(7)),
                ),
                child: pw.Row(crossAxisAlignment: pw.CrossAxisAlignment.start, children: [
                  pw.SizedBox(width: 30, child: pw.Center(child: icon(Icons.assignment_outlined, size: 21))),
                  pw.SizedBox(width: 6),
                  pw.Expanded(child: pw.Column(crossAxisAlignment: pw.CrossAxisAlignment.start, children: [
                    pw.Text('Observações', style: pw.TextStyle(font: bold, fontSize: 10.5, color: royal)),
                    pw.SizedBox(height: 4),
                    pw.Text(notes, style: pw.TextStyle(font: regular, fontSize: 10.5, color: textColor)),
                  ])),
                ]),
              ),
              pw.SizedBox(height: 10),
              pw.Row(children: [
                signatureBox('Assinatura de quem recebeu', receiver, receiverSig),
                pw.SizedBox(width: 10),
                signatureBox('Assinatura de quem abasteceu', operator, operatorSig),
              ]),
            ]),
          )),
          pw.SizedBox(height: 16),
          pw.Container(height: 1.5, width: double.infinity, color: royal),
        ]),
      ));

      final evidence = <MapEntry<String, String>>[];
      void addEvidence(String label, dynamic value) {
        if (_hasValue(value)) evidence.add(MapEntry(label, '$value'));
      }
      for (final p in _rowsFromPaths(x['photo_paths'])) { evidence.add(MapEntry('Foto do abastecimento', p)); }
      for (final p in _rowsFromPaths(x['damage_photo_paths'])) { evidence.add(MapEntry('Medidor danificado', p)); }
      addEvidence('KM/Horímetro antes', x['km_photo_before_path']);
      addEvidence('KM/Horímetro depois', x['km_photo_after_path']);
      addEvidence('Totalizador antes', x['totalizer_photo_before_path']);
      addEvidence('Totalizador depois', x['totalizer_photo_after_path']);
      addEvidence('Placa ou ativo antes', x['plate_photo_before_path']);
      addEvidence('Placa ou ativo depois', x['plate_photo_after_path']);
      final loaded = <MapEntry<String, Uint8List>>[];
      for (final e in evidence) {
        final b = await api.downloadMedia(e.value);
        if (b != null) loaded.add(MapEntry(e.key, b));
      }
      if (loaded.isNotEmpty) {
        doc.addPage(pw.Page(
          pageFormat: PdfPageFormat.a4,
          margin: const pw.EdgeInsets.all(30),
          theme: pw.ThemeData.withFont(base: regular, bold: bold),
          build: (_) => pw.Column(crossAxisAlignment: pw.CrossAxisAlignment.start, children: [
            pw.Text(companyName, style: pw.TextStyle(font: bold, fontSize: 24, color: navy)),
            pw.Text('Evidências do registro', style: pw.TextStyle(font: bold, fontSize: 16, color: navy)),
            pw.SizedBox(height: 5),
            pw.Text(title, style: pw.TextStyle(font: regular, fontSize: 11, color: textColor)),
            pw.SizedBox(height: 10),
            pw.Container(height: 1.2, color: royal),
            pw.SizedBox(height: 12),
            pw.Wrap(
              spacing: 10,
              runSpacing: 10,
              children: loaded.map((e) => pw.Container(
                width: 245,
                padding: const pw.EdgeInsets.all(7),
                decoration: pw.BoxDecoration(border: pw.Border.all(color: lineColor), borderRadius: const pw.BorderRadius.all(pw.Radius.circular(6))),
                child: pw.Column(crossAxisAlignment: pw.CrossAxisAlignment.start, children: [
                  pw.Container(width: 230, height: 150, child: pw.Image(pw.MemoryImage(e.value), fit: pw.BoxFit.contain)),
                  pw.SizedBox(height: 5),
                  pw.Text(e.key, style: pw.TextStyle(font: bold, fontSize: 9, color: royal)),
                ]),
              )).toList(),
            ),
          ]),
        ));
      }
    }
    return doc.save();
  }
}

'''

text = text[:start] + new_class + text[end:]
pdf = text[text.index('class FuelPdfReport'):text.index('class AdminUsersOnlineScreen')]
required = [
    "'Assinatura de quem recebeu'",
    "'Assinatura de quem abasteceu'",
    "_brNumber(x['liters'], liters: true)",
    "'Estoque do $source antes'",
    "'Estoque do $source depois'",
    "companySubtitle",
    "pw.Image(pw.MemoryImage(bytes)",
]
for marker in required:
    if marker not in pdf:
        raise SystemExit(f'v17: marcador obrigatório ausente: {marker}')
if 'REGISTRO CONFERIDO' in pdf or 'carimbo' in pdf.lower():
    raise SystemExit('v17: carimbo não deve existir no PDF final')
if 'pw.Icon(' in pdf:
    raise SystemExit('v17: não usar pw.Icon por causa da incompatibilidade de caracteres privados')
path.write_text(text)
print('v17: PDF refeito no layout visual aprovado, com litragem e duas assinaturas.')
