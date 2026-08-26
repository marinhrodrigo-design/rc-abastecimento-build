import 'package:flutter_test/flutter_test.dart';
import 'package:rc_intelligence/models.dart';
import 'package:rc_intelligence/oem_maintenance.dart';

void main() {
  final service = OemMaintenanceService(rules: const []);

  test('faixas OEM seguem 250 100 50 10 e vencida', () {
    expect(service.levelForRemaining(250).code, 'PLANNING');
    expect(service.levelForRemaining(100).code, 'ATTENTION');
    expect(service.levelForRemaining(50).code, 'SCHEDULE');
    expect(service.levelForRemaining(10).code, 'VERY_CLOSE');
    expect(service.levelForRemaining(-1).code, 'OVERDUE');
  });

  test('previsao OEM usa ultima revisao confirmada mais intervalo', () {
    const rule = OemMaintenanceRule(
      id: 'teste_500h',
      brandContains: 'TESTE',
      modelContains: 'X1',
      serviceName: 'Revisão preventiva OEM',
      interval: 500,
      unit: 'H',
      sourceTitle: 'Manual OEM de teste',
      sourceUrl: 'https://example.com/manual',
      evidence: 'Regra de teste.',
      fullPreventive: true,
    );
    final asset = Asset(
      id: 'A1',
      description: 'Máquina',
      brand: 'TESTE',
      model: 'X1',
      meterType: 'HORIMETRO',
    );
    final forecast = service.forecastRule(
      asset: asset,
      rule: rule,
      readings: [
        MeterReading(
          assetId: 'A1',
          date: DateTime(2026, 8, 1),
          rawValue: '1720',
          value: 1720,
          type: 'HORIMETRO',
          source: 'OS',
        ),
      ],
      averagePerDay: 2,
      lastCompletedMeter: 1300,
      now: DateTime(2026, 8, 1),
    );
    expect(forecast, isNotNull);
    expect(forecast!.nextTarget, 1800);
    expect(forecast.remaining, 80);
    expect(forecast.levelCode, 'ATTENTION');
    expect(forecast.userMessage, contains('próxima revisão preventiva'));
  });

  test('item OEM isolado nao e chamado de revisao completa', () {
    const rule = OemMaintenanceRule(
      id: 'oleo_500h',
      brandContains: 'TESTE',
      modelContains: 'X1',
      serviceName: 'Troca do óleo do motor',
      interval: 500,
      unit: 'H',
      sourceTitle: 'OEM',
      sourceUrl: 'https://example.com',
      evidence: 'OEM',
      fullPreventive: false,
    );
    final asset = Asset(
      id: 'A1',
      description: 'Máquina',
      brand: 'TESTE',
      model: 'X1',
      meterType: 'HORIMETRO',
    );
    final forecast = service.forecastRule(
      asset: asset,
      rule: rule,
      readings: [
        MeterReading(
          assetId: 'A1',
          date: DateTime(2026, 8, 1),
          rawValue: '1720',
          value: 1720,
          type: 'HORIMETRO',
          source: 'OS',
        ),
      ],
      averagePerDay: 1,
      now: DateTime(2026, 8, 1),
    );
    expect(forecast!.userMessage, contains('Troca do óleo do motor'));
    expect(forecast.userMessage, isNot(contains('próxima revisão preventiva')));
  });
}
