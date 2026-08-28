from pathlib import Path

p = Path('lib/main_online.dart')
s = p.read_text()

old = "subtitle:Text(k,style:const TextStyle(fontSize:11)),"
if old not in s:
    raise SystemExit('permission technical-key subtitle anchor not found')

s = s.replace(old, '', 1)

# Safety: the permission key remains used internally for saving/access control,
# but it must not be rendered as visible subtitle text in the permissions UI.
if "title:Text(_permissionLabelV23(k)),subtitle:Text(k" in s:
    raise SystemExit('technical permission key is still visible in permissions UI')

p.write_text(s)
print('v29 permission technical keys hidden from UI', len(s))
