import 'package:flutter/material.dart';
import 'package:url_launcher/url_launcher.dart';

import 'backend_service.dart';
import 'models.dart';
import 'oem_catalog.dart';
import 'phase4_theme.dart';

class DashboardPage extends StatelessWidget {
  const DashboardPage({
    super.key,
    required this.dashboard,
    required this.onRefresh,
    required this.onOpenInsight,
  });

  final Map<String, dynamic> dashboard;
  final Future<void> Function() onRefresh;
  final Future<void> Function(String id) onOpenInsight;

  @override
  Widget build(BuildContext context) {
    final open = _map(dashboard['open_insights']);
    final stock = _map(dashboard['stock']);
    final maintenance = _map(dashboard['maintenance']);
    final quality = _map(dashboard['data_quality']);
    final top = _list(dashboard['top_insights']);
    final avgQuality = _num(quality['avg_score']);

    return RefreshIndicator(
      onRefresh: onRefresh,
      child: ListView(
        physics: const AlwaysScrollableScrollPhysics(),
        padding: const EdgeInsets.fromLTRB(16, 14, 16, 28),
        children: [
          const Text(
            'Visão da operação',
            style: TextStyle(fontSize: 26, fontWeight: FontWeight.w800, color: RCTheme.navy),
          ),
          const SizedBox(height: 4),
          const Text(
            'O Intelligence cruza abastecimento, manutenção e contexto operacional sem alterar os registros de origem.',
          ),
          const SizedBox(height: 18),
          LayoutBuilder(
            builder: (context, c) {
              final columns = c.maxWidth >= 700 ? 4 : 2;
              return GridView.count(
                shrinkWrap: true,
                physics: const NeverScrollableScrollPhysics(),
                crossAxisCount: columns,
                crossAxisSpacing: 10,
                mainAxisSpacing: 10,
                childAspectRatio: c.maxWidth >= 700 ? 1.8 : 1.35,
                children: [
                  _SummaryTile(
                    title: 'Críticos',
                    value: '${_int(open['critical'])}',
                    icon: Icons.error_rounded,
                    accent: RCTheme.severityColor('critical'),
                  ),
                  _SummaryTile(
                    title: 'Altos',
                    value: '${_int(open['high'])}',
                    icon: Icons.warning_amber_rounded,
                    accent: RCTheme.severityColor('high'),
                  ),
                  _SummaryTile(
                    title: 'Atenção',
                    value: '${_int(open['attention'])}',
                    icon: Icons.info_rounded,
                    accent: RCTheme.severityColor('attention'),
                  ),
                  _SummaryTile(
                    title: 'Qualidade dos dados',
                    value: '${avgQuality.toStringAsFixed(0)}/100',
                    icon: Icons.fact_check_outlined,
                    accent: avgQuality >= 80
                        ? const Color(0xFF268A5B)
                        : avgQuality >= 60
                            ? const Color(0xFFB7791F)
                            : const Color(0xFFB42318),
                  ),
                ],
              );
            },
          ),
          const SizedBox(height: 18),
          const _SectionTitle('Combustível'),
          _InfoCard(
            icon: Icons.local_gas_station_rounded,
            title: '${_formatNumber(_num(stock['current_liters']))} L em unidades operacionais',
            lines: [
              '${_int(stock['active_tanks'])} unidade(s) com operação registrada',
              '${_int(stock['pending_setup'])} unidade(s) cadastrada(s) ainda sem movimentação',
              '${_int(stock['critical'])} em nível crítico • ${_int(stock['low_or_critical'])} em nível baixo/crítico',
            ],
          ),
          const SizedBox(height: 12),
          const _SectionTitle('Manutenção'),
          _InfoCard(
            icon: Icons.build_circle_outlined,
            title: '${_int(maintenance['open_orders'])} O.S. aberta(s)',
            lines: [
              '${_int(maintenance['overdue_orders'])} O.S. vencida(s)',
              '${_int(maintenance['maintenances_7d'])} manutenção(ões) registrada(s) nos últimos 7 dias',
            ],
          ),
          const SizedBox(height: 18),
          Row(
            children: [
              const Expanded(child: _SectionTitle('Insights prioritários')),
              if (top.isNotEmpty) Text('${top.length} exibido(s)', style: Theme.of(context).textTheme.bodySmall),
            ],
          ),
          if (top.isEmpty)
            const _EmptyCard(
              icon: Icons.check_circle_outline_rounded,
              title: 'Nenhum insight ativo',
              message: 'As regras continuam processando os dados automaticamente.',
            )
          else
            ...top.map(
              (item) => Padding(
                padding: const EdgeInsets.only(bottom: 10),
                child: _InsightCard(
                  item: item,
                  onTap: () => onOpenInsight('${item['id']}'),
                ),
              ),
            ),
        ],
      ),
    );
  }
}

class AlertsPage extends StatefulWidget {
  const AlertsPage({
    super.key,
    required this.api,
    required this.onChanged,
  });

  final IntelligenceApi api;
  final Future<void> Function() onChanged;

  @override
  State<AlertsPage> createState() => _AlertsPageState();
}

class _AlertsPageState extends State<AlertsPage> {
  final search = TextEditingController();
  String? status;
  String? severity;
  late Future<List<Map<String, dynamic>>> future;

  @override
  void initState() {
    super.initState();
    future = _load();
  }

  @override
  void dispose() {
    search.dispose();
    super.dispose();
  }

