from pathlib import Path
import re

path = Path('lib/main_online.dart')
text = path.read_text()

# Este patch preserva integralmente o fluxo existente do card "Novo abastecimento".
# Em vez de reconstruir seu callback, ele reutiliza o próprio HomeActionCard já existente
# dentro da mesma classe/State e troca apenas o corpo visual para usuários Operacionais.

CARD_TITLE = "title: 'Novo abastecimento'"
card_title_pos = text.find(CARD_TITLE)
if card_title_pos < 0:
    raise SystemExit('v22: card Novo abastecimento não encontrado')

# Encontra o HomeActionCard que contém o título e extrai a chamada completa.
card_start = text.rfind('HomeActionCard(', 0, card_title_pos)
if card_start < 0:
    raise SystemExit('v22: início do card Novo abastecimento não encontrado')


def matching_paren(source: str, open_pos: int) -> int:
    depth = 0
    quote = None
    escape = False
    line_comment = False
    block_comment = False
    i = open_pos
    while i < len(source):
        ch = source[i]
        nx = source[i + 1] if i + 1 < len(source) else ''
        if line_comment:
            if ch == '\n':
                line_comment = False
            i += 1
            continue
        if block_comment:
            if ch == '*' and nx == '/':
                block_comment = False
                i += 2
                continue
            i += 1
            continue
        if quote is not None:
            if escape:
                escape = False
            elif ch == '\\':
                escape = True
            elif ch == quote:
                quote = None
            i += 1
            continue
        if ch == '/' and nx == '/':
            line_comment = True
            i += 2
            continue
        if ch == '/' and nx == '*':
            block_comment = True
            i += 2
            continue
        if ch in ("'", '"'):
            quote = ch
            i += 1
            continue
        if ch == '(':
            depth += 1
        elif ch == ')':
            depth -= 1
            if depth == 0:
                return i
        i += 1
    raise SystemExit('v22: parênteses do card Novo abastecimento não fecham')


card_open = text.find('(', card_start)
card_end = matching_paren(text, card_open)
new_fueling_card = text[card_start:card_end + 1]

# Localiza a classe State que contém o card.
class_matches = list(re.finditer(r'class\s+(_?\w+)\s+extends\s+State<[^>]+>\s*\{', text[:card_start]))
if not class_matches:
    raise SystemExit('v22: State da tela inicial não encontrado')
state_match = class_matches[-1]
state_start = state_match.start()
state_body_start = text.find('{', state_match.start(), state_match.end())

# Determina fim da classe por balanceamento de chaves.
def matching_brace(source: str, open_pos: int) -> int:
    depth = 0
    quote = None
    escape = False
    line_comment = False
    block_comment = False
    i = open_pos
    while i < len(source):
        ch = source[i]
        nx = source[i + 1] if i + 1 < len(source) else ''
        if line_comment:
            if ch == '\n':
                line_comment = False
            i += 1
            continue
        if block_comment:
            if ch == '*' and nx == '/':
                block_comment = False
                i += 2
                continue
            i += 1
            continue
        if quote is not None:
            if escape:
                escape = False
            elif ch == '\\':
                escape = True
            elif ch == quote:
                quote = None
            i += 1
            continue
        if ch == '/' and nx == '/':
            line_comment = True
            i += 2
            continue
        if ch == '/' and nx == '*':
            block_comment = True
            i += 2
            continue
        if ch in ("'", '"'):
            quote = ch
            i += 1
            continue
        if ch == '{':
            depth += 1
        elif ch == '}':
            depth -= 1
            if depth == 0:
                return i
        i += 1
    raise SystemExit('v22: classe inicial não fecha corretamente')

state_end = matching_brace(text, state_body_start)
state = text[state_start:state_end + 1]

# Carrega o papel real do usuário. Enquanto resolve, mostra loading para impedir
# o painel administrativo de piscar na tela de um Operacional.
role_fields = r'''
  bool _homeRoleLoading = true;
  bool _isOperationalHome = false;

  Future<void> _loadHomeRole() async {
    try {
      final value = await Supabase.instance.client.rpc('rca_user_role');
      if (!mounted) return;
      setState(() {
        _isOperationalHome = '${value ?? ''}'.trim().toLowerCase() == 'operator';
        _homeRoleLoading = false;
      });
    } catch (_) {
      if (!mounted) return;
      setState(() {
        _isOperationalHome = false;
        _homeRoleLoading = false;
      });
    }
  }

'''

if '_homeRoleLoading' not in state:
    insert_rel = state.find('{') + 1
    state = state[:insert_rel] + '\n' + role_fields + state[insert_rel:]

