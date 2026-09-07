part of 'main_online.dart';

extension FuelApiV29 on FuelApi {
  Future<List<Map<String, dynamic>>> myFuelingsV29(
          {DateTime? start,
          DateTime? end,
          String? asset,
          String? work,
          String? fuelType,
          String? source}) async =>
      _rows(await client.rpc('rca_my_fuelings_v71', params: {
        'p_start': start?.toUtc().toIso8601String(),
        'p_end': end?.toUtc().toIso8601String(),
        'p_asset_query': asset,
        'p_work_query': work,
        'p_fuel_type': fuelType,
        'p_source_code': source
      }));
  Future<bool> hasPermissionV29(String key) async =>
      (await client.rpc('rca_has_permission', params: {'p_key': key})) == true;
  Future<List<Map<String, dynamic>>> adminUsersV29() async =>
      _rows(await client.rpc('rca_admin_list_users_v29'));
  Future<Map<String, dynamic>> adminPermissionCatalogV29() async =>
      _map(await client.rpc('rca_admin_permission_catalog_v29'));
  Future<void> adminSetUserPermissionV29(
          String userId, String key, bool allowed) async =>
      client.rpc('rca_admin_set_user_permission_v29', params: {
        'p_user_id': userId,
        'p_permission_key': key,
        'p_allowed': allowed
      });
  Future<void> adminResetUserPermissionsV29(String userId) async =>
      client.rpc('rca_admin_reset_user_permissions_v29',
          params: {'p_user_id': userId});
}

class OperationalHomeV29Screen extends StatefulWidget {
  final Map<String, dynamic> profile;
  final Future<void> Function() onLogout;
  const OperationalHomeV29Screen(
      {super.key, required this.profile, required this.onLogout});
  @override
  State<OperationalHomeV29Screen> createState() =>
      _OperationalHomeV29ScreenState();
}

class _OperationalHomeV29ScreenState extends State<OperationalHomeV29Screen> {
  Map<String, dynamic>? ref;
  bool canFuel = true, canView = true, loading = true;
  String? error;

  @override
  void initState() {
    super.initState();
    unawaited(offlineStore.setLastTankId(null));
    load();
  }

  Future<void> load() async {
    try {
      final results = await Future.wait<dynamic>([
        api.referenceData(),
        api.hasPermissionV29('fueling.create'),
      ]);
      if (mounted) {
        setState(() {
          ref = results[0] as Map<String, dynamic>;
          canFuel = results[1] == true;
          canView =
              true; // Operacional sempre pode consultar somente os próprios registros.
          loading = false;
          error = null;
        });
      }
    } catch (e) {
      if (mounted)
        setState(() {
          loading = false;
          error = _friendlyError(e);
        });
    }
  }

  List<Map<String, dynamic>> get sources => _sortedFuelUnits(ref?['tanks'])
      .where((t) =>
          t['authorized'] != false &&
          const {'stationary', 'comboio', 'truck'}
              .contains('${t['tank_type']}'))
      .toList();

  Future<void> newFueling() async {
    if (!canFuel) {
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(
          content: Text(
              'Seu acesso para registrar abastecimentos está restrito pelo administrador.')));
      return;
    }
    if (ref == null) {
      await load();
      if (ref == null) return;
    }
    final list = sources;
    if (list.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(
          content: Text(
              'Nenhuma origem de combustível está liberada para este usuário.')));
      return;
    }
    final source = await showModalBottomSheet<Map<String, dynamic>>(
      context: context,
      showDragHandle: true,
      isScrollControlled: true,
      builder: (ctx) => SafeArea(
          child: ConstrainedBox(
        constraints:
            BoxConstraints(maxHeight: MediaQuery.of(ctx).size.height * .72),
        child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              const Padding(
                  padding: EdgeInsets.fromLTRB(18, 4, 18, 2),
                  child: Text('Origem do combustível',
                      style: TextStyle(
                          fontWeight: FontWeight.w900, fontSize: 19))),
              const Padding(
                  padding: EdgeInsets.fromLTRB(18, 0, 18, 10),
                  child:
                      Text('Selecione de onde o combustível será retirado.')),
              Flexible(
                  child: ListView.separated(
                      shrinkWrap: true,
                      padding: const EdgeInsets.fromLTRB(12, 4, 12, 18),
                      itemCount: list.length,
                      separatorBuilder: (_, __) => const SizedBox(height: 4),
                      itemBuilder: (_, i) {
                        final t = list[i];
                        final stationary = '${t['tank_type']}' == 'stationary';
                        return Card(
                            child: ListTile(
                                contentPadding: const EdgeInsets.symmetric(
                                    horizontal: 14, vertical: 7),
                                leading: Icon(
                                    stationary
                                        ? Icons.oil_barrel_outlined
                                        : Icons.local_shipping_outlined,
                                    color: _blue),
                                title: Text('${t['code']} • ${t['name']}',
                                    style: const TextStyle(
                                        fontWeight: FontWeight.w900)),
                                subtitle: Text(
                                    'Saldo disponível: ${_fmtLiters(t['current_balance_liters'])}'),
                                trailing:
                                    const Icon(Icons.chevron_right_rounded),
                                onTap: () => Navigator.pop(ctx, t)));
                      })),
            ]),
      )),
    );
    if (!mounted || source == null || ref == null) return;
    await Navigator.push(
        context,
        MaterialPageRoute(
            builder: (_) => FuelingV23Screen(
                source: source, ref: ref!, profile: widget.profile)));
    if (mounted) await load();
  }

  void openMyFuelings() {
    if (!canView) {
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(
          content: Text(
              'Seu acesso aos registros está restrito pelo administrador.')));
      return;
    }
    Navigator.push(context,
        MaterialPageRoute(builder: (_) => const MyFuelingsV29Screen()));
  }

  @override
  Widget build(BuildContext context) => Scaffold(
        appBar: AppBar(
            title: const Text('R&C Abastecimento',
                style: TextStyle(fontWeight: FontWeight.w900)),
            actions: [
              IconButton(
                  onPressed: () async =>
                      _logoutToLogin(context, widget.onLogout),
                  tooltip: 'Sair',
                  icon: const Icon(Icons.logout_rounded))
            ]),
        body: loading
            ? const Center(child: CircularProgressIndicator())
            : RefreshIndicator(
                onRefresh: load,
                child: ListView(
                    physics: const AlwaysScrollableScrollPhysics(),
                    padding: const EdgeInsets.all(20),
                    children: [
                      GreetingLine(name: '${widget.profile['display_name']}'),
                      const SizedBox(height: 4),
                      const Text('Área Operacional',
                          style: TextStyle(
                              color: Colors.black54,
                              fontWeight: FontWeight.w700)),
                      if (error != null) ...[
                        const SizedBox(height: 10),
                        Card(
                            child: ListTile(
                                leading: const Icon(Icons.warning_amber_rounded,
                                    color: _blue),
                                title: const Text('Não foi possível atualizar'),
                                subtitle: Text(error!)))
                      ],
                      const SizedBox(height: 18),
                      HomeActionCard(
                          icon: Icons.local_gas_station_rounded,
                          title: 'Novo abastecimento',
                          subtitle: canFuel
                              ? 'Registrar um novo abastecimento'
                              : 'Acesso restrito pelo administrador',
                          onTap: newFueling),
                      const SizedBox(height: 12),
                      HomeActionCard(
                          icon: Icons.history_rounded,
                          title: 'Meus abastecimentos',
                          subtitle: canView
                              ? 'Todos os abastecimentos registrados por mim'
                              : 'Acesso restrito pelo administrador',
                          onTap: openMyFuelings),
                    ])),
      );
}

class MyFuelingsV29Screen extends StatefulWidget {
  const MyFuelingsV29Screen({super.key});
  @override
  State<MyFuelingsV29Screen> createState() => _MyFuelingsV29ScreenState();
}