  Future<List<Map<String, dynamic>>> _load() => widget.api.feed(
        status: status,
        severity: severity,
        query: search.text.trim().isEmpty ? null : search.text.trim(),
      );

  Future<void> _reload() async {
    setState(() => future = _load());
    await future;
  }

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        Padding(
          padding: const EdgeInsets.fromLTRB(16, 14, 16, 8),
          child: Column(
            children: [
              TextField(
                controller: search,
                textInputAction: TextInputAction.search,
                onSubmitted: (_) => _reload(),
                decoration: InputDecoration(
                  labelText: 'Buscar ativo, placa, tanque ou alerta',
                  prefixIcon: const Icon(Icons.search),
                  suffixIcon: IconButton(icon: const Icon(Icons.arrow_forward), onPressed: _reload),
                ),
              ),
              const SizedBox(height: 10),
              Row(
                children: [
                  Expanded(
                    child: DropdownButtonFormField<String?>(
                      value: status,
                      decoration: const InputDecoration(labelText: 'Status'),
                      items: const [
                        DropdownMenuItem(value: null, child: Text('Todos')),
                        DropdownMenuItem(value: 'open', child: Text('Aberto')),
                        DropdownMenuItem(value: 'in_review', child: Text('Em análise')),
                        DropdownMenuItem(value: 'confirmed', child: Text('Confirmado')),
                        DropdownMenuItem(value: 'dismissed', child: Text('Não procede')),
                        DropdownMenuItem(value: 'resolved', child: Text('Resolvido')),
                      ],
                      onChanged: (v) {
                        status = v;
                        _reload();
                      },
                    ),
                  ),
                  const SizedBox(width: 10),
                  Expanded(
                    child: DropdownButtonFormField<String?>(
                      value: severity,
                      decoration: const InputDecoration(labelText: 'Severidade'),
                      items: const [
                        DropdownMenuItem(value: null, child: Text('Todas')),
                        DropdownMenuItem(value: 'critical', child: Text('Crítico')),
                        DropdownMenuItem(value: 'high', child: Text('Alto')),
                        DropdownMenuItem(value: 'attention', child: Text('Atenção')),
                        DropdownMenuItem(value: 'info', child: Text('Informativo')),
                      ],
                      onChanged: (v) {
                        severity = v;
                        _reload();
                      },
                    ),
                  ),
                ],
              ),
            ],
          ),
        ),
        Expanded(
          child: FutureBuilder<List<Map<String, dynamic>>>(
            future: future,
            builder: (context, snapshot) {
              if (snapshot.connectionState != ConnectionState.done) {
                return const Center(child: CircularProgressIndicator());
              }
              if (snapshot.hasError) {
                return _ErrorView(error: snapshot.error, retry: _reload);
              }
              final values = snapshot.data ?? const [];
              if (values.isEmpty) {
                return RefreshIndicator(
                  onRefresh: _reload,
                  child: ListView(
                    physics: const AlwaysScrollableScrollPhysics(),
                    children: const [
                      SizedBox(height: 140),
                      _EmptyCard(
                        icon: Icons.notifications_none_rounded,
                        title: 'Nenhum alerta neste filtro',
                        message: 'Altere os filtros ou atualize a lista.',
                      ),
                    ],
                  ),
                );
              }
              return RefreshIndicator(
                onRefresh: _reload,
                child: ListView.builder(
                  padding: const EdgeInsets.fromLTRB(12, 4, 12, 28),
                  itemCount: values.length,
                  itemBuilder: (context, i) {
                    final item = values[i];
                    return Padding(
                      padding: const EdgeInsets.only(bottom: 10),
                      child: _InsightCard(
                        item: item,
                        onTap: () async {
                          await Navigator.of(context).push(
                            MaterialPageRoute(
                              builder: (_) => InsightDetailPage(api: widget.api, insightId: '${item['id']}'),
                            ),
                          );
                          await _reload();
                          await widget.onChanged();
                        },
                      ),
                    );
                  },
                ),
              );
            },
          ),
        ),
      ],
    );
  }
}

class InsightDetailPage extends StatefulWidget {
  const InsightDetailPage({
    super.key,
    required this.api,
    required this.insightId,
  });

  final IntelligenceApi api;
  final String insightId;

  @override
  State<InsightDetailPage> createState() => _InsightDetailPageState();
}

class _InsightDetailPageState extends State<InsightDetailPage> {
  late Future<Map<String, dynamic>> future;
  bool busy = false;

  @override
  void initState() {
    super.initState();
    future = widget.api.detail(widget.insightId);
  }

  Future<void> _reload() async {
    setState(() => future = widget.api.detail(widget.insightId));
    await future;
  }

  Future<String?> _noteDialog(String title, {bool required = false}) async {
    final controller = TextEditingController();
    final value = await showDialog<String?>(
      context: context,
      builder: (context) => AlertDialog(
        title: Text(title),
        content: TextField(
          controller: controller,
          minLines: 3,
          maxLines: 6,
          decoration: InputDecoration(
            labelText: required ? 'Observação obrigatória' : 'Observação (opcional)',
          ),
        ),
        actions: [
          TextButton(onPressed: () => Navigator.pop(context), child: const Text('Cancelar')),
          FilledButton(
            onPressed: () {
              final text = controller.text.trim();
              if (required && text.isEmpty) return;
              Navigator.pop(context, text);
            },
            child: const Text('Continuar'),
          ),
        ],
      ),
    );
    controller.dispose();
    return value;
  }

