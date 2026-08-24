from pathlib import Path

path = Path('lib/main_online.dart')
text = path.read_text()

# 1) Tela de detalhe: a linha que antes se chamava "Quantidade abastecida"
# passa a representar o tipo do atendimento, mantendo a litragem logo abaixo.
if "'Quantidade abastecida'" not in text:
    raise SystemExit('v18: marcador Quantidade abastecida não encontrado na tela de detalhe')
text = text.replace("'Quantidade abastecida'", "'Abastecimento/Lubrificação'")

# 2) PDF: desenhar separadores em vez de enviar o caractere bullet à fonte Helvetica.
marker = "    pw.Widget rule() => pw.Container(height: 0.7, color: lineColor);\n"
if marker not in text:
    raise SystemExit('v18: marcador rule() do PDF não encontrado')
helper = r'''    pw.Widget bulletText(String value, pw.TextStyle style, {double dotSize = 3.4}) {
      final parts = value.split('•').map((e) => e.trim()).where((e) => e.isNotEmpty).toList();
      if (parts.length <= 1) return pw.Text(value.replaceAll('•', ''), style: style);
      final children = <pw.Widget>[];
      for (var i = 0; i < parts.length; i++) {
        if (i > 0) {
          children.add(pw.Padding(
            padding: const pw.EdgeInsets.symmetric(horizontal: 7, vertical: 5),
            child: pw.Container(
              width: dotSize,
              height: dotSize,
              decoration: pw.BoxDecoration(color: style.color ?? textColor, shape: pw.BoxShape.circle),
            ),
          ));
        }
        children.add(pw.Text(parts[i], style: style));
      }
      return pw.Wrap(crossAxisAlignment: pw.WrapCrossAlignment.center, children: children);
    }

'''
text = text.replace(marker, helper + marker, 1)

# 3) Qualquer valor com separador dentro das linhas do PDF usa bulletText.
old = "              pw.Text(value, style: pw.TextStyle(font: regular, fontSize: 13.5, color: textColor)),"
new = "              bulletText(value, pw.TextStyle(font: regular, fontSize: 13.5, color: textColor)),"
if old not in text:
    raise SystemExit('v18: valor de fullRow não encontrado')
text = text.replace(old, new, 1)

old = "              pw.Text(value, style: pw.TextStyle(font: regular, fontSize: 13, color: textColor)),"
new = "              bulletText(value, pw.TextStyle(font: regular, fontSize: 13, color: textColor)),"
if old not in text:
    raise SystemExit('v18: valor de halfRow não encontrado')
text = text.replace(old, new, 1)

# 4) Cabeçalho do cartão: título com ponto gráfico; segunda linha = data/hora + quem abasteceu.
old = "                  pw.Text(title, style: pw.TextStyle(font: bold, fontSize: 17.5, color: navy)),\n                  pw.SizedBox(height: 5),\n                  pw.Text('${_fmtDate(x['created_at'])}  •  $liters', style: pw.TextStyle(font: regular, fontSize: 13, color: textColor)),"
new = "                  bulletText(title, pw.TextStyle(font: bold, fontSize: 17.5, color: navy)),\n                  pw.SizedBox(height: 5),\n                  bulletText('${_fmtDate(x['created_at'])} • $operator', pw.TextStyle(font: regular, fontSize: 13, color: textColor)),"
if old not in text:
    raise SystemExit('v18: cabeçalho do cartão PDF v17 não encontrado')
text = text.replace(old, new, 1)

# 5) Ordem aprovada do conteúdo do PDF:
# Obra; depois Localização + Combustível; depois tipo do atendimento; depois litragem como valor;
# em seguida Recebedor, Quem abasteceu, KM/horímetro e estoques.
old = r'''              pw.Row(children: [
                halfRow(Icons.location_city_outlined, 'Obra', work),
                pw.Container(width: 0.7, height: 50, color: lineColor),
                halfRow(Icons.water_drop_outlined, 'Combustível', fuel),
              ]),
              rule(),
              fullRow(Icons.location_on_outlined, 'Localização', location, height: 62),
              rule(),
              fullRow(Icons.person_outline_rounded, 'Recebedor', receiver),
'''
new = r'''              fullRow(Icons.location_city_outlined, 'Obra', work),
              rule(),
              pw.Row(crossAxisAlignment: pw.CrossAxisAlignment.start, children: [
                halfRow(Icons.location_on_outlined, 'Localização', location),
                pw.Container(width: 0.7, height: 58, color: lineColor),
                halfRow(Icons.water_drop_outlined, 'Combustível', fuel),
              ]),
              rule(),
              fullRow(Icons.local_gas_station_rounded, _movementLabelForItem(x), liters),
              rule(),
              fullRow(Icons.person_outline_rounded, 'Recebedor', receiver),
'''
if old not in text:
    raise SystemExit('v18: sequência Obra/Combustível/Localização do PDF v17 não encontrada')
text = text.replace(old, new, 1)

# 6) Endereço da empresa também não envia bullet diretamente para Helvetica.
old = "          pw.Text('Endereço: $companyAddress', style: pw.TextStyle(font: regular, fontSize: 11.5, color: textColor)),"
new = "          bulletText('Endereço: $companyAddress', pw.TextStyle(font: regular, fontSize: 11.5, color: textColor), dotSize: 2.7),"
if old not in text:
    raise SystemExit('v18: linha de endereço da empresa não encontrada')
text = text.replace(old, new, 1)

# Validações estruturais finais.
pdf_start = text.find('class FuelPdfReport {')
pdf_end = text.find('class AdminUsersOnlineScreen', pdf_start)
if pdf_start < 0 or pdf_end < 0:
    raise SystemExit('v18: classe FuelPdfReport não encontrada após alteração')
pdf = text[pdf_start:pdf_end]
required = [
    "bulletText('${_fmtDate(x['created_at'])} • $operator'",
    "halfRow(Icons.location_on_outlined, 'Localização', location)",
    "halfRow(Icons.water_drop_outlined, 'Combustível', fuel)",
    "fullRow(Icons.local_gas_station_rounded, _movementLabelForItem(x), liters)",
    "signatureBox('Assinatura de quem recebeu'",
    "signatureBox('Assinatura de quem abasteceu'",
    "'Estoque do $source antes'",
    "'Estoque do $source depois'",
]
for value in required:
    if value not in pdf:
        raise SystemExit(f'v18: marcador final ausente: {value}')
if "pw.Text('${_fmtDate(x['created_at'])}  •  $liters'" in pdf:
    raise SystemExit('v18: litragem ainda está no cabeçalho antigo do PDF')
if 'REGISTRO CONFERIDO' in pdf or 'carimbo' in pdf.lower():
    raise SystemExit('v18: carimbo não deve existir')
if 'pw.Icon(' in pdf:
    raise SystemExit('v18: não usar pw.Icon no PDF')

path.write_text(text)
print('v18: ordem final aprovada aplicada ao detalhe e PDF; separadores PDF desenhados sem caractere inválido.')
