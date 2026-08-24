from pathlib import Path
import re

path = Path('lib/main_online.dart')
text = path.read_text()

start = text.index('class _FuelingOnlineScreenState extends State<FuelingOnlineScreen> {')
end = text.index('class ', start + 10)
segment = text[start:end]

# Insere a regra logo após a declaração da lista de obras, sem depender das linhas vizinhas.
if "final workRequired = widget.sourceTank['tank_type'] == 'comboio';" not in segment:
    segment, count = re.subn(
        r"(?m)^(\s*)final works = ([^\n]+);$",
        r"\1final works = \2;\n\1final workRequired = widget.sourceTank['tank_type'] == 'comboio';",
        segment,
        count=1,
    )
    if count != 1:
        raise SystemExit('v13: não foi possível localizar a lista de obras no formulário')

# Comboio mostra obra obrigatória; tanque estacionário mostra obra opcional.
segment, count = re.subn(
    r"decoration:\s*(?:const\s+)?InputDecoration\(labelText:\s*'Obra \*'\),",
    "decoration: InputDecoration(labelText: workRequired ? 'Obra *' : 'Obra (opcional)'),",
    segment,
    count=1,
)
if count != 1:
    raise SystemExit('v13: não foi possível localizar rótulo da obra')

# A validação só impede salvar sem obra quando a origem é comboio.
segment, count = re.subn(
    r"validator:\s*\(v\)\s*=>\s*v\s*==\s*null\s*\?\s*'Selecione a obra\. O administrador pode cadastrá-la\.'\s*:\s*null,",
    "validator: (v) => workRequired && v == null ? 'Selecione a obra. O administrador pode cadastrá-la.' : null,",
    segment,
    count=1,
)
if count != 1:
    raise SystemExit('v13: não foi possível localizar validação da obra')

text = text[:start] + segment + text[end:]

if "workRequired ? 'Obra *' : 'Obra (opcional)'" not in text:
    raise SystemExit('v13: rótulo condicional não aplicado')
if "workRequired && v == null" not in text:
    raise SystemExit('v13: validação condicional não aplicada')

path.write_text(text)
print('v13: obra obrigatória no comboio e opcional no tanque estacionário.')