  Future<void> _run(Future<void> Function() action) async {
    if (busy) return;
    setState(() => busy = true);
    try {
      await action();
      await _reload();
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Insight atualizado.')));
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(_friendlyError(e))));
      }
    } finally {
      if (mounted) setState(() => busy = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Detalhe do insight')),
      body: FutureBuilder<Map<String, dynamic>>(
        future: future,
        builder: (context, snapshot) {
          if (snapshot.connectionState != ConnectionState.done) {
            return const Center(child: CircularProgressIndicator());
          }
          if (snapshot.hasError) {
            return _ErrorView(error: snapshot.error, retry: _reload);
          }
          final data = snapshot.data ?? const {};
          final insight = _map(data['insight']);
          final ctx = _map(data['context']);
          final permissions = _map(data['permissions']);
          final evidence = _list(data['evidence']);
          final actions = _list(data['actions']);
          final metrics = _map(insight['metrics']);
          final canManage = permissions['can_manage'] == true;
          final status = '${insight['status'] ?? ''}';
          final severity = '${insight['severity'] ?? 'info'}';
          final confidence = _num(insight['confidence']);

          return ListView(
            padding: const EdgeInsets.fromLTRB(16, 12, 16, 32),
            children: [
              Container(
                padding: const EdgeInsets.all(16),
                decoration: BoxDecoration(
                  color: RCTheme.severityColor(severity).withValues(alpha: .08),
                  borderRadius: BorderRadius.circular(18),
                  border: Border.all(color: RCTheme.severityColor(severity).withValues(alpha: .35)),
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: [
                        Icon(RCTheme.severityIcon(severity), color: RCTheme.severityColor(severity)),
                        const SizedBox(width: 8),
                        Text(
                          RCTheme.severityLabel(severity),
                          style: TextStyle(fontWeight: FontWeight.w800, color: RCTheme.severityColor(severity)),
                        ),
                        const Spacer(),
                        _StatusChip(status),
                      ],
                    ),
                    const SizedBox(height: 12),
                    Text('${insight['title'] ?? ''}', style: const TextStyle(fontSize: 23, fontWeight: FontWeight.w800)),
                    const SizedBox(height: 6),
                    Text('${insight['summary'] ?? ''}'),
                    const SizedBox(height: 14),
                    Row(
                      children: [
                        Expanded(child: _MiniMetric(label: 'Confiança', value: '${confidence.toStringAsFixed(0)}/100')),
                        const SizedBox(width: 8),
                        Expanded(child: _MiniMetric(label: 'Regra', value: '${insight['rule_code'] ?? '-'}')),
                      ],
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 16),
              const _SectionTitle('Contexto'),
              _InfoCard(
                icon: Icons.precision_manufacturing_outlined,
                title: _contextTitle(ctx),
                lines: [
                  if (_nonEmpty(ctx['plate'])) 'Placa: ${ctx['plate']}',
                  if (_nonEmpty(ctx['machine_type'])) 'Tipo: ${ctx['machine_type']}',
                  if (_nonEmpty(ctx['work_name'])) 'Obra: ${ctx['work_name']}',
                  if (_nonEmpty(ctx['tank_name'])) 'Unidade: ${ctx['tank_name']}',
                  if (ctx['current_meter'] != null) 'Horímetro/Km atual: ${ctx['current_meter']}',
                ],
              ),
              if (metrics.isNotEmpty) ...[
                const SizedBox(height: 16),
                const _SectionTitle('Cálculo e métricas'),
                Card(
                  child: Padding(
                    padding: const EdgeInsets.all(14),
                    child: Column(
                      children: metrics.entries
                          .map(
                            (e) => Padding(
                              padding: const EdgeInsets.symmetric(vertical: 6),
                              child: Row(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  Expanded(child: Text(_humanize(e.key), style: const TextStyle(fontWeight: FontWeight.w600))),
                                  const SizedBox(width: 12),
                                  Flexible(child: Text('${e.value}', textAlign: TextAlign.right)),
                                ],
                              ),
                            ),
                          )
                          .toList(),
                    ),
                  ),
                ),
              ],
              const SizedBox(height: 16),
              Row(
                children: [
                  const Expanded(child: _SectionTitle('Evidências')),
                  Text('${evidence.length}', style: Theme.of(context).textTheme.labelLarge),
                ],
              ),
              if (evidence.isEmpty)
                const _EmptyCard(
                  icon: Icons.manage_search_rounded,
                  title: 'Sem evidência estruturada',
                  message: 'O insight pode ser histórico ou anterior à cadeia de evidências atual.',
                )
              else
                ...evidence.map((e) => _EvidenceCard(e)),
              const SizedBox(height: 16),
              const _SectionTitle('Ações'),
              Wrap(
                spacing: 8,
                runSpacing: 8,
                children: [
                  if (status == 'open')
                    FilledButton.icon(
                      onPressed: busy
                          ? null
                          : () => _run(() => widget.api.startReview(widget.insightId)),
                      icon: const Icon(Icons.visibility_outlined),
                      label: const Text('Assumir análise'),
                    ),
                  OutlinedButton.icon(
                    onPressed: busy
                        ? null
                        : () async {
                            final note = await _noteDialog('Adicionar observação', required: true);
                            if (note == null) return;
                            await _run(() => widget.api.addNote(widget.insightId, note));
                          },
                    icon: const Icon(Icons.note_add_outlined),
                    label: const Text('Adicionar nota'),
                  ),
                  if (canManage && status != 'confirmed' && status != 'resolved' && status != 'dismissed')
                    OutlinedButton.icon(
                      onPressed: busy
                          ? null
                          : () async {
                              final note = await _noteDialog('Confirmar insight');
                              if (note == null) return;
                              await _run(() => widget.api.setStatus(widget.insightId, 'confirmed', notes: note));
                            },
                      icon: const Icon(Icons.verified_outlined),
                      label: const Text('Confirmar'),
                    ),
                  if (canManage && status != 'dismissed' && status != 'resolved')
                    TextButton.icon(
                      onPressed: busy
                          ? null
                          : () async {
                              final note = await _noteDialog('Marcar como não procede', required: true);
                              if (note == null) return;
                              await _run(() => widget.api.setStatus(widget.insightId, 'dismissed', notes: note));
                            },
                      icon: const Icon(Icons.block_outlined),
                      label: const Text('Não procede'),
                    ),
                  if (canManage && status != 'resolved')
                    FilledButton.tonalIcon(
                      onPressed: busy
                          ? null
                          : () async {
                              final note = await _noteDialog('Resolver insight');
                              if (note == null) return;
                              await _run(() => widget.api.setStatus(widget.insightId, 'resolved', notes: note));
                            },
                      icon: const Icon(Icons.task_alt_rounded),
                      label: const Text('Resolver'),
                    ),
                ],
              ),
              const SizedBox(height: 18),
              const _SectionTitle('Histórico de decisões'),
              if (actions.isEmpty)
                const Text('Nenhuma ação humana registrada ainda.')
              else
                ...actions.map(
                  (a) => ListTile(
                    contentPadding: EdgeInsets.zero,
                    leading: const CircleAvatar(child: Icon(Icons.history, size: 18)),
                    title: Text('${a['actor_name'] ?? 'Sistema'} • ${RCTheme.statusLabel('${a['action_type'] ?? ''}') }'),
                    subtitle: Text([
                      if (_nonEmpty(a['notes'])) '${a['notes']}',
                      _dateTimeText(a['created_at']),
                    ].join('\n')),
                  ),
                ),
            ],
          );
        },
      ),
    );
  }
}

