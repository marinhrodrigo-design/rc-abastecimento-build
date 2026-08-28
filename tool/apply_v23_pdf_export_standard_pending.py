from pathlib import Path
p=Path('lib/main_online.dart')
s=p.read_text()

def rep(old,new,label):
    global s
    if old not in s:
        raise SystemExit(f'anchor missing: {label}')
    s=s.replace(old,new,1)

# Helpers: origem e número sequencial do abastecimento.
marker="""  static String _nfs(Map<String,dynamic> ctx) {
    final values = _rows(ctx['nfs']).map((x) => 'NF ${x['invoice_number']}${_hasValue(x['batch_number']) ? ' / Lote ${x['batch_number']}' : ''}').toSet().toList();
    return values.isEmpty ? '-' : values.join(' • ');
  }

"""
helpers=marker+"""  static String _fuelOrigin(Map<String,dynamic> ctx, Map<String,dynamic> x) {
    final fromContext = '${ctx['origem'] ?? ''}'.trim();
    if (fromContext.isNotEmpty && fromContext != 'null') return fromContext;
    final source = '${x['source_tank'] ?? ''}'.trim();
    if (source.isNotEmpty && source != 'null') return source;
    final code = '${x['code'] ?? ''}'.trim();
    final match = RegExp(r'^(.+?)-\\d+$').firstMatch(code);
    return (match?.group(1) ?? code).trim();
  }

  static String _fuelSequence(Map<String,dynamic> x) {
    final code = '${x['code'] ?? ''}'.trim();
    final match = RegExp(r'(\\d+)$').firstMatch(code);
    final raw = match?.group(1) ?? '';
    final number = int.tryParse(raw);
    if (number == null) return raw.isEmpty ? '0000' : raw;
    return number.toString().padLeft(4, '0');
  }

  static String _fuelLabel(dynamic value) {
    final raw = '${value ?? ''}'.trim();
    final low = raw.toLowerCase();
    if (low == 'diesel' || low == 'diesel s10' || low == 'óleo diesel s10' || low == 'oleo diesel s10') return 'Diesel S10';
    if (low == 'arla' || low == 'arla32' || low == 'arla 32') return 'Arla 32';
    return raw.isEmpty ? '-' : raw;
  }

"""
rep(marker,helpers,'pdf helpers')

# Compactar linhas e deixar títulos em azul-marinho e valores em preto.
rep("""        constraints: const pw.BoxConstraints(minHeight: 46),
        padding: const pw.EdgeInsets.symmetric(vertical: 7),""","""        constraints: const pw.BoxConstraints(minHeight: 30),
        padding: const pw.EdgeInsets.symmetric(vertical: 4),""",'row compact')
rep("""          pw.SizedBox(width: 35, child: pw.Center(child: icon(d))),
          pw.SizedBox(width: 7),""","""          pw.SizedBox(width: 28, child: pw.Center(child: icon(d, size: 17))),
          pw.SizedBox(width: 5),""",'row icon compact')
rep("""            pw.Text(label, style: pw.TextStyle(font: bold, fontSize: 9.4, color: accent)),
            pw.SizedBox(height: 2),
            pw.Text(value, style: pw.TextStyle(font: regular, fontSize: 10.6, color: text)),""","""            pw.Text(label, style: pw.TextStyle(font: bold, fontSize: 8.1, color: accent)),
            pw.SizedBox(height: 1),
            pw.Text(value, style: pw.TextStyle(font: regular, fontSize: 9.2, color: text)),""",'row title and value colors')
rep("height: 88,","height: 72,",'signature compact')

# Helper de duas colunas.
marker2="""    pw.Widget signature(String title, String name, Uint8List? bytes, PdfColor accent) {"""
pair="""    pw.Widget pairRows(pw.Widget left, pw.Widget right) {
      return pw.Row(crossAxisAlignment: pw.CrossAxisAlignment.start, children: [
        pw.Expanded(child: left),
        pw.SizedBox(width: 8),
        pw.Expanded(child: right),
      ]);
    }

"""+marker2
rep(marker2,pair,'pair rows helper')

