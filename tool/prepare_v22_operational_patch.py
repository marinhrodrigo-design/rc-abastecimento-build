from pathlib import Path

path = Path('tool/apply_v22_operational_my_fuelings.py')
text = path.read_text()

# HomeActionCard exige subtitle; o v22 já fornece esse campo em Meus abastecimentos.

# Corrige o balanceamento de chaves usado para localizar o body do Scaffold.
text = text.replace("        elif ch == '{{': cur += 1", "        elif ch == '{': cur += 1")
text = text.replace("        elif ch == '}}':", "        elif ch == '}':")

# Evita dependência de helpers que podem variar entre snapshots do app.
text = text.replace("${_friendlyError(e)}", "${e.toString()}")
text = text.replace("${_hasValue(assetText) ? ' • $assetText' : ''}", "${assetText.toString().trim().isNotEmpty ? ' • $assetText' : ''}")

# O card Novo abastecimento já usa o tanque/origem selecionado no FieldHomeScreen.
# Como o v22 o move para um método separado, recriamos a variável local `t` nesse
# método para preservar exatamente o fluxo atual sem hardcode de CB/CT/TE.
method_needle = "  Widget _operationalHomeBody() {\n    return SafeArea("
method_replacement = "  Widget _operationalHomeBody() {\n    final t = tank;\n    if (t == null || ref == null) {\n      return const Center(child: CircularProgressIndicator());\n    }\n    return SafeArea("
if method_needle in text:
    text = text.replace(method_needle, method_replacement, 1)
elif "final t = tank;" not in text:
    raise SystemExit('prepare v22: método operacional não localizado')

# Remove qualquer diagnóstico temporário inserido em tentativas anteriores.
diagnostic = "print('V22_REUSED_CARD_START')\nprint(new_fueling_card)\nprint('V22_REUSED_CARD_END')\n"
text = text.replace(diagnostic, '')

required_absent = [
    "elif ch == '{{': cur += 1",
    "${_friendlyError(e)}",
    "${_hasValue(assetText) ? ' • $assetText' : ''}",
    "V22_REUSED_CARD_START",
]
for marker in required_absent:
    if marker in text:
        raise SystemExit(f'prepare v22: correção não aplicada: {marker}')

required_present = [
    "final t = tank;",
    "if (t == null || ref == null)",
]
for marker in required_present:
    if marker not in text:
        raise SystemExit(f'prepare v22: marcador obrigatório ausente: {marker}')

path.write_text(text)
print('prepare v22: origem selecionada preservada no home Operacional.')