class _MyFuelingsV29ScreenState extends State<MyFuelingsV29Screen> {
  final asset = TextEditingController(),
      work = TextEditingController(),
      fuel = TextEditingController(),
      source = TextEditingController();
  DateTime? start, end;
  List<Map<String, dynamic>>? items;
  List<Map<String, dynamic>> localPending = <Map<String, dynamic>>[];
  bool busy = false;
  String? error;

  @override
  void initState() {
    super.initState();
    offlineStore.pendingCount.addListener(_queueChanged);
    offlineStore.syncRevision.addListener(_queueChanged);
    load();
  }

  void _queueChanged() {
    if (mounted) unawaited(load());
  }

  @override
  void dispose() {
    offlineStore.pendingCount.removeListener(_queueChanged);
    offlineStore.syncRevision.removeListener(_queueChanged);
    asset.dispose();
    work.dispose();
    fuel.dispose();
    source.dispose();
    super.dispose();
  }

  String? clean(TextEditingController c) =>
      c.text.trim().isEmpty ? null : c.text.trim();
  DateTime? dayStart(DateTime? d) =>
      d == null ? null : DateTime(d.year, d.month, d.day);
  DateTime? dayEnd(DateTime? d) => d == null
      ? null
      : DateTime(d.year, d.month, d.day).add(const Duration(days: 1));
  String dlabel(DateTime? d) => d == null
      ? 'Selecionar'
      : '${d.day.toString().padLeft(2, '0')}/${d.month.toString().padLeft(2, '0')}/${d.year}';

  Future<void> choose(bool first) async {
    final now = DateTime.now();
    final v = await showDatePicker(
        context: context,
        firstDate: DateTime(2024),
        lastDate: DateTime(now.year + 2),
        initialDate: (first ? start : end) ?? start ?? now);
    if (v != null && mounted) {
      setState(() {
        if (first) {
          start = v;
        } else {
          end = v;
        }
      });
    }
  }

  bool _localMatchesV70(Map<String, dynamic> x) {
    if (!_recordInRangeV70(x, dayStart(start), dayEnd(end))) return false;
    bool has(String value, String? needle) {
      final n = (needle ?? '').trim();
      return n.isEmpty || value.toLowerCase().contains(n.toLowerCase());
    }

    if (!has(
        '${x['asset_number'] ?? ''} ${x['asset_plate'] ?? ''} ${x['asset_model'] ?? ''} ${x['third_party_plate'] ?? ''} ${x['third_party_description'] ?? ''}',
        clean(asset))) return false;
    if (!has('${x['work'] ?? ''}', clean(work))) return false;
    if (!has('${x['fuel_type'] ?? ''}', clean(fuel))) return false;
    if (!has('${x['source_tank'] ?? ''} ${x['source_tank_name'] ?? ''}',
        clean(source))) return false;
    return true;
  }