# Ícone branco também para o cabeçalho das evidências.
rep(
"white[Icons.local_gas_station_rounded.codePoint] = pw.MemoryImage(await _materialIconPng(Icons.local_gas_station_rounded, Colors.white));",
"white[Icons.local_gas_station_rounded.codePoint] = pw.MemoryImage(await _materialIconPng(Icons.local_gas_station_rounded, Colors.white));\n    white[Icons.assignment_outlined.codePoint] = pw.MemoryImage(await _materialIconPng(Icons.assignment_outlined, Colors.white));",
'white evidence icon')

# Título padrão: no abastecimento, origem (CB/CT/TE) + número sequencial vermelho.
rep("""      final title = '${_movementLabelForItem(x)}${equipment.isNotEmpty ? ' • $equipment' : ''}';
      final operator = '${x['operator'] ?? '-'}';""","""      final title = '${_movementLabelForItem(x)}${equipment.isNotEmpty ? ' • $equipment' : ''}';
      final fuelOrigin = _fuelOrigin(ctx, x);
      final fuelSequence = _fuelSequence(x);
      final operator = '${x['operator'] ?? '-'}';""",'fuel header metadata')

# Layout oficial aprovado da página principal do abastecimento.
old="""      } else {
        rows.add(row(Icons.business_outlined, 'Empresa fornecedora/vendedora do combustível', '${ctx['empresa_fornecedora_vendedora'] ?? companyName}', accent));
        rows.add(row(Icons.business_outlined, 'Empresa recebedora/compradora', '${ctx['empresa_recebedora_compradora'] ?? '-'}', accent));
        rows.add(row(Icons.location_city_outlined, 'Obra', '${ctx['obra'] ?? x['work'] ?? '-'}', accent));
        rows.add(row(Icons.person_outline_rounded, 'Responsável da obra', '${ctx['responsavel_obra'] ?? '-'}', accent));
        rows.add(row(Icons.precision_manufacturing_outlined, 'Equipamento abastecido', equipment.isEmpty ? '-' : equipment, accent));
        rows.add(row(Icons.business_outlined, 'Proprietário do equipamento', '${ctx['proprietario_equipamento'] ?? '-'}', accent));
        rows.add(row(Icons.location_on_outlined, 'Localização', '${x['location_address'] ?? '-'}', accent));
        rows.add(row(Icons.water_drop_outlined, 'Combustível', '${x['fuel_type'] ?? '-'}', accent));
        rows.add(row(Icons.local_gas_station_rounded, 'Volume', _fmtLiters(x['liters']), accent));
        rows.add(row(Icons.person_outline_rounded, 'Quem recebeu', receiver, accent));
        rows.add(row(Icons.person_outline_rounded, 'Quem abasteceu', operator, accent));
        rows.add(row(Icons.speed_outlined, 'KM', '${x['km_value'] ?? x['km_hourmeter'] ?? '-'}', accent));
        rows.add(row(Icons.speed_outlined, 'Horímetro', '${x['hourmeter_value'] ?? '-'}', accent));
        if (x['sale_price_per_liter'] != null) rows.add(row(Icons.assignment_outlined, 'Preço de venda/L', _fmtMoney(x['sale_price_per_liter']), accent));
        rows.add(row(Icons.storage_outlined, 'Totalizador', _fmtLiters(x['totalizer'] ?? x['closing_meter']), accent));
        rows.add(row(Icons.receipt_long_outlined, 'NF(s)/Lote(s) utilizados', nfs, accent));
      }
"""
new="""      } else {
        final litersValue = _num(x['liters']);
        final salePriceValue = _num(x['sale_price_per_liter']);
        final totalSaleValue = x['sale_total'] ?? x['total_value'] ?? (litersValue * salePriceValue);

        rows.add(pairRows(
          row(Icons.business_outlined, 'Empresa fornecedora/vendedora do combustível', '${ctx['empresa_fornecedora_vendedora'] ?? companyName}', navy),
          row(Icons.business_outlined, 'Empresa recebedora/compradora', '${ctx['empresa_recebedora_compradora'] ?? '-'}', navy),
        ));
        rows.add(pairRows(
          row(Icons.location_city_outlined, 'Obra', '${ctx['obra'] ?? x['work'] ?? '-'}', navy),
          row(Icons.person_outline_rounded, 'Responsável da obra', '${ctx['responsavel_obra'] ?? '-'}', navy),
        ));
        rows.add(pairRows(
          row(Icons.precision_manufacturing_outlined, 'Equipamento abastecido', equipment.isEmpty ? '-' : equipment, navy),
          row(Icons.business_outlined, 'Proprietário do equipamento', '${ctx['proprietario_equipamento'] ?? '-'}', navy),
        ));
        rows.add(pairRows(
          row(Icons.location_on_outlined, 'Localização', '${x['location_address'] ?? '-'}', navy),
          row(Icons.water_drop_outlined, 'Combustível', _fuelLabel(x['fuel_type']), navy),
        ));
        rows.add(pairRows(
          row(Icons.speed_outlined, 'KM', '${x['km_value'] ?? x['km_hourmeter'] ?? '-'}', navy),
          row(Icons.speed_outlined, 'Horímetro', '${x['hourmeter_value'] ?? '-'}', navy),
        ));
        rows.add(pairRows(
          row(Icons.person_outline_rounded, 'Quem abasteceu', operator, navy),
          row(Icons.person_outline_rounded, 'Quem recebeu', receiver, navy),
        ));
        rows.add(pairRows(
          row(Icons.assignment_outlined, 'Preço de venda/L', x['sale_price_per_liter'] == null ? '-' : _fmtMoney(x['sale_price_per_liter']), navy),
          row(Icons.assignment_outlined, 'Valor total', x['sale_price_per_liter'] == null ? '-' : _fmtMoney(totalSaleValue), navy),
        ));
        rows.add(pairRows(
          row(Icons.local_gas_station_rounded, 'Volume', _fmtLiters(x['liters']), navy),
          row(Icons.storage_outlined, 'Totalizador', _fmtLiters(x['totalizer'] ?? x['closing_meter']), navy),
        ));
        if (_hasValue(x['notes'])) {
          rows.add(row(Icons.assignment_outlined, 'Observações', '${x['notes']}', navy));
        }
      }
"""
rep(old,new,'official fueling layout')

