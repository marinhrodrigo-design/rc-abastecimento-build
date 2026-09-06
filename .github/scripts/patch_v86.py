from pathlib import Path

main_path = Path('app/lib/main_online.dart')
v29_path = Path('app/lib/v29_features.dart')
main = main_path.read_text()
v29 = v29_path.read_text()

def rep(text, old, new, label):
    if old not in text:
        raise SystemExit(f'v86 patch anchor not found: {label}')
    return text.replace(old, new, 1)

main = rep(main, "Text('v85'", "Text('v86'", 'version')
main = rep(main, "title: const Text('Lubrificação realizada'),", "title: const Text('Lubrificou?'),", 'new Lubrificou')
main = rep(main, "title: const Text('Lubrificado'))," , "title: const Text('Lubrificou?'))," , 'edit Lubrificou')

main = rep(main,
"""      quick(
          Icons.manage_search_rounded,
          'Registro Geral',
          'Histórico e pesquisa',
          () => openRecordsV71(const GeneralRecordsV28Screen())),
      if (isAdmin || isManager)
""",
"""      quick(
          Icons.manage_search_rounded,
          'Registro Geral',
          'Histórico e pesquisa',
          () => openRecordsV71(const GeneralRecordsV28Screen())),
      if (canCorrect)
        quick(
            Icons.rule_folder_outlined,
            'Pendências / conflitos',
            'Abastecimentos aguardando análise',
            () => open(const OfflineConflictsV58Screen())),
      if (isAdmin || isManager)
""", 'admin conflict tile')

main = rep(main,
"""        actions: [
          if (fueling && canEdit && _intOrNull(item['id']) != null)
""",
"""        actions: [
          if (fueling)
            Padding(
                padding: const EdgeInsets.symmetric(horizontal: 6),
                child: Center(
                    child: Text('Nº ${_recordSequenceV28(item)}',
                        style: const TextStyle(
                            color: Color(0xFFD51F2A),
                            fontWeight: FontWeight.w900)))),
          if (fueling && canEdit && _intOrNull(item['id']) != null)
""", 'detail red sequence')

main = rep(main,
"""  Widget build(BuildContext context) => Scaffold(
      appBar: AppBar(title: const Text('Editar / corrigir abastecimento')),
      body: loading
""",
"""  Widget build(BuildContext context) => Scaffold(
      appBar: AppBar(
          title: const Text('Editar / corrigir abastecimento'),
          actions: [
            Padding(
                padding: const EdgeInsets.symmetric(horizontal: 12),
                child: Center(
                    child: Text('Nº ${_recordSequenceV28(widget.item)}',
                        style: const TextStyle(
                            color: Color(0xFFD51F2A),
                            fontSize: 17,
                            fontWeight: FontWeight.w900))))
          ]),
      body: loading
""", 'edit red sequence')

main = rep(main,
"""                            label: Text(
                                '${_recordOriginV28(item)} • Nº: ${_recordSequenceV28(item)}',
                                style: const TextStyle(
                                    fontWeight: FontWeight.w800)),
""",
"""                            label: Text.rich(TextSpan(children: [
                              TextSpan(
                                  text: '${_recordOriginV28(item)} • Nº: ',
                                  style: const TextStyle(
                                      fontWeight: FontWeight.w800)),
                              TextSpan(
                                  text: _recordSequenceV28(item),
                                  style: const TextStyle(
                                      color: Color(0xFFD51F2A),
                                      fontWeight: FontWeight.w900))
                            ])),
""", 'general red sequence')

v29 = rep(v29,
"""                                const SizedBox(height: 10),
                                Text(
                                    '${_fmtDate(x['occurred_at'] ?? x['created_at'])}\\n${x['work'] ?? 'Sem obra'} • ${_fmtLiters(x['liters'])}\\n${x['fuel_type'] ?? 'Combustível'} • Origem: $sourceText'),
""",
"""                                const SizedBox(height: 8),
                                Text(
                                    '${_recordOriginV28(x)} • Nº ${_recordSequenceV28(x)}',
                                    style: const TextStyle(
                                        color: Color(0xFFD51F2A),
                                        fontSize: 18,
                                        fontWeight: FontWeight.w900)),
                                const SizedBox(height: 8),
                                Text(
                                    '${_fmtDate(x['occurred_at'] ?? x['created_at'])}\\n${x['work'] ?? 'Sem obra'} • ${_fmtLiters(x['liters'])}\\n${x['fuel_type'] ?? 'Combustível'} • Origem: $sourceText'),
""", 'pending red sequence')

v29 = rep(v29,
"""                        title: Text('Abastecimento • $assetText',
                            style:
                                const TextStyle(fontWeight: FontWeight.w900)),
""",
"""                        title: Column(
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
""", 'final red sequence')

v29 = rep(v29,
"""  String tank(dynamic id) {
    for (final t in _rows(offlineStore.cachedReferenceData?['tanks'])) {
      if (_intOrNull(t['id']) == _intOrNull(id))
        return '${t['code'] ?? ''}${('${t['name'] ?? ''}'.trim()).isNotEmpty ? ' • ${t['name']}' : ''}';
    }
    return 'Unidade #$id';
  }

  Future<void> decide""",
"""  String tank(dynamic id) {
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

  Future<void> decide""", 'conflict asset helper')

v29 = rep(v29,
"""                            Text(
                                'Usuário: ${x['user_name'] ?? '-'}\\nHorário do abastecimento: ${_fmtDate(x['occurred_at'])}\\nVolume: ${_fmtLiters(p['liters'])}\\nLocalização: ${p['location_address'] ?? '-'}\\nRegistros concorrentes: ${mids.isEmpty ? '-' : mids}'),
""",
"""                            Text(
                                'Usuário: ${x['user_name'] ?? '-'}\\nAtivo: ${asset(p['machine_id'])}\\nHorário do abastecimento: ${_fmtDate(x['occurred_at'])}\\nVolume: ${_fmtLiters(p['liters'])}\\nHorímetro: ${p['hourmeter_value'] ?? '-'}\\nKM: ${p['km_value'] ?? '-'}\\nLubrificou?: ${p['lubricated'] == true ? 'Sim' : 'Não'}\\nLocalização: ${p['location_address'] ?? '-'}\\nRegistros concorrentes: ${mids.isEmpty ? '-' : mids}'),
""", 'conflict detail')

main_path.write_text(main)
v29_path.write_text(v29)
