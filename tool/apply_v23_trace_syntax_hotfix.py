from pathlib import Path
p=Path('lib/main_online.dart')
s=p.read_text()
start=s.find('class MovementTraceV23Screen')
end=s.find('class WorkFinalPdf', start)
if start < 0 or end < 0:
    raise SystemExit('MovementTraceV23Screen markers missing')
replacement=r'''class MovementTraceV23Screen extends StatefulWidget {
  final int movementId;
  const MovementTraceV23Screen({super.key, required this.movementId});

  @override
  State<MovementTraceV23Screen> createState() => _MovementTraceV23ScreenState();
}

class _MovementTraceV23ScreenState extends State<MovementTraceV23Screen> {
  Map<String, dynamic>? data;
  String? error;

  @override
  void initState() {
    super.initState();
    load();
  }

  Future<void> load() async {
    setState(() => error = null);
    try {
      final x = await api.movementTraceV23(widget.movementId);
      if (mounted) setState(() => data = x);
    } catch (e) {
      if (mounted) setState(() => error = _friendlyError(e));
    }
  }

  Widget errorBody() {
    return Padding(
      padding: const EdgeInsets.all(24),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          Text(error ?? 'Não foi possível carregar a rastreabilidade.', textAlign: TextAlign.center),
          const SizedBox(height: 10),
          FilledButton.icon(
            onPressed: load,
            icon: const Icon(Icons.refresh),
            label: const Text('Tentar novamente'),
          ),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final d = data;
    Widget body;
    if (d == null) {
      body = Center(
        child: error == null ? const CircularProgressIndicator() : errorBody(),
      );
    } else {
      final allocations = _rows(d['allocations']);
      final lineage = _rows(d['lineage']);
      body = ListView(
        padding: const EdgeInsets.all(16),
        children: [
          const Card(
            child: ListTile(
              leading: Icon(Icons.route_rounded, color: _blue),
              title: Text('Origem do combustível deste registro'),
              subtitle: Text('Quando há mistura de NFs, o app mostra exatamente quantos litros vieram de cada lote.'),
            ),
          ),
          const Text(
            'NF(s) utilizadas',
            style: TextStyle(fontSize: 17, fontWeight: FontWeight.w900),
          ),
          if (allocations.isEmpty)
            const Card(child: ListTile(title: Text('Nenhuma alocação de NF encontrada para este registro.'))),
          ...allocations.map((a) {
            final unitCost = a['unit_cost'];
            final extra = unitCost != null ? '\nCusto/L: ${_fmtMoney(unitCost)}' : '';
            return Card(
              child: ListTile(
                title: Text(
                  'NF ${a['invoice_number'] ?? '-'} • ${_fmtLiters(a['liters'])}',
                  style: const TextStyle(fontWeight: FontWeight.w900),
                ),
                subtitle: Text('${a['supplier_name'] ?? '-'} • ${a['fuel_type'] ?? '-'}$extra'),
              ),
            );
          }),
          const SizedBox(height: 10),
          const Text(
            'Caminho anterior dos lotes',
            style: TextStyle(fontSize: 17, fontWeight: FontWeight.w900),
          ),
          if (lineage.isEmpty)
            const Card(child: ListTile(title: Text('Nenhum movimento anterior encontrado para estes lotes.'))),
          ...lineage.map((m) {
            final source = '${m['source'] ?? 'Entrada'}';
            final destination = m['destination'];
            final route = destination != null ? '$source → $destination' : source;
            return Card(
              child: ListTile(
                title: Text(
                  'NF ${m['invoice_number'] ?? '-'} • ${_movementLabel('${m['type'] ?? ''}')}',
                  style: const TextStyle(fontWeight: FontWeight.w900),
                ),
                subtitle: Text('${_fmtDate(m['created_at'])}\n$route • ${_fmtLiters(m['liters'])}'),
              ),
            );
          }),
        ],
      );
    }

    return Scaffold(
      appBar: AppBar(title: const Text('Rastreabilidade do combustível')),
      body: body,
    );
  }
}

'''
s=s[:start]+replacement+s[end:]
p.write_text(s)
print('trace syntax hotfix applied', len(s))