class AssetsPage extends StatefulWidget {
  const AssetsPage({super.key, required this.api, required this.onChanged});

  final IntelligenceApi api;
  final Future<void> Function() onChanged;

  @override
  State<AssetsPage> createState() => _AssetsPageState();
}

class _AssetsPageState extends State<AssetsPage> {
  final search = TextEditingController();
  late Future<List<Map<String, dynamic>>> future;

  @override
  void initState() {
    super.initState();
    future = widget.api.assets();
  }

  @override
  void dispose() {
    search.dispose();
    super.dispose();
  }

  Future<void> _reload() async {
    setState(() => future = widget.api.assets(query: search.text.trim().isEmpty ? null : search.text.trim()));
    await future;
  }

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        Padding(
          padding: const EdgeInsets.fromLTRB(16, 14, 16, 8),
          child: TextField(
            controller: search,
            textInputAction: TextInputAction.search,
            onSubmitted: (_) => _reload(),
            decoration: InputDecoration(
              labelText: 'Buscar Nº do ativo, placa, marca ou modelo',
              prefixIcon: const Icon(Icons.search),
              suffixIcon: IconButton(onPressed: _reload, icon: const Icon(Icons.arrow_forward)),
            ),
          ),
        ),
        Expanded(
          child: FutureBuilder<List<Map<String, dynamic>>>(
            future: future,
            builder: (context, snapshot) {
              if (snapshot.connectionState != ConnectionState.done) {
                return const Center(child: CircularProgressIndicator());
              }
              if (snapshot.hasError) return _ErrorView(error: snapshot.error, retry: _reload);
              final values = snapshot.data ?? const [];
              return RefreshIndicator(
                onRefresh: _reload,
                child: ListView.builder(
                  physics: const AlwaysScrollableScrollPhysics(),
                  padding: const EdgeInsets.fromLTRB(12, 4, 12, 28),
                  itemCount: values.length,
                  itemBuilder: (context, i) {
                    final a = values[i];
                    final open = _int(a['open_insights']);
                    final critical = _int(a['critical_insights']);
                    return Padding(
                      padding: const EdgeInsets.only(bottom: 10),
                      child: Card(
                        child: ListTile(
                          contentPadding: const EdgeInsets.all(14),
                          leading: CircleAvatar(
                            backgroundColor: critical > 0
                                ? RCTheme.severityColor('critical').withValues(alpha: .1)
                                : RCTheme.lightBlue,
                            child: Icon(
                              Icons.precision_manufacturing_rounded,
                              color: critical > 0 ? RCTheme.severityColor('critical') : RCTheme.blue,
                            ),
                          ),
                          title: Text(
                            '${a['asset_number'] ?? 'Sem nº'} • ${a['brand'] ?? ''} ${a['model'] ?? ''}'.trim(),
                            style: const TextStyle(fontWeight: FontWeight.w700),
                          ),
                          subtitle: Text([
                            if (_nonEmpty(a['plate'])) 'Placa ${a['plate']}',
                            if (_nonEmpty(a['machine_type'])) '${a['machine_type']}',
                            if (a['current_meter'] != null) 'Horímetro/Km: ${a['current_meter']}',
                            if (a['quality_score'] != null) 'Qualidade do dado: ${_num(a['quality_score']).toStringAsFixed(0)}/100',
                          ].join(' • ')),
                          trailing: open > 0
                              ? Badge(
                                  label: Text('$open'),
                                  backgroundColor: critical > 0 ? RCTheme.severityColor('critical') : RCTheme.blue,
                                  child: const Icon(Icons.notifications_active_outlined),
                                )
                              : const Icon(Icons.chevron_right),
                          onTap: () async {
                            await Navigator.of(context).push(
                              MaterialPageRoute(builder: (_) => AssetOverviewPage(api: widget.api, asset: a)),
                            );
                            await _reload();
                            await widget.onChanged();
                          },
                        ),
                      ),
                    );
                  },
                ),
              );
            },
          ),
        ),
      ],
    );
  }
}