  Future<void> load() async {
    if (busy) return;
    final local = offlineStore
        .pendingFuelingsForCurrentUser()
        .where(_localMatchesV70)
        .toList();
    if (mounted)
      setState(() {
        busy = true;
        error = null;
        localPending = local;
      });
    try {
      if (offlineStore.online.value) {
        final x = await api.myFuelingsV29(
            start: dayStart(start),
            end: dayEnd(end),
            asset: clean(asset),
            work: clean(work),
            fuelType: clean(fuel),
            source: clean(source));
        if (mounted) setState(() => items = _sortRecordsV70([...local, ...x]));
      } else {
        if (mounted) setState(() => items = _sortRecordsV70(local));
      }
    } catch (e) {
      if (mounted)
        setState(() {
          items = _sortRecordsV70(local);
          error = local.isEmpty ? _friendlyError(e) : null;
        });
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
      start = null;
      end = null;
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
            child: ListView(padding: const EdgeInsets.all(14), children: [
              Card(
                  child: ExpansionTile(
                      leading:
                          const Icon(Icons.filter_alt_outlined, color: _blue),
                      title: const Text('Filtros',
                          style: TextStyle(fontWeight: FontWeight.w900)),
                      subtitle: const Text(
                          'Use somente quando quiser localizar um registro'),
                      childrenPadding: const EdgeInsets.fromLTRB(14, 0, 14, 14),
                      children: [
                    Row(children: [
                      Expanded(
                          child: OutlinedButton.icon(
                              onPressed: busy ? null : () => choose(true),
                              icon: const Icon(Icons.event_outlined),
                              label: Text('De ${dlabel(start)}'))),
                      const SizedBox(width: 8),
                      Expanded(
                          child: OutlinedButton.icon(
                              onPressed: busy ? null : () => choose(false),
                              icon: const Icon(Icons.event_outlined),
                              label: Text('Até ${dlabel(end)}')))
                    ]),
                    const SizedBox(height: 10),
                    TextField(
                        controller: asset,
                        decoration: const InputDecoration(
                            labelText: 'Ativo',
                            hintText: 'Nº do ativo, placa, marca ou modelo')),
                    const SizedBox(height: 10),
                    TextField(
                        controller: work,
                        decoration: const InputDecoration(labelText: 'Obra')),
                    const SizedBox(height: 10),
                    TextField(
                        controller: fuel,
                        decoration: const InputDecoration(
                            labelText: 'Tipo de combustível',
                            hintText: 'Ex.: Diesel S10')),
                    const SizedBox(height: 10),
                    TextField(
                        controller: source,
                        onSubmitted: (_) => load(),
                        decoration: const InputDecoration(
                            labelText: 'Origem do combustível',
                            hintText: 'Ex.: CB01, CT01 ou TE0001')),
                    const SizedBox(height: 12),
                    Row(children: [
                      Expanded(
                          child: FilledButton.icon(
                              onPressed: busy ? null : load,
                              icon: const Icon(Icons.search_rounded),
                              label: const Text('Filtrar'))),
                      const SizedBox(width: 8),
                      OutlinedButton(
                          onPressed: busy ? null : clearFilters,
                          child: const Text('Limpar'))
                    ]),
                  ])),
              if (busy)
                const Padding(
                    padding: EdgeInsets.only(top: 8),
                    child: LinearProgressIndicator(minHeight: 2)),
              if (error != null)
                Card(
                    child: ListTile(
                        leading: const Icon(Icons.error_outline_rounded,
                            color: _blue),
                        title: const Text('Não foi possível carregar'),
                        subtitle: Text(error!),
                        trailing: IconButton(
                            onPressed: busy ? null : load,
                            icon: const Icon(Icons.refresh_rounded)))),
              if (!busy && error == null && items != null && list.isEmpty)
                const Padding(
                    padding: EdgeInsets.all(40),
                    child: Center(
                        child: Text('Nenhum abastecimento encontrado.'))),
              if (items != null && list.isNotEmpty)
                Padding(
                    padding: const EdgeInsets.fromLTRB(4, 6, 4, 8),
                    child: Text('${list.length} abastecimento(s)',
                        style: const TextStyle(
                            fontWeight: FontWeight.w800,
                            color: Colors.black54))),
              ...list.map((x) {
                final assetText =
                    x['asset_number'] ?? x['third_party_plate'] ?? '-';
                final sourceText =
                    x['source_tank'] ?? x['source_tank_name'] ?? '-';
                final pending = x['offline_pending'] == true;
                final legacy = x['offline_legacy_owner'] == true;
                final syncError = '${x['sync_error'] ?? ''}'.trim();
                final syncConflict = x['sync_conflict'] == true;
                final syncRejected = x['sync_rejected'] == true ||
                    '${x['sync_status'] ?? ''}'.toLowerCase() == 'rejected';
                if (pending) {
                  final status = syncRejected
                      ? 'REJEITADO'
                      : legacy
                          ? 'PENDENTE (OFFLINE) • confirme o usuário'
                          : syncConflict
                              ? 'CONFLITO • AGUARDANDO ANÁLISE'
                              : syncError.isNotEmpty
                                  ? 'PENDENTE • falha ao sincronizar'
                                  : 'PENDENTE (OFFLINE)';
                  return Card(
                      child: Padding(
                          padding: const EdgeInsets.all(14),
                          child: Column(
                              crossAxisAlignment: CrossAxisAlignment.stretch,
                              children: [
                                Row(children: [
                                  const CircleAvatar(
                                      child: Icon(Icons.cloud_off_rounded)),
                                  const SizedBox(width: 12),
                                  Expanded(
                                      child: Text('Abastecimento • $assetText',
                                          maxLines: 2,
                                          overflow: TextOverflow.ellipsis,
                                          style: const TextStyle(
                                              fontWeight: FontWeight.w900)))
                                ]),
                                const SizedBox(height: 8),
                                Align(
                                    alignment: Alignment.centerLeft,
                                    child: Container(
                                        padding: const EdgeInsets.symmetric(
                                            horizontal: 10, vertical: 6),
                                        decoration: BoxDecoration(
                                            color: const Color(0xFFFFF4E5),
                                            borderRadius:
                                                BorderRadius.circular(999)),
                                        child: Text(status,
                                            softWrap: true,
                                            style: const TextStyle(
                                                fontSize: 11,
                                                fontWeight: FontWeight.w900,
                                                color: Colors.orange)))),
                                const SizedBox(height: 8),
                                Text(
                                    '${_recordOriginV28(x)} • Nº ${_recordSequenceV28(x)}',
                                    style: const TextStyle(
                                        color: Color(0xFFD51F2A),
                                        fontSize: 18,
                                        fontWeight: FontWeight.w900)),
                                const SizedBox(height: 8),
                                Text(
                                    '${_fmtDate(x['occurred_at'] ?? x['created_at'])}\n${x['work'] ?? 'Sem obra'} • ${_fmtLiters(x['liters'])}\n${x['fuel_type'] ?? 'Combustível'} • Origem: $sourceText'),
                                if (_hasValue(x['location_address'])) ...[
                                  const SizedBox(height: 6),
                                  Text('Localização: ${x['location_address']}')
                                ],
                                if (syncError.isNotEmpty) ...[
                                  const SizedBox(height: 8),
                                  Text(syncError,
                                      style: const TextStyle(
                                          color: Colors.redAccent,
                                          fontWeight: FontWeight.w700))
                                ],
                                const SizedBox(height: 10),
                                Row(children: [
                                  Expanded(
                                      child: OutlinedButton.icon(
                                          onPressed: () => Navigator.push(
                                              context,
                                              MaterialPageRoute(
                                                  builder: (_) =>
                                                      MovementDetailScreen(
                                                          item: x))),
                                          icon: const Icon(
                                              Icons.visibility_outlined),
                                          label: const Text('Ver registro'))),
                                  const SizedBox(width: 8),
                                  IconButton(
                                      onPressed: () => Navigator.push(
                                          context,
                                          MaterialPageRoute(
                                              builder: (_) =>
                                                  OfficialPdfPreviewV28Screen(
                                                      items: [x],
                                                      title:
                                                          'Prévia • Pendente offline'))),
                                      tooltip: 'Prévia / PDF',
                                      icon: const Icon(
                                          Icons.picture_as_pdf_outlined,
                                          color: _blue))
                                ]),
                                OutlinedButton.icon(
                                    onPressed:
                                        (busy || syncConflict || syncRejected)
                                            ? null
                                            : () async {
                                                try {
                                                  if (legacy) {
                                                    final ok = await showDialog<
                                                                bool>(
                                                            context: context,
                                                            builder: (ctx) =>
                                                                AlertDialog(
                                                                    title: const Text(
                                                                        'Confirmar usuário'),
                                                                    content:
                                                                        const Text(
                                                                            'Este registro foi criado em uma versão anterior. Confirme somente se este é o mesmo usuário que realizou o abastecimento.'),
                                                                    actions: [
                                                                      TextButton(
                                                                          onPressed: () => Navigator.pop(
                                                                              ctx,
                                                                              false),
                                                                          child:
                                                                              const Text('Cancelar')),
                                                                      FilledButton(
                                                                          onPressed: () => Navigator.pop(
                                                                              ctx,
                                                                              true),
                                                                          child:
                                                                              const Text('Confirmar e sincronizar'))
                                                                    ])) ??
                                                        false;
                                                    if (!ok) return;
                                                    await offlineStore
                                                        .claimLegacyPending(
                                                            '${x['queue_id']}');
                                                  }
                                                  await offlineStore
                                                      .retryPending();
                                                  await load();
                                                } catch (e) {
                                                  if (mounted)
                                                    ScaffoldMessenger.of(
                                                            context)
                                                        .showSnackBar(SnackBar(
                                                            content: Text(
                                                                _friendlyError(
                                                                    e))));
                                                }
                                              },
                                    icon: Icon(syncRejected
                                        ? Icons.block_rounded
                                        : syncConflict
                                            ? Icons.lock_clock_rounded
                                            : Icons.sync_rounded),
                                    label: Text(syncRejected
                                        ? 'Rejeitado'
                                        : syncConflict
                                            ? 'Aguardando análise'
                                            : legacy
                                                ? 'Confirmar e sincronizar'
                                                : 'Tentar sincronizar')),
                              ])));
                }
                return Card(
                    child: ListTile(
                        contentPadding: const EdgeInsets.all(14),
                        leading: const CircleAvatar(
                            child: Icon(Icons.local_gas_station_rounded)),
                        title: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text('Abastecimento • $assetText',
                                  style: const TextStyle(
                                      fontWeight: FontWeight.w900)),
                              const SizedBox(height: 3),
                              Text(
                                  '${_recordOriginV28(x)} • Nº ${_recordSequenceV28(x)}',
                                  style: const TextStyle(
                                      color: Color(0xFFD51F2A),
                                      fontWeight: FontWeight.w900))
                            ]),
                        subtitle: Text(
                            '${_fmtDate(x['occurred_at'] ?? x['created_at'])}\n${x['work'] ?? 'Sem obra'} • ${_fmtLiters(x['liters'])}\n${x['fuel_type'] ?? 'Combustível'} • Origem: $sourceText'),
                        isThreeLine: true,
                        trailing: const Icon(Icons.chevron_right_rounded),
                        onTap: () => Navigator.push(
                            context,
                            MaterialPageRoute(
                                builder: (_) =>
                                    MovementDetailScreen(item: x)))));
              }),
              const SizedBox(height: 24),
            ])));
  }
}

class UnifiedUsersV29Screen extends StatefulWidget {
  final Map<String, dynamic> referenceData;
  const UnifiedUsersV29Screen({super.key, required this.referenceData});
  @override
  State<UnifiedUsersV29Screen> createState() => _UnifiedUsersV29ScreenState();
}

class _UnifiedUsersV29ScreenState extends State<UnifiedUsersV29Screen> {
  List<Map<String, dynamic>>? users;
  List<String> keys = [];
  List<Map<String, dynamic>> defaults = [];
  bool busy = false, loading = true;
  String? error;

  @override
  void initState() {
    super.initState();
    load();
  }

  String roleLabel(String role) => role == 'manager'
      ? 'Gerente'
      : role == 'supervisor'
          ? 'Supervisor'
          : 'Operacional';
  String dbRole(String role) => role == 'operational' ? 'operator' : role;

  Map<String, bool> roleDefaults(String role) {
    final r = dbRole(role);
    final out = <String, bool>{for (final k in keys) k: false};
    for (final d in defaults) {
      if ('${d['role']}' == r)
        out['${d['permission_key']}'] = d['allowed'] == true;
    }
    return out;
  }

  Future<void> load() async {
    if (mounted)
      setState(() {
        loading = true;
        error = null;
      });
    try {
      final r = await Future.wait<dynamic>(
          [api.adminUsersV29(), api.adminPermissionCatalogV29()]);
      final catalog = r[1] as Map<String, dynamic>;
      if (mounted) {
        setState(() {
          users = (r[0] as List<Map<String, dynamic>>);
          keys = ((catalog['keys'] as List?) ?? const [])
              .map((e) => '$e')
              .toList()
            ..sort();
          defaults = _rows(catalog['defaults']);
          loading = false;
        });
      }
    } catch (e) {
      if (mounted)
        setState(() {
          loading = false;
          error = _friendlyError(e);
        });
    }
  }

