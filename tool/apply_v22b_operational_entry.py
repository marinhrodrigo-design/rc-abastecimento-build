from pathlib import Path

path = Path('lib/main_online.dart')
text = path.read_text()

old_route = """    if (profile == null) return LoginScreen(onLogin: _login, error: error);
    final lastTankId = offlineStore.lastTankId;
    if (lastTankId != null) return FieldHomeScreen(profile: profile!, tankId: lastTankId, onLogout: _logout);
    if (profile!['is_admin'] == true) return AdminHomeScreen(profile: profile!, onLogout: _logout);
    return UnitSelectionScreen(profile: profile!, onLogout: _logout);"""

new_route = """    if (profile == null) return LoginScreen(onLogin: _login, error: error);
    final role = '${profile!['role'] ?? ''}'.trim().toLowerCase();
    final operational = role == 'fuel_driver' || role == 'operator' || role == 'operational';
    if (operational) return OperationalHomeScreen(profile: profile!, onLogout: _logout);
    final lastTankId = offlineStore.lastTankId;
    if (lastTankId != null) return FieldHomeScreen(profile: profile!, tankId: lastTankId, onLogout: _logout);
    if (profile!['is_admin'] == true) return AdminHomeScreen(profile: profile!, onLogout: _logout);
    return UnitSelectionScreen(profile: profile!, onLogout: _logout);"""

if old_route not in text:
    raise SystemExit('v22b: rota principal esperada não encontrada')
text = text.replace(old_route, new_route, 1)

screen = r'''

class OperationalHomeScreen extends StatefulWidget {
  final Map<String, dynamic> profile;
  final Future<void> Function() onLogout;
  const OperationalHomeScreen({super.key, required this.profile, required this.onLogout});

  @override
  State<OperationalHomeScreen> createState() => _OperationalHomeScreenState();
}

class _OperationalHomeScreenState extends State<OperationalHomeScreen> {
  Map<String, dynamic>? data;
  String? error;
  bool refreshing = false;

  @override
  void initState() {
    super.initState();
    refresh();
    // A origem não deve prender a tela inicial do Operacional.
    offlineStore.setLastTankId(null);
  }

  Future<void> refresh() async {
    if (refreshing) return;
    refreshing = true;
    try {
      final d = await api.referenceData();
      if (mounted) setState(() { data = d; error = null; });
    } catch (e) {
      if (mounted) setState(() => error = _friendlyError(e));
    } finally {
      refreshing = false;
    }
  }

  Future<void> openMyFuelings() async {
    await Navigator.push(context, MaterialPageRoute(builder: (_) => const MyFuelingsOnlineScreen()));
  }

  Future<void> newFueling() async {
    var reference = data;
    if (reference == null) {
      try {
        reference = await api.referenceData();
        if (mounted) setState(() { data = reference; error = null; });
      } catch (e) {
        if (mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(_friendlyError(e))));
        return;
      }
    }
    if (!mounted || reference == null) return;

    final available = _sortedFuelUnits(reference['tanks'])
        .where((t) => t['authorized'] != false)
        .toList();

    if (available.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Nenhuma origem de combustível foi liberada para este usuário.')),
      );
      return;
    }

    final source = await showModalBottomSheet<Map<String, dynamic>>(
      context: context,
      isScrollControlled: true,
      builder: (ctx) => SafeArea(
        child: ConstrainedBox(
          constraints: BoxConstraints(maxHeight: MediaQuery.of(ctx).size.height * .72),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              const Padding(
                padding: EdgeInsets.fromLTRB(20, 18, 20, 8),
                child: Text('Origem do combustível', style: TextStyle(fontSize: 19, fontWeight: FontWeight.w900)),
              ),
              const Padding(
                padding: EdgeInsets.fromLTRB(20, 0, 20, 10),
                child: Text('Selecione de onde o combustível será retirado.'),
              ),
              Flexible(
                child: ListView.separated(
                  shrinkWrap: true,
                  padding: const EdgeInsets.fromLTRB(12, 4, 12, 18),
                  itemCount: available.length,
                  separatorBuilder: (_, __) => const SizedBox(height: 4),
                  itemBuilder: (_, index) {
                    final t = available[index];
                    final stationary = '${t['tank_type']}' == 'stationary';
                    return Card(
                      child: ListTile(
                        contentPadding: const EdgeInsets.symmetric(horizontal: 14, vertical: 7),
                        leading: Icon(stationary ? Icons.oil_barrel_outlined : Icons.local_shipping_outlined, color: _blue),
                        title: Text('${t['code']} • ${t['name']}', style: const TextStyle(fontWeight: FontWeight.w900)),
                        subtitle: Text('Saldo disponível: ${_fmtLiters(t['current_balance_liters'])}'),
                        trailing: const Icon(Icons.chevron_right_rounded),
                        onTap: () => Navigator.pop(ctx, t),
                      ),
                    );
                  },
                ),
              ),
            ],
          ),
        ),
      ),
    );

    if (!mounted || source == null) return;
    await Navigator.push(
      context,
      MaterialPageRoute(builder: (_) => FuelingOnlineScreen(sourceTank: source, referenceData: reference!)),
    );
    await refresh();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('R&C Abastecimento', style: TextStyle(fontWeight: FontWeight.w900)),
        actions: [
          IconButton(
            onPressed: () async { await _logoutToLogin(context, widget.onLogout); },
            tooltip: 'Sair',
            icon: const Icon(Icons.logout_rounded),
          ),
        ],
      ),
      body: RefreshIndicator(
        onRefresh: refresh,
        child: ListView(
          physics: const AlwaysScrollableScrollPhysics(),
          padding: const EdgeInsets.all(20),
          children: [
            GreetingLine(name: '${widget.profile['display_name']}'),
            const SizedBox(height: 6),
            const Text('Área Operacional', style: TextStyle(color: Colors.black54, fontWeight: FontWeight.w700)),
            if (error != null) ...[
              const SizedBox(height: 10),
              Text(error!, style: const TextStyle(color: Colors.redAccent)),
            ],
            const SizedBox(height: 20),
            HomeActionCard(
              icon: Icons.local_gas_station_rounded,
              title: 'Novo abastecimento',
              subtitle: 'Registrar um novo abastecimento',
              onTap: newFueling,
            ),
            const SizedBox(height: 12),
            HomeActionCard(
              icon: Icons.history_rounded,
              title: 'Meus abastecimentos',
              subtitle: 'Todos os abastecimentos registrados por mim',
              onTap: openMyFuelings,
            ),
          ],
        ),
      ),
    );
  }
}
'''

if 'class OperationalHomeScreen extends StatefulWidget' not in text:
    insert_at = text.find('class UnitSelectionScreen extends StatefulWidget')
    if insert_at < 0:
        raise SystemExit('v22b: ponto de inserção da tela Operacional não encontrado')
    text = text[:insert_at] + screen + '\n' + text[insert_at:]

checks = [
    "if (operational) return OperationalHomeScreen",
    "title: 'Novo abastecimento'",
    "title: 'Meus abastecimentos'",
    "Text('Origem do combustível'",
    "FuelingOnlineScreen(sourceTank: source, referenceData: reference!)",
]
for marker in checks:
    if marker not in text:
        raise SystemExit(f'v22b: marcador ausente: {marker}')

path.write_text(text)
print('v22b: login Operacional direcionado para home exclusiva de dois cards.')
