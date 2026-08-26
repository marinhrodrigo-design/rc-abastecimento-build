import 'package:file_picker/file_picker.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:url_launcher/url_launcher.dart';

import 'advanced_insights.dart';
import 'data_import.dart';
import 'data_store.dart';
import 'intelligence_engine.dart';
import 'models.dart';
import 'notifications.dart';
import 'oem_catalog.dart';
import 'oem_maintenance.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  final store = DataStore();
  await store.load();
  final notifications = IntelligenceNotifications();
  await notifications.initialize();
  runApp(RCIntelligenceApp(store: store, notifications: notifications));
}

class RCIntelligenceApp extends StatelessWidget {
  const RCIntelligenceApp({
    super.key,
    required this.store,
    required this.notifications,
  });

  final DataStore store;
  final IntelligenceNotifications notifications;

  @override
  Widget build(BuildContext context) => MaterialApp(
        debugShowCheckedModeBanner: false,
        title: 'R&C Intelligence v6',
        theme: ThemeData(
          colorScheme: ColorScheme.fromSeed(seedColor: const Color(0xFF075EA8)),
          useMaterial3: true,
        ),
        home: HomePage(store: store, notifications: notifications),
      );
}

class HomePage extends StatefulWidget {
  const HomePage({
    super.key,
    required this.store,
    required this.notifications,
  });

  final DataStore store;
  final IntelligenceNotifications notifications;

  @override
  State<HomePage> createState() => _HomePageState();
}

class _HomePageState extends State<HomePage> {
  int index = 0;
  final importService = DataImportService();
  final oem = OemCatalogService();
  late final IntelligenceEngine engine = IntelligenceEngine(widget.store);
  late final AdvancedInsightsService insights = AdvancedInsightsService(widget.store);
  final importMessages = <String>[];

  @override
  Widget build(BuildContext context) {
    final pages = [
      _dashboard(),
      _assets(),
      _dataCenter(),
      _oemLibrary(),
      _alerts(),
    ];
    return Scaffold(
      appBar: AppBar(
        title: const Text('R&C Intelligence • SIMULADOR v6'),
        actions: [
          Padding(
            padding: const EdgeInsets.only(right: 12),
            child: Chip(
              label: Text(
                '${widget.store.learningRules.where((r) => r.confirmed).length} regras aprendidas',
              ),
            ),
          ),
        ],
      ),
      body: pages[index],
      bottomNavigationBar: NavigationBar(
        selectedIndex: index,
        onDestinationSelected: (v) => setState(() => index = v),
        destinations: const [
          NavigationDestination(icon: Icon(Icons.insights), label: 'Intelligence'),
          NavigationDestination(icon: Icon(Icons.precision_manufacturing), label: 'Ativos'),
          NavigationDestination(icon: Icon(Icons.storage), label: 'Central de Dados'),
          NavigationDestination(icon: Icon(Icons.menu_book), label: 'OEM'),
          NavigationDestination(icon: Icon(Icons.notifications_active), label: 'Alertas'),
        ],
      ),
    );
  }

