from pathlib import Path
p=Path('lib/main_online.dart')
s=p.read_text()
old="Text('Não foi possível carregar os registros.\n$errorMessage',textAlign:TextAlign.center)"
if old not in s:
    raise SystemExit('follow-up hotfix anchor missing')
s=s.replace(old,"Text('Não foi possível carregar os registros.\\n$errorMessage',textAlign:TextAlign.center)",1)
p.write_text(s)
print('follow-up string hotfix applied')
