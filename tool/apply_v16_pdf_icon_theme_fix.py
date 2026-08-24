from pathlib import Path

path = Path('lib/main_online.dart')
text = path.read_text()

old_theme = "theme: pw.ThemeData.withFont(base: regular, bold: bold),"
new_theme = "theme: pw.ThemeData.withFont(base: regular, bold: bold, icons: iconFont),"
if old_theme not in text:
    raise SystemExit('v16: tema do PDF sem fonte de ícones não encontrado')
text = text.replace(old_theme, new_theme, 1)

old_icon = "return pw.Icon(pw.IconData(icon.codePoint), font: iconFont, size: size, color: blue);"
new_icon = "return pw.Icon(pw.IconData(icon.codePoint), size: size, color: blue);"
if old_icon not in text:
    raise SystemExit('v16: renderização de ícone v15 não encontrada')
text = text.replace(old_icon, new_icon, 1)

old_header = "pw.Icon(pw.IconData(Icons.local_gas_station_rounded.codePoint), font: iconFont, size: 22, color: PdfColors.white)"
new_header = "pw.Icon(pw.IconData(Icons.local_gas_station_rounded.codePoint), size: 22, color: PdfColors.white)"
if old_header not in text:
    raise SystemExit('v16: ícone do cabeçalho v15 não encontrado')
text = text.replace(old_header, new_header, 1)

pdf = text[text.index('class FuelPdfReport'):]
if 'ThemeData.withFont(base: regular, bold: bold, icons: iconFont)' not in pdf:
    raise SystemExit('v16: fonte Material Icons não foi registrada no tema do PDF')
if 'String.fromCharCode(' in pdf:
    raise SystemExit('v16: ainda existe conversão textual de ícone no PDF')

path.write_text(text)
print('v16: fonte Material Icons registrada no tema do PDF; pw.Icon usa o tema corretamente.')