  Widget _dashboard() {
    final open = widget.store.anomalies.where((a) => !a.resolved).length;
    final questions = widget.store.anomalies
        .where((a) => !a.resolved && a.needsConfirmation)
        .length;
    final lastAnalysisText = widget.store.rule('system:last_analysis')?.value;
    final lastAnalysis = DateTime.tryParse(lastAnalysisText ?? '') ??
        DateTime.now().subtract(const Duration(days: 3650));
    final changes = insights.changesSince(lastAnalysis);

    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        const Text(
          'O Intelligence compara dados, procura padrões e aprende com suas confirmações.',
          style: TextStyle(fontSize: 18, fontWeight: FontWeight.w600),
        ),
        const SizedBox(height: 12),
        Wrap(
          spacing: 10,
          runSpacing: 10,
          children: [
            _metric('Ativos', '${widget.store.assets.length}', Icons.precision_manufacturing),
            _metric('Anomalias abertas', '$open', Icons.warning_amber),
            _metric('Dúvidas para você', '$questions', Icons.help_outline),
            _metric(
              'Regras confirmadas',
              '${widget.store.learningRules.where((r) => r.confirmed).length}',
              Icons.psychology,
            ),
          ],
        ),
        const SizedBox(height: 18),
        FilledButton.icon(
          onPressed: _runAnalysis,
          icon: const Icon(Icons.psychology_alt),
          label: const Text('Executar análise agora'),
        ),
        const SizedBox(height: 12),
        Card(
          child: ListTile(
            leading: const Icon(Icons.update),
            title: const Text('O que mudou desde a última análise?'),
            subtitle: Text(
              changes.newAnomalies == 0
                  ? 'Nenhuma novidade detectada desde a última análise registrada.'
                  : '${changes.newAnomalies} novidade(s), sendo ${changes.newQuestions} dúvida(s) para confirmação.\n${changes.summary.join('\n')}',
            ),
          ),
        ),
        const Card(
          child: Padding(
            padding: EdgeInsets.all(16),
            child: Text(
              'Princípio de raciocínio: uma peça usada é evidência de intervenção. O Intelligence só chama de defeito confirmado quando O.S., providência, histórico ou outra evidência sustentarem a conclusão.',
            ),
          ),
        ),
        const Card(
          child: ListTile(
            leading: Icon(Icons.event_available),
            title: Text('Previsão preventiva OEM'),
            subtitle: Text(
              'Regra OEM confirmada + Horímetro/Km + ritmo real de uso. A previsão inclui faixa de datas, confiança e alertas 250/100/50/10 h.',
            ),
          ),
        ),
        const Card(
          child: ListTile(
            leading: Icon(Icons.inventory_2_outlined),
            title: Text('Estoque fora do Intelligence v6'),
            subtitle: Text(
              'A preparação preventiva mostra itens OEM e itens históricos, mas não consulta disponibilidade. O estoque ficará para um app próprio.',
            ),
          ),
        ),
      ],
    );
  }

  Widget _metric(String title, String value, IconData icon) => SizedBox(
        width: 175,
        child: Card(
          child: Padding(
            padding: const EdgeInsets.all(14),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Icon(icon),
                const SizedBox(height: 8),
                Text(value, style: const TextStyle(fontSize: 26, fontWeight: FontWeight.bold)),
                Text(title),
              ],
            ),
          ),
        ),
      );

  Widget _assets() => ListView.builder(
        padding: const EdgeInsets.all(12),
        itemCount: widget.store.assets.length,
        itemBuilder: (context, i) {
          final a = widget.store.assets[i];
          final catalog = oem.match(a);
          final confidence = insights.confidenceForAsset(a.id);
          return Card(
            child: ListTile(
              title: Text('${a.id} • ${a.brand} ${a.model}'.trim()),
              subtitle: Text(
                '${a.description}\nSérie/Chassi: ${a.serial.isEmpty ? 'Vazio' : a.serial} • Confiança: ${confidence.label} ${(confidence.score * 100).round()}%',
              ),
              isThreeLine: true,
              trailing: IconButton(
                icon: const Icon(Icons.edit),
                onPressed: () => _editAsset(a),
              ),
              onTap: () => _showAsset(a, catalog),
            ),
          );
        },
      );

  Widget _dataCenter() => ListView(
        padding: const EdgeInsets.all(16),
        children: [
          const Text('Central de Dados', style: TextStyle(fontSize: 24, fontWeight: FontWeight.bold)),
          const SizedBox(height: 8),
          const Text(
            'Importe a Relação de Ativos. Valores originais são preservados e conflitos devem ser corrigidos manualmente.',
          ),
          const SizedBox(height: 12),
          FilledButton.icon(
            onPressed: _importAssets,
            icon: const Icon(Icons.upload_file),
            label: const Text('Importar e analisar planilha XLSX'),
          ),
          const SizedBox(height: 8),
          const Card(
            child: ListTile(
              leading: Icon(Icons.rule),
              title: Text('Conflitos para correção'),
              subtitle: Text(
                'Leituras regressivas, valores divergentes entre fontes e unidades ambíguas não são corrigidos silenciosamente.',
              ),
            ),
          ),
          ...importMessages.map(
            (m) => ListTile(leading: const Icon(Icons.info_outline), title: Text(m)),
          ),
        ],
      );

  Widget _oemLibrary() => ListView.builder(
        padding: const EdgeInsets.all(12),
        itemCount: widget.store.assets.length,
        itemBuilder: (context, i) {
          final a = widget.store.assets[i];
          final usages = widget.store.partUsages.where((p) => p.assetId == a.id).toList()
            ..sort((x, y) => y.date.compareTo(x.date));
          final part = usages.isEmpty ? null : usages.first;
          final match = oem.match(a, partReference: part?.reference ?? '');
          final maintenanceRules = engine.oemRulesForAsset(a);
          final forecasts = engine.oemItemForecastsForAsset(a);
          return Card(
            child: ExpansionTile(
              title: Text('${a.id} • ${a.brand} ${a.model}'),
              subtitle: Text(match.status),
              childrenPadding: const EdgeInsets.fromLTRB(16, 0, 16, 14),
              children: [
                Align(
                  alignment: Alignment.centerLeft,
                  child: Text('Série: ${a.serial.isEmpty ? 'não informada' : a.serial}'),
                ),
                Align(alignment: Alignment.centerLeft, child: Text('Fonte: ${match.provider}')),
                Align(alignment: Alignment.centerLeft, child: Text(match.notes)),
                const Divider(),
                if (maintenanceRules.isEmpty)
                  const Align(
                    alignment: Alignment.centerLeft,
                    child: Text('Regra de manutenção OEM: ainda não confirmada para este modelo/série.'),
                  )
                else
                  ...maintenanceRules.map((rule) => _oemRuleTile(a, rule, forecasts)),
                if (part != null) ...[
                  const Divider(),
                  Align(
                    alignment: Alignment.centerLeft,
                    child: Text('Peça mais recente: ${part.partName} • Ref. ${part.reference}'),
                  ),
                ],
                const SizedBox(height: 10),
                Wrap(
                  spacing: 8,
                  runSpacing: 8,
                  children: [
                    OutlinedButton.icon(
                      onPressed: match.catalogUrl.isEmpty ? null : () => _openUrl(match.catalogUrl),
                      icon: const Icon(Icons.open_in_new),
                      label: const Text('Abrir catálogo OEM'),
                    ),
                    if (match.partUrl != null)
                      FilledButton.icon(
                        onPressed: () => _openUrl(match.partUrl!),
                        icon: const Icon(Icons.build_circle_outlined),
                        label: const Text('Abrir peça no catálogo'),
                      ),
                    if (part != null && part.reference.isNotEmpty)
                      TextButton.icon(
                        onPressed: () async {
                          await Clipboard.setData(ClipboardData(text: part.reference));
                          if (mounted) {
                            ScaffoldMessenger.of(context).showSnackBar(
                              const SnackBar(content: Text('Referência copiada.')),
                            );
                          }
                        },
                        icon: const Icon(Icons.copy),
                        label: const Text('Copiar referência'),
                      ),
                  ],
                ),
              ],
            ),
          );
        },
      );

  Widget _oemRuleTile(
    Asset asset,
    OemMaintenanceRule rule,
    List<OemMaintenanceForecast> forecasts,
  ) {
    OemMaintenanceForecast? forecast;
    for (final value in forecasts) {
      if (value.rule.id == rule.id) forecast = value;
    }
    final intervalText = rule.interval == rule.interval.roundToDouble()
        ? rule.interval.round().toString()
        : rule.interval.toStringAsFixed(1).replaceAll('.', ',');
    final unit = rule.unit == 'H' ? 'h' : 'km';
    final range = forecast == null
        ? null
        : insights.forecastRange(
            forecast: forecast,
            averagePerDay: engine.averageUsage(asset.id, 90),
            assetId: asset.id,
          );
    return Padding(
      padding: const EdgeInsets.only(bottom: 10),
      child: Align(
        alignment: Alignment.centerLeft,
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              '${rule.fullPreventive ? 'Revisão preventiva OEM' : rule.serviceName}: a cada $intervalText $unit',
              style: const TextStyle(fontWeight: FontWeight.w600),
            ),
            Text(rule.evidence),
            if (forecast != null) ...[
              Text(forecast.userMessage),
              if (range != null) Text('Faixa provável: ${range.text} • confiança ${range.confidence.label}.'),
              if (forecast.levelCode != 'MONITOR')
                Text(
                  forecast.remaining < 0
                      ? '${forecast.levelEmoji} ${forecast.levelLabel}: intervalo ultrapassado'
                      : '${forecast.levelEmoji} ${forecast.levelLabel}: faltam ${forecast.remainingText}',
                  style: const TextStyle(fontWeight: FontWeight.bold),
                ),
              if (!forecast.baselineConfirmed)
                const Text(
                  'Última execução OEM ainda não confirmada; o Intelligence pedirá confirmação antes de classificar como vencida.',
                ),
            ] else
              const Text('Sem Horímetro/Km confiável suficiente para calcular a previsão.'),
            TextButton.icon(
              onPressed: () => _openUrl(rule.sourceUrl),
              icon: const Icon(Icons.description_outlined),
              label: const Text('Abrir fonte OEM'),
            ),
          ],
        ),
      ),
    );
  }

  Widget _alerts() {
    final values = [...widget.store.anomalies]
      ..sort((a, b) => b.createdAt.compareTo(a.createdAt));
    if (values.isEmpty) {
      return const Center(child: Text('Nenhuma anomalia detectada ainda.'));
    }
    return ListView.builder(
      padding: const EdgeInsets.all(12),
      itemCount: values.length,
      itemBuilder: (context, i) {
        final a = values[i];
        return Card(
          child: ListTile(
            leading: Icon(a.needsConfirmation ? Icons.help : Icons.warning_amber),
            title: Text(
              a.title,
              style: TextStyle(decoration: a.resolved ? TextDecoration.lineThrough : null),
            ),
            subtitle: Text(a.message),
            trailing: a.resolved ? const Icon(Icons.check_circle) : const Icon(Icons.chevron_right),
            onTap: a.resolved ? null : () => _handleAlert(a),
          ),
        );
      },
    );
  }

  Future<void> _runAnalysis() async {
    final found = engine.analyzeAll();
    var added = 0;
    for (final a in found) {
      if (insights.isSuppressed(a)) continue;
      final exists = widget.store.anomalies.any((x) => x.id == a.id);
      if (!exists) {
        await widget.store.addAnomaly(a);
        await widget.notifications.showAnomaly(a);
        added++;
      }
    }
    await widget.store.learn(
      LearningRule(
        key: 'system:last_analysis',
        value: DateTime.now().toIso8601String(),
        reason: 'Marcador interno para mostrar apenas mudanças desde a última análise.',
        updatedAt: DateTime.now(),
        confidence: 1,
        confirmed: true,
      ),
    );
    if (mounted) {
      setState(() {});
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(
            added == 0
                ? 'Análise concluída. Nenhuma nova anomalia.'
                : '$added nova(s) anomalia(s) detectada(s).',
          ),
        ),
      );
    }
  }

  Future<void> _importAssets() async {
    final result = await FilePicker.platform.pickFiles(
      type: FileType.custom,
      allowedExtensions: ['xlsx'],
      withData: true,
    );
    if (result == null || result.files.single.bytes == null) return;
    try {
      final parsed = importService.parseAssets(result.files.single.bytes!);
      await widget.store.importAssetsBatch(parsed.assets);
      importMessages
        ..clear()
        ..add('Importados/atualizados: ${parsed.assets.length} ativos.')
        ..addAll(parsed.conflicts.map((e) => 'CONFLITO: $e'))
        ..addAll(parsed.notes);
      setState(() {});
    } catch (e) {
      setState(() => importMessages
        ..clear()
        ..add('Falha ao ler a planilha: $e'));
    }
  }

  Future<void> _editAsset(Asset a) async {
    final brand = TextEditingController(text: a.brand);
    final model = TextEditingController(text: a.model);
    final year = TextEditingController(text: a.year);
    final serial = TextEditingController(text: a.serial);
    final plate = TextEditingController(text: a.plate);
    final saved = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: Text('Editar ${a.id}'),
        content: SingleChildScrollView(
          child: Column(
            children: [
              TextField(controller: brand, decoration: const InputDecoration(labelText: 'Marca')),
              TextField(controller: model, decoration: const InputDecoration(labelText: 'Modelo')),
              TextField(controller: year, decoration: const InputDecoration(labelText: 'Ano')),
              TextField(controller: serial, decoration: const InputDecoration(labelText: 'Chassi / Série')),
              TextField(controller: plate, decoration: const InputDecoration(labelText: 'Placa')),
            ],
          ),
        ),
        actions: [
          TextButton(onPressed: () => Navigator.pop(context, false), child: const Text('Cancelar')),
          FilledButton(onPressed: () => Navigator.pop(context, true), child: const Text('Salvar')),
        ],
      ),
    );
    if (saved == true) {
      await widget.store.updateAsset(
        a.copyWith(
          brand: brand.text.trim(),
          model: model.text.trim(),
          year: year.text.trim(),
          serial: serial.text.trim(),
          plate: plate.text.trim(),
        ),
      );
      setState(() {});
    }
  }

  void _showAsset(Asset a, CatalogMatch catalog) {
    final avg30 = engine.averageUsage(a.id, 30);
    final avg90 = engine.averageUsage(a.id, 90);
    final preventive = engine.oemPreventiveForecastForAsset(a);
    final itemForecasts = engine.oemItemForecastsForAsset(a);
    final rules = engine.oemRulesForAsset(a);
    final confidence = insights.confidenceForAsset(a.id);
    final health = insights.healthForAsset(a.id);
    final benchmark = insights.compareWithPeers(a);
    final risk = insights.futureRisk(a.id);
    final preparation = insights.preventivePreparation(asset: a, oemRules: rules);
    final incomplete = insights.maintenanceCompletenessQuestions(a);
    final partLife = insights.partLife(a.id);
    final next = insights.nextAction(asset: a, oemForecast: preventive ?? (itemForecasts.isEmpty ? null : itemForecasts.first));
    final forecastForRange = preventive ?? (itemForecasts.isEmpty ? null : itemForecasts.first);
    final range = forecastForRange == null
        ? null
        : insights.forecastRange(
            forecast: forecastForRange,
            averagePerDay: avg90,
            assetId: a.id,
          );

    showModalBottomSheet(
      context: context,
      showDragHandle: true,
      isScrollControlled: true,
      builder: (context) => SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(18),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                '${a.id} • ${a.brand} ${a.model}',
                style: const TextStyle(fontSize: 20, fontWeight: FontWeight.bold),
              ),
              Text('Ano: ${a.year.isEmpty ? 'Vazio' : a.year}'),
              Text('Série/Chassi: ${a.serial.isEmpty ? 'Vazio' : a.serial}'),
              Text(
                'Média 30 dias: ${avg30 == 0 ? 'dados insuficientes' : avg30.toStringAsFixed(1)} ${a.meterType == 'KM' ? 'km/dia' : 'h/dia'}',
              ),
              const SizedBox(height: 8),
              Card(
                child: ListTile(
                  leading: const Icon(Icons.verified_user_outlined),
                  title: Text('Confiança ${confidence.label} • ${(confidence.score * 100).round()}%'),
                  subtitle: Text(confidence.reasons.join('\n')),
                ),
              ),
              Card(
                child: ListTile(
                  leading: const Icon(Icons.task_alt),
                  title: const Text('Próxima ação recomendada'),
                  subtitle: Text(next),
                ),
              ),
              if (preventive != null) ...[
                const Divider(),
                Text(preventive.userMessage, style: const TextStyle(fontWeight: FontWeight.w600)),
                if (range != null) Text('Faixa provável: ${range.text} • confiança ${range.confidence.label}.'),
                if (preventive.levelCode != 'MONITOR')
                  Text(
                    preventive.remaining < 0
                        ? '${preventive.levelEmoji} ${preventive.levelLabel}: intervalo ultrapassado'
                        : '${preventive.levelEmoji} ${preventive.levelLabel}: faltam ${preventive.remainingText}',
                    style: const TextStyle(fontWeight: FontWeight.bold),
                  ),
              ] else if (rules.isNotEmpty) ...[
                const Divider(),
                const Text(
                  'Regra OEM completa da preventiva ainda não confirmada. Itens OEM confirmados:',
                  style: TextStyle(fontWeight: FontWeight.w600),
                ),
                for (final forecast in itemForecasts)
                  Text('${forecast.rule.serviceName}: ${forecast.targetText} • ${forecast.estimatedDateText}'),
                if (range != null) Text('Faixa provável do próximo item OEM: ${range.text}.'),
              ],
              const Divider(),
              Text('Saúde mais crítica: ${health.isEmpty ? 'dados insuficientes' : '${health.first.system} • ${health.first.status}'}'),
              Text('Comparação: ${benchmark.summary}'),
              Text('Risco futuro: ${risk.level} • ${risk.message}'),
              if (partLife.isNotEmpty)
                Text(
                  'Vida observada: ${partLife.first.partName} / ${partLife.first.reference} reapareceu após ${partLife.first.days} dias${partLife.first.meterDelta == null ? '' : ' e ${partLife.first.meterDelta!.toStringAsFixed(1)} ${a.meterType == 'KM' ? 'km' : 'h'}'}.',
                ),
              const SizedBox(height: 10),
              Wrap(
                spacing: 8,
                runSpacing: 8,
                children: [
                  OutlinedButton.icon(
                    onPressed: () => _showHealth(a, health),
                    icon: const Icon(Icons.monitor_heart_outlined),
                    label: const Text('Saúde por sistemas'),
                  ),
                  OutlinedButton.icon(
                    onPressed: () => _showTimeline(a),
                    icon: const Icon(Icons.timeline),
                    label: const Text('Linha do tempo'),
                  ),
                  OutlinedButton.icon(
                    onPressed: () => _showBenchmark(a, benchmark),
                    icon: const Icon(Icons.compare_arrows),
                    label: const Text('Comparar semelhantes'),
                  ),
                  OutlinedButton.icon(
                    onPressed: () => _showPreparation(a, preparation),
                    icon: const Icon(Icons.fact_check_outlined),
                    label: const Text('Preparar preventiva'),
                  ),
                  OutlinedButton.icon(
                    onPressed: () => _showPartLife(a, partLife),
                    icon: const Icon(Icons.history),
                    label: const Text('Vida das peças'),
                  ),
                  OutlinedButton.icon(
                    onPressed: () => _showCompleteness(a, incomplete),
                    icon: const Icon(Icons.rule_folder_outlined),
                    label: const Text('Revisar completude'),
                  ),
                  FilledButton.icon(
                    onPressed: catalog.catalogUrl.isEmpty ? null : () => _openUrl(catalog.catalogUrl),
                    icon: const Icon(Icons.menu_book),
                    label: const Text('Abrir catálogo OEM'),
                  ),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }

  void _showHealth(Asset a, List<SystemHealth> values) {
    _showInfoDialog(
      'Saúde por sistemas • ${a.id}',
      values
          .map((v) => '${v.system}: ${v.status} (${v.score}/100)\n${v.evidence.join(' ')}')
          .join('\n\n'),
    );
  }

  void _showTimeline(Asset a) {
    final values = insights.timeline(a.id);
    _showInfoDialog(
      'Linha do tempo inteligente • ${a.id}',
      values.isEmpty
          ? 'Ainda não há eventos suficientes.'
          : values.take(80).map((e) => '${_date(e.date)} • ${e.kind}\n${e.title}\n${e.detail}').join('\n\n'),
    );
  }

  void _showBenchmark(Asset a, PeerBenchmark benchmark) {
    _showInfoDialog(
      'Comparação entre ativos iguais • ${a.id}',
      '${benchmark.summary}\n\nPares comparados: ${benchmark.peerCount}\nIntervenções do ativo no período: ${benchmark.assetRate.toStringAsFixed(0)}\nMédia dos pares: ${benchmark.peerAverage.toStringAsFixed(1)}',
    );
  }

  void _showPreparation(Asset a, PreventivePreparation preparation) {
    final oemText = preparation.oemItems.isEmpty
        ? 'Nenhum item OEM confirmado para esta preventiva.'
        : preparation.oemItems.map((e) => '• $e').join('\n');
    final historicalText = preparation.historicalItems.isEmpty
        ? 'Histórico ainda insuficiente.'
        : preparation.historicalItems.map((e) => '• $e').join('\n');
    _showInfoDialog(
      'Preparação automática • ${a.id}',
      'OEM confirmado:\n$oemText\n\nHistoricamente utilizado em ativos iguais:\n$historicalText\n\n${preparation.notes.join('\n')}',
    );
  }

  void _showPartLife(Asset a, List<PartLifeObservation> values) {
    _showInfoDialog(
      'Vida observada das peças • ${a.id}',
      values.isEmpty
          ? 'Ainda não há repetição suficiente da mesma referência para estimar vida observada.'
          : values
              .take(20)
              .map((v) => '${v.partName} • ${v.reference}: ${v.days} dias${v.meterDelta == null ? '' : ' • ${v.meterDelta!.toStringAsFixed(1)} ${a.meterType == 'KM' ? 'km' : 'h'}'}')
              .join('\n\n'),
    );
  }

  void _showCompleteness(Asset a, List<String> questions) {
    _showInfoDialog(
      'Manutenção aparentemente incompleta • ${a.id}',
      questions.isEmpty
          ? 'Não há evidência suficiente para apontar uma manutenção aparentemente incompleta.'
          : 'Estas são perguntas, não acusações de erro:\n\n${questions.map((e) => '• $e').join('\n\n')}',
    );
  }

  void _showInfoDialog(String title, String text) {
    showDialog<void>(
      context: context,
      builder: (context) => AlertDialog(
        title: Text(title),
        content: SingleChildScrollView(child: SelectableText(text)),
        actions: [TextButton(onPressed: () => Navigator.pop(context), child: const Text('Fechar'))],
      ),
    );
  }

  Future<void> _handleAlert(Anomaly a) async {
    final choice = await showModalBottomSheet<String>(
      context: context,
      showDragHandle: true,
      builder: (context) => SafeArea(
        child: Wrap(
          children: [
            ListTile(
              leading: const Icon(Icons.psychology_alt),
              title: const Text('Ver raciocínio'),
              subtitle: const Text('Mostra evidências, confiança e por que o alerta foi criado.'),
              onTap: () => Navigator.pop(context, 'reason'),
            ),
            if (a.needsConfirmation)
              ListTile(
                leading: const Icon(Icons.school_outlined),
                title: const Text('Confirmar e ensinar'),
                onTap: () => Navigator.pop(context, 'confirm'),
              )
            else
              ListTile(
                leading: const Icon(Icons.check),
                title: const Text('Marcar como tratado'),
                onTap: () => Navigator.pop(context, 'resolve'),
              ),
            ListTile(
              leading: const Icon(Icons.thumb_down_alt_outlined),
              title: const Text('Não é anomalia'),
              subtitle: const Text('Registra este alerta como falso positivo.'),
              onTap: () => Navigator.pop(context, 'reject'),
            ),
            ListTile(
              leading: const Icon(Icons.notifications_off_outlined),
              title: const Text('Não avisar neste contexto'),
              subtitle: const Text('Aprende uma regra de supressão para casos equivalentes.'),
              onTap: () => Navigator.pop(context, 'suppress'),
            ),
          ],
        ),
      ),
    );
    if (choice == null) return;
    if (choice == 'reason') {
      _showInfoDialog('Por que o Intelligence está dizendo isso?', '${a.message}\n\n${insights.explainAnomaly(a)}');
      return;
    }
    if (choice == 'resolve') {
      await widget.store.resolveAnomaly(a.id);
      setState(() {});
      return;
    }
    if (choice == 'reject') {
      await widget.store.learn(
        LearningRule(
          key: 'feedback:not_anomaly:${a.id}',
          value: 'NAO_E_ANOMALIA',
          reason: 'Administrador rejeitou este alerta como falso positivo.',
          updatedAt: DateTime.now(),
          confidence: 1,
          confirmed: true,
        ),
      );
      await widget.store.resolveAnomaly(a.id);
      setState(() {});
      return;
    }
    if (choice == 'suppress') {
      await widget.store.learn(
        LearningRule(
          key: insights.suppressionKey(a),
          value: 'SUPRIMIR_ALERTA_EQUIVALENTE',
          reason: 'Administrador pediu para não avisar novamente neste contexto.',
          updatedAt: DateTime.now(),
          confidence: 1,
          confirmed: true,
        ),
      );
      await widget.store.resolveAnomaly(a.id);
      setState(() {});
      return;
    }
    if (choice == 'confirm') await _confirmAndTeach(a);
  }

  Future<void> _confirmAndTeach(Anomaly a) async {
    final controller = TextEditingController();
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Sua confirmação ensina o Intelligence'),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(a.message),
            const SizedBox(height: 12),
            TextField(
              controller: controller,
              decoration: const InputDecoration(
                labelText: 'Valor/regra correta ou explicação',
                border: OutlineInputBorder(),
              ),
              maxLines: 3,
            ),
          ],
        ),
        actions: [
          TextButton(onPressed: () => Navigator.pop(context, false), child: const Text('Depois')),
          FilledButton(onPressed: () => Navigator.pop(context, true), child: const Text('Confirmar e ensinar')),
        ],
      ),
    );
    if (confirmed == true && controller.text.trim().isNotEmpty) {
      final key = a.ruleKey.isEmpty ? 'correction:${a.id}' : a.ruleKey;
      await engine.confirm(
        key,
        controller.text.trim(),
        'Correção manual do administrador a partir de uma dúvida do Intelligence.',
      );
      await widget.store.resolveAnomaly(a.id);
      setState(() {});
    }
  }

  String _date(DateTime d) =>
      '${d.day.toString().padLeft(2, '0')}/${d.month.toString().padLeft(2, '0')}/${d.year}';

  Future<void> _openUrl(String value) async {
    final uri = Uri.tryParse(value);
    if (uri == null || !await launchUrl(uri, mode: LaunchMode.externalApplication)) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Não foi possível abrir o catálogo.')),
        );
      }
    }
  }
}
