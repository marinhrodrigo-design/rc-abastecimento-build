import 'dart:math';

import 'data_store.dart';
import 'models.dart';
import 'oem_maintenance.dart';

class ConfidenceAssessment {
  const ConfidenceAssessment(this.score, this.label, this.reasons);
  final double score;
  final String label;
  final List<String> reasons;
}

class ForecastRange {
  const ForecastRange(this.earliest, this.latest, this.confidence);
  final DateTime? earliest;
  final DateTime? latest;
  final ConfidenceAssessment confidence;

  String get text {
    if (earliest == null || latest == null) return 'Faixa indisponível';
    String f(DateTime d) =>
        '${d.day.toString().padLeft(2, '0')}/${d.month.toString().padLeft(2, '0')}/${d.year}';
    return '${f(earliest!)} a ${f(latest!)}';
  }
}

class SystemHealth {
  const SystemHealth({
    required this.system,
    required this.score,
    required this.status,
    required this.evidence,
  });
  final String system;
  final int score;
  final String status;
  final List<String> evidence;
}

class PeerBenchmark {
  const PeerBenchmark({
    required this.peerCount,
    required this.assetRate,
    required this.peerAverage,
    required this.summary,
  });
  final int peerCount;
  final double assetRate;
  final double peerAverage;
  final String summary;
}

class PartLifeObservation {
  const PartLifeObservation({
    required this.reference,
    required this.partName,
    required this.days,
    this.meterDelta,
  });
  final String reference;
  final String partName;
  final int days;
  final double? meterDelta;
}

class PreventivePreparation {
  const PreventivePreparation({
    required this.oemItems,
    required this.historicalItems,
    required this.notes,
  });
  final List<String> oemItems;
  final List<String> historicalItems;
  final List<String> notes;
}

class TimelineEvent {
  const TimelineEvent(this.date, this.kind, this.title, this.detail);
  final DateTime date;
  final String kind;
  final String title;
  final String detail;
}

class ChangeDigest {
  const ChangeDigest({
    required this.newAnomalies,
    required this.newQuestions,
    required this.summary,
  });
  final int newAnomalies;
  final int newQuestions;
  final List<String> summary;
}

class FutureRisk {
  const FutureRisk(this.level, this.system, this.message, this.confidence);
  final String level;
  final String system;
  final String message;
  final ConfidenceAssessment confidence;
}

class AdvancedInsightsService {
  AdvancedInsightsService(this.store);
  final DataStore store;

  static const meaningfulSystems = <String>{
    'DIREÇÃO',
    'FREIO',
    'HIDRÁULICO',
    'MOTOR/LUBRIFICAÇÃO',
    'COMBUSTÍVEL',
    'TRANSMISSÃO',
    'ACIONAMENTO',
    'ELÉTRICO',
    'RODAGEM',
  };

  String classifySystem(String text) {
    final t = text.toUpperCase();
    if (t.contains('DIRE') || t.contains('BARRA') || t.contains('PONTEIRA')) {
      return 'DIREÇÃO';
    }
    if (t.contains('FREIO') || t.contains('SAPATA') || t.contains('TAMBOR')) {
      return 'FREIO';
    }
    if (t.contains('HIDRAUL') || t.contains('MANGUEIRA') || t.contains('CILINDRO')) {
      return 'HIDRÁULICO';
    }
    if (t.contains('MOTOR') || t.contains('LUBRIFICANTE') || t.contains('15W40') || t.contains('5W30')) {
      return 'MOTOR/LUBRIFICAÇÃO';
    }
    if (t.contains('COMBUST') || t.contains('RACOR')) return 'COMBUSTÍVEL';
    if (t.contains('TRANSM') || t.contains('CAIXA') || t.contains('80W90') || t.contains('85W140')) {
      return 'TRANSMISSÃO';
    }
    if (t.contains('CORREIA') || t.contains('POLIA')) return 'ACIONAMENTO';
    if (t.contains('BATERIA') || t.contains('LAMP') || t.contains('FUSIVEL') || t.contains('ELETR')) {
      return 'ELÉTRICO';
    }
    if (t.contains('PNEU') || t.contains('RODA') || t.contains('ROLAMENTO')) return 'RODAGEM';
    return 'OUTROS';
  }

