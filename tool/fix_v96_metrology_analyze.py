from pathlib import Path

p = Path('lib/main_online.dart')
s = p.read_text()
old = 'previousPhysicalLiters == null || previousPhysicalLiters! < 0'
new = 'previousPhysicalLiters == null || previousPhysicalLiters < 0'
count = s.count(old)
if count != 2:
    raise SystemExit(f'V96 analyze fix expected 2 anchors, found {count}')
s = s.replace(old, new)
if 'previousPhysicalLiters!' in s:
    raise SystemExit('V96 analyze fix left a non-null assertion')
p.write_text(s)
print('V96_METROLOGY_ANALYZE_FIX_PASS')