# Acopla o carregamento do papel ao initState já existente ou cria um initState.
if '_loadHomeRole();' not in state:
    init_match = re.search(r'void\s+initState\s*\(\s*\)\s*\{', state)
    if init_match:
        super_pos = state.find('super.initState();', init_match.end())
        if super_pos >= 0:
            super_end = super_pos + len('super.initState();')
            state = state[:super_end] + '\n    _loadHomeRole();' + state[super_end:]
        else:
            brace_pos = state.find('{', init_match.start(), init_match.end())
            state = state[:brace_pos + 1] + '\n    _loadHomeRole();' + state[brace_pos + 1:]
    else:
        insert_rel = state.find('{') + 1
        init_code = r'''

  @override
  void initState() {
    super.initState();
    _loadHomeRole();
  }
'''
        state = state[:insert_rel] + init_code + state[insert_rel:]

# Corpo exclusivo do Operacional. O primeiro card é a chamada original, mantendo
# exatamente o comportamento de seleção da origem de combustível já aprovado.
operational_body = f'''
  Widget _operationalHomeBody() {{
    return SafeArea(
      child: LayoutBuilder(
        builder: (context, constraints) => SingleChildScrollView(
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              const Text('Operacional', style: TextStyle(fontSize: 13, color: Colors.black54, fontWeight: FontWeight.w700)),
              const SizedBox(height: 10),
              GridView.count(
                crossAxisCount: 2,
                shrinkWrap: true,
                physics: const NeverScrollableScrollPhysics(),
                mainAxisSpacing: 12,
                crossAxisSpacing: 12,
                childAspectRatio: constraints.maxWidth < 430 ? 1.05 : 1.35,
                children: [
                  {new_fueling_card},
                  HomeActionCard(
                    icon: Icons.history_rounded,
                    title: 'Meus abastecimentos',
                    subtitle: 'Todos os meus registros',
                    onTap: () => Navigator.push(context, MaterialPageRoute(builder: (_) => const MyFuelingsOnlineScreen())),
                  ),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }}

'''

if '_operationalHomeBody()' not in state:
    # Insere antes do build para manter organização e acesso aos métodos do State.
    build_match = re.search(r'@override\s+Widget\s+build\s*\(BuildContext\s+context\)', state)
    if not build_match:
        build_match = re.search(r'Widget\s+build\s*\(BuildContext\s+context\)', state)
    if not build_match:
        raise SystemExit('v22: build da tela inicial não encontrado')
    state = state[:build_match.start()] + operational_body + state[build_match.start():]

# Substitui apenas a expressão body do Scaffold principal, preservando AppBar,
# logout e demais comportamentos do painel para Admin/Gerente/Supervisor.
build_match = re.search(r'Widget\s+build\s*\(BuildContext\s+context\)', state)
if not build_match:
    raise SystemExit('v22: build não localizado após inserções')
body_pos = state.find('body:', build_match.end())
if body_pos < 0:
    raise SystemExit('v22: body do painel inicial não encontrado')
expr_start = body_pos + len('body:')
while expr_start < len(state) and state[expr_start].isspace():
    expr_start += 1

# Lê a expressão do body até a vírgula de nível zero.
def expression_end(source: str, start: int) -> int:
    par = bra = cur = 0
    quote = None
    escape = False
    line_comment = False
    block_comment = False
    i = start
    while i < len(source):
        ch = source[i]
        nx = source[i + 1] if i + 1 < len(source) else ''
        if line_comment:
            if ch == '\n': line_comment = False
            i += 1; continue
        if block_comment:
            if ch == '*' and nx == '/': block_comment = False; i += 2; continue
            i += 1; continue
        if quote is not None:
            if escape: escape = False
            elif ch == '\\': escape = True
            elif ch == quote: quote = None
            i += 1; continue
        if ch == '/' and nx == '/': line_comment = True; i += 2; continue
        if ch == '/' and nx == '*': block_comment = True; i += 2; continue
        if ch in ("'", '"'): quote = ch; i += 1; continue
        if ch == '(': par += 1
        elif ch == ')':
            if par > 0: par -= 1
        elif ch == '[': bra += 1
        elif ch == ']':
            if bra > 0: bra -= 1
        elif ch == '{{': cur += 1
        elif ch == '}}':
            if cur > 0: cur -= 1
        elif ch == ',' and par == 0 and bra == 0 and cur == 0:
            return i
        i += 1
    raise SystemExit('v22: fim da expressão body não encontrado')

