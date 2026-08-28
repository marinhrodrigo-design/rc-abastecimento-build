from pathlib import Path

p = Path('lib/main_online.dart')
s = p.read_text()

def rep(old, new, label):
    global s
    if old not in s:
        raise SystemExit(f'anchor missing: {label}')
    s = s.replace(old, new, 1)

# Evita glifos que a Helvetica do PDF não renderiza bem.
s = s.replace("values.join(' • ')", "values.join(' | ')")
s = s.replace("].join(' • ')", "].join(' - ')")
s = s.replace(" ? ' • $equipment' : ''", " ? ' - $equipment' : ''")
s = s.replace("${_fmtDate(x['created_at'])} • $operator", "${_fmtDate(x['created_at'])} | $operator")

# Linhas mais compactas para manter a ficha principal em uma página.
rep(
"""        constraints: const pw.BoxConstraints(minHeight: 46),
        padding: const pw.EdgeInsets.symmetric(vertical: 7),""",
"""        constraints: const pw.BoxConstraints(minHeight: 27),
        padding: const pw.EdgeInsets.symmetric(vertical: 3),""",
'compact row size')
rep(
"""          pw.SizedBox(width: 35, child: pw.Center(child: icon(d))),
          pw.SizedBox(width: 7),""",
"""          pw.SizedBox(width: 27, child: pw.Center(child: icon(d, size: 16))),
          pw.SizedBox(width: 4),""",
'compact row icon')
rep(
"""            pw.Text(label, style: pw.TextStyle(font: bold, fontSize: 9.4, color: accent)),
            pw.SizedBox(height: 2),
            pw.Text(value, style: pw.TextStyle(font: regular, fontSize: 10.6, color: text)),""",
"""            pw.Text(label, style: pw.TextStyle(font: bold, fontSize: 7.8, color: accent)),
            pw.SizedBox(height: 1),
            pw.Text(value, style: pw.TextStyle(font: regular, fontSize: 8.9, color: text)),""",
'compact row fonts')
rep("height: 88,", "height: 68,", 'signature height')

# Rótulo padronizado do combustível no PDF.
insert = """  static String _fuelLabel(dynamic value) {
    final raw = '${value ?? ''}'.trim();
    final low = raw.toLowerCase();
    if (low == 'diesel') return 'Diesel S10';
    if (low == 'diesel s10') return 'Diesel S10';
    if (low == 'arla' || low == 'arla32' || low == 'arla 32') return 'Arla 32';
    return raw.isEmpty ? '-' : raw;
  }

"""
marker = "  static Future<Uint8List> build(List<Map<String,dynamic>> items) async {"
if marker not in s:
    raise SystemExit('anchor missing: build marker')
s = s.replace(marker, insert + marker, 1)
s = s.replace("'Combustível', '${x['fuel_type'] ?? '-'}'", "'Combustível', _fuelLabel(x['fuel_type'])")

# Helper para aproximar o layout oficial em duas colunas e reduzir altura.
helper = """    pw.Widget pairRows(pw.Widget left, pw.Widget right) {
      return pw.Row(crossAxisAlignment: pw.CrossAxisAlignment.start, children: [
        pw.Expanded(child: left),
        pw.SizedBox(width: 8),
        pw.Expanded(child: right),
      ]);
    }

"""
marker2 = "    pw.Widget signature(String title, String name, Uint8List? bytes, PdfColor accent) {"
if marker2 not in s:
    raise SystemExit('anchor missing: signature marker')
s = s.replace(marker2, helper + marker2, 1)

