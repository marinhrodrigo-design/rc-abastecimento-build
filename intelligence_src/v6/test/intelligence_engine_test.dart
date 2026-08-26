import 'package:flutter_test/flutter_test.dart';
import 'package:rc_intelligence/data_store.dart';
import 'package:rc_intelligence/intelligence_engine.dart';
import 'package:rc_intelligence/models.dart';

void main() {
  test('peca usada gera inferencia de intervencao, nao quebra confirmada', () {
    final engine = IntelligenceEngine(DataStore());
    final text = engine.inferIntervention(PartUsage(
      assetId: '005-001',
      date: DateTime(2026, 1, 1),
      partName: 'BARRA DE DIRECAO',
      quantity: 1,
      unit: 'un',
    ));
    expect(text, contains('Intervenção provável'));
    expect(text, contains('não prova'));
  });

  test('reincidencia no mesmo sistema em menos de 180 dias e sinalizada', () {
    final store = DataStore();
    store.partUsages.addAll([
      PartUsage(assetId: 'A1', date: DateTime(2026, 1, 1), partName: 'BARRA DE DIRECAO', reference: 'R1', quantity: 1, unit: 'un'),
      PartUsage(assetId: 'A1', date: DateTime(2026, 2, 1), partName: 'TERMINAL DE DIRECAO', reference: 'R2', quantity: 1, unit: 'un'),
    ]);
    final found = IntelligenceEngine(store).analyzeAll();
    expect(found.any((a) => a.title.contains('reincidência')), isTrue);
  });

  test('horimetro regressivo vira duvida para confirmacao', () {
    final store = DataStore();
    store.readings.addAll([
      MeterReading(assetId: 'A1', date: DateTime(2026, 1, 1), rawValue: '4023', value: 4023, type: 'HORIMETRO', source: 'OS'),
      MeterReading(assetId: 'A1', date: DateTime(2026, 1, 2), rawValue: '402,3', value: 402.3, type: 'HORIMETRO', source: 'STTS'),
    ]);
    final found = IntelligenceEngine(store).analyzeAll();
    expect(found.any((a) => a.needsConfirmation), isTrue);
  });
}
