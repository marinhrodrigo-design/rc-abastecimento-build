from pathlib import Path
p=Path('lib/main_online.dart')
s=p.read_text()

anchor="""  Future<void> refresh() async {
    if (running) return; running = true;
    try { final d = await api.referenceData(); if (mounted) setState(() => ref = d); } catch (_) {} finally { running = false; }
  }

  @override
  Widget build(BuildContext context) {
"""
insert="""  Future<void> refresh() async {
    if (running) return; running = true;
    try { final d = await api.referenceData(); if (mounted) setState(() => ref = d); } catch (_) {} finally { running = false; }
  }

  List<Map<String,dynamic>> _shortcutSources(Set<String> types) {
    return _sortedFuelUnits(ref?['tanks']).where((t) =>
      t['authorized'] != false && types.contains('${t['tank_type']}')
    ).toList();
  }

  Future<Map<String,dynamic>?> _chooseShortcutSource({
    required String title,
    required String subtitle,
    required Set<String> types,
  }) async {
    final sources = _shortcutSources(types);
    if (sources.isEmpty) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Nenhuma unidade disponível para $title.')));
      }
      return null;
    }
    if (sources.length == 1) return sources.first;
    if (!mounted) return null;
    return showModalBottomSheet<Map<String,dynamic>>(
      context: context,
      showDragHandle: true,
      builder: (ctx) => SafeArea(
        child: ListView(
          shrinkWrap: true,
          padding: const EdgeInsets.fromLTRB(16, 0, 16, 18),
          children: [
            Text(title, style: Theme.of(ctx).textTheme.titleLarge?.copyWith(fontWeight: FontWeight.w900)),
            const SizedBox(height: 4),
            Text(subtitle, style: const TextStyle(color: Colors.black54)),
            const SizedBox(height: 10),
            ...sources.map((t) => Card(
              margin: const EdgeInsets.only(bottom: 8),
              child: ListTile(
                leading: Icon(t['tank_type']=='stationary' ? Icons.oil_barrel_outlined : t['tank_type']=='truck' ? Icons.local_shipping_rounded : Icons.local_shipping_outlined, color: _blue),
                title: Text('${t['code']} • ${t['name']}', style: const TextStyle(fontWeight: FontWeight.w800)),
                subtitle: Text('Saldo disponível: ${_fmtLiters(t['current_balance_liters'])}'),
                trailing: const Icon(Icons.chevron_right_rounded),
                onTap: () => Navigator.pop(ctx, t),
              ),
            )),
          ],
        ),
      ),
    );
  }

  Future<void> _openFuelingShortcut() async {
    if (ref == null) return;
    final source = await _chooseShortcutSource(
      title: 'Novo abastecimento',
      subtitle: 'Selecione somente a unidade de origem do combustível.',
      types: const {'stationary','comboio','truck'},
    );
    if (!mounted || source == null || ref == null) return;
    await Navigator.push(context, MaterialPageRoute(builder: (_) => FuelingV23Screen(source: source, ref: ref!, profile: widget.profile)));
    if (mounted) await refresh();
  }

  Future<void> _openTransferShortcut() async {
    if (ref == null) return;
    final source = await _chooseShortcutSource(
      title: 'Transferir',
      subtitle: 'Selecione a unidade doadora. Em seguida você informa o destino da transferência.',
      types: const {'comboio','truck'},
    );
    if (!mounted || source == null || ref == null) return;
    await Navigator.push(context, MaterialPageRoute(builder: (_) => TransferV23Screen(source: source, ref: ref!, profile: widget.profile)));
    if (mounted) await refresh();
  }

  Future<void> _openReceiptShortcut() async {
    if (ref == null) return;
    final source = await _chooseShortcutSource(
      title: 'Recebimento de combustível / NF',
      subtitle: 'Selecione o caminhão-tanque que está recebendo a carga da refinaria/fornecedor.',
      types: const {'truck'},
    );
    if (!mounted || source == null) return;
    await Navigator.push(context, MaterialPageRoute(builder: (_) => RefineryLoadV23Screen(truck: source)));
    if (mounted) await refresh();
  }

  @override
  Widget build(BuildContext context) {
"""
if anchor not in s:
    raise SystemExit('anchor AdminHome refresh not found')
s=s.replace(anchor,insert,1)

old="""      quick(Icons.local_gas_station_rounded,'Novo abastecimento','Selecionar unidade',()=>open(UnitSelectionScreen(profile:widget.profile,onLogout:widget.onLogout))),
      quick(Icons.swap_horiz_rounded,'Transferir','Entre unidades',()=>open(UnitSelectionScreen(profile:widget.profile,onLogout:widget.onLogout))),
      quick(Icons.receipt_long_rounded,'Recebimento (NF)','Entrada de combustível',()=>open(UnitSelectionScreen(profile:widget.profile,onLogout:widget.onLogout))),
"""
new="""      quick(Icons.local_gas_station_rounded,'Novo abastecimento','Registrar abastecimento',()=>_openFuelingShortcut()),
      quick(Icons.swap_horiz_rounded,'Transferir','Registrar transferência',()=>_openTransferShortcut()),
      quick(Icons.receipt_long_rounded,'Recebimento (NF)','Registrar entrada de combustível',()=>_openReceiptShortcut()),
"""
if old not in s:
    raise SystemExit('dashboard shortcut anchors not found')
s=s.replace(old,new,1)

p.write_text(s)
print('direct dashboard shortcuts applied', len(s))
