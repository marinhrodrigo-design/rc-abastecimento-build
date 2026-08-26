import 'package:flutter_test/flutter_test.dart';
import 'package:rc_intelligence/advanced_insights.dart';
import 'package:rc_intelligence/data_store.dart';
import 'package:rc_intelligence/models.dart';
import 'package:rc_intelligence/oem_maintenance.dart';

void main() {
  test('classifica sistemas e gera saude explicavel', () {
    final store = DataStore();
    final now = DateTime.now();
    store.partUsages.addAll([
      PartUsage(
        assetId: 'A1',
        date: now.subtract(const Duration(days: 10)),
        partName: 'BARRA DE DIRECAO',
        reference: 'R1',
        quantity: 1,
        unit: 'un',
      ),
      PartUsage(
        assetId: 'A1',
        date: now.subtract(const Duration(days: 5)),
        partName: 'TERMINAL DE DIRECAO',
        reference: 'R2',
        quantity: 1,
        unit: 'un',
      ),
    ]);
    final service = AdvancedInsightsService(store);
    expect(service.classifySystem('barra de direcao'), 'DIREÇÃO');
    final health = service.healthForAsset('A1');
    expect(health.any((h) => h.system == 'DIREÇÃO' && h.score < 100), isTrue);
  });

  test('compara ativos iguais sem transformar diferenca em diagnostico', () {
    final store = DataStore();
    final now = DateTime.now();
    store.assets.addAll([
      Asset(id: 'A1', description: 'Retro', brand: 'NH', model: 'B110', meterType: 'HORIMETRO'),
      Asset(id: 'A2', description: 'Retro', brand: 'NH', model: 'B110', meterType: 'HORIMETRO'),
    ]);
    store.partUsages.addAll([
      for (var i = 0; i < 4; i++)
        PartUsage(
          assetId: 'A1',
          date: now.subtract(Duration(days: 10 + i)),
          partName: 'MANGUEIRA HIDRAULICA $i',
          quantity: 1,
          unit: 'un',
        ),
      PartUsage(
        assetId: 'A2',
        date: now.subtract(const Duration(days: 20)),
        partName: 'MANGUEIRA HIDRAULICA',
        quantity: 1,
        unit: 'un',
      ),
    ]);
    final result = AdvancedInsightsService(store).compareWithPeers(store.assets.first);
    expect(result.peerCount, 1);
    expect(result.summary, contains('mais intervenções'));
  });

  test('vida observada usa repeticao da mesma referencia e medidor quando disponivel', () {
    final store = DataStore();
    final d1 = DateTime(2026, 1, 1);
    final d2 = DateTime(2026, 3, 1);
    store.partUsages.addAll([
      PartUsage(assetId: 'A1', date: d1, partName: 'BARRA', reference: 'X', quantity: 1, unit: 'un'),
      PartUsage(assetId: 'A1', date: d2, partName: 'BARRA', reference: 'X', quantity: 1, unit: 'un'),
    ]);
    store.readings.addAll([
      MeterReading(assetId: 'A1', date: d1, rawValue: '1000', value: 1000, type: 'HORIMETRO', source: 'OS'),
      MeterReading(assetId: 'A1', date: d2, rawValue: '1120', value: 1120, type: 'HORIMETRO', source: 'OS'),
    ]);
    final life = AdvancedInsightsService(store).partLife('A1');
    expect(life, isNotEmpty);
    expect(life.first.meterDelta, 120);
  });

  test('preparacao separa OEM de historico e nao consulta estoque', () {
    final store = DataStore();
    final asset = Asset(id: 'A1', description: 'Retro', brand: 'TESTE', model: 'X1', meterType: 'HORIMETRO');
    store.assets.add(asset);
    store.partUsages.add(
      PartUsage(assetId: 'A1', date: DateTime.now(), partName: 'FILTRO MOTOR', reference: 'F1', quantity: 1, unit: 'un'),
    );
    const rule = OemMaintenanceRule(
      id: 'oem',
      brandContains: 'TESTE',
      modelContains: 'X1',
      serviceName: 'Troca de oleo',
      interval: 500,
      unit: 'H',
      sourceTitle: 'OEM',
      sourceUrl: 'https://example.com',
      evidence: 'OEM',
    );
    final prep = AdvancedInsightsService(store).preventivePreparation(asset: asset, oemRules: const [rule]);
    expect(prep.oemItems, isNotEmpty);
    expect(prep.historicalItems, isNotEmpty);
    expect(prep.notes.join(' '), contains('Estoque não é consultado'));
  });

  test('feedback pode suprimir contexto equivalente', () {
    final store = DataStore();
    final service = AdvancedInsightsService(store);
    final anomaly = Anomaly(
      id: 'a',
      title: 'Teste',
      message: 'Teste',
      severity: 'média',
      createdAt: DateTime.now(),
      assetId: 'A1',
      ruleKey: 'contexto:x',
    );
    expect(service.isSuppressed(anomaly), isFalse);
    store.learningRules.add(LearningRule(
      key: service.suppressionKey(anomaly),
      value: 'SUPRIMIR',
      reason: 'Teste em memória',
      updatedAt: DateTime.now(),
      confidence: 1,
      confirmed: true,
    ));
    expect(service.isSuppressed(anomaly), isTrue);
  });

  test('linha do tempo combina medidor pecas e alertas', () {
    final store = DataStore();
    final now = DateTime.now();
    store.readings.add(MeterReading(assetId: 'A1', date: now, rawValue: '100', value: 100, type: 'HORIMETRO', source: 'OS'));
    store.partUsages.add(PartUsage(assetId: 'A1', date: now, partName: 'FILTRO', quantity: 1, unit: 'un'));
    store.anomalies.add(Anomaly(id: 'x', title: 'Alerta', message: 'Teste', severity: 'info', createdAt: now, assetId: 'A1'));
    final timeline = AdvancedInsightsService(store).timeline('A1');
    expect(timeline.map((e) => e.kind).toSet(), containsAll(['MEDIDOR', 'PEÇA/RM', 'ALERTA']));
  });
}