  ConfidenceAssessment confidenceForAsset(String assetId) {
    final reasons = <String>[];
    var score = .35;
    final readings = store.readings.where((r) => r.assetId == assetId && r.confidence >= .6).toList();
    final parts = store.partUsages.where((p) => p.assetId == assetId).toList();
    final unresolved = store.anomalies.where((a) => a.assetId == assetId && !a.resolved && a.needsConfirmation).length;

    if (readings.length >= 2) {
      score += .25;
      reasons.add('Há histórico confiável de Horímetro/Km.');
    } else {
      reasons.add('Poucas leituras confiáveis de Horímetro/Km.');
    }
    if (parts.length >= 2) {
      score += .15;
      reasons.add('Há histórico de peças/materiais associado ao ativo.');
    }
    if (unresolved == 0) {
      score += .15;
      reasons.add('Não há conflito pendente relevante para o ativo.');
    } else {
      score -= min(.2, unresolved * .05);
      reasons.add('$unresolved conflito(s)/dúvida(s) ainda pendente(s).');
    }
    final asset = _asset(assetId);
    if (asset != null && asset.serial.trim().isNotEmpty) {
      score += .1;
      reasons.add('Série/chassi disponível para identificação técnica.');
    }
    score = score.clamp(0, 1);
    final label = score >= .8 ? 'Alta' : score >= .6 ? 'Média' : 'Baixa';
    return ConfidenceAssessment(score, label, reasons);
  }

  ForecastRange forecastRange({
    required OemMaintenanceForecast forecast,
    required double averagePerDay,
    required String assetId,
  }) {
    final confidence = confidenceForAsset(assetId);
    if (forecast.estimatedDate == null || averagePerDay <= 0 || forecast.remaining < 0) {
      return ForecastRange(null, null, confidence);
    }
    final today = DateTime.now();
    final slower = max(.05, averagePerDay * .75);
    final faster = averagePerDay * 1.25;
    final earliestDays = (forecast.remaining / faster).ceil();
    final latestDays = (forecast.remaining / slower).ceil();
    return ForecastRange(
      today.add(Duration(days: max(0, earliestDays))),
      today.add(Duration(days: max(0, latestDays))),
      confidence,
    );
  }

  List<SystemHealth> healthForAsset(String assetId) {
    final now = DateTime.now();
    final cutoff = now.subtract(const Duration(days: 180));
    final bySystem = <String, List<PartUsage>>{};
    for (final p in store.partUsages.where((p) => p.assetId == assetId && !p.date.isBefore(cutoff))) {
      final system = classifySystem('${p.partName} ${p.reference}');
      if (!meaningfulSystems.contains(system)) continue;
      bySystem.putIfAbsent(system, () => []).add(p);
    }
    final result = <SystemHealth>[];
    for (final system in meaningfulSystems) {
      final items = bySystem[system] ?? const <PartUsage>[];
      final alerts = store.anomalies.where((a) =>
          a.assetId == assetId && !a.resolved && a.message.toUpperCase().contains(system)).length;
      var score = 100 - items.length * 12 - alerts * 15;
      score = score.clamp(0, 100);
      final status = score >= 80 ? '🟢 Estável' : score >= 60 ? '🟡 Observar' : '🔴 Atenção';
      final evidence = <String>[];
      if (items.isNotEmpty) evidence.add('${items.length} intervenção(ões) nos últimos 180 dias.');
      if (alerts > 0) evidence.add('$alerts alerta(s) aberto(s) relacionado(s).');
      if (evidence.isEmpty) evidence.add('Sem sinal relevante recente nos dados disponíveis.');
      result.add(SystemHealth(system: system, score: score, status: status, evidence: evidence));
    }
    result.sort((a, b) => a.score.compareTo(b.score));
    return result;
  }

  PeerBenchmark compareWithPeers(Asset asset) {
    final peers = store.assets.where((a) =>
        a.id != asset.id &&
        a.brand.toUpperCase() == asset.brand.toUpperCase() &&
        a.model.toUpperCase() == asset.model.toUpperCase()).toList();
    final cutoff = DateTime.now().subtract(const Duration(days: 365));
    double countFor(String id) => store.partUsages.where((p) => p.assetId == id && !p.date.isBefore(cutoff)).length.toDouble();
    final assetRate = countFor(asset.id);
    if (peers.isEmpty) {
      return PeerBenchmark(peerCount: 0, assetRate: assetRate, peerAverage: 0, summary: 'Não há ativos iguais suficientes para comparação.');
    }
    final avg = peers.map((p) => countFor(p.id)).fold<double>(0, (a, b) => a + b) / peers.length;
    final ratio = avg <= 0 ? 0 : assetRate / avg;
    final summary = avg <= 0
        ? 'Os pares ainda não têm histórico suficiente.'
        : ratio >= 1.5
            ? '${asset.id} apresenta ${ratio.toStringAsFixed(1)}x mais intervenções registradas que a média dos ${peers.length} ativos iguais.'
            : ratio <= .65
                ? '${asset.id} apresenta menos intervenções que a média dos ativos iguais.'
                : '${asset.id} está próximo da média dos ativos iguais.';
    return PeerBenchmark(peerCount: peers.length, assetRate: assetRate, peerAverage: avg, summary: summary);
  }

