from pathlib import Path

ROOT=Path('.')
main=ROOT/'lib/main_online.dart'
v29=ROOT/'lib/v29_features.dart'
v31=ROOT/'lib/v31_features.dart'

def replace(path, old, new, label):
    text=path.read_text(encoding='utf-8')
    if old not in text:
        raise SystemExit(f'PATCH_V68_FAIL[{label}]: trecho não encontrado em {path}')
    text=text.replace(old,new,1)
    path.write_text(text,encoding='utf-8')


for _part in range(1,7):
    _p=Path(__file__).with_name(f'v68_patch_{_part}.pyinc')
    exec(compile(_p.read_text(encoding='utf-8'),str(_p),'exec'),globals(),globals())
