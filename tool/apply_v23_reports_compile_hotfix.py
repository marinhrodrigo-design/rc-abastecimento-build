from pathlib import Path
p=Path('lib/main_online.dart')
s=p.read_text()

def replace_between(start,end,new,label):
    global s
    i=s.find(start)
    if i<0: raise SystemExit(f'start missing: {label}')
    j=s.find(end,i)
    if j<0: raise SystemExit(f'end missing: {label}')
    s=s[:i]+new+s[j:]

work_pdf=r'''class WorkFinalPdf {
  static Future<Uint8List> build(Map<String,dynamic> snapshot) async {
    final doc = pw.Document();
    final regular = pw.Font.helvetica();
    final bold = pw.Font.helveticaBold();
    final navy = PdfColor.fromHex('#062A69');
    final royal = PdfColor.fromHex('#0E58C7');
    final line = PdfColor.fromHex('#D9E2EE');
    final text = PdfColor.fromHex('#20242B');
    final work = _map(snapshot['work']);
    final inst = _map(work['institutional_company']);
    final summary = _map(snapshot['summary']);
    final company = _hasValue(inst['company_name']) ? '${inst['company_name']}' : 'Empresa não cadastrada';
    final subtitle = '${inst['company_subtitle'] ?? ''}';

    pw.Widget header(String title) {
      return pw.Column(crossAxisAlignment: pw.CrossAxisAlignment.start, children: [
        pw.Text(company, style: pw.TextStyle(font: bold, fontSize: 28, color: navy)),
        if (subtitle.isNotEmpty) pw.Text(subtitle, style: pw.TextStyle(font: regular, fontSize: 18, color: navy)),
        pw.SizedBox(height: 8),
        pw.Container(height: 1.5, color: royal),
        pw.SizedBox(height: 8),
        pw.Text('CNPJ: ${inst['document'] ?? '-'}', style: pw.TextStyle(font: regular, fontSize: 9.5, color: text)),
        pw.Text('Endereço: ${inst['address'] ?? '-'}', style: pw.TextStyle(font: regular, fontSize: 9.5, color: text)),
        pw.SizedBox(height: 14),
        pw.Text(title, style: pw.TextStyle(font: bold, fontSize: 19, color: navy)),
        pw.SizedBox(height: 8),
      ]);
    }

    pw.Widget infoRow(String label, String value) {
      return pw.Container(
        padding: const pw.EdgeInsets.symmetric(vertical: 7),
        decoration: pw.BoxDecoration(border: pw.Border(bottom: pw.BorderSide(color: line, width: .6))),
        child: pw.Row(crossAxisAlignment: pw.CrossAxisAlignment.start, children: [
          pw.SizedBox(width: 175, child: pw.Text(label, style: pw.TextStyle(font: bold, fontSize: 9.5, color: royal))),
          pw.Expanded(child: pw.Text(value, style: pw.TextStyle(font: regular, fontSize: 10, color: text))),
        ]),
      );
    }

    doc.addPage(pw.Page(
      pageFormat: PdfPageFormat.a4,
      margin: const pw.EdgeInsets.all(30),
      theme: pw.ThemeData.withFont(base: regular, bold: bold),
      build: (_) {
        return pw.Column(crossAxisAlignment: pw.CrossAxisAlignment.start, children: [
          header('Relatório Final da Obra'),
          pw.Container(
            padding: const pw.EdgeInsets.all(14),
            decoration: pw.BoxDecoration(border: pw.Border.all(color: line), borderRadius: const pw.BorderRadius.all(pw.Radius.circular(10))),
            child: pw.Column(children: [
              infoRow('Obra', '${work['name'] ?? '-'}'),
              infoRow('Empresa da obra', '${work['company_name'] ?? '-'}'),
              infoRow('Responsável da obra', '${work['responsible'] ?? '-'}'),
              infoRow('Local', '${work['location'] ?? '-'}'),
              infoRow('Início', _fmtDate(work['created_at'])),
              infoRow('Finalização', _fmtDate(work['finalized_at'] ?? snapshot['generated_at'])),
            ]),
          ),
          pw.SizedBox(height: 14),
          pw.Text('Resumo geral', style: pw.TextStyle(font: bold, fontSize: 15, color: navy)),
          infoRow('Registros vinculados', '${summary['movement_count'] ?? 0}'),
          infoRow('Abastecimentos', '${summary['fueling_count'] ?? 0}'),
          infoRow('Volume abastecido', _fmtLiters(summary['fueling_liters'])),
          infoRow('Custo do combustível utilizado', _fmtMoney(summary['purchase_cost_total'])),
          infoRow('Valor de venda', _fmtMoney(summary['sale_total'])),
          infoRow('Lucro total', _fmtMoney(summary['profit_total'])),
          pw.Spacer(),
          pw.Container(height: 1.5, color: royal),
          pw.SizedBox(height: 6),
          pw.Text('Documento gerado automaticamente pelo R&C Abastecimento. Os registros e a rastreabilidade permanecem armazenados no sistema.', style: pw.TextStyle(font: regular, fontSize: 8.5, color: text)),
        ]);
      },
    ));

    final details = <pw.Widget>[
      pw.Text('Consumo por combustível', style: pw.TextStyle(font: bold, fontSize: 14, color: navy)),
    ];
    for (final f in _rows(snapshot['fuel_summary'])) {
      details.add(infoRow('${f['fuel_type'] ?? '-'}', '${_fmtLiters(f['liters'])} • ${f['fueling_count'] ?? 0} abastecimento(s)'));
    }
    details.add(pw.SizedBox(height: 14));
    details.add(pw.Text('Ativos e equipamentos atendidos', style: pw.TextStyle(font: bold, fontSize: 14, color: navy)));
    for (final a in _rows(snapshot['assets'])) {
      final kind = a['kind'] == 'third_party' ? 'Equipamento de terceiros' : 'Ativo próprio';
      details.add(infoRow('$kind • ${a['label'] ?? '-'}', 'Proprietário: ${a['owner_company'] ?? '-'} • ${_fmtLiters(a['liters'])} • ${a['fueling_count'] ?? 0} registro(s)'));
    }
    details.add(pw.SizedBox(height: 14));
    details.add(pw.Text('Notas Fiscais utilizadas', style: pw.TextStyle(font: bold, fontSize: 14, color: navy)));
    for (final n in _rows(snapshot['nfs'])) {
      details.add(infoRow('NF ${n['invoice_number'] ?? '-'}', 'Fornecedor: ${n['supplier_name'] ?? '-'} • Usado na obra: ${_fmtLiters(n['liters_used_by_work'])} • Custo: ${_fmtMoney(n['cost_used_by_work'])}'));
    }
    details.add(pw.SizedBox(height: 14));
    details.add(pw.Text('Registros da obra', style: pw.TextStyle(font: bold, fontSize: 14, color: navy)));
    for (final m in _rows(snapshot['movements'])) {
      details.add(pw.Container(
        margin: const pw.EdgeInsets.only(bottom: 7),
        padding: const pw.EdgeInsets.all(9),
        decoration: pw.BoxDecoration(border: pw.Border.all(color: line), borderRadius: const pw.BorderRadius.all(pw.Radius.circular(6))),
        child: pw.Column(crossAxisAlignment: pw.CrossAxisAlignment.start, children: [
          pw.Text('${m['code'] ?? '-'} • ${_movementLabel('${m['type'] ?? ''}')} • ${_fmtLiters(m['liters'])}', style: pw.TextStyle(font: bold, fontSize: 10.5, color: navy)),
          pw.SizedBox(height: 3),
          pw.Text('${_fmtDate(m['created_at'])} • ${m['asset_number'] ?? m['third_party_plate'] ?? m['third_party_description'] ?? '-'} • ${m['operator'] ?? '-'}', style: pw.TextStyle(font: regular, fontSize: 9.5, color: text)),
          if (_hasValue(m['location_address'])) pw.Text('${m['location_address']}', style: pw.TextStyle(font: regular, fontSize: 9, color: text)),
        ]),
      ));
    }
    details.add(pw.SizedBox(height: 14));
    details.add(pw.Text('Rastreabilidade dos lotes usados', style: pw.TextStyle(font: bold, fontSize: 14, color: navy)));
    for (final m in _rows(snapshot['lineage'])) {
      final route = '${m['source'] ?? 'Entrada'}${m['destination'] != null ? ' → ${m['destination']}' : ''}';
      details.add(infoRow('NF ${m['invoice_number'] ?? '-'} • ${m['code'] ?? '-'}', '${_movementLabel('${m['type'] ?? ''}')} • $route • ${_fmtLiters(m['liters'])} • ${_fmtDate(m['created_at'])}'));
    }
    if (_rows(snapshot['audit']).isNotEmpty) {
      details.add(pw.SizedBox(height: 14));
      details.add(pw.Text('Auditoria e correções', style: pw.TextStyle(font: bold, fontSize: 14, color: navy)));
      for (final a in _rows(snapshot['audit'])) {
        details.add(infoRow('${a['action'] ?? '-'} • ${a['user_name'] ?? '-'}', '${_fmtDate(a['created_at'])} • Registro ${a['record_id'] ?? '-'}'));
      }
    }

    doc.addPage(pw.MultiPage(
      pageFormat: PdfPageFormat.a4,
      margin: const pw.EdgeInsets.all(30),
      theme: pw.ThemeData.withFont(base: regular, bold: bold),
      header: (_) => header('Detalhamento do Relatório Final'),
      build: (_) => details,
    ));
    return doc.save();
  }
}

'''
replace_between('class WorkFinalPdf {','class AdminHomeScreen',work_pdf,'work final pdf')