# Observação do abastecimento já está dentro da ordem oficial.
rep("""          if (_hasValue(x['notes'])) row(Icons.assignment_outlined, 'Observações', '${x['notes']}', accent),""","""          if (_hasValue(x['notes']) && !fueling) row(Icons.assignment_outlined, 'Observações', '${x['notes']}', accent),""",'no duplicate notes')

# Cabeçalho institucional no padrão aprovado: somente nome + linha.
old_body="""      final body = <pw.Widget>[
        pw.Text(companyName, style: pw.TextStyle(font: bold, fontSize: 32, color: accentN)),
        if (companySubtitle.isNotEmpty) pw.Text(companySubtitle, style: pw.TextStyle(font: regular, fontSize: 21, color: accentN)),
        pw.SizedBox(height: 7),
        pw.Container(height: 1.5, color: accent),
        pw.SizedBox(height: 8),
        pw.Text('CNPJ: $companyDocument', style: pw.TextStyle(font: regular, fontSize: 10, color: text)),
        pw.Text('Endereço: $companyAddress', style: pw.TextStyle(font: regular, fontSize: 10, color: text)),
        pw.SizedBox(height: 14),
      ];"""
new_body="""      final body = <pw.Widget>[
        pw.Text(companyName, style: pw.TextStyle(font: bold, fontSize: 27, color: navy)),
        pw.SizedBox(height: 7),
        pw.Container(height: 1.5, color: royal),
        pw.SizedBox(height: 12),
      ];"""
rep(old_body,new_body,'approved institutional header')

# Cabeçalho do card: Abastecimento • CB01 • Nº: 0001 (número em vermelho).
old_card="""            pw.Expanded(child: pw.Column(crossAxisAlignment: pw.CrossAxisAlignment.start, children: [
              pw.Text(title, style: pw.TextStyle(font: bold, fontSize: 15, color: accentN)),
              pw.SizedBox(height: 3),
              pw.Text('${_fmtDate(x['created_at'])} • $operator', style: pw.TextStyle(font: regular, fontSize: 10.5, color: text)),
            ])),"""