  List<Map<String, dynamic>> get operationalUnits {
    final out = <Map<String, dynamic>>[];
    for (final m in _rows(widget.referenceData['machines'])) {
      final mid = _intOrNull(m['id']);
      if (mid == null) continue;
      final asset = '${m['numeroAtivo'] ?? ''}'.trim(),
          model = '${m['modelo'] ?? ''}'.trim(),
          plate = '${m['placa'] ?? ''}'.trim();
      out.add({
        'key': 'M:$mid',
        'kind': 'machine',
        'machine_id': mid,
        'tank_id': _intOrNull(m['comboio_tank_id']),
        'label':
            '${asset.isNotEmpty ? asset : 'Ativo $mid'}${model.isNotEmpty ? ' • $model' : ''}${plate.isNotEmpty ? ' • $plate' : ''}'
      });
    }
    for (final t in _rows(widget.referenceData['tanks'])) {
      if ('${t['tank_type']}' != 'stationary' && '${t['tank_type']}' != 'truck')
        continue;
      final tid = _intOrNull(t['id']);
      if (tid == null) continue;
      out.add({
        'key': 'T:$tid',
        'kind': 'tank',
        'machine_id': null,
        'tank_id': tid,
        'label':
            '${t['tank_type'] == 'stationary' ? 'T.E.' : 'Caminhão-tanque'} • ${t['code']} • ${t['name']}'
      });
    }
    out.sort((a, b) =>
        '${a['label']}'.toLowerCase().compareTo('${b['label']}'.toLowerCase()));
    return out;
  }

  String? assignmentKey(Map<String, dynamic> u) {
    final mid = _intOrNull(u['machine_id']);
    if (mid != null) return 'M:$mid';
    final ids = ((u['tank_ids'] as List?) ?? const [])
        .map(_intOrNull)
        .whereType<int>()
        .toSet();
    for (final x in operationalUnits) {
      if (ids.contains(_intOrNull(x['tank_id']))) return '${x['key']}';
    }
    return null;
  }

  Map<String, dynamic> assignmentPayload(String key) {
    final x = operationalUnits.firstWhere((e) => '${e['key']}' == key);
    return x['kind'] == 'machine'
        ? {'machine_id': x['machine_id']}
        : {'tank_id': x['tank_id']};
  }

  String assignmentLabel(Map<String, dynamic> u) {
    final k = assignmentKey(u);
    if (k == null) return 'Sem unidade';
    for (final x in operationalUnits) {
      if ('${x['key']}' == k) return '${x['label']}';
    }
    return 'Sem unidade';
  }

  Future<void> createUser() async {
    final name = TextEditingController(),
        username = TextEditingController(),
        password = TextEditingController();
    String? role;
    final ok = await showDialog<bool>(
        context: context,
        builder: (ctx) => StatefulBuilder(
            builder: (ctx, setD) => AlertDialog(
                  title: const Text('Cadastrar usuário'),
                  content: SizedBox(
                      width: 520,
                      child: SingleChildScrollView(
                          child:
                              Column(mainAxisSize: MainAxisSize.min, children: [
                        TextField(
                            controller: name,
                            decoration:
                                const InputDecoration(labelText: 'Nome *')),
                        const SizedBox(height: 9),
                        TextField(
                            controller: username,
                            decoration: const InputDecoration(
                                labelText: 'Usuário / login *')),
                        const SizedBox(height: 9),
                        TextField(
                            controller: password,
                            obscureText: true,
                            decoration: const InputDecoration(
                                labelText: 'Senha / PIN inicial *')),
                        const SizedBox(height: 9),
                        DropdownButtonFormField<String>(
                            initialValue: role,
                            decoration:
                                const InputDecoration(labelText: 'Função *'),
                            items: const [
                              DropdownMenuItem(
                                  value: 'supervisor',
                                  child: Text('Supervisor')),
                              DropdownMenuItem(
                                  value: 'manager', child: Text('Gerente')),
                              DropdownMenuItem(
                                  value: 'operator', child: Text('Operacional'))
                            ],
                            onChanged: (v) => setD(() => role = v)),
                        if (role == 'operator')
                          const Padding(
                              padding: EdgeInsets.only(top: 10),
                              child: Align(
                                  alignment: Alignment.centerLeft,
                                  child: Text(
                                      'O Operacional escolherá uma unidade disponível ao iniciar o trabalho.',
                                      style: TextStyle(
                                          color: Colors.black54,
                                          fontSize: 12)))),
                        const SizedBox(height: 10),
                        const Align(
                            alignment: Alignment.centerLeft,
                            child: Text(
                                'As permissões individuais são configuradas depois em “Editar usuário”.',
                                style: TextStyle(
                                    color: Colors.black54, fontSize: 12))),
                      ]))),
                  actions: [
                    TextButton(
                        onPressed: () => Navigator.pop(ctx, false),
                        child: const Text('Cancelar')),
                    FilledButton(
                        onPressed: () => Navigator.pop(ctx, true),
                        child: const Text('Cadastrar'))
                  ],
                )));
    if (ok == true) {
      if (name.text.trim().isEmpty ||
          username.text.trim().isEmpty ||
          password.text.trim().length < 4 ||
          role == null) {
        if (mounted)
          ScaffoldMessenger.of(context).showSnackBar(const SnackBar(
              content: Text('Preencha os campos obrigatórios.')));
      } else {
        setState(() => busy = true);
        try {
          if (role == 'operator') {
            await api.operatorUserActionV31({
              'action': 'create_operator',
              'name': name.text.trim(),
              'username': username.text.trim(),
              'password': password.text
            });
          } else {
            await api.userActionMap({
              'action': 'create_manager',
              'name': name.text.trim(),
              'username': username.text.trim(),
              'password': password.text,
              'role': role
            });
          }
          await load();
          if (mounted)
            ScaffoldMessenger.of(context).showSnackBar(const SnackBar(
                content: Text('Usuário cadastrado com sucesso ✓')));
        } catch (e) {
          if (mounted)
            ScaffoldMessenger.of(context).showSnackBar(SnackBar(
                content: Text('Erro ao cadastrar: ${_friendlyError(e)}')));
        } finally {
          if (mounted) setState(() => busy = false);
        }
      }
    }
    name.dispose();
    username.dispose();
    password.dispose();
  }

