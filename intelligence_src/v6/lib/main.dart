import 'package:file_picker/file_picker.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:url_launcher/url_launcher.dart';

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
          )
        ],
      ),
      body: pages[index],
      bottomNavigationBar: NavigationBar(
        selectedIndex: index,
        onDestinationSelected: (v) => setState(() => index = v),
        destinations: const [
          NavigationDestination(
            icon: Icon(Icons.insights),
            label: 'Intelligence',
          ),
          NavigationDestination(
            icon: Icon(Icons.precision_manufacturing),
            label: 'Ativos',
          ),
          NavigationDestination(
            icon: Icon(Icons.storage),
            label: 'Central de Dados',
          ),
          NavigationDestination(
            icon: Icon(Icons.menu_book),
            label: 'OEM',
          ),
          NavigationDestination(
            icon: Icon(Icons.notifications_active),
            label: 'Alertas',
          ),
        ],
      ),
    );
  }

  Widget _dashboard() {
    final open = widget.store.anomalies.where((a) => !a.resolved).length;
    final questions = widget.store.anomalies
        .where((a) => !a.resolved && a.needsConfirmation)
        .length;
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
            _metric(
              'Ativos',
              '${widget.store.assets.length}',
              Icons.precision_manufacturing,
            ),
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
            leading: Icon(Icons.location_on),
            title: Text('FROTAS = OFICINA BANGU'),
            subtitle: Text(
              'Av. Brasil 33060 • Base / Oficina / Tanque estacionário. Abastecimento na base, sozinho, não prova liberação do ativo.',
            ),
            trailing: Icon(Icons.verified),
          ),
        ),
        const Card(
          child: ListTile(
            leading: Icon(Icons.speed),
            title: Text('Média de utilização: Calculada automaticamente'),
            subtitle: Text(
              'Usa somente leituras confiáveis e nunca converte Horímetro em Km ou Km em Horímetro.',
            ),
          ),
        ),
        const Card(
          child: ListTile(
            leading: Icon(Icons.event_available),
            title: Text('Previsão preventiva OEM'),
            subtitle: Text(
              'Quando a regra OEM estiver confirmada, o Intelligence calcula o próximo marco, estima a data pela utilização real e gera alertas em 250 h, 100 h, 50 h e 10 h.',
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
                Text(
                  value,
                  style: const TextStyle(
                    fontSize: 26,
                    fontWeight: FontWeight.bold,
                  ),
                ),
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
          return Card(
            child: ListTile(
              title: Text('${a.id} • ${a.brand} ${a.model}'.trim()),
              subtitle: Text(
                '${a.description}\nSérie/Chassi: ${a.serial.isEmpty ? 'Vazio' : a.serial} • Medidor: ${a.meterType}',
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
          const Text(
            'Central de Dados',
            style: TextStyle(fontSize: 24, fontWeight: FontWeight.bold),
          ),
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
            (m) => ListTile(
              leading: const Icon(Icons.info_outline),
              title: Text(m),
            ),
          ),
        ],
      );

  Widget _oemLibrary() => ListView.builder(
        padding: const EdgeInsets.all(12),
        itemCount: widget.store.assets.length,
        itemBuilder: (context, i) {
          final a = widget.store.assets[i];
          final usages = widget.store.partUsages
              .where((p) => p.assetId == a.id)
              .toList()
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
                  child: Text(
                    'Série: ${a.serial.isEmpty ? 'não informada' : a.serial}',
                  ),
                ),
                const SizedBox(height: 4),
                Align(
                  alignment: Alignment.centerLeft,
                  child: Text('Fonte: ${match.provider}'),
                ),
                Align(
                  alignment: Alignment.centerLeft,
                  child: Text(match.notes),
                ),
                const Divider(),
                if (maintenanceRules.isEmpty)
                  const Align(
                    alignment: Alignment.centerLeft,
                    child: Text(
                      'Regra de manutenção OEM: ainda não confirmada para este modelo/série.',
                    ),
                  )
                else
                  ...maintenanceRules.map(
                    (rule) => _oemRuleTile(rule, forecasts),
                  ),
                if (part != null) ...[
                  const Divider(),
                  Align(
                    alignment: Alignment.centerLeft,
                    child: Text(
                      'Peça mais recente: ${part.partName} • Ref. ${part.reference}',
                    ),
                  ),
                ],
                const SizedBox(height: 10),
                Wrap(
                  spacing: 8,
                  runSpacing: 8,
                  children: [
                    OutlinedButton.icon(
                      onPressed: match.catalogUrl.isEmpty
                          ? null
                          : () => _openUrl(match.catalogUrl),
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
                          await Clipboard.setData(
                            ClipboardData(text: part.reference),
                          );
                          if (mounted) {
                            ScaffoldMessenger.of(context).showSnackBar(
                              const SnackBar(
                                content: Text('Referência copiada.'),
                              ),
                            );
                          }
                        },
                        icon: const Icon(Icons.copy),
                        label: const Text('Copiar referência'),
                      ),
                  ],
                )
              ],
            ),
          );
        },
      );

  Widget _oemRuleTile(
    OemMaintenanceRule rule,
    List<OemMaintenanceForecast> forecasts,
  ) {
    OemMaintenanceForecast? forecast;
    for (final value in forecasts) {
      if (value.rule.id == rule.id) {
        forecast = value;
        break;
      }
    }
    final unit = rule.unit == 'H' ? 'h' : 'km';
    final intervalText = rule.interval == rule.interval.roundToDouble()
        ? rule.interval.round().toString()
        : rule.interval.toStringAsFixed(1).replaceAll('.', ',');
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
              const SizedBox(height: 4),
              Text(forecast.userMessage),
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
              const Text(
                'Sem Horímetro/Km confiável suficiente para calcular a previsão.',
              ),
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
            leading: Icon(
              a.needsConfirmation ? Icons.help : Icons.warning_amber,
            ),
            title: Text(
              a.title,
              style: TextStyle(
                decoration: a.resolved ? TextDecoration.lineThrough : null,
              ),
            ),
            subtitle: Text(a.message),
            trailing: a.resolved
                ? const Icon(Icons.check_circle)
                : const Icon(Icons.chevron_right),
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
      final exists = widget.store.anomalies.any((x) => x.id == a.id);
      if (!exists) {
        await widget.store.addAnomaly(a);
        await widget.notifications.showAnomaly(a);
        added++;
      }
    }
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
      setState(
        () => importMessages
          ..clear()
          ..add('Falha ao ler a planilha: $e'),
      );
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
              TextField(
                controller: brand,
                decoration: const InputDecoration(labelText: 'Marca'),
              ),
              TextField(
                controller: model,
                decoration: const InputDecoration(labelText: 'Modelo'),
              ),
              TextField(
                controller: year,
                decoration: const InputDecoration(labelText: 'Ano'),
              ),
              TextField(
                controller: serial,
                decoration: const InputDecoration(labelText: 'Chassi / Série'),
              ),
              TextField(
                controller: plate,
                decoration: const InputDecoration(labelText: 'Placa'),
              ),
            ],
          ),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context, false),
            child: const Text('Cancelar'),
          ),
          FilledButton(
            onPressed: () => Navigator.pop(context, true),
            child: const Text('Salvar'),
          ),
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
    final preventive = engine.oemPreventiveForecastForAsset(a);
    final itemForecasts = engine.oemItemForecastsForAsset(a);
    final rules = engine.oemRulesForAsset(a);
    showModalBottomSheet(
      context: context,
      showDragHandle: true,
      isScrollControlled: true,
      builder: (context) => SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(18),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                '${a.id} • ${a.brand} ${a.model}',
                style: const TextStyle(
                  fontSize: 20,
                  fontWeight: FontWeight.bold,
                ),
              ),
              Text('Ano: ${a.year.isEmpty ? 'Vazio' : a.year}'),
              Text('Série/Chassi: ${a.serial.isEmpty ? 'Vazio' : a.serial}'),
              Text(
                'Média 30 dias: ${avg30 == 0 ? 'dados insuficientes' : avg30.toStringAsFixed(1)} ${a.meterType == 'KM' ? 'km/dia' : 'h/dia'}',
              ),
              const Divider(),
              if (preventive != null) ...[
                Text(
                  preventive.userMessage,
                  style: const TextStyle(fontWeight: FontWeight.w600),
                ),
                if (preventive.levelCode != 'MONITOR')
                  Text(
                    preventive.remaining < 0
                        ? '${preventive.levelEmoji} ${preventive.levelLabel}: intervalo ultrapassado'
                        : '${preventive.levelEmoji} ${preventive.levelLabel}: faltam ${preventive.remainingText}',
                    style: const TextStyle(fontWeight: FontWeight.bold),
                  ),
                const Divider(),
              ] else if (rules.isNotEmpty) ...[
                const Text(
                  'Regra OEM completa de revisão preventiva ainda não confirmada. Itens OEM confirmados:',
                  style: TextStyle(fontWeight: FontWeight.w600),
                ),
                for (final forecast in itemForecasts)
                  Padding(
                    padding: const EdgeInsets.only(top: 6),
                    child: Text(
                      '${forecast.rule.serviceName}: ${forecast.targetText} • ${forecast.estimatedDateText}',
                    ),
                  ),
                const Divider(),
              ],
              Text('Catálogo: ${catalog.title}'),
              Text(catalog.status),
              const SizedBox(height: 8),
              FilledButton(
                onPressed: catalog.catalogUrl.isEmpty
                    ? null
                    : () => _openUrl(catalog.catalogUrl),
                child: const Text('Abrir catálogo'),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Future<void> _handleAlert(Anomaly a) async {
    if (!a.needsConfirmation) {
      await widget.store.resolveAnomaly(a.id);
      setState(() {});
      return;
    }
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
          TextButton(
            onPressed: () => Navigator.pop(context, false),
            child: const Text('Depois'),
          ),
          FilledButton(
            onPressed: () => Navigator.pop(context, true),
            child: const Text('Confirmar e ensinar'),
          ),
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

  Future<void> _openUrl(String value) async {
    final uri = Uri.tryParse(value);
    if (uri == null ||
        !await launchUrl(uri, mode: LaunchMode.externalApplication)) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Não foi possível abrir o catálogo.')),
        );
      }
    }
  }
}
