import 'package:flutter_test/flutter_test.dart';
import 'package:rc_intelligence/intelligence_engine.dart';

void main() {
  test('calcula restante por horímetro', () {
    expect(IntelligenceEngine.remainingToService(currentMeter: 4720, lastServiceMeter: 4500, interval: 500), 280);
  });

  test('calcula restante por km sem converter em horas', () {
    expect(IntelligenceEngine.remainingToService(currentMeter: 86500, lastServiceMeter: 80000, interval: 10000), 3500);
  });

  test('prevê dias para próxima revisão', () {
    expect(IntelligenceEngine.forecastDays(remaining: 48, averagePerDay: 8), 6);
  });

  test('classifica janelas de alerta', () {
    expect(IntelligenceEngine.alertLevel(daysToDue: 1.1), 'CRÍTICO');
    expect(IntelligenceEngine.alertLevel(daysToDue: 6), 'URGENTE');
    expect(IntelligenceEngine.alertLevel(daysToDue: 12), 'ATENÇÃO');
    expect(IntelligenceEngine.alertLevel(daysToDue: 25), 'PLANEJAR');
  });

  test('calcula disponibilidade inerente', () {
    final value = IntelligenceEngine.availabilityPercent(mtbfHours: 256, mttrHours: 4.1);
    expect(value, closeTo(98.42, 0.02));
  });

  test('calcula RUL linear de desgaste', () {
    final rul = IntelligenceEngine.remainingUsefulLifeHours(firstMeasurement: 6.8, latestMeasurement: 6.2, limitMeasurement: 5.8, elapsedHours: 280);
    expect(rul, closeTo(186.67, 0.1));
  });

  test('calcula desvio de combustível', () {
    final deviation = IntelligenceEngine.deviationPercent(observed: 349, expected: 226.8);
    expect(deviation, closeTo(53.88, 0.1));
  });
}
