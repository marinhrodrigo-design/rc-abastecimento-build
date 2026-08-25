from pathlib import Path

patch = Path('tool/apply_v19_company_registry_pdf.py')
s = patch.read_text()
start = s.find("old_home = r'''")
end = s.find("\n\nmarker = 'class AdminCatalogScreen extends StatelessWidget {'", start)
if start < 0 or end < 0:
    raise SystemExit('v19 precompat: bloco antigo de encaixe do Mais não encontrado')

replacement = r'''home_start = text.find('class AdminHomeScreen extends StatefulWidget {')
home_end = text.find('class AdminRecordsScreen extends StatefulWidget {', home_start)
if home_start < 0 or home_end < 0:
    raise SystemExit('v19: AdminHomeScreen não encontrado')
home = text[home_start:home_end]
if "tooltip: 'Mais'" not in home:
    actions_marker = 'actions: ['
    pos = home.find(actions_marker)
    if pos < 0:
        raise SystemExit('v19: lista de ações do AdminHomeScreen não encontrada')
    insert_at = pos + len(actions_marker)
    more_action = "IconButton(onPressed: () => Navigator.push(context, MaterialPageRoute(builder: (_) => const AdminMoreScreen())), tooltip: 'Mais', icon: const Icon(Icons.more_horiz_rounded)), "
    home = home[:insert_at] + more_action + home[insert_at:]
    text = text[:home_start] + home + text[home_end:]
'''

s = s[:start] + replacement + s[end:]
patch.write_text(s)
print('v19 precompat: página Mais será aberta pelo ícone do painel admin.')