  Future<void> editUser(Map<String, dynamic> u) async {
    final name = TextEditingController(text: '${u['name'] ?? ''}'),
        username = TextEditingController(text: '${u['username'] ?? ''}'),
        password = TextEditingController();
    final role = '${u['role']}';
    bool active = u['active'] == true;
    Map<String, bool> permissions = <String, bool>{
      for (final k in keys) k: _map(u['permissions'])[k] == true
    };
    final ok = await showDialog<bool>(
        context: context,
        builder: (ctx) => StatefulBuilder(
            builder: (ctx, setD) => AlertDialog(
                  title: const Text('Editar usuário'),
                  content: SizedBox(
                      width: 560,
                      child: SingleChildScrollView(
                          child:
                              Column(mainAxisSize: MainAxisSize.min, children: [
                        TextField(
                            controller: name,
                            decoration:
                                const InputDecoration(labelText: 'Nome *')),
                        const SizedBox(height: 8),
                        TextField(
                            controller: username,
                            decoration: const InputDecoration(
                                labelText: 'Usuário / login *')),
                        const SizedBox(height: 8),
                        TextField(
                            controller: password,
                            obscureText: true,
                            decoration: const InputDecoration(
                                labelText:
                                    'Nova senha / PIN (deixe em branco para manter)')),
                        const SizedBox(height: 8),
                        ListTile(
                            contentPadding: EdgeInsets.zero,
                            leading:
                                const Icon(Icons.badge_outlined, color: _blue),
                            title: const Text('Função'),
                            subtitle: Text(roleLabel(role))),
                        if (role == 'operator')
                          const Align(
                              alignment: Alignment.centerLeft,
                              child: Padding(
                                  padding: EdgeInsets.only(bottom: 8),
                                  child: Text(
                                      'A unidade de abastecimento é escolhida pelo próprio Operacional durante o trabalho.',
                                      style: TextStyle(
                                          color: Colors.black54,
                                          fontSize: 12)))),
                        SwitchListTile(
                            contentPadding: EdgeInsets.zero,
                            title: const Text('Acesso ativo',
                                style: TextStyle(fontWeight: FontWeight.w800)),
                            subtitle: Text(active
                                ? 'Pode fazer login normalmente'
                                : 'Continua cadastrado, mas não pode acessar o sistema'),
                            value: active,
                            onChanged: (v) => setD(() => active = v)),
                        const Divider(height: 24),
                        Row(children: [
                          Expanded(
                              child: Text('Permissões',
                                  style: Theme.of(ctx)
                                      .textTheme
                                      .titleMedium
                                      ?.copyWith(fontWeight: FontWeight.w900))),
                          TextButton(
                              onPressed: () =>
                                  setD(() => permissions = roleDefaults(role)),
                              child: const Text('Usar padrão'))
                        ]),
                        ...keys.map((k) {
                          final ownOnly =
                              role == 'operator' && k == 'movements.view';
                          return SwitchListTile(
                            contentPadding: EdgeInsets.zero,
                            title: Text(_permissionLabelV23(k)),
                            subtitle: ownOnly
                                ? const Text(
                                    'Operacional vê somente os próprios abastecimentos.')
                                : null,
                            value: ownOnly ? false : permissions[k] == true,
                            onChanged: ownOnly
                                ? null
                                : (v) => setD(() => permissions[k] = v),
                          );
                        }),
                      ]))),
                  actions: [
                    TextButton(
                        onPressed: () => Navigator.pop(ctx, false),
                        child: const Text('Cancelar')),
                    FilledButton(
                        onPressed: () => Navigator.pop(ctx, true),
                        child: const Text('Salvar'))
                  ],
                )));
    if (ok == true) {
      if (name.text.trim().isEmpty ||
          username.text.trim().isEmpty ||
          (password.text.isNotEmpty && password.text.length < 4)) {
        if (mounted)
          ScaffoldMessenger.of(context).showSnackBar(
              const SnackBar(content: Text('Confira os campos obrigatórios.')));
      } else {
        setState(() => busy = true);
        try {
          final userId = '${u['user_id']}';
          if (role == 'operator') {
            await api.operatorUserActionV31({
              'action': 'update_operator',
              'user_id': userId,
              'name': name.text.trim(),
              'username': username.text.trim(),
              'password': password.text
            });
            if (active != (u['active'] == true))
              await api.operatorUserActionV31({
                'action': 'set_operator_active',
                'user_id': userId,
                'active': active
              });
          } else {
            await api.userActionMap({
              'action': 'update_manager',
              'user_id': userId,
              'name': name.text.trim(),
              'username': username.text.trim(),
              'password': password.text,
              'role': role
            });
            if (active != (u['active'] == true))
              await api.userActionMap({
                'action': 'set_manager_active',
                'user_id': userId,
                'active': active
              });
          }
          for (final k in keys) {
            final allowed = (role == 'operator' && k == 'movements.view')
                ? false
                : permissions[k] == true;
            await api.adminSetUserPermissionV29(userId, k, allowed);
          }
          await load();
          if (mounted)
            ScaffoldMessenger.of(context).showSnackBar(const SnackBar(
                content: Text('Usuário atualizado com sucesso ✓')));
        } catch (e) {
          if (mounted)
            ScaffoldMessenger.of(context).showSnackBar(SnackBar(
                content: Text('Erro ao salvar: ${_friendlyError(e)}')));
        } finally {
          if (mounted) setState(() => busy = false);
        }
      }
    }
    name.dispose();
    username.dispose();
    password.dispose();
  }

  Future<void> toggleAccess(Map<String, dynamic> u) async {
    setState(() => busy = true);
    try {
      final role = '${u['role']}',
          active = u['active'] != true,
          userId = '${u['user_id']}';
      if (role == 'operator') {
        await api.operatorUserActionV31({
          'action': 'set_operator_active',
          'user_id': userId,
          'active': active
        });
      } else {
        await api.userActionMap({
          'action': 'set_manager_active',
          'user_id': userId,
          'active': active
        });
      }
      await load();
    } catch (e) {
      if (mounted)
        ScaffoldMessenger.of(context)
            .showSnackBar(SnackBar(content: Text(_friendlyError(e))));
    } finally {
      if (mounted) setState(() => busy = false);
    }
  }

  Future<void> disconnectUser(Map<String, dynamic> u) async {
    final ok = await showDialog<bool>(
        context: context,
        builder: (ctx) => AlertDialog(
                title: const Text('Desconectar usuário?'),
                content: Text(
                    'O usuário ${u['name']} será desconectado e a unidade vinculada será liberada. O acesso continuará ativo e ele poderá entrar novamente depois.'),
                actions: [
                  TextButton(
                      onPressed: () => Navigator.pop(ctx, false),
                      child: const Text('Cancelar')),
                  FilledButton(
                      onPressed: () => Navigator.pop(ctx, true),
                      child: const Text('Desconectar'))
                ]));
    if (ok != true) return;
    setState(() => busy = true);
    try {
      final r = await api.adminDisconnectUserV30('${u['user_id']}');
      await load();
      if (mounted)
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(
            content: Text(r['released_tank_id'] != null
                ? 'Usuário desconectado. Unidade liberada ✓'
                : 'Usuário desconectado ✓')));
    } catch (e) {
      if (mounted)
        ScaffoldMessenger.of(context)
            .showSnackBar(SnackBar(content: Text(_friendlyError(e))));
    } finally {
      if (mounted) setState(() => busy = false);
    }
  }

  Future<void> deleteUser(Map<String, dynamic> u) async {
    final ok = await showDialog<bool>(
        context: context,
        builder: (ctx) => AlertDialog(
                title: const Text('Excluir usuário?'),
                content: Text(
                    '${u['name']} perderá o acesso, mas todos os registros, movimentações, correções e assinaturas permanecerão preservados.'),
                actions: [
                  TextButton(
                      onPressed: () => Navigator.pop(ctx, false),
                      child: const Text('Cancelar')),
                  FilledButton(
                      onPressed: () => Navigator.pop(ctx, true),
                      child: const Text('Excluir'))
                ]));
    if (ok != true) return;
    setState(() => busy = true);
    try {
      if ('${u['role']}' == 'operator') {
        await api.userActionMap({
          'action': 'remove_access',
          'user_id': u['user_id'],
          'reason': 'Exclusão pelo Admin'
        });
      } else {
        await api.userActionMap(
            {'action': 'delete_manager', 'user_id': u['user_id']});
      }
      await load();
      if (mounted)
        ScaffoldMessenger.of(context).showSnackBar(const SnackBar(
            content: Text('Acesso removido. Histórico preservado ✓')));
    } catch (e) {
      if (mounted)
        ScaffoldMessenger.of(context)
            .showSnackBar(SnackBar(content: Text(_friendlyError(e))));
    } finally {
      if (mounted) setState(() => busy = false);
    }
  }

  @override
  Widget build(BuildContext context) => Scaffold(
        appBar: AppBar(title: const Text('Usuários')),
        floatingActionButton: FloatingActionButton.extended(
            onPressed: busy || loading ? null : createUser,
            icon: const Icon(Icons.person_add_alt_1_rounded),
            label: const Text('Cadastrar usuário')),
        body: loading
            ? const Center(child: CircularProgressIndicator())
            : error != null
                ? Center(
                    child: Padding(
                        padding: const EdgeInsets.all(24),
                        child:
                            Column(mainAxisSize: MainAxisSize.min, children: [
                          const Icon(Icons.cloud_off_rounded,
                              size: 54, color: _blue),
                          const SizedBox(height: 12),
                          Text(error!, textAlign: TextAlign.center),
                          const SizedBox(height: 12),
                          FilledButton.icon(
                              onPressed: load,
                              icon: const Icon(Icons.refresh_rounded),
                              label: const Text('Tentar novamente'))
                        ])))
                : RefreshIndicator(
                    onRefresh: load,
                    child: ListView(
                        padding: const EdgeInsets.fromLTRB(16, 16, 16, 90),
                        children: [
                          const Card(
                              child: ListTile(
                                  leading: Icon(Icons.people_alt_outlined,
                                      color: _blue),
                                  title: Text('Todos os usuários',
                                      style: TextStyle(
                                          fontWeight: FontWeight.w900)),
                                  subtitle: Text(
                                      'Cadastre Supervisor, Gerente ou Operacional. O Operacional escolhe uma unidade disponível durante o trabalho.'))),
                          if (users!.isEmpty)
                            const Padding(
                                padding: EdgeInsets.all(48),
                                child: Center(
                                    child: Text('Nenhum usuário cadastrado.'))),
                          ...users!.map((u) {
                            final role = '${u['role']}';
                            return Card(
                                child: ListTile(
                                    contentPadding: const EdgeInsets.all(14),
                                    leading: CircleAvatar(
                                        child: Icon(role == 'manager'
                                            ? Icons.manage_accounts_rounded
                                            : role == 'supervisor'
                                                ? Icons
                                                    .supervisor_account_rounded
                                                : Icons.engineering_outlined)),
                                    title: Text('${u['name']}',
                                        style: const TextStyle(
                                            fontWeight: FontWeight.w900)),
                                    subtitle: Text(
                                        '${roleLabel(role)} • ${u['username'] ?? ''}\n${u['active'] == true ? 'Acesso ativo' : 'Acesso bloqueado'}'),
                                    isThreeLine: true,
                                    onTap: busy ? null : () => editUser(u),
                                    trailing: PopupMenuButton<String>(
                                        enabled: !busy,
                                        onSelected: (v) {
                                          if (v == 'edit') editUser(u);
                                          if (v == 'disconnect')
                                            disconnectUser(u);
                                          if (v == 'active') toggleAccess(u);
                                          if (v == 'delete') deleteUser(u);
                                        },
                                        itemBuilder: (_) => [
                                              const PopupMenuItem(
                                                  value: 'edit',
                                                  child: Text(
                                                      'Editar usuário e permissões')),
                                              const PopupMenuItem(
                                                  value: 'disconnect',
                                                  child: Text(
                                                      'Desconectar usuário')),
                                              PopupMenuItem(
                                                  value: 'active',
                                                  child: Text(
                                                      u['active'] == true
                                                          ? 'Bloquear login'
                                                          : 'Liberar login')),
                                              const PopupMenuItem(
                                                  value: 'delete',
                                                  child:
                                                      Text('Excluir usuário'))
                                            ])));
                          }),
                        ])),
      );
}

