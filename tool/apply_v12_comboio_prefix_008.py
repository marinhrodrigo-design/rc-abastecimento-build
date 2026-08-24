from pathlib import Path

path = Path('lib/main_online.dart')
text = path.read_text()


def one(old: str, new: str, label: str) -> None:
    global text
    if old not in text:
        raise SystemExit(f'v12 não aplicado: {label}')
    text = text.replace(old, new, 1)

# A classificação do comboio vem exclusivamente do prefixo do ativo.
one(
"""    final out = _rows(widget.referenceData['machines']).where((m) {
      final comboio = m['is_comboio'] == true || '${m['tipo'] ?? ''}'.toUpperCase().contains('COMBOIO');
      return comboio && _intOrNull(m['comboio_tank_id']) != null;
    }).toList();""",
"""    final out = _rows(widget.referenceData['machines']).where((m) {
      final asset = '${m['numeroAtivo'] ?? ''}'.trim();
      return asset.startsWith('008');
    }).toList();""",
'lista de comboios por prefixo 008',
)

text = text.replace(
    "Cadastre primeiro um ativo do tipo Comboio.",
    "Cadastre primeiro um ativo cujo número comece com 008.",
)

# No cadastro/edição do ativo, o número 008-... é que abre a capacidade do comboio.
one(
"""      final isComboio = type.text.trim().toUpperCase().contains('COMBOIO');
      return AlertDialog(title: Text(item == null ? 'Cadastrar ativo' : 'Editar ativo'), content: SingleChildScrollView(child: Column(mainAxisSize: MainAxisSize.min, children: [
        TextField(controller: number, decoration: const InputDecoration(labelText: 'Número do ativo *')),""",
"""      final isComboio = number.text.trim().startsWith('008');
      return AlertDialog(title: Text(item == null ? 'Cadastrar ativo' : 'Editar ativo'), content: SingleChildScrollView(child: Column(mainAxisSize: MainAxisSize.min, children: [
        TextField(controller: number, onChanged: (_) => setLocal(() {}), decoration: const InputDecoration(labelText: 'Número do ativo *')),""",
'capacidade exibida pelo prefixo',
)

one(
"""        const SizedBox(height: 8), TextField(controller: type, onChanged: (_) => setLocal(() {}), decoration: const InputDecoration(labelText: 'Tipo', hintText: 'Ex.: CAMINHÃO COMBOIO')),""",
"""        const SizedBox(height: 8), TextField(controller: type, decoration: const InputDecoration(labelText: 'Tipo')),""",
'tipo não define comboio',
)

one(
"""      final isComboio = type.text.trim().toUpperCase().contains('COMBOIO');
      final parsed = double.tryParse(capacity.text.trim().replaceAll(',', '.'));""",
"""      final isComboio = number.text.trim().startsWith('008');
      final parsed = double.tryParse(capacity.text.trim().replaceAll(',', '.'));""",
'salvamento por prefixo',
)

# Confirma que a regra antiga deixou de existir nos pontos operacionais da v11.
if "final comboio = m['is_comboio'] == true || '${m['tipo'] ?? ''}'.toUpperCase().contains('COMBOIO');" in text:
    raise SystemExit('v12: filtro antigo por Tipo ainda presente')
if "final isComboio = type.text.trim().toUpperCase().contains('COMBOIO');" in text:
    raise SystemExit('v12: detecção antiga por Tipo ainda presente')
if "asset.startsWith('008')" not in text or "number.text.trim().startsWith('008')" not in text:
    raise SystemExit('v12: regra do prefixo 008 não encontrada')

path.write_text(text)
print('v12: todo ativo iniciado por 008 é tratado como comboio.')
