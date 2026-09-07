from pathlib import Path

p = Path('lib/main_online.dart')
s = p.read_text(encoding='utf-8')

if "Text('v90'" not in s:
    raise SystemExit('v90 label not found')
s = s.replace("Text('v90'", "Text('v91'", 1)

unit_home = """                  const Card(\n                      child: ListTile(\n                          leading: Icon(Icons.location_on_outlined,\n                              color: Colors.orange),\n                          title: Text('Localização deve estar ativada',\n                              style: TextStyle(fontWeight: FontWeight.w900)),\n                          subtitle: Text(\n                              'O ponto exato do abastecimento será capturado automaticamente ao concluir.'))),\n                  const SizedBox(height: 12),\n                  if (truck) ...[\n"""
unit_repl = """                  if (truck) ...[\n"""
if s.count(unit_home) != 1:
    raise SystemExit(f'unit home location block count={s.count(unit_home)}')
s = s.replace(unit_home, unit_repl, 1)

global_home = """                  const SizedBox(height: 12),\n                  const Card(\n                      child: ListTile(\n                          leading: Icon(Icons.location_on_outlined,\n                              color: Colors.orange),\n                          title: Text('Localização deve estar ativada',\n                              style: TextStyle(fontWeight: FontWeight.w900)),\n                          subtitle: Text(\n                              'O ponto exato do abastecimento será capturado automaticamente ao concluir.'))),\n                  const SizedBox(height: 10),\n                  GridView.count(\n"""
global_repl = """                  const SizedBox(height: 12),\n                  GridView.count(\n"""
if s.count(global_home) != 1:
    raise SystemExit(f'global home location block count={s.count(global_home)}')
s = s.replace(global_home, global_repl, 1)

post_totalizer = """              const Card(\n                  child: ListTile(\n                      leading: Icon(Icons.location_on_outlined,\n                          color: Colors.orange),\n                      title: Text('Localização deve estar ativada',\n                          style: TextStyle(fontWeight: FontWeight.w900)))),\n              const SizedBox(height: 12),\n"""
if s.count(post_totalizer) != 1:
    raise SystemExit(f'post-totalizer location block count={s.count(post_totalizer)}')
s = s.replace(post_totalizer, '', 1)

primary_anchor = """                          const SizedBox(height: 16),\n                          FilledButton.icon(\n                              onPressed: captureTotalizerBeforeV70,\n"""
primary_insert = """                          const SizedBox(height: 12),\n                          const Row(\n                            crossAxisAlignment: CrossAxisAlignment.center,\n                            children: [\n                              Icon(Icons.location_on_outlined,\n                                  color: Colors.orange, size: 22),\n                              SizedBox(width: 8),\n                              Expanded(\n                                child: Text(\n                                  'Localização deve estar ativada',\n                                  style: TextStyle(\n                                      fontWeight: FontWeight.w800),\n                                ),\n                              ),\n                            ],\n                          ),\n                          const SizedBox(height: 12),\n                          FilledButton.icon(\n                              onPressed: captureTotalizerBeforeV70,\n"""
if s.count(primary_anchor) != 1:
    raise SystemExit(f'primary pre-photo anchor count={s.count(primary_anchor)}')
s = s.replace(primary_anchor, primary_insert, 1)

legacy_anchor = """              const SizedBox(height: 22),\n              SizedBox(\n                  height: 54,\n                  child: FilledButton.icon(\n                      onPressed: busy ? null : captureTotalizerBeforeLegacyV70,\n"""
legacy_insert = """              const SizedBox(height: 14),\n              const Row(\n                crossAxisAlignment: CrossAxisAlignment.center,\n                children: [\n                  Icon(Icons.location_on_outlined,\n                      color: Colors.orange, size: 22),\n                  SizedBox(width: 8),\n                  Expanded(\n                    child: Text(\n                      'Localização deve estar ativada',\n                      style: TextStyle(fontWeight: FontWeight.w800),\n                    ),\n                  ),\n                ],\n              ),\n              const SizedBox(height: 14),\n              SizedBox(\n                  height: 54,\n                  child: FilledButton.icon(\n                      onPressed: busy ? null : captureTotalizerBeforeLegacyV70,\n"""
if s.count(legacy_anchor) != 1:
    raise SystemExit(f'legacy pre-photo anchor count={s.count(legacy_anchor)}')
s = s.replace(legacy_anchor, legacy_insert, 1)

if s.count('O ponto exato do abastecimento será capturado automaticamente ao concluir.') != 0:
    raise SystemExit('old dashboard location explanation still present')
if s.count('Localização deve estar ativada') != 2:
    raise SystemExit(f'unexpected location reminder count={s.count("Localização deve estar ativada")}')
if "Text('v91'" not in s:
    raise SystemExit('v91 label not applied')

p.write_text(s, encoding='utf-8')
print('V91_LOCATION_UI_PATCH_PASS')