class OfflineConflictsV58Screen extends StatefulWidget {
  const OfflineConflictsV58Screen({super.key});
  @override
  State<OfflineConflictsV58Screen> createState() =>
      _OfflineConflictsV58ScreenState();
}

class _OfflineConflictsV58ScreenState extends State<OfflineConflictsV58Screen> {
  List<Map<String, dynamic>> items = [];
  List<Map<String, dynamic>> unitItemsV87 = [];
  bool busy = false;
  String? error;
  @override
  void initState() {
    super.initState();
    load();
  }

  Future<void> load() async {
    setState(() {
      busy = true;
      error = null;
    });
    try {
      final values = await Future.wait<dynamic>([
        api.offlineConflictsV58(),
        api.offlineUnitUseConflictsV87(),
      ]);
      if (mounted)
        setState(() {
          items = (values[0] as List).cast<Map<String, dynamic>>();
          unitItemsV87 = (values[1] as List).cast<Map<String, dynamic>>();
        });
    } catch (e) {
      if (mounted) setState(() => error = _friendlyError(e));
    } finally {
      if (mounted) setState(() => busy = false);
    }
  }

  String tank(dynamic id) {
    for (final t in _rows(offlineStore.cachedReferenceData?['tanks'])) {
      if (_intOrNull(t['id']) == _intOrNull(id))
        return '${t['code'] ?? ''}${('${t['name'] ?? ''}'.trim()).isNotEmpty ? ' • ${t['name']}' : ''}';
    }
    return 'Unidade #$id';
  }

  String asset(dynamic id) {
    for (final m in _rows(offlineStore.cachedReferenceData?['machines'])) {
      if (_intOrNull(m['id']) == _intOrNull(id)) {
        final number = '${m['numeroAtivo'] ?? ''}'.trim();
        final model = '${m['modelo'] ?? ''}'.trim();
        return [number, model].where((x) => x.isNotEmpty).join(' • ');
      }
    }
    return id == null ? '-' : 'Ativo #$id';
  }

  String conflictMeasurementTypeV89(Map<String, dynamic> payload) {
    final machineId = _intOrNull(payload['machine_id']);
    if (machineId == null) return '';
    for (final m in _rows(offlineStore.cachedReferenceData?['machines'])) {
      if (_intOrNull(m['id']) == machineId) {
        return '${m['measurement_type'] ?? ''}'.trim().toLowerCase();
      }
    }
    return '';
  }

