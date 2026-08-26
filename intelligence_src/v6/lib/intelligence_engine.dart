import 'dart:math';

import 'data_store.dart';
import 'models.dart';

class IntelligenceEngine {
  IntelligenceEngine(this.store);
  final DataStore store;

  String classifySystem(String text) {
    final t = text.toUpperCase();
    if (t.contains('DIRE') || t.contains('TERMINAL DE DIRE') || t.contains('BARRA')) return 'DIREÇÃO';
    if (t.contains('FREIO') || t.contains('SAPATA') || t.contains('TAMBOR')) return 'FREIO';
    if (t.contains('HIDRAUL') || t.contains('MANGUEIRA') || t.contains('CILINDRO')) return 'HIDRÁULICO';
    if (t.contains('MOTOR') || t.contains('LUBRIFICANTE') || t.contains('15W40') || t.contains('5W30')) return 'MOTOR/LUBRIFICAÇÃO';
    if (t.contains('COMBUST') || t.contains('RACOR')) return 'COMBUSTÍVEL';
    if (t.contains('TRANSM') || t.contains('CAIXA') || t.contains('80W90') || t.contains('85W140')) return 'TRANSMISSÃO';
    if (t.contains('CORREIA') || t.contains('POLIA')) return 'ACIONAMENTO';
    if (t.contains('BATERIA') || t.contains('LAMP') || t.contains('FUSIVEL') || t.contains('ELÉTR')) return 'ELÉTRICO';
    if (t.contains('PNEU') || t.contains('RODA') || t.contains('ROLAMENTO')) return 'RODAGEM';
    if (t.contains('FILTRO')) return 'FILTRAGEM';
    return 'OUTROS';
  }

  String inferIntervention(PartUsage usage) {
    final system = classifySystem('${usage.partName} ${usage.reference}');
    return 'Intervenção provável no sistema $system. A peça usada é evidência de intervenção, mas não prova sozinha que o componente anterior estava quebrado.';
  }

  List<Anomaly> analyzeAll() {
    final out = <Anomaly>[];
    out.addAll(_meterAnomalies());
    out.addAll(_partRecurrences());
    out.addAll(_dataQuality());
    return _dedupe(out);
  }

  List<Anomaly> _meterAnomalies() {
    final out = <Anomaly>[];
    final byAsset = <String, List<MeterReading>>{};
    for (final r in store.readings) {
      byAsset.putIfAbsent(r.assetId, () => []).add(r);
    }
    for (final entry in byAsset.entries) {
      final list = entry.value..sort((a, b) => a.date.compareTo(b.date));
      for (var i = 1; i < list.length; i++) {
        final prev = list[i - 1];
        final cur = list[i];
        if (prev.type != cur.type) continue;
        if (cur.value + .01 < prev.value) {
          out.add(Anomaly(
            id: 'meter:${entry.key}:${cur.date.toIso8601String()}:${cur.rawValue}',
            title: 'Leitura regressiva para confirmar',
            message: '${entry.key}: ${prev.rawValue} → ${cur.rawValue} (${cur.type}). O valor original foi preservado e não será corrigido automaticamente.',
            severity: 'alta',
            createdAt: DateTime.now(),
            assetId: entry.key,
            needsConfirmation: true,
            ruleKey: 'meter:${entry.key}:${cur.date.toIso8601String()}',
          ));
        }
      }
    }
    return out;
  }

  List<Anomaly> _partRecurrences() {
    final out = <Anomaly>[];
    final usages = [...store.partUsages]..sort((a, b) => a.date.compareTo(b.date));
    const meaningfulSystems = {
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
    for (var i = 0; i < usages.length; i++) {
      final a = usages[i];
      for (var j = i + 1; j < usages.length; j++) {
        final b = usages[j];
        final days = b.date.difference(a.date).inDays;
        if (days > 180) break;
        if (a.assetId != b.assetId) continue;
        final sameRef = a.reference.isNotEmpty &&
            a.reference.toUpperCase() == b.reference.toUpperCase();
        final systemA = classifySystem(a.partName);
        final sameSystem = meaningfulSystems.contains(systemA) &&
            systemA == classifySystem(b.partName);
        if (sameRef || sameSystem) {
          final label = sameRef
              ? 'mesma referência ${a.reference}'
              : 'mesmo sistema $systemA';
          out.add(Anomaly(
            id: 'repeat:${a.assetId}:${a.date.toIso8601String()}:${b.date.toIso8601String()}:$label',
            title: 'Possível reincidência de manutenção',
            message: '${a.assetId}: $label apareceu novamente após $days dias. Cruzar O.S., providência tomada e Horímetro/Km antes de concluir falha repetida.',
            severity: days <= 30 ? 'alta' : 'média',
            createdAt: DateTime.now(),
            assetId: a.assetId,
          ));
        }
      }
    }
    return out;
  }

  List<Anomaly> _dataQuality() {
    final out = <Anomaly>[];
    for (final p in store.partUsages) {
      final unit = p.unit.trim().toLowerCase();
      final oil = RegExp(
        r'óleo|oleo|lubrificante|hidraul|hydro|hydraulic|15w|5w|10w|80w|85w|sae|atf',
        caseSensitive: false,
      ).hasMatch(p.partName);
      if (oil && unit == 'un') {
        out.add(Anomaly(
          id: 'unit:${p.assetId}:${p.date.toIso8601String()}:${p.rm}:${p.reference}',
          title: 'Unidade de fluido precisa de contexto',
          message: '${p.assetId}: ${p.partName} está como ${p.quantity} ${p.unit}. Pode ser embalagem, unidade comercial ou volume. Confirmar antes de converter para litros.',
          severity: 'média',
          createdAt: DateTime.now(),
          assetId: p.assetId,
          needsConfirmation: true,
          ruleKey: 'package:${p.internalCode.isEmpty ? p.reference : p.internalCode}',
        ));
      }
      if (p.quantity <= 0) {
        out.add(Anomaly(
          id: 'qty:${p.assetId}:${p.date.toIso8601String()}:${p.rm}:${p.reference}',
          title: 'Quantidade inválida ou zerada',
          message: '${p.assetId}: ${p.partName} tem quantidade ${p.quantity}.',
          severity: 'média',
          createdAt: DateTime.now(),
          assetId: p.assetId,
          needsConfirmation: true,
        ));
      }
    }
    return out;
  }

  double averageUsage(String assetId, int days) {
    final list = store.readings
        .where((r) => r.assetId == assetId && r.confidence >= .6)
        .toList()
      ..sort((a, b) => a.date.compareTo(b.date));
    if (list.length < 2) return 0;
    final end = list.last.date;
    final startLimit = end.subtract(Duration(days: days));
    final window = list.where((r) => !r.date.isBefore(startLimit)).toList();
    if (window.length < 2) return 0;
    final first = window.first;
    final last = window.last;
    if (first.type != last.type) return 0;
    final elapsed = max(1, last.date.difference(first.date).inDays);
    final delta = last.value - first.value;
    return delta > 0 ? delta / elapsed : 0;
  }

  Future<void> confirm(String ruleKey, String value, String reason) async {
    await store.learn(LearningRule(
      key: ruleKey,
      value: value,
      reason: reason,
      updatedAt: DateTime.now(),
      confidence: 1,
      confirmed: true,
    ));
  }

  List<Anomaly> _dedupe(List<Anomaly> values) {
    final seen = <String>{};
    return values.where((a) => seen.add(a.id)).toList();
  }
}
