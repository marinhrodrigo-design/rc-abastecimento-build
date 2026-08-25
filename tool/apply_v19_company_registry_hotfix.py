from pathlib import Path
p=Path('lib/main_online.dart')
t=p.read_text()
old="TextField(controller: name, decoration: const InputDecoration(labelText: 'Nome da empresa *'))"
new="TextField(controller: name, onChanged: (_) => setDialogState(() {}), decoration: const InputDecoration(labelText: 'Nome da empresa *'))"
if old not in t:
    raise SystemExit('v19 hotfix: campo Nome da empresa não encontrado')
t=t.replace(old,new,1)
p.write_text(t)
print('v19 hotfix: botão Salvar reage ao preenchimento do nome da empresa.')