  List<PartLifeObservation> partLife(String assetId) {
    final usages = store.partUsages.where((p) => p.assetId == assetId && p.reference.trim().isNotEmpty).toList()
      ..sort((a, b) => a.date.compareTo(b.date));
    final result = <PartLifeObservation>[];
    for (var i = 0; i < usages.length; i++) {
      for (var j = i + 1; j < usages.length; j++) {
        if (usages[i].reference.toUpperCase() != usages[j].reference.toUpperCase()) continue;
        final meterA = _nearestReading(assetId, usages[i].date);
        final meterB = _nearestReading(assetId, usages[j].date);
        double? delta;
        if (meterA != null && meterB != null && meterA.type == meterB.type && meterB.value >= meterA.value) {
          delta = meterB.value - meterA.value;
        }
        result.add(PartLifeObservation(
          reference: usages[i].reference,
          partName: usages[i].partName,
          days: usages[j].date.difference(usages[i].date).inDays,
          meterDelta: delta,
        ));
        break;
      }
    }
    return result;
  }

  PreventivePreparation preventivePreparation({
    required Asset asset,
    required List<OemMaintenanceRule> oemRules,
  }) {
    final oemItems = oemRules.map((r) => '${r.serviceName} — ${r.interval.toStringAsFixed(0)} ${r.unit == 'H' ? 'h' : 'km'}').toList();
    final sameModelIds = store.assets.where((a) =>
        a.brand.toUpperCase() == asset.brand.toUpperCase() &&
        a.model.toUpperCase() == asset.model.toUpperCase()).map((a) => a.id).toSet();
    final freq = <String, int>{};
    for (final p in store.partUsages.where((p) => sameModelIds.contains(p.assetId))) {
      final key = p.reference.trim().isNotEmpty ? '${p.partName} • ${p.reference}' : p.partName;
      freq[key] = (freq[key] ?? 0) + 1;
    }
    final historical = freq.entries.toList()..sort((a, b) => b.value.compareTo(a.value));
    return PreventivePreparation(
      oemItems: oemItems,
      historicalItems: historical.take(8).map((e) => '${e.key} — apareceu ${e.value}x no histórico').toList(),
      notes: const [
        'OEM e histórico operacional são mostrados separadamente.',
        'A lista histórica não significa recomendação OEM e deve ser conferida antes da manutenção.',
        'Estoque não é consultado nesta versão.',
      ],
    );
  }

  List<String> maintenanceCompletenessQuestions(Asset asset) {
    final sameModelIds = store.assets.where((a) =>
        a.brand.toUpperCase() == asset.brand.toUpperCase() &&
        a.model.toUpperCase() == asset.model.toUpperCase()).map((a) => a.id).toSet();
    final byOs = <String, Set<String>>{};
    for (final p in store.partUsages.where((p) => sameModelIds.contains(p.assetId) && p.os.trim().isNotEmpty)) {
      final key = '${p.assetId}:${p.os}';
      byOs.putIfAbsent(key, () => <String>{}).add(p.reference.isEmpty ? p.partName : p.reference);
    }
    if (byOs.length < 2) return const [];
    final frequency = <String, int>{};
    for (final set in byOs.values) {
      for (final item in set) frequency[item] = (frequency[item] ?? 0) + 1;
    }
    final common = frequency.entries.where((e) => e.value >= max(2, (byOs.length * .6).ceil())).map((e) => e.key).toSet();
    if (common.isEmpty) return const [];
    final questions = <String>[];
    for (final entry in byOs.entries) {
      final missing = common.difference(entry.value);
      if (missing.isNotEmpty) {
        questions.add('${entry.key}: não localizei ${missing.take(3).join(', ')} entre os materiais. Confirmar se foi compra externa, reutilização ou ausência de registro.');
      }
    }
    return questions.take(5).toList();
  }

  ChangeDigest changesSince(DateTime since) {
    final recent = store.anomalies.where((a) => a.createdAt.isAfter(since)).toList();
    final questions = recent.where((a) => a.needsConfirmation).length;
    final summary = recent.take(5).map((a) => '${a.assetId.isEmpty ? '' : '${a.assetId}: '}${a.title}').toList();
    return ChangeDigest(newAnomalies: recent.length, newQuestions: questions, summary: summary);
  }

