from pathlib import Path
import re

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
path.write_text(text)
print('v14 compat: catálogo administrativo preparado.')