new_card="""            pw.Expanded(child: pw.Column(crossAxisAlignment: pw.CrossAxisAlignment.start, children: [
              if (fueling)
                pw.Row(mainAxisSize: pw.MainAxisSize.min, children: [
                  pw.Text('Abastecimento', style: pw.TextStyle(font: bold, fontSize: 14, color: navy)),
                  pw.SizedBox(width: 7), pw.Container(width: 3, height: 3, decoration: pw.BoxDecoration(color: navy, shape: pw.BoxShape.circle)), pw.SizedBox(width: 7),
                  pw.Text(fuelOrigin.isEmpty ? '-' : fuelOrigin, style: pw.TextStyle(font: bold, fontSize: 14, color: navy)),
                  pw.SizedBox(width: 7), pw.Container(width: 3, height: 3, decoration: pw.BoxDecoration(color: navy, shape: pw.BoxShape.circle)), pw.SizedBox(width: 7),
                  pw.Text('Nº: $fuelSequence', style: pw.TextStyle(font: bold, fontSize: 14, color: PdfColor.fromHex('#D51F2A'))),
                ])
              else
                pw.Text(title, style: pw.TextStyle(font: bold, fontSize: 15, color: accentN)),
              pw.SizedBox(height: 3),
              pw.Text('${_fmtDate(x['created_at'])} | $operator', style: pw.TextStyle(font: regular, fontSize: 9.5, color: text)),
            ])),"""
rep(old_card,new_card,'fuel card header sequence')

# Mais compacto e ficha principal sempre em uma única página.
s=s.replace("body.add(pw.Container(\n        padding: const pw.EdgeInsets.all(14),","body.add(pw.Container(\n        padding: const pw.EdgeInsets.all(10),",1)
s=s.replace("width: 48, height: 48","width: 42, height: 42",1)
s=s.replace("size: 24, isWhite: true","size: 21, isWhite: true",1)
old_page="""      doc.addPage(pw.MultiPage(
        pageFormat: PdfPageFormat.a4,
        margin: const pw.EdgeInsets.fromLTRB(30, 28, 30, 24),
        theme: pw.ThemeData.withFont(base: regular, bold: bold),
        build: (_) => body,
      ));"""
new_page="""      doc.addPage(pw.Page(
        pageFormat: PdfPageFormat.a4,
        margin: const pw.EdgeInsets.fromLTRB(26, 22, 26, 20),
        theme: pw.ThemeData.withFont(base: regular, bold: bold),
        build: (_) => pw.Column(crossAxisAlignment: pw.CrossAxisAlignment.start, children: body),
      ));"""
rep(old_page,new_page,'single page official pdf')

# 4ª foto com legenda aprovada.
rep("""        addEvidence('Foto do abastecimento', x['extra_evidence_photo_path']);""","""        addEvidence('4ª foto (opcional)', x['extra_evidence_photo_path']);""",'fourth photo label')