  FutureRisk futureRisk(String assetId) {
    final now = DateTime.now();
    final recentStart = now.subtract(const Duration(days: 180));
    final previousStart = now.subtract(const Duration(days: 360));
    final recent = <String, int>{};
    final previous = <String, int>{};
    for (final p in store.partUsages.where((p) => p.assetId == assetId)) {
      final system = classifySystem('${p.partName} ${p.reference}');
      if (!meaningfulSystems.contains(system)) continue;
      if (!p.date.isBefore(recentStart)) {
        recent[system] = (recent[system] ?? 0) + 1;
      } else if (!p.date.isBefore(previousStart)) {
        previous[system] = (previous[system] ?? 0) + 1;
      }
    }
    String top = 'GERAL';
    double maxGrowth = 0;
    for (final s in meaningfulSystems) {
      final r = recent[s] ?? 0;
      final p = previous[s] ?? 0;
      final growth = r - p.toDouble();
      if (r >= 2 && growth > maxGrowth) {
        maxGrowth = growth;
        top = s;
      }
    }
    final confidence = confidenceForAsset(assetId);
    if (top == 'GERAL') {
      return FutureRisk('baixo/indefinido', top, 'Não há evidência suficiente de aumento recente de intervenções para estimar risco de parada.', confidence);
    }
    return FutureRisk(
      maxGrowth >= 3 ? 'alto' : 'moderado',
      top,
      'Há aumento de intervenções no sistema $top nos últimos 180 dias. Isso não prevê quebra; indica tendência que merece acompanhamento.',
      confidence,
    );
  }

  List<TimelineEvent> timeline(String assetId) {
    final out = <TimelineEvent>[];
    for (final r in store.readings.where((r) => r.assetId == assetId)) {
      out.add(TimelineEvent(r.date, 'MEDIDOR', '${r.type}: ${r.rawValue}', 'Fonte: ${r.source} • confiança ${(r.confidence * 100).round()}%'));
    }
    for (final p in store.partUsages.where((p) => p.assetId == assetId)) {
      out.add(TimelineEvent(p.date, 'PEÇA/RM', p.partName, 'Qtd. ${p.quantity} ${p.unit} • O.S. ${p.os} • RM ${p.rm} • Ref. ${p.reference}'));
    }
    for (final a in store.anomalies.where((a) => a.assetId == assetId)) {
      out.add(TimelineEvent(a.createdAt, 'ALERTA', a.title, a.message));
    }
    out.sort((a, b) => b.date.compareTo(a.date));
    return out;
  }

  String explainAnomaly(Anomaly anomaly) {
    final evidence = <String>[];
    if (anomaly.assetId.isNotEmpty) {
      final confidence = confidenceForAsset(anomaly.assetId);
      evidence.add('Confiança geral do ativo: ${confidence.label} (${(confidence.score * 100).round()}%).');
    }
    if (anomaly.ruleKey.isNotEmpty) evidence.add('Regra/contexto: ${anomaly.ruleKey}.');
    if (anomaly.needsConfirmation) evidence.add('A conclusão depende de confirmação humana; não será tratada como fato até ser confirmada.');
    evidence.add('Dados originais permanecem preservados; o Intelligence não corrige a fonte silenciosamente.');
    return evidence.join('\n');
  }

  String nextAction({
    required Asset asset,
    OemMaintenanceForecast? oemForecast,
  }) {
    final openQuestions = store.anomalies.where((a) => a.assetId == asset.id && !a.resolved && a.needsConfirmation).length;
    if (openQuestions > 0) {
      return 'Resolver $openQuestions dúvida(s)/conflito(s) antes de decisões de alta confiança.';
    }
    if (oemForecast != null && oemForecast.remaining <= 50) {
      return 'Programar ${oemForecast.rule.serviceName}: faltam ${oemForecast.remainingText}; previsão ${oemForecast.estimatedDateText}.';
    }
    final health = healthForAsset(asset.id);
    if (health.isNotEmpty && health.first.score < 60) {
      return 'Acompanhar ${health.first.system}: é o sistema com mais sinais recentes no histórico disponível.';
    }
    return 'Continuar coletando Horímetro/Km, O.S. e materiais para aumentar a confiança das previsões.';
  }

  bool isSuppressed(Anomaly anomaly) {
    final key = suppressionKey(anomaly);
    return store.rule(key)?.confirmed == true;
  }

  String suppressionKey(Anomaly anomaly) {
    final context = anomaly.ruleKey.isNotEmpty ? anomaly.ruleKey : anomaly.title;
    return 'suppress:${anomaly.assetId}:$context';
  }

  Asset? _asset(String id) {
    for (final a in store.assets) {
      if (a.id == id) return a;
    }
    return null;
  }

  MeterReading? _nearestReading(String assetId, DateTime date) {
    final values = store.readings.where((r) => r.assetId == assetId && r.confidence >= .6).toList();
    if (values.isEmpty) return null;
    values.sort((a, b) => (a.date.difference(date).inDays.abs()).compareTo(b.date.difference(date).inDays.abs()));
    return values.first;
  }
}