class AssetOverviewPage extends StatelessWidget {
  const AssetOverviewPage({super.key, required this.api, required this.asset});

  final IntelligenceApi api;
  final Map<String, dynamic> asset;

  @override
  Widget build(BuildContext context) {
    final machineId = _int(asset['machine_id']);
    final oemAsset = Asset(
      id: '${asset['asset_number'] ?? machineId}',
      description: '${asset['machine_type'] ?? ''}',
      brand: '${asset['brand'] ?? ''}',
      model: '${asset['model'] ?? ''}',
      plate: '${asset['plate'] ?? ''}',
    );
    final catalog = OemCatalogService().match(oemAsset);

    return Scaffold(
      appBar: AppBar(title: Text('${asset['asset_number'] ?? 'Ativo'}')),
      body: FutureBuilder<List<Map<String, dynamic>>>(
        future: api.feed(machineId: machineId, limit: 50),
        builder: (context, snapshot) {
          final insights = snapshot.data ?? const [];
          return ListView(
            padding: const EdgeInsets.all(16),
            children: [
              _InfoCard(
                icon: Icons.precision_manufacturing_rounded,
                title: '${asset['brand'] ?? ''} ${asset['model'] ?? ''}'.trim(),
                lines: [
                  if (_nonEmpty(asset['plate'])) 'Placa: ${asset['plate']}',
                  if (_nonEmpty(asset['machine_type'])) 'Tipo: ${asset['machine_type']}',
                  if (asset['current_meter'] != null) 'Horímetro/Km: ${asset['current_meter']}',
                  if (asset['latest_fueling_at'] != null) 'Último abastecimento: ${_dateTimeText(asset['latest_fueling_at'])}',
                  if (asset['latest_maintenance_at'] != null) 'Última manutenção: ${_dateTimeText(asset['latest_maintenance_at'])}',
                ],
              ),
              const SizedBox(height: 16),
              const _SectionTitle('Leitura do Intelligence'),
              if (snapshot.connectionState != ConnectionState.done)
                const Center(child: Padding(padding: EdgeInsets.all(24), child: CircularProgressIndicator()))
              else if (snapshot.hasError)
                Text(_friendlyError(snapshot.error))
              else if (insights.isEmpty)
                const _EmptyCard(
                  icon: Icons.check_circle_outline,
                  title: 'Nenhum insight para este ativo',
                  message: 'O histórico continuará sendo acompanhado.',
                )
              else
                ...insights.map(
                  (i) => Padding(
                    padding: const EdgeInsets.only(bottom: 10),
                    child: _InsightCard(
                      item: i,
                      onTap: () => Navigator.of(context).push(
                        MaterialPageRoute(builder: (_) => InsightDetailPage(api: api, insightId: '${i['id']}')),
                      ),
                    ),
                  ),
                ),
              const SizedBox(height: 16),
              const _SectionTitle('Fonte OEM'),
              _InfoCard(
                icon: Icons.menu_book_outlined,
                title: catalog.provider,
                lines: [catalog.status, catalog.notes],
                trailing: catalog.catalogUrl.isEmpty
                    ? null
                    : OutlinedButton.icon(
                        onPressed: () => _launch(catalog.catalogUrl),
                        icon: const Icon(Icons.open_in_new),
                        label: const Text('Abrir catálogo'),
                      ),
              ),
            ],
          );
        },
      ),
    );
  }
}

class DataHealthPage extends StatelessWidget {
  const DataHealthPage({
    super.key,
    required this.dashboard,
    required this.profile,
    required this.onRefresh,
  });

  final Map<String, dynamic> dashboard;
  final Map<String, dynamic> profile;
  final Future<void> Function() onRefresh;

