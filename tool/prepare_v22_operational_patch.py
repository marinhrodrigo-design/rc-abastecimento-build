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