old_fueling = """      } else {
        rows.add(row(Icons.business_outlined, 'Empresa fornecedora/vendedora do combustível', '${ctx['empresa_fornecedora_vendedora'] ?? companyName}', accent));
        rows.add(row(Icons.business_outlined, 'Empresa recebedora/compradora', '${ctx['empresa_recebedora_compradora'] ?? '-'}', accent));
        rows.add(row(Icons.location_city_outlined, 'Obra', '${ctx['obra'] ?? x['work'] ?? '-'}', accent));
        rows.add(row(Icons.person_outline_rounded, 'Responsável da obra', '${ctx['responsavel_obra'] ?? '-'}', accent));
        rows.add(row(Icons.precision_manufacturing_outlined, 'Equipamento abastecido', equipment.isEmpty ? '-' : equipment, accent));
        rows.add(row(Icons.business_outlined, 'Proprietário do equipamento', '${ctx['proprietario_equipamento'] ?? '-'}', accent));
        rows.add(row(Icons.location_on_outlined, 'Localização', '${x['location_address'] ?? '-'}', accent));
        rows.add(row(Icons.water_drop_outlined, 'Combustível', _fuelLabel(x['fuel_type']), accent));
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
new_fueling = """      } else {
        final litersValue = _num(x['liters']);
        final salePriceValue = _num(x['sale_price_per_liter']);
        final totalSaleValue = x['sale_total'] ?? (litersValue * salePriceValue);

        rows.add(pairRows(
          row(Icons.business_outlined, 'Empresa fornecedora/vendedora do combustível', '${ctx['empresa_fornecedora_vendedora'] ?? companyName}', accent),
          row(Icons.business_outlined, 'Empresa recebedora/compradora', '${ctx['empresa_recebedora_compradora'] ?? '-'}', accent),
        ));
        rows.add(pairRows(
          row(Icons.location_city_outlined, 'Obra', '${ctx['obra'] ?? x['work'] ?? '-'}', accent),
          row(Icons.person_outline_rounded, 'Responsável da obra', '${ctx['responsavel_obra'] ?? '-'}', accent),
        ));
        rows.add(pairRows(
          row(Icons.precision_manufacturing_outlined, 'Equipamento abastecido', equipment.isEmpty ? '-' : equipment, accent),
          row(Icons.business_outlined, 'Proprietário do equipamento', '${ctx['proprietario_equipamento'] ?? '-'}', accent),
        ));
        rows.add(row(Icons.location_on_outlined, 'Localização', '${x['location_address'] ?? '-'}', accent));
        rows.add(pairRows(
          row(Icons.water_drop_outlined, 'Combustível', _fuelLabel(x['fuel_type']), accent),
          row(Icons.local_gas_station_rounded, 'Volume', _fmtLiters(x['liters']), accent),
        ));
        rows.add(pairRows(
          row(Icons.speed_outlined, 'KM', '${x['km_value'] ?? x['km_hourmeter'] ?? '-'}', accent),
          row(Icons.speed_outlined, 'Horímetro', '${x['hourmeter_value'] ?? '-'}', accent),
        ));
        rows.add(pairRows(
          row(Icons.person_outline_rounded, 'Quem recebeu', receiver, accent),
          row(Icons.person_outline_rounded, 'Quem abasteceu', operator, accent),
        ));
        rows.add(row(Icons.receipt_long_outlined, 'NF(s)/Lote(s) utilizados', nfs, accent));
        if (x['sale_price_per_liter'] != null) {
          rows.add(pairRows(
            row(Icons.assignment_outlined, 'Preço de venda/L', _fmtMoney(x['sale_price_per_liter']), accent),
            row(Icons.assignment_outlined, 'Valor total', _fmtMoney(totalSaleValue), accent),
          ));
        }
        if (_hasValue(x['notes'])) {
          rows.add(row(Icons.assignment_outlined, 'Observações', '${x['notes']}', accent));
        }
        // O Totalizador é sempre o último dado operacional, imediatamente antes das assinaturas.
        rows.add(row(Icons.storage_outlined, 'Totalizador', _fmtLiters(x['totalizer'] ?? x['closing_meter']), accent));
      }
"""
rep(old_fueling, new_fueling, 'fueling rows/order/value total')

# Evita duplicar Observações depois do Totalizador nos abastecimentos.
rep(
"if (_hasValue(x['notes'])) row(Icons.assignment_outlined, 'Observações', '${x['notes']}', accent),",
"if (_hasValue(x['notes']) && !fueling) row(Icons.assignment_outlined, 'Observações', '${x['notes']}', accent),",
'notes after rows')

# Cabeçalho/card mais compactos.
s = s.replace("fontSize: 32", "fontSize: 27")
s = s.replace("fontSize: 21", "fontSize: 17")
s = s.replace("pw.SizedBox(height: 14),\n      ];", "pw.SizedBox(height: 8),\n      ];")
s = s.replace("padding: const pw.EdgeInsets.all(14),", "padding: const pw.EdgeInsets.all(10),")
s = s.replace("width: 48, height: 48", "width: 40, height: 40")
s = s.replace("size: 24, isWhite: true", "size: 20, isWhite: true")
s = s.replace("pw.SizedBox(width: 12)", "pw.SizedBox(width: 8)")
s = s.replace("fontSize: 15, color: accentN", "fontSize: 13.5, color: accentN")
s = s.replace("fontSize: 10.5, color: text", "fontSize: 9, color: text")

# A ficha principal passa a ser uma única página; evidências continuam em páginas separadas.
old_page = """      doc.addPage(pw.MultiPage(
        pageFormat: PdfPageFormat.a4,
        margin: const pw.EdgeInsets.fromLTRB(30, 28, 30, 24),
        theme: pw.ThemeData.withFont(base: regular, bold: bold),
        build: (_) => body,
      ));
"""
new_page = """      doc.addPage(pw.Page(
        pageFormat: PdfPageFormat.a4,
        margin: const pw.EdgeInsets.fromLTRB(24, 20, 24, 18),
        theme: pw.ThemeData.withFont(base: regular, bold: bold),
        build: (_) => pw.Column(crossAxisAlignment: pw.CrossAxisAlignment.start, children: body),
      ));
"""
rep(old_page, new_page, 'single main page')

p.write_text(s)
print('pdf review corrections staged', len(s))