  @override
  Widget build(BuildContext context) {
    final quality = _map(dashboard['data_quality']);
    final freshness = _map(dashboard['freshness']);
    final stock = _map(dashboard['stock']);
    return RefreshIndicator(
      onRefresh: onRefresh,
      child: ListView(
        physics: const AlwaysScrollableScrollPhysics(),
        padding: const EdgeInsets.fromLTRB(16, 14, 16, 30),
        children: [
          const Text('Saúde dos dados', style: TextStyle(fontSize: 26, fontWeight: FontWeight.w800, color: RCTheme.navy)),
          const SizedBox(height: 6),
          const Text(
            'No uso normal não é necessário importar planilhas: o Intelligence recebe os registros diretamente dos outros módulos do ecossistema.',
          ),
          const SizedBox(height: 18),
          _InfoCard(
            icon: Icons.fact_check_outlined,
            title: 'Qualidade média: ${_num(quality['avg_score']).toStringAsFixed(1)}/100',
            lines: [
              '${_int(quality['machines_7d'])} ativo(s) com métricas nos últimos 7 dias',
              '${_int(quality['metric_rows_7d'])} conjunto(s) de métricas analisados',
              'Último cálculo: ${_dateTimeText(quality['last_calculated_at'])}',
            ],
          ),
          const SizedBox(height: 12),
          const _SectionTitle('Fontes'),
          _SourceTile(
            icon: Icons.local_gas_station_outlined,
            title: 'R&C Abastecimento',
            value: _dateTimeText(freshness['last_fuel_event']),
            caption: 'Último fato operacional recebido',
          ),
          const SizedBox(height: 8),
          _SourceTile(
            icon: Icons.build_outlined,
            title: 'R&C Manutenção',
            value: _dateTimeText(freshness['last_maintenance']),
            caption: 'Última manutenção disponível',
          ),
          const SizedBox(height: 8),
          _SourceTile(
            icon: Icons.psychology_alt_outlined,
            title: 'R&C Intelligence',
            value: _dateTimeText(freshness['last_metric_refresh']),
            caption: 'Último processamento de métricas',
          ),
          const SizedBox(height: 16),
          const _SectionTitle('Cadastro ainda sem operação'),
          _InfoCard(
            icon: Icons.hourglass_empty_rounded,
            title: '${_int(stock['pending_setup'])} unidade(s)',
            lines: const [
              'Unidades cadastradas sem movimentação ou medição física ficam fora dos alertas de estoque até entrarem em operação.',
            ],
          ),
          const SizedBox(height: 16),
          const _SectionTitle('Seu acesso'),
          _InfoCard(
            icon: Icons.admin_panel_settings_outlined,
            title: '${profile['display_name'] ?? profile['username'] ?? 'Usuário'}',
            lines: [
              'Perfil: ${RCTheme.roleLabel('${profile['role'] ?? ''}')}',
              dashboard['can_manage'] == true
                  ? 'Pode confirmar, descartar e resolver insights.'
                  : 'Pode visualizar e assumir análise; decisões finais dependem de Gerente/Admin.',
            ],
          ),
        ],
      ),
    );
  }
}

class OemPage extends StatefulWidget {
  const OemPage({super.key, required this.api});

  final IntelligenceApi api;

  @override
  State<OemPage> createState() => _OemPageState();
}

class _OemPageState extends State<OemPage> {
  final service = OemCatalogService();
  late Future<List<Map<String, dynamic>>> future;

  @override
  void initState() {
    super.initState();
    future = widget.api.assets(limit: 500);
  }

  Future<void> _reload() async {
    setState(() => future = widget.api.assets(limit: 500));
    await future;
  }

  @override
  Widget build(BuildContext context) {
    return FutureBuilder<List<Map<String, dynamic>>>(
      future: future,
      builder: (context, snapshot) {
        if (snapshot.connectionState != ConnectionState.done) {
          return const Center(child: CircularProgressIndicator());
        }
        if (snapshot.hasError) return _ErrorView(error: snapshot.error, retry: _reload);
        final values = snapshot.data ?? const [];
        return RefreshIndicator(
          onRefresh: _reload,
          child: ListView.builder(
            physics: const AlwaysScrollableScrollPhysics(),
            padding: const EdgeInsets.fromLTRB(12, 14, 12, 28),
            itemCount: values.length + 1,
            itemBuilder: (context, i) {
              if (i == 0) {
                return const Padding(
                  padding: EdgeInsets.fromLTRB(4, 0, 4, 14),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text('Biblioteca OEM', style: TextStyle(fontSize: 26, fontWeight: FontWeight.w800, color: RCTheme.navy)),
                      SizedBox(height: 4),
                      Text('Catálogos oficiais são uma fonte de apoio. O Intelligence não trata um catálogo genérico como prova de defeito.'),
                    ],
                  ),
                );
              }
              final item = values[i - 1];
              final asset = Asset(
                id: '${item['asset_number'] ?? item['machine_id']}',
                description: '${item['machine_type'] ?? ''}',
                brand: '${item['brand'] ?? ''}',
                model: '${item['model'] ?? ''}',
                plate: '${item['plate'] ?? ''}',
              );
              final match = service.match(asset);
              return Padding(
                padding: const EdgeInsets.only(bottom: 10),
                child: Card(
                  child: ExpansionTile(
                    leading: const Icon(Icons.menu_book_outlined),
                    title: Text('${asset.id} • ${asset.brand} ${asset.model}'.trim()),
                    subtitle: Text(match.provider),
                    childrenPadding: const EdgeInsets.fromLTRB(16, 0, 16, 14),
                    children: [
                      Align(alignment: Alignment.centerLeft, child: Text(match.status)),
                      const SizedBox(height: 4),
                      Align(alignment: Alignment.centerLeft, child: Text(match.notes)),
                      const SizedBox(height: 10),
                      Align(
                        alignment: Alignment.centerLeft,
                        child: OutlinedButton.icon(
                          onPressed: match.catalogUrl.isEmpty ? null : () => _launch(match.catalogUrl),
                          icon: const Icon(Icons.open_in_new),
                          label: const Text('Abrir fonte oficial'),
                        ),
                      ),
                    ],
                  ),
                ),
              );
            },
          ),
        );
      },
    );
  }
}

