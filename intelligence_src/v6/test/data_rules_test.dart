import 'package:flutter_test/flutter_test.dart';
import 'package:rc_intelligence/data_import.dart';

void main() {
  test('FROTAS e OFICINA BANGU sao a mesma base', () {
    final service = DataImportService();
    expect(service.normalizeLocation('FROTAS'), DataImportService.baseLocation);
    expect(service.normalizeLocation('OFICINA BANGU'), DataImportService.baseLocation);
  });

  test('abastecimento na base sozinho nao prova liberacao', () {
    final service = DataImportService();
    expect(service.baseFuelingProvesRelease('FROTAS'), isFalse);
  });
}
