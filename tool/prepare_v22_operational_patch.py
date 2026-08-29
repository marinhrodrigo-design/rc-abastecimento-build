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

# Diagnóstico temporário: mostra exatamente qual card Novo abastecimento foi reutilizado.
needle = "new_fueling_card = text[card_start:card_end + 1]\n"
if "V22_REUSED_CARD_START" not in text:
    text = text.replace(
        needle,
        needle + "print('V22_REUSED_CARD_START')\nprint(new_fueling_card)\nprint('V22_REUSED_CARD_END')\n",
        1,
    )

required_absent = [
    "elif ch == '{{': cur += 1",
    "${_friendlyError(e)}",
    "${_hasValue(assetText) ? ' • $assetText' : ''}",
]
for marker in required_absent:
    if marker in text:
        raise SystemExit(f'prepare v22: correção não aplicada: {marker}')

path.write_text(text)
print('prepare v22: patch operacional compatibilizado para compilação.')