# Evidências: quatro fotos por página, grade 2x2, número sequencial repetido em todas as páginas.
start="""      for (final e in evidence) {
        final b = await api.downloadMedia(e.value);
        if (b == null) continue;
        doc.addPage(pw.Page(
          pageFormat: PdfPageFormat.a4,
          margin: const pw.EdgeInsets.all(30),
          theme: pw.ThemeData.withFont(base: regular, bold: bold),
          build: (_) => pw.Column(crossAxisAlignment: pw.CrossAxisAlignment.start, children: [
            pw.Text(companyName, style: pw.TextStyle(font: bold, fontSize: 24, color: accentN)),
            pw.Text('Evidências do registro', style: pw.TextStyle(font: bold, fontSize: 16, color: accentN)),
            pw.SizedBox(height: 6),
            pw.Container(height: 1.2, color: accent),
            pw.SizedBox(height: 14),
            pw.Container(width: 330, height: 500, decoration: pw.BoxDecoration(border: pw.Border.all(color: line), borderRadius: const pw.BorderRadius.all(pw.Radius.circular(6))), child: pw.Padding(padding: const pw.EdgeInsets.all(7), child: pw.Image(pw.MemoryImage(b), fit: pw.BoxFit.contain))),
            pw.SizedBox(height: 6),
            pw.Text(e.key, style: pw.TextStyle(font: bold, fontSize: 10, color: accent)),
          ]),
        ));
      }
"""
replacement="""      final loadedEvidence = <MapEntry<String,Uint8List>>[];
      for (final e in evidence) {
        final bytes = await api.downloadMedia(e.value);
        if (bytes != null) loadedEvidence.add(MapEntry(e.key, bytes));
      }

      for (var offset = 0; offset < loadedEvidence.length; offset += 4) {
        final pageItems = loadedEvidence.skip(offset).take(4).toList();

        pw.Widget evidenceSlot(int index) {
          if (index >= pageItems.length) {
            return pw.Expanded(child: pw.Container(
              decoration: pw.BoxDecoration(border: pw.Border.all(color: line), borderRadius: const pw.BorderRadius.all(pw.Radius.circular(7))),
            ));
          }
          final item = pageItems[index];
          return pw.Expanded(child: pw.Container(
            padding: const pw.EdgeInsets.all(7),
            decoration: pw.BoxDecoration(border: pw.Border.all(color: line), borderRadius: const pw.BorderRadius.all(pw.Radius.circular(7))),
            child: pw.Column(children: [
              pw.Expanded(child: pw.Center(child: pw.Image(pw.MemoryImage(item.value), fit: pw.BoxFit.contain))),
              pw.SizedBox(height: 5),
              pw.Text(item.key, textAlign: pw.TextAlign.center, style: pw.TextStyle(font: bold, fontSize: 9, color: navy)),
            ]),
          ));
        }

        doc.addPage(pw.Page(
          pageFormat: PdfPageFormat.a4,
          margin: const pw.EdgeInsets.fromLTRB(28, 24, 28, 22),
          theme: pw.ThemeData.withFont(base: regular, bold: bold),
          build: (_) => pw.Column(crossAxisAlignment: pw.CrossAxisAlignment.start, children: [
            pw.Text(companyName, style: pw.TextStyle(font: bold, fontSize: 27, color: navy)),
            pw.SizedBox(height: 7),
            pw.Container(height: 1.5, color: royal),
            pw.SizedBox(height: 12),
            pw.Container(
              padding: const pw.EdgeInsets.all(10),
              decoration: pw.BoxDecoration(border: pw.Border.all(color: line), borderRadius: const pw.BorderRadius.all(pw.Radius.circular(8))),
              child: pw.Row(children: [
                pw.Container(width: 40, height: 40, decoration: pw.BoxDecoration(color: navy, shape: pw.BoxShape.circle), child: pw.Center(child: icon(Icons.assignment_outlined, size: 20, isWhite: true))),
                pw.SizedBox(width: 10),
                pw.Expanded(child: pw.Column(crossAxisAlignment: pw.CrossAxisAlignment.start, children: [
                  if (fueling)
                    pw.Row(mainAxisSize: pw.MainAxisSize.min, children: [
                      pw.Text('Evidências do registro', style: pw.TextStyle(font: bold, fontSize: 13.5, color: navy)),
                      pw.SizedBox(width: 7), pw.Container(width: 3, height: 3, decoration: pw.BoxDecoration(color: navy, shape: pw.BoxShape.circle)), pw.SizedBox(width: 7),
                      pw.Text(fuelOrigin.isEmpty ? '-' : fuelOrigin, style: pw.TextStyle(font: bold, fontSize: 13.5, color: navy)),
                      pw.SizedBox(width: 7), pw.Container(width: 3, height: 3, decoration: pw.BoxDecoration(color: navy, shape: pw.BoxShape.circle)), pw.SizedBox(width: 7),
                      pw.Text('Nº: $fuelSequence', style: pw.TextStyle(font: bold, fontSize: 13.5, color: PdfColor.fromHex('#D51F2A'))),
                    ])
                  else
                    pw.Text('Evidências do registro', style: pw.TextStyle(font: bold, fontSize: 13.5, color: navy)),
                  pw.SizedBox(height: 3),
                  pw.Text('${_fmtDate(x['created_at'])} | $operator', style: pw.TextStyle(font: regular, fontSize: 9.2, color: text)),
                ])),
              ]),
            ),
            pw.SizedBox(height: 12),
            pw.Expanded(child: pw.Column(children: [
              pw.Expanded(child: pw.Row(children: [evidenceSlot(0), pw.SizedBox(width: 10), evidenceSlot(1)])),
              pw.SizedBox(height: 10),
              pw.Expanded(child: pw.Row(children: [evidenceSlot(2), pw.SizedBox(width: 10), evidenceSlot(3)])),
            ])),
            pw.SizedBox(height: 10),
            pw.Container(height: 1.5, color: royal),
          ]),
        ));
      }
"""
rep(start,replacement,'evidence 2x2 standard')

p.write_text(s)
print('final pdf export standard staged', len(s))