  Future<void> correctConflictV89(Map<String, dynamic> x) async {
    final p = _map(x['payload']);
    final mt = conflictMeasurementTypeV89(p);
    final liters = TextEditingController(text: '${p['liters'] ?? ''}');
    final km = TextEditingController(
        text: p['km_value'] == null ? '' : '${p['km_value']}');
    final hour = TextEditingController(
        text: p['hourmeter_value'] == null ? '' : '${p['hourmeter_value']}');
    final sale =
        TextEditingController(text: '${p['sale_price_per_liter'] ?? ''}');
    final receiver = TextEditingController(text: '${p['receiver_name'] ?? ''}');
    final fuel = TextEditingController(text: '${p['fuel_type'] ?? ''}');
    final location =
        TextEditingController(text: '${p['location_address'] ?? ''}');
    final notes = TextEditingController(text: '${p['notes'] ?? ''}');
    final reason = TextEditingController();
    bool lubricated = p['lubricated'] == true;
    try {
      final changes = await showDialog<Map<String, dynamic>>(
          context: context,
          builder: (ctx) => StatefulBuilder(builder: (ctx, setLocal) {
                String? invalid() {
                  final l =
                      double.tryParse(liters.text.trim().replaceAll(',', '.'));
                  final s =
                      double.tryParse(sale.text.trim().replaceAll(',', '.'));
                  if (reason.text.trim().isEmpty)
                    return 'Informe o motivo da correção.';
                  if (l == null || l <= 0)
                    return 'Informe uma quantidade válida.';
                  if (s == null || s <= 0)
                    return 'Informe um preço por litro válido.';
                  if ((mt == 'km' || mt == 'both')) {
                    final v =
                        double.tryParse(km.text.trim().replaceAll(',', '.'));
                    if (v == null || v < 0) return 'Informe um KM válido.';
                  }
                  if ((mt == 'hourmeter' || mt == 'both')) {
                    final v =
                        double.tryParse(hour.text.trim().replaceAll(',', '.'));
                    if (v == null || v < 0)
                      return 'Informe um horímetro válido.';
                  }
                  if (receiver.text.trim().isEmpty)
                    return 'Informe quem recebeu.';
                  if (fuel.text.trim().isEmpty) return 'Informe o combustível.';
                  if (location.text.trim().isEmpty)
                    return 'Informe a localização.';
                  return null;
                }

                final error = invalid();
                InputDecoration deco(String label) => InputDecoration(
                    labelText: label, border: const OutlineInputBorder());
                return AlertDialog(
                    title: const Text('Corrigir dados do conflito'),
                    content: SizedBox(
                        width: 560,
                        child: SingleChildScrollView(
                            child: Column(
                                mainAxisSize: MainAxisSize.min,
                                children: [
                              Text('Ativo: ${asset(p['machine_id'])}',
                                  style: const TextStyle(
                                      fontWeight: FontWeight.w800)),
                              const SizedBox(height: 12),
                              TextField(
                                  controller: reason,
                                  onChanged: (_) => setLocal(() {}),
                                  maxLines: 2,
                                  decoration: deco('Motivo da correção *')),
                              const SizedBox(height: 10),
                              TextField(
                                  controller: liters,
                                  onChanged: (_) => setLocal(() {}),
                                  keyboardType:
                                      const TextInputType.numberWithOptions(
                                          decimal: true),
                                  decoration: deco('Quantidade (L) *')),
                              if (mt == 'km' || mt == 'both') ...[
                                const SizedBox(height: 10),
                                TextField(
                                    controller: km,
                                    onChanged: (_) => setLocal(() {}),
                                    keyboardType:
                                        const TextInputType.numberWithOptions(
                                            decimal: true),
                                    decoration: deco('KM *')),
                              ],
                              if (mt == 'hourmeter' || mt == 'both') ...[
                                const SizedBox(height: 10),
                                TextField(
                                    controller: hour,
                                    onChanged: (_) => setLocal(() {}),
                                    keyboardType:
                                        const TextInputType.numberWithOptions(
                                            decimal: true),
                                    decoration: deco('Horímetro *')),
                              ],
                              const SizedBox(height: 10),
                              TextField(
                                  controller: sale,
                                  onChanged: (_) => setLocal(() {}),
                                  keyboardType:
                                      const TextInputType.numberWithOptions(
                                          decimal: true),
                                  decoration: deco('Preço por litro *')),
                              const SizedBox(height: 10),
                              TextField(
                                  controller: receiver,
                                  onChanged: (_) => setLocal(() {}),
                                  decoration:
                                      deco('Responsável pelo recebimento *')),
                              const SizedBox(height: 10),
                              TextField(
                                  controller: fuel,
                                  onChanged: (_) => setLocal(() {}),
                                  decoration: deco('Combustível *')),
                              const SizedBox(height: 10),
                              TextField(
                                  controller: location,
                                  onChanged: (_) => setLocal(() {}),
                                  decoration: deco('Localização *')),
                              const SizedBox(height: 10),
                              TextField(
                                  controller: notes,
                                  onChanged: (_) => setLocal(() {}),
                                  maxLines: 2,
                                  decoration: deco('Observações')),
                              SwitchListTile.adaptive(
                                  contentPadding: EdgeInsets.zero,
                                  title: const Text('Lubrificou?'),
                                  value: lubricated,
                                  onChanged: (v) =>
                                      setLocal(() => lubricated = v)),
                              if (error != null)
                                Align(
                                    alignment: Alignment.centerLeft,
                                    child: Text(error,
                                        style: const TextStyle(
                                            color: Colors.red))),
                            ]))),
                    actions: [
                      TextButton(
                          onPressed: () => Navigator.pop(ctx),
                          child: const Text('Cancelar')),
                      FilledButton(
                          onPressed: error == null
                              ? () => Navigator.pop(ctx, {
                                    'reason': reason.text.trim(),
                                    'changes': <String, dynamic>{
                                      'liters': double.parse(liters.text
                                          .trim()
                                          .replaceAll(',', '.')),
                                      'km_value': (mt == 'km' || mt == 'both')
                                          ? double.parse(km.text
                                              .trim()
                                              .replaceAll(',', '.'))
                                          : null,
                                      'hourmeter_value':
                                          (mt == 'hourmeter' || mt == 'both')
                                              ? double.parse(hour.text
                                                  .trim()
                                                  .replaceAll(',', '.'))
                                              : null,
                                      'sale_price_per_liter': double.parse(sale
                                          .text
                                          .trim()
                                          .replaceAll(',', '.')),
                                      'receiver_name': receiver.text.trim(),
                                      'fuel_type': fuel.text.trim(),
                                      'location_address': location.text.trim(),
                                      'notes': notes.text.trim().isEmpty
                                          ? null
                                          : notes.text.trim(),
                                      'lubricated': lubricated,
                                    }
                                  })
                              : null,
                          child: const Text('Salvar correção')),
                    ]);
              }));
      if (changes == null) return;
      setState(() => busy = true);
      await api.correctOfflineConflictV89(
          _intOrNull(x['id'])!,
          (changes['changes'] as Map).cast<String, dynamic>(),
          '${changes['reason']}');
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(const SnackBar(
            content: Text(
                'Dados corrigidos. Agora confira e aprove ou rejeite o abastecimento.')));
      }
      await load();
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context)
            .showSnackBar(SnackBar(content: Text(_friendlyError(e))));
      }
    } finally {
      liters.dispose();
      km.dispose();
      hour.dispose();
      sale.dispose();
      receiver.dispose();
      fuel.dispose();
      location.dispose();
      notes.dispose();
      reason.dispose();
      if (mounted) setState(() => busy = false);
    }
  }

  Future<void> decide(Map<String, dynamic> x, String decision) async {
    final approve = decision == 'approve';
    final notes = TextEditingController();
    final reviewNote = await showDialog<String>(
        context: context,
        builder: (ctx) => StatefulBuilder(builder: (ctx, setLocal) {
              final valid = notes.text.trim().isNotEmpty;
              return AlertDialog(
                title: Text(approve
                    ? 'Aprovar abastecimento'
                    : 'Rejeitar abastecimento'),
                content: Column(
                    mainAxisSize: MainAxisSize.min,
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(approve
                          ? 'Confirme que as evidências foram analisadas. A decisão ficará registrada permanentemente na auditoria.'
                          : 'O abastecimento não será consolidado. O motivo ficará preservado permanentemente para auditoria.'),
                      const SizedBox(height: 12),
                      TextField(
                          controller: notes,
                          maxLines: 4,
                          onChanged: (_) => setLocal(() {}),
                          decoration: InputDecoration(
                              labelText: 'Observação obrigatória *',
                              hintText: approve
                                  ? 'Ex.: Fotos, localização e totalizador conferidos.'
                                  : 'Ex.: Totalizador incompatível com os demais registros.',
                              errorText: valid
                                  ? null
                                  : 'Informe a justificativa da decisão.')),
                    ]),
                actions: [
                  TextButton(
                      onPressed: () => Navigator.pop(ctx),
                      child: const Text('Cancelar')),
                  FilledButton(
                      onPressed: valid
                          ? () => Navigator.pop(ctx, notes.text.trim())
                          : null,
                      child: Text(approve
                          ? 'Aprovar abastecimento'
                          : 'Rejeitar abastecimento')),
                ],
              );
            }));
    notes.dispose();
    if (reviewNote == null || reviewNote.trim().isEmpty) return;
    try {
      setState(() => busy = true);
      await api.reviewOfflineConflictV58(_intOrNull(x['id'])!, decision,
          notes: reviewNote.trim());
      final offlineEventId = '${x['offline_event_id'] ?? ''}'.trim();
      if (offlineEventId.isNotEmpty) {
        await offlineStore.applyConflictReviewV77(
            offlineEventId, decision, reviewNote.trim());
        if (approve) {
          await offlineStore.retryPending();
        }
      }
      if (mounted)
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(
            content: Text(approve
                ? 'Abastecimento aprovado. A decisão e a justificativa foram registradas.'
                : 'Abastecimento rejeitado. O registro e a justificativa foram preservados para auditoria.')));
      await load();
    } catch (e) {
      if (mounted)
        ScaffoldMessenger.of(context)
            .showSnackBar(SnackBar(content: Text(_friendlyError(e))));
    } finally {
      if (mounted) setState(() => busy = false);
    }
  }

  Future<void> resolveUnitConflictV87(Map<String, dynamic> x) async {
    final notes = TextEditingController();
    try {
      final value = await showDialog<String>(
          context: context,
          builder: (ctx) => StatefulBuilder(builder: (ctx, setLocal) {
                final valid = notes.text.trim().isNotEmpty;
                return AlertDialog(
                    title: const Text('Analisar uso simultâneo offline'),
                    content: Column(
                        mainAxisSize: MainAxisSize.min,
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                              '${x['user_a_name'] ?? 'Usuário A'} e ${x['user_b_name'] ?? 'Usuário B'} selecionaram ${x['unit_code'] ?? tank(x['tank_id'])} em períodos offline sobrepostos.'),
                          const SizedBox(height: 10),
                          const Text(
                              'A trilha permanece intacta. Registre abaixo a conclusão da análise.'),
                          const SizedBox(height: 12),
                          TextField(
                              controller: notes,
                              maxLines: 4,
                              onChanged: (_) => setLocal(() {}),
                              decoration: InputDecoration(
                                  labelText: 'Observação da análise *',
                                  errorText: valid
                                      ? null
                                      : 'Informe a conclusão da análise.')),
                        ]),
                    actions: [
                      TextButton(
                          onPressed: () => Navigator.pop(ctx),
                          child: const Text('Voltar')),
                      FilledButton(
                          onPressed: valid
                              ? () => Navigator.pop(ctx, notes.text.trim())
                              : null,
                          child: const Text('Registrar análise')),
                    ]);
              }));
      if (value == null || value.trim().isEmpty) return;
      setState(() => busy = true);
      await api.reviewOfflineUnitUseConflictV87(
          _intOrNull(x['id'])!, value.trim());
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(const SnackBar(
            content: Text(
                'Análise registrada. As duas trilhas offline foram preservadas na auditoria.')));
      }
      await load();
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context)
            .showSnackBar(SnackBar(content: Text(_friendlyError(e))));
      }
    } finally {
      notes.dispose();
      if (mounted) setState(() => busy = false);
    }
  }

  @override
  Widget build(BuildContext context) => Scaffold(
      appBar: AppBar(title: const Text('Conflitos offline')),
      body: RefreshIndicator(
          onRefresh: load,
          child: ListView(padding: const EdgeInsets.all(12), children: [
            const Card(
                child: ListTile(
                    leading: Icon(Icons.shield_outlined, color: _blue),
                    title: Text('Proteção contra concorrência offline',
                        style: TextStyle(fontWeight: FontWeight.w900)),
                    subtitle: Text(
                        'Registros conflitantes não alteram estoque nem totalizador até revisão.'))),
            if (busy) const LinearProgressIndicator(minHeight: 2),
            if (error != null)
              Padding(
                  padding: const EdgeInsets.all(18),
                  child:
                      Text(error!, style: const TextStyle(color: Colors.red))),
            if (!busy && error == null && items.isEmpty && unitItemsV87.isEmpty)
              const Padding(
                  padding: EdgeInsets.all(40),
                  child: Center(child: Text('Nenhum conflito pendente.'))),
            if (unitItemsV87.isNotEmpty) ...[
              const Padding(
                  padding: EdgeInsets.fromLTRB(4, 16, 4, 6),
                  child: Text('Uso simultâneo da mesma unidade',
                      style: TextStyle(
                          fontSize: 17, fontWeight: FontWeight.w900))),
              ...unitItemsV87.map((x) => Card(
                    color: const Color(0xFFFFF4E5),
                    child: Padding(
                        padding: const EdgeInsets.all(14),
                        child: Column(
                            crossAxisAlignment: CrossAxisAlignment.stretch,
                            children: [
                              Row(children: [
                                const Icon(Icons.people_alt_outlined,
                                    color: Colors.orange),
                                const SizedBox(width: 8),
                                Expanded(
                                    child: Text(
                                        '${x['unit_code'] ?? tank(x['tank_id'])}${_hasValue(x['unit_name']) ? ' • ${x['unit_name']}' : ''}',
                                        style: const TextStyle(
                                            fontWeight: FontWeight.w900))),
                                const Text('OFFLINE',
                                    style: TextStyle(
                                        fontSize: 11,
                                        fontWeight: FontWeight.w900,
                                        color: Colors.orange)),
                              ]),
                              const SizedBox(height: 8),
                              Text(
                                  'Usuário A: ${x['user_a_name'] ?? '-'}\nInício A: ${_fmtDate(x['started_a'])}\nFim A: ${x['ended_a'] == null ? 'não registrado' : _fmtDate(x['ended_a'])}\n\nUsuário B: ${x['user_b_name'] ?? '-'}\nInício B: ${_fmtDate(x['started_b'])}\nFim B: ${x['ended_b'] == null ? 'não registrado' : _fmtDate(x['ended_b'])}'),
                              const SizedBox(height: 8),
                              Text('${x['reason'] ?? ''}',
                                  style: const TextStyle(
                                      fontWeight: FontWeight.w700)),
                              const SizedBox(height: 12),
                              FilledButton.icon(
                                  onPressed: busy
                                      ? null
                                      : () => resolveUnitConflictV87(x),
                                  icon: const Icon(Icons.fact_check_outlined),
                                  label: const Text('Registrar análise')),
                            ])),
                  )),
              const Padding(
                  padding: EdgeInsets.fromLTRB(4, 16, 4, 6),
                  child: Text('Divergências de abastecimento',
                      style: TextStyle(
                          fontSize: 17, fontWeight: FontWeight.w900))),
            ],
            ...items.map((x) {
              final p = _map(x['payload']);
              final mids = (x['conflicting_movement_ids'] is List)
                  ? (x['conflicting_movement_ids'] as List).join(', ')
                  : '${x['conflicting_movement_ids'] ?? ''}';
              return Card(
                  child: Padding(
                      padding: const EdgeInsets.all(14),
                      child: Column(
                          crossAxisAlignment: CrossAxisAlignment.stretch,
                          children: [
                            Row(children: [
                              const Icon(Icons.warning_amber_rounded,
                                  color: Colors.orange),
                              const SizedBox(width: 8),
                              Expanded(
                                  child: Text(tank(x['source_tank_id']),
                                      style: const TextStyle(
                                          fontWeight: FontWeight.w900))),
                              const Text('REVISÃO',
                                  style: TextStyle(
                                      fontSize: 11,
                                      fontWeight: FontWeight.w900,
                                      color: Colors.orange))
                            ]),
                            const SizedBox(height: 8),
                            Text(
                                'Usuário: ${x['user_name'] ?? '-'}\nAtivo: ${asset(p['machine_id'])}\nHorário do abastecimento: ${_fmtDate(x['occurred_at'])}\nVolume: ${_fmtLiters(p['liters'])}\nHorímetro: ${p['hourmeter_value'] ?? '-'}\nKM: ${p['km_value'] ?? '-'}\nLubrificou?: ${p['lubricated'] == true ? 'Sim' : 'Não'}\nLocalização: ${p['location_address'] ?? '-'}\nRegistros concorrentes: ${mids.isEmpty ? '-' : mids}'),
                            const SizedBox(height: 8),
                            Text('${x['reason'] ?? ''}',
                                style: const TextStyle(
                                    fontWeight: FontWeight.w700)),
                            const SizedBox(height: 12),
                            OutlinedButton.icon(
                                onPressed:
                                    busy ? null : () => correctConflictV89(x),
                                icon: const Icon(Icons.edit_outlined),
                                label: const Text(
                                    'Corrigir dados antes da análise')),
                            const SizedBox(height: 8),
                            Row(children: [
                              Expanded(
                                  child: OutlinedButton.icon(
                                      onPressed: busy
                                          ? null
                                          : () => decide(x, 'reject'),
                                      icon: const Icon(Icons.close_rounded),
                                      label: const Text('Rejeitar'))),
                              const SizedBox(width: 8),
                              Expanded(
                                  child: FilledButton.icon(
                                      onPressed: busy
                                          ? null
                                          : () => decide(x, 'approve'),
                                      icon: const Icon(Icons.check_rounded),
                                      label: const Text('Aprovar')))
                            ])
                          ])));
            })
          ])));
}