body_end = expression_end(state, expr_start)
old_body = state[expr_start:body_end]
if '_homeRoleLoading ?' not in old_body:
    wrapped_body = "_homeRoleLoading\n            ? const Center(child: CircularProgressIndicator())\n            : (_isOperationalHome ? _operationalHomeBody() : (" + old_body + "))"
    state = state[:expr_start] + wrapped_body + state[body_end:]

# Recoloca State alterado no arquivo completo.
text = text[:state_start] + state + text[state_end + 1:]

# Tela Meus abastecimentos: nenhum filtro inicial. Todos os abastecimentos do
# usuário autenticado vêm do RPC rca_my_fuelings, que também aplica propriedade
# no servidor; filtros são opcionais e só entram quando o operador quiser pesquisar.
my_screen = r'''

class MyFuelingsOnlineScreen extends StatefulWidget {
  const MyFuelingsOnlineScreen({super.key});
  @override
  State<MyFuelingsOnlineScreen> createState() => _MyFuelingsOnlineScreenState();
}

class _MyFuelingsOnlineScreenState extends State<MyFuelingsOnlineScreen> {
  final asset = TextEditingController();
  final work = TextEditingController();
  final fuel = TextEditingController();
  final source = TextEditingController();
  DateTime? startDate;
  DateTime? endDate;
  List<Map<String, dynamic>>? items;
  bool busy = false;
  bool filtersExpanded = false;

  @override
  void initState() {
    super.initState();
    load();
  }

  @override
  void dispose() {
    asset.dispose();
    work.dispose();
    fuel.dispose();
    source.dispose();
    super.dispose();
  }

  String? valueOf(TextEditingController c) {
    final value = c.text.trim();
    return value.isEmpty ? null : value;
  }

  String? startIso() {
    final d = startDate;
    if (d == null) return null;
    return DateTime(d.year, d.month, d.day).toUtc().toIso8601String();
  }

  String? endIso() {
    final d = endDate;
    if (d == null) return null;
    return DateTime(d.year, d.month, d.day).add(const Duration(days: 1)).toUtc().toIso8601String();
  }

  String shortDate(DateTime? d) {
    if (d == null) return 'Selecionar';
    return '${d.day.toString().padLeft(2, '0')}/${d.month.toString().padLeft(2, '0')}/${d.year}';
  }

  Future<void> pickStart() async {
    final now = DateTime.now();
    final picked = await showDatePicker(
      context: context,
      initialDate: startDate ?? now,
      firstDate: DateTime(2020),
      lastDate: DateTime(now.year + 2),
    );
    if (picked != null && mounted) setState(() => startDate = picked);
  }

  Future<void> pickEnd() async {
    final now = DateTime.now();
    final picked = await showDatePicker(
      context: context,
      initialDate: endDate ?? startDate ?? now,
      firstDate: DateTime(2020),
      lastDate: DateTime(now.year + 2),
    );
    if (picked != null && mounted) setState(() => endDate = picked);
  }

  Future<void> load() async {
    if (busy) return;
    setState(() => busy = true);
    try {
      final data = await Supabase.instance.client.rpc('rca_my_fuelings', params: {
        'p_start': startIso(),
        'p_end': endIso(),
        'p_asset_query': valueOf(asset),
        'p_work_query': valueOf(work),
        'p_fuel_type': valueOf(fuel),
        'p_source_code': valueOf(source),
      });
      if (mounted) setState(() => items = _rows(data));
    } catch (e) {
      if (mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Falha ao carregar meus abastecimentos: ${_friendlyError(e)}')));
    } finally {
      if (mounted) setState(() => busy = false);
    }
  }

  Future<void> clearFilters() async {
    asset.clear();
    work.clear();
    fuel.clear();
    source.clear();
    setState(() {
      startDate = null;
      endDate = null;
    });
    await load();
  }

  @override
  Widget build(BuildContext context) {
    final list = items ?? const <Map<String, dynamic>>[];
    return Scaffold(
      appBar: AppBar(title: const Text('Meus abastecimentos')),
      body: RefreshIndicator(
        onRefresh: load,
        child: ListView(
          padding: const EdgeInsets.all(14),
          children: [
            Card(
              child: ExpansionTile(
                initiallyExpanded: filtersExpanded,
                onExpansionChanged: (v) => filtersExpanded = v,
                leading: const Icon(Icons.filter_alt_outlined),
                title: const Text('Filtros', style: TextStyle(fontWeight: FontWeight.w800)),
                subtitle: const Text('Data, ativo, obra, combustível e origem'),
                childrenPadding: const EdgeInsets.fromLTRB(14, 0, 14, 14),
                children: [
                  Row(children: [
                    Expanded(child: OutlinedButton.icon(onPressed: busy ? null : pickStart, icon: const Icon(Icons.event_outlined), label: Text('De ${shortDate(startDate)}'))),
                    const SizedBox(width: 8),
                    Expanded(child: OutlinedButton.icon(onPressed: busy ? null : pickEnd, icon: const Icon(Icons.event_outlined), label: Text('Até ${shortDate(endDate)}'))),
                  ]),
                  const SizedBox(height: 10),
                  TextField(controller: asset, textInputAction: TextInputAction.next, decoration: const InputDecoration(labelText: 'Ativo', hintText: 'Nº do ativo, placa, marca ou modelo')),
                  const SizedBox(height: 10),
                  TextField(controller: work, textInputAction: TextInputAction.next, decoration: const InputDecoration(labelText: 'Obra')),
                  const SizedBox(height: 10),
                  TextField(controller: fuel, textInputAction: TextInputAction.next, decoration: const InputDecoration(labelText: 'Tipo de combustível', hintText: 'Ex.: Diesel S10')),
                  const SizedBox(height: 10),
                  TextField(controller: source, onSubmitted: (_) => load(), decoration: const InputDecoration(labelText: 'Origem do combustível', hintText: 'Ex.: CB01, CT01 ou TE0001')),
                  const SizedBox(height: 12),
                  Row(children: [
                    Expanded(child: FilledButton.icon(onPressed: busy ? null : load, icon: const Icon(Icons.search_rounded), label: const Text('Filtrar'))),
                    const SizedBox(width: 8),
                    OutlinedButton(onPressed: busy ? null : clearFilters, child: const Text('Limpar')),
                  ]),
                ],
              ),
            ),
            const SizedBox(height: 10),
            if (busy && items == null) const Padding(padding: EdgeInsets.all(36), child: Center(child: CircularProgressIndicator())),
            if (!busy && items != null && list.isEmpty)
              const Padding(padding: EdgeInsets.all(32), child: Center(child: Text('Nenhum abastecimento encontrado.'))),
            if (items != null && list.isNotEmpty)
              Padding(
                padding: const EdgeInsets.fromLTRB(4, 2, 4, 8),
                child: Text('${list.length} abastecimento(s)', style: const TextStyle(fontWeight: FontWeight.w700, color: Colors.black54)),
              ),
            ...list.map((x) {
              final assetText = x['asset_number'] ?? x['third_party_plate'] ?? '';
              final sourceText = x['source_tank'] ?? x['source_tank_name'] ?? '-';
              final when = x['occurred_at'] ?? x['created_at'];
              final fuelText = '${x['fuel_type'] ?? 'Combustível'}';
              return Card(
                child: ListTile(
                  contentPadding: const EdgeInsets.all(14),
                  leading: const CircleAvatar(child: Icon(Icons.local_gas_station_rounded)),
                  title: Text('${_movementLabelForItem(x)}${_hasValue(assetText) ? ' • $assetText' : ''}', style: const TextStyle(fontWeight: FontWeight.w900)),
                  subtitle: Text('${_fmtDate(when)}\n${x['work'] ?? 'Sem obra'} • ${_fmtLiters(x['liters'])}\n$fuelText • Origem: $sourceText'),
                  isThreeLine: true,
                  trailing: const Icon(Icons.chevron_right_rounded),
                  onTap: () => Navigator.push(context, MaterialPageRoute(builder: (_) => MovementDetailScreen(item: x))),
                ),
              );
            }),
            if (busy && items != null) const Padding(padding: EdgeInsets.all(16), child: Center(child: CircularProgressIndicator())),
            const SizedBox(height: 28),
          ],
        ),
      ),
    );
  }
}
'''

if 'class MyFuelingsOnlineScreen extends StatefulWidget' not in text:
    text += my_screen

required = [
    "rpc('rca_user_role')",
    "title: 'Meus abastecimentos'",
    "class MyFuelingsOnlineScreen extends StatefulWidget",
    "rpc('rca_my_fuelings'",
    "labelText: 'Origem do combustível'",
    "labelText: 'Tipo de combustível'",
    "labelText: 'Obra'",
    "labelText: 'Ativo'",
]
for marker in required:
    if marker not in text:
        raise SystemExit(f'v22: marcador final ausente: {marker}')

path.write_text(text)
print('v22: Operacional com apenas Novo abastecimento + Meus abastecimentos e filtros completos.')
