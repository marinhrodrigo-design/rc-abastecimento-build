from pathlib import Path

path = Path('lib/main_online.dart')
text = path.read_text()

start = text.index('class _FuelingOnlineScreenState extends State<FuelingOnlineScreen> {')
end = text.index('class ', start + 10)
segment = text[start:end]

old_head = "    final works = _rows(widget.referenceData['works']);\n    final machines = _rows(widget.referenceData['machines']);\n    return Scaffold("
new_head = "    final works = _rows(widget.referenceData['works']);\n    final machines = _rows(widget.referenceData['machines']);\n    final workRequired = widget.sourceTank['tank_type'] == 'comboio';\n    return Scaffold("
if old_head not in segment:
    raise SystemExit('v13: não foi possível localizar cabeçalho do formulário de abastecimento')
segment = segment.replace(old_head, new_head, 1)

old_decoration = "              decoration: const InputDecoration(labelText: 'Obra *'),"
new_decoration = "              decoration: InputDecoration(labelText: workRequired ? 'Obra *' : 'Obra (opcional)'),"
if old_decoration not in segment:
    raise SystemExit('v13: não foi possível localizar rótulo da obra')
segment = segment.replace(old_decoration, new_decoration, 1)

old_validator = "              validator: (v) => v == null ? 'Selecione a obra. O administrador pode cadastrá-la.' : null,"
new_validator = "              validator: (v) => workRequired && v == null ? 'Selecione a obra. O administrador pode cadastrá-la.' : null,"
if old_validator not in segment:
    raise SystemExit('v13: não foi possível localizar validação da obra')
segment = segment.replace(old_validator, new_validator, 1)

text = text[:start] + segment + text[end:]

if "workRequired ? 'Obra *' : 'Obra (opcional)'" not in text:
    raise SystemExit('v13: rótulo condicional não aplicado')
if "workRequired && v == null" not in text:
    raise SystemExit('v13: validação condicional não aplicada')

path.write_text(text)
print('v13: obra obrigatória no comboio e opcional no tanque estacionário.')