class _SummaryTile extends StatelessWidget {
  const _SummaryTile({required this.title, required this.value, required this.icon, required this.accent});
  final String title;
  final String value;
  final IconData icon;
  final Color accent;

  @override
  Widget build(BuildContext context) => Card(
        child: Padding(
          padding: const EdgeInsets.all(14),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Icon(icon, color: accent),
              const Spacer(),
              Text(value, style: const TextStyle(fontSize: 25, fontWeight: FontWeight.w800)),
              Text(title, maxLines: 2),
            ],
          ),
        ),
      );
}

class _MiniMetric extends StatelessWidget {
  const _MiniMetric({required this.label, required this.value});
  final String label;
  final String value;
  @override
  Widget build(BuildContext context) => Container(
        padding: const EdgeInsets.all(12),
        decoration: BoxDecoration(color: Colors.white.withValues(alpha: .65), borderRadius: BorderRadius.circular(12)),
        child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Text(label, style: Theme.of(context).textTheme.labelMedium),
          const SizedBox(height: 3),
          Text(value, style: const TextStyle(fontWeight: FontWeight.w800)),
        ]),
      );
}

class _SectionTitle extends StatelessWidget {
  const _SectionTitle(this.text);
  final String text;
  @override
  Widget build(BuildContext context) => Padding(
        padding: const EdgeInsets.only(bottom: 8),
        child: Text(text, style: const TextStyle(fontSize: 18, fontWeight: FontWeight.w800, color: RCTheme.navy)),
      );
}

class _InfoCard extends StatelessWidget {
  const _InfoCard({required this.icon, required this.title, required this.lines, this.trailing});
  final IconData icon;
  final String title;
  final List<String> lines;
  final Widget? trailing;

  @override
  Widget build(BuildContext context) => Card(
        child: Padding(
          padding: const EdgeInsets.all(15),
          child: Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              CircleAvatar(backgroundColor: RCTheme.lightBlue, child: Icon(icon, color: RCTheme.blue)),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(title, style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w800)),
                    const SizedBox(height: 5),
                    ...lines.where((x) => x.trim().isNotEmpty).map(
                          (x) => Padding(
                            padding: const EdgeInsets.only(bottom: 3),
                            child: Text(x),
                          ),
                        ),
                    if (trailing != null) ...[const SizedBox(height: 10), trailing!],
                  ],
                ),
              ),
            ],
          ),
        ),
      );
}

class _SourceTile extends StatelessWidget {
  const _SourceTile({required this.icon, required this.title, required this.value, required this.caption});
  final IconData icon;
  final String title;
  final String value;
  final String caption;
  @override
  Widget build(BuildContext context) => Card(
        child: ListTile(
          leading: Icon(icon, color: RCTheme.blue),
          title: Text(title, style: const TextStyle(fontWeight: FontWeight.w700)),
          subtitle: Text('$caption\n$value'),
          isThreeLine: true,
        ),
      );
}

class _InsightCard extends StatelessWidget {
  const _InsightCard({required this.item, required this.onTap});
  final Map<String, dynamic> item;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    final severity = '${item['severity'] ?? 'info'}';
    final contextName = _nonEmpty(item['asset_number'])
        ? '${item['asset_number']}'
        : _nonEmpty(item['tank_name'])
            ? '${item['tank_name']}'
            : _nonEmpty(item['work_name'])
                ? '${item['work_name']}'
                : 'Ecossistema R&C';
    return Card(
      child: InkWell(
        borderRadius: BorderRadius.circular(18),
        onTap: onTap,
        child: Padding(
          padding: const EdgeInsets.all(14),
          child: Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Container(
                width: 42,
                height: 42,
                decoration: BoxDecoration(
                  color: RCTheme.severityColor(severity).withValues(alpha: .1),
                  borderRadius: BorderRadius.circular(12),
                ),
                child: Icon(RCTheme.severityIcon(severity), color: RCTheme.severityColor(severity)),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Wrap(
                      spacing: 8,
                      runSpacing: 4,
                      crossAxisAlignment: WrapCrossAlignment.center,
                      children: [
                        Text(contextName, style: const TextStyle(fontWeight: FontWeight.w800)),
                        _StatusChip('${item['status'] ?? ''}'),
                      ],
                    ),
                    const SizedBox(height: 5),
                    Text('${item['title'] ?? ''}', style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w700)),
                    const SizedBox(height: 3),
                    Text('${item['summary'] ?? ''}', maxLines: 3, overflow: TextOverflow.ellipsis),
                    const SizedBox(height: 7),
                    Text(
                      '${RCTheme.severityLabel(severity)} • Confiança ${_num(item['confidence']).toStringAsFixed(0)}/100 • ${_dateTimeText(item['detected_at'])}',
                      style: Theme.of(context).textTheme.bodySmall,
                    ),
                  ],
                ),
              ),
              const Icon(Icons.chevron_right),
            ],
          ),
        ),
      ),
    );
  }
}

class _EvidenceCard extends StatelessWidget {
  const _EvidenceCard(this.evidence);
  final Map<String, dynamic> evidence;

