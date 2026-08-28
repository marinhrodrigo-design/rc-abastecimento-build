from pathlib import Path
p = Path('lib/main_online.dart')
s = p.read_text()
count = s.count('_navy')
if count == 0:
    raise SystemExit('expected _navy references not found')
s = s.replace('_navy', '_blue')
p.write_text(s)
print('v24 compile hotfix applied', count)