fuel_pdf=r'''class FuelPdfReport {
  static const Color _iconBlue = Color(0xFF08367C);

  static Future<Uint8List> _materialIconPng(IconData icon, Color color) async {
    const canvasSize = 72.0;
    const glyphSize = 52.0;
    final recorder = ui.PictureRecorder();
    final canvas = ui.Canvas(recorder);
    final painter = TextPainter(
      text: TextSpan(text: String.fromCharCode(icon.codePoint), style: TextStyle(fontFamily: icon.fontFamily, package: icon.fontPackage, fontSize: glyphSize, color: color)),
      textDirection: ui.TextDirection.ltr,
      textAlign: TextAlign.center,
    );
    painter.layout();
    painter.paint(canvas, ui.Offset((canvasSize - painter.width) / 2, (canvasSize - painter.height) / 2));
    final picture = recorder.endRecording();
    final image = await picture.toImage(canvasSize.toInt(), canvasSize.toInt());
    final data = await image.toByteData(format: ui.ImageByteFormat.png);
    image.dispose();
    picture.dispose();
    if (data == null) throw StateError('Falha ao preparar ícone para o PDF.');
    return data.buffer.asUint8List();
  }

  static String _nfs(Map<String,dynamic> ctx) {
    final values = _rows(ctx['nfs']).map((x) => 'NF ${x['invoice_number']}${_hasValue(x['batch_number']) ? ' / Lote ${x['batch_number']}' : ''}').toSet().toList();
    return values.isEmpty ? '-' : values.join(' • ');
  }

  static Future<Uint8List> build(List<Map<String,dynamic>> items) async {
    final doc = pw.Document();
    final regular = pw.Font.helvetica();
    final bold = pw.Font.helveticaBold();
    final navy = PdfColor.fromHex('#062A69');
    final royal = PdfColor.fromHex('#0E58C7');
    final line = PdfColor.fromHex('#D9E2EE');
    final text = PdfColor.fromHex('#20242B');

    final iconSet = <IconData>[
      Icons.local_gas_station_rounded, Icons.local_shipping_outlined, Icons.location_city_outlined,
      Icons.location_on_outlined, Icons.water_drop_outlined, Icons.person_outline_rounded,
      Icons.speed_outlined, Icons.storage_outlined, Icons.assignment_outlined, Icons.draw_outlined,
      Icons.business_outlined, Icons.receipt_long_outlined, Icons.swap_horiz_rounded,
      Icons.precision_manufacturing_outlined,
    ];
    final blue = <int,pw.MemoryImage>{};
    final white = <int,pw.MemoryImage>{};
    for (final i in iconSet) {
      blue[i.codePoint] = pw.MemoryImage(await _materialIconPng(i, _iconBlue));
    }
    white[Icons.local_gas_station_rounded.codePoint] = pw.MemoryImage(await _materialIconPng(Icons.local_gas_station_rounded, Colors.white));

    pw.Widget icon(IconData d, {double size = 22, bool isWhite = false}) {
      final m = (isWhite ? white : blue)[d.codePoint];
      if (m == null) return pw.SizedBox(width: size, height: size);
      return pw.Image(m, width: size, height: size, fit: pw.BoxFit.contain);
    }

    pw.Widget row(IconData d, String label, String value, PdfColor accent) {
      return pw.Container(
        constraints: const pw.BoxConstraints(minHeight: 46),
        padding: const pw.EdgeInsets.symmetric(vertical: 7),
        decoration: pw.BoxDecoration(border: pw.Border(bottom: pw.BorderSide(color: line, width: .6))),
        child: pw.Row(crossAxisAlignment: pw.CrossAxisAlignment.center, children: [
          pw.SizedBox(width: 35, child: pw.Center(child: icon(d))),
          pw.SizedBox(width: 7),
          pw.Expanded(child: pw.Column(crossAxisAlignment: pw.CrossAxisAlignment.start, mainAxisAlignment: pw.MainAxisAlignment.center, children: [
            pw.Text(label, style: pw.TextStyle(font: bold, fontSize: 9.4, color: accent)),
            pw.SizedBox(height: 2),
            pw.Text(value, style: pw.TextStyle(font: regular, fontSize: 10.6, color: text)),
          ])),
        ]),
      );
    }

    pw.Widget signature(String title, String name, Uint8List? bytes, PdfColor accent) {
      return pw.Expanded(child: pw.Container(
        height: 88,
        padding: const pw.EdgeInsets.all(8),
        decoration: pw.BoxDecoration(border: pw.Border.all(color: line), borderRadius: const pw.BorderRadius.all(pw.Radius.circular(6))),
        child: pw.Column(crossAxisAlignment: pw.CrossAxisAlignment.start, children: [
          pw.Row(children: [icon(Icons.draw_outlined, size: 15), pw.SizedBox(width: 4), pw.Text(title, style: pw.TextStyle(font: bold, fontSize: 8.5, color: accent))]),
          pw.SizedBox(height: 4),
          pw.Expanded(child: pw.Center(child: bytes == null ? pw.Text('Assinatura não disponível', style: pw.TextStyle(font: regular, fontSize: 7.5, color: PdfColors.grey600)) : pw.Image(pw.MemoryImage(bytes), fit: pw.BoxFit.contain))),
          pw.Container(height: .5, color: line),
          pw.Text(name, style: pw.TextStyle(font: regular, fontSize: 8, color: text), maxLines: 1),
        ]),
      ));
    }

    for (final x in items) {
      final id = _intOrNull(x['id']);
      Map<String,dynamic> ctx = {};
      if (id != null) {
        try { ctx = await api.reportContextV23(id); } catch (_) {}
      }
      final inst = _map(ctx['institutional_company']);
      final companyName = _hasValue(inst['company_name']) ? '${inst['company_name']}' : 'Empresa não cadastrada';
      final companySubtitle = '${inst['company_subtitle'] ?? ''}';
      final companyDocument = '${inst['document'] ?? '-'}';
      final companyAddress = '${inst['address'] ?? '-'}';
      final type = '${x['type'] ?? ''}';
      final transfer = type == 'tank_transfer';
      final fueling = type == 'fueling';
      final refinery = type == 'refinery_entry';
      final accentN = transfer ? PdfColor.fromHex('#9A4D00') : navy;
      final accent = transfer ? PdfColor.fromHex('#E67E22') : royal;
      final own = [if (_hasValue(x['asset_number'])) '${x['asset_number']}', if (_hasValue(x['asset_model'])) '${x['asset_model']}'].join(' • ');
      final third = [if (_hasValue(x['third_party_plate'])) '${x['third_party_plate']}', if (_hasValue(x['third_party_description'])) '${x['third_party_description']}'].join(' • ');
      final equipment = [if (own.isNotEmpty) own, if (third.isNotEmpty) third].join(' + ');
      final title = '${_movementLabelForItem(x)}${equipment.isNotEmpty ? ' • $equipment' : ''}';
      final operator = '${x['operator'] ?? '-'}';
      final receiver = '${x['receiver'] ?? '-'}';
      final nfs = _nfs(ctx);
      final rows = <pw.Widget>[];

      if (refinery) {
        rows.add(row(Icons.business_outlined, 'Empresa compradora', '${ctx['empresa_compradora'] ?? companyName}', accent));
        rows.add(row(Icons.business_outlined, 'Fornecedor do combustível', '${ctx['fornecedor_combustivel'] ?? '-'}', accent));
        rows.add(row(Icons.receipt_long_outlined, 'Nota Fiscal / lote', nfs, accent));
        rows.add(row(Icons.water_drop_outlined, 'Combustível', '${x['fuel_type'] ?? '-'}', accent));
        rows.add(row(Icons.local_gas_station_rounded, 'Volume recebido', _fmtLiters(x['liters']), accent));
        rows.add(row(Icons.local_shipping_outlined, 'Caminhão-tanque', '${x['destination_tank'] ?? '-'}', accent));
        rows.add(row(Icons.person_outline_rounded, 'Quem registrou', operator, accent));
      } else if (transfer) {
        rows.add(row(Icons.business_outlined, 'Empresa', '${ctx['empresa'] ?? companyName}', accent));
        rows.add(row(Icons.swap_horiz_rounded, 'Tipo de movimento', 'Transferência interna — sem venda', accent));
        rows.add(row(Icons.storage_outlined, 'Origem', '${ctx['origem'] ?? x['source_tank'] ?? '-'}', accent));
        rows.add(row(Icons.storage_outlined, 'Destino', '${ctx['destino'] ?? x['destination_tank'] ?? '-'}', accent));
        rows.add(row(Icons.water_drop_outlined, 'Volume', _fmtLiters(x['liters']), accent));
        rows.add(row(Icons.person_outline_rounded, 'Responsável doador', '${x['donor_responsible'] ?? operator}', accent));
        rows.add(row(Icons.person_outline_rounded, 'Responsável recebedor', '${x['receiver_responsible'] ?? receiver}', accent));
        rows.add(row(Icons.receipt_long_outlined, 'NF(s)/Lote(s) envolvidos', nfs, accent));
      } else {
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

      Uint8List? sig1;
      Uint8List? sig2;
      String sig1Name = '';
      String sig2Name = '';
      String sig1Title = '';
      String sig2Title = '';
      if (transfer) {
        sig1 = await api.downloadMedia('${x['donor_signature_path'] ?? ''}');
        sig2 = await api.downloadMedia('${x['receiver_transfer_signature_path'] ?? x['receiver_signature_path'] ?? ''}');
        sig1Name = '${x['donor_responsible'] ?? operator}';
        sig2Name = '${x['receiver_responsible'] ?? receiver}';
        sig1Title = 'Assinatura responsável doador';
        sig2Title = 'Assinatura responsável recebedor';
      } else if (fueling) {
        sig1 = await api.downloadMedia('${x['receiver_signature_path'] ?? ''}');
        sig2 = await api.downloadMedia('${x['operator_signature_path'] ?? ''}');
        sig1Name = receiver;
        sig2Name = operator;
        sig1Title = 'Assinatura de quem recebeu';
        sig2Title = 'Assinatura de quem abasteceu';
      }

      final body = <pw.Widget>[
        pw.Text(companyName, style: pw.TextStyle(font: bold, fontSize: 32, color: accentN)),
        if (companySubtitle.isNotEmpty) pw.Text(companySubtitle, style: pw.TextStyle(font: regular, fontSize: 21, color: accentN)),
        pw.SizedBox(height: 7),
        pw.Container(height: 1.5, color: accent),
        pw.SizedBox(height: 8),
        pw.Text('CNPJ: $companyDocument', style: pw.TextStyle(font: regular, fontSize: 10, color: text)),
        pw.Text('Endereço: $companyAddress', style: pw.TextStyle(font: regular, fontSize: 10, color: text)),
        pw.SizedBox(height: 14),
      ];
      body.add(pw.Container(
        padding: const pw.EdgeInsets.all(14),
        decoration: pw.BoxDecoration(border: pw.Border.all(color: line), borderRadius: const pw.BorderRadius.all(pw.Radius.circular(10))),
        child: pw.Column(crossAxisAlignment: pw.CrossAxisAlignment.start, children: [
          pw.Row(children: [
            pw.Container(width: 48, height: 48, decoration: pw.BoxDecoration(color: accentN, shape: pw.BoxShape.circle), child: pw.Center(child: icon(Icons.local_gas_station_rounded, size: 24, isWhite: true))),
            pw.SizedBox(width: 12),
            pw.Expanded(child: pw.Column(crossAxisAlignment: pw.CrossAxisAlignment.start, children: [
              pw.Text(title, style: pw.TextStyle(font: bold, fontSize: 15, color: accentN)),
              pw.SizedBox(height: 3),
              pw.Text('${_fmtDate(x['created_at'])} • $operator', style: pw.TextStyle(font: regular, fontSize: 10.5, color: text)),
            ])),
          ]),
          pw.SizedBox(height: 8),
          ...rows,
          if (_hasValue(x['notes'])) row(Icons.assignment_outlined, 'Observações', '${x['notes']}', accent),
          if (sig1Title.isNotEmpty) ...[
            pw.SizedBox(height: 10),
            pw.Row(children: [signature(sig1Title, sig1Name, sig1, accent), pw.SizedBox(width: 8), signature(sig2Title, sig2Name, sig2, accent)]),
          ],
        ]),
      ));
      body.add(pw.SizedBox(height: 10));
      body.add(pw.Container(height: 1.5, color: accent));

      doc.addPage(pw.MultiPage(
        pageFormat: PdfPageFormat.a4,
        margin: const pw.EdgeInsets.fromLTRB(30, 28, 30, 24),
        theme: pw.ThemeData.withFont(base: regular, bold: bold),
        build: (_) => body,
      ));

      final evidence = <MapEntry<String,String>>[];
      void addEvidence(String label, dynamic value) {
        if (_hasValue(value)) evidence.add(MapEntry(label, '$value'));
      }
      if (refinery) {
        addEvidence('Foto da placa do caminhão-tanque', ctx['truck_plate_photo_path']);
        addEvidence('Foto legível da Nota Fiscal', ctx['invoice_photo_path']);
        if (evidence.isEmpty) {
          for (final p in _rowsFromPaths(x['photo_paths'])) {
            evidence.add(MapEntry('Evidência do recebimento', p));
          }
        }
      }
      if (fueling) {
        addEvidence('Foto do KM ou Horímetro', x['meter_photo_path']);
        addEvidence('Foto do Totalizador', x['totalizer_evidence_photo_path']);
        addEvidence('Foto da placa ou identificação', x['identity_evidence_photo_path']);
        addEvidence('Foto do abastecimento', x['extra_evidence_photo_path']);
      }
      for (final e in evidence) {
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
    }
    return doc.save();
  }
}

'''
replace_between('class FuelPdfReport {','class AdminUsersOnlineScreen',fuel_pdf,'fuel pdf')

p.write_text(s)
print('reports compile hotfix applied', len(s))