  @override
  Widget build(BuildContext context) {
    String value = '';
    if (evidence['numeric_value'] != null) {
      value = '${evidence['numeric_value']}';
    } else if (_nonEmpty(evidence['text_value'])) {
      value = '${evidence['text_value']}';
    } else if (evidence['json_value'] != null) {
      value = '${evidence['json_value']}';
    }
    return Padding(
      padding: const EdgeInsets.only(bottom: 8),
      child: Card(
        child: Padding(
          padding: const EdgeInsets.all(13),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text('${evidence['label'] ?? evidence['type'] ?? 'Evidência'}', style: const TextStyle(fontWeight: FontWeight.w800)),
              if (value.isNotEmpty) ...[const SizedBox(height: 4), Text(value)],
              const SizedBox(height: 6),
              Text(
                '${evidence['source_schema'] ?? ''}.${evidence['source_table'] ?? ''} • registro ${evidence['source_record_id'] ?? '-'} • ${_dateTimeText(evidence['occurred_at'])}',
                style: Theme.of(context).textTheme.bodySmall,
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _StatusChip extends StatelessWidget {
  const _StatusChip(this.status);
  final String status;
  @override
  Widget build(BuildContext context) => Container(
        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
        decoration: BoxDecoration(color: RCTheme.lightBlue, borderRadius: BorderRadius.circular(99)),
        child: Text(RCTheme.statusLabel(status), style: const TextStyle(fontSize: 11, fontWeight: FontWeight.w700, color: RCTheme.navy)),
      );
}

class _EmptyCard extends StatelessWidget {
  const _EmptyCard({required this.icon, required this.title, required this.message});
  final IconData icon;
  final String title;
  final String message;
  @override
  Widget build(BuildContext context) => Padding(
        padding: const EdgeInsets.all(12),
        child: Center(
          child: Column(
            children: [
              Icon(icon, size: 46, color: RCTheme.blue),
              const SizedBox(height: 8),
              Text(title, style: const TextStyle(fontWeight: FontWeight.w800)),
              const SizedBox(height: 4),
              Text(message, textAlign: TextAlign.center),
            ],
          ),
        ),
      );
}

class _ErrorView extends StatelessWidget {
  const _ErrorView({required this.error, required this.retry});
  final Object? error;
  final Future<void> Function() retry;
  @override
  Widget build(BuildContext context) => Center(
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              const Icon(Icons.cloud_off_outlined, size: 48),
              const SizedBox(height: 10),
              Text(_friendlyError(error), textAlign: TextAlign.center),
              const SizedBox(height: 12),
              OutlinedButton.icon(onPressed: retry, icon: const Icon(Icons.refresh), label: const Text('Tentar novamente')),
            ],
          ),
        ),
      );
}

Map<String, dynamic> _map(dynamic value) {
  if (value is Map<String, dynamic>) return value;
  if (value is Map) return Map<String, dynamic>.from(value);
  return const {};
}

List<Map<String, dynamic>> _list(dynamic value) {
  if (value is! List) return const [];
  return value.whereType<Map>().map((e) => Map<String, dynamic>.from(e)).toList(growable: false);
}

num _num(dynamic value) {
  if (value is num) return value;
  return num.tryParse('$value') ?? 0;
}

int _int(dynamic value) => _num(value).toInt();

bool _nonEmpty(dynamic value) => value != null && '$value'.trim().isNotEmpty && '$value' != 'null';

String _formatNumber(num value) {
  final text = value.toStringAsFixed(value % 1 == 0 ? 0 : 1);
  final parts = text.split('.');
  final chars = parts[0].split('').reversed.toList();
  final out = <String>[];
  for (var i = 0; i < chars.length; i++) {
    if (i > 0 && i % 3 == 0) out.add('.');
    out.add(chars[i]);
  }
  final integer = out.reversed.join();
  return parts.length == 1 ? integer : '$integer,${parts[1]}';
}

String _dateTimeText(dynamic value) {
  if (!_nonEmpty(value)) return 'Sem registro';
  final d = DateTime.tryParse('$value')?.toLocal();
  if (d == null) return '$value';
  String two(int x) => x.toString().padLeft(2, '0');
  return '${two(d.day)}/${two(d.month)}/${d.year} ${two(d.hour)}:${two(d.minute)}';
}

String _humanize(String key) {
  final words = key.replaceAll('_', ' ').trim();
  if (words.isEmpty) return key;
  return '${words[0].toUpperCase()}${words.substring(1)}';
}

String _contextTitle(Map<String, dynamic> ctx) {
  if (_nonEmpty(ctx['asset_number'])) {
    final model = '${ctx['brand'] ?? ''} ${ctx['model'] ?? ''}'.trim();
    return '${ctx['asset_number']}${model.isEmpty ? '' : ' • $model'}';
  }
  if (_nonEmpty(ctx['tank_name'])) return '${ctx['tank_name']}';
  if (_nonEmpty(ctx['work_name'])) return '${ctx['work_name']}';
  return 'Contexto operacional';
}

String _friendlyError(Object? error) {
  final text = '$error';
  if (text.contains('Sem permissão')) return 'Seu perfil não possui permissão para esta área do R&C Intelligence.';
  if (text.toLowerCase().contains('invalid login credentials')) return 'Usuário ou senha inválidos.';
  if (text.toLowerCase().contains('socket') || text.toLowerCase().contains('network')) {
    return 'Não foi possível acessar o servidor agora. Confira a conexão e tente novamente.';
  }
  return text.replaceFirst('Exception: ', '');
}

Future<void> _launch(String raw) async {
  if (raw.trim().isEmpty) return;
  final uri = Uri.tryParse(raw);
  if (uri == null) return;
  await launchUrl(uri, mode: LaunchMode.externalApplication);
}
