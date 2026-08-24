from pathlib import Path
import re, ast, base64, gzip

# 1) Normaliza o cartão Obras na fonte final após v13.
path = Path('lib/main_online.dart')
text = path.read_text()
expected = "HomeActionCard(icon: Icons.location_city_outlined, title: 'Obras'"
if expected not in text:
    text, count = re.subn(
        r"HomeActionCard\(icon:\s*[^,]+,\s*title:\s*'Obras'",
        expected,
        text,
        count=1,
    )
    if count != 1:
        raise SystemExit('v14 compat: cartão Obras não encontrado')

text, count = re.subn(
    r"(?m)^\s*(HomeActionCard\(icon: Icons\.location_city_outlined, title: 'Obras'.*)$",
    r"      \1",
    text,
    count=1,
)
if count != 1:
    raise SystemExit('v14 compat: linha do cartão Obras não pôde ser normalizada')
path.write_text(text)

# 2) Corrige o limite interno do pacote v14.
# O patch original substituía _AdminUsers... até TanksAdminScreen e, na fonte atual,
# AdminCatalogScreen fica dentro desse intervalo. Isso apagava a tela Cadastros/Obras
# antes da etapa que precisava inserir "Dados da empresa".
wrapper_path = Path('tool/apply_v14_final_package.py')
wrapper = wrapper_path.read_text()
m = re.search(r"payload\s*=\s*('''.*?''')", wrapper, re.S)
if not m:
    raise SystemExit('v14 compat: payload interno do v14 não encontrado')
payload = ast.literal_eval(m.group(1))
inner = gzip.decompress(base64.b64decode(payload)).decode()
old = "ue = text.index('class TanksAdminScreen extends StatefulWidget {', us)"
new = "ue = text.index('class AdminCatalogScreen extends StatelessWidget {', us)"
if old in inner:
    inner = inner.replace(old, new, 1)
elif new not in inner:
    raise SystemExit('v14 compat: limite da gestão de usuários não encontrado')
new_payload = base64.b64encode(gzip.compress(inner.encode(), mtime=0)).decode()
wrapper = wrapper[:m.start(1)] + "'''" + new_payload + "'''" + wrapper[m.end(1):]
wrapper_path.write_text(wrapper)

print('v14 compat: catálogo preservado e limite da gestão de usuários corrigido.')
