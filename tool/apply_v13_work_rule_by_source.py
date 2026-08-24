from pathlib import Path
import re

path = Path('lib/main_online.dart')
text = path.read_text()

start = text.index('class _FuelingOnlineScreenState extends State<FuelingOnlineScreen> {')
end = text.index('class ', start + 10)
segment = text[start:end]

if "final workRequired = widget.sourceTank['tank_type'] == 'comboio';" not in segment:
    segment, count = re.subn(
        r"(?m)^(\s*)final works = ([^\n]+);$",
        r"\1final works = \2;\n\1final workRequired = widget.sourceTank['tank_type'] == 'comboio';",
        segment,
        count=1,
    )
    if count != 1:
        raise SystemExit('v13: não foi possível localizar a lista de obras no formulário')

segment, count = re.subn(
    r"decoration:\s*(?:const\s+)?InputDecoration\(labelText:\s*'Obra \*'\),",
    "decoration: InputDecoration(labelText: workRequired ? 'Obra *' : 'Obra (opcional)'),",
    segment,
    count=1,
)
if count != 1:
    raise SystemExit('v13: não foi possível localizar rótulo da obra')

# Substitui a linha de validação logo após o campo Obra, sem depender do texto anterior.
label_pos = segment.index("workRequired ? 'Obra *' : 'Obra (opcional)'")
validator_pos = segment.find('validator:', label_pos, min(len(segment), label_pos + 1600))
if validator_pos < 0:
    raise SystemExit('v13: não foi possível localizar validação da obra')
line_start = segment.rfind('\n', 0, validator_pos) + 1
line_end = segment.find('\n', validator_pos)
if line_end < 0:
    line_end = len(segment)
indent = segment[line_start:validator_pos]
segment = (
    segment[:line_start]
    + indent
    + "validator: (v) => workRequired && v == null ? 'Selecione a obra. O administrador pode cadastrá-la.' : null,"
    + segment[line_end:]
)

text = text[:start] + segment + text[end:]

if "workRequired ? 'Obra *' : 'Obra (opcional)'" not in text:
    raise SystemExit('v13: rótulo condicional não aplicado')
if "workRequired && v == null" not in text:
    raise SystemExit('v13: validação condicional não aplicada')

path.write_text(text)
print('v13: obra obrigatória no comboio e opcional no tanque estacionário.')
