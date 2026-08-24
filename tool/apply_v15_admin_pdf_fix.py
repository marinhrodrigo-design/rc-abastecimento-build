from pathlib import Path

path = Path('lib/main_online.dart')
text = path.read_text()

old_icon = "return pw.Text(String.fromCharCode(icon.codePoint), style: pw.TextStyle(font: iconFont, fontSize: size, color: blue));"
new_icon = "return pw.Icon(pw.IconData(icon.codePoint), font: iconFont, size: size, color: blue);"
if old_icon not in text:
    raise SystemExit('v15: renderização textual dos ícones do PDF não encontrada')
text = text.replace(old_icon, new_icon, 1)

old_header = "pw.Text(String.fromCharCode(Icons.local_gas_station_rounded.codePoint), style: pw.TextStyle(font: iconFont, fontSize: 22, color: PdfColors.white))"
new_header = "pw.Icon(pw.IconData(Icons.local_gas_station_rounded.codePoint), font: iconFont, size: 22, color: PdfColors.white)"
if old_header not in text:
    raise SystemExit('v15: ícone do cabeçalho do PDF não encontrado')
text = text.replace(old_header, new_header, 1)

# Garante que nenhum outro ícone Material do PDF continue sendo transformado em string.
if 'String.fromCharCode(' in text[text.index('class FuelPdfReport'):]:
    raise SystemExit('v15: ainda existe String.fromCharCode dentro do gerador de PDF')

path.write_text(text)
print('v15: ícones do PDF corrigidos com pw.Icon/pw.IconData; layout preservado.')
