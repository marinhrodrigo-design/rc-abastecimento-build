import 'package:flutter_test/flutter_test.dart';
import 'package:rc_intelligence/models.dart';
import 'package:rc_intelligence/oem_catalog.dart';
import 'package:rc_intelligence/phase4_theme.dart';

void main() {
  test('severidade e status usam linguagem operacional em português', () {
    expect(RCTheme.severityLabel('critical'), 'Crítico');
    expect(RCTheme.severityLabel('high'), 'Alto');
    expect(RCTheme.statusLabel('in_review'), 'Em análise');
    expect(RCTheme.statusLabel('dismissed'), 'Não procede');
  });

  test('biblioteca OEM continua sem inventar catálogo desconhecido', () {
    final match = OemCatalogService().match(
      Asset(id: '008-999', description: 'Teste', brand: 'MARCA DESCONHECIDA', model: 'X'),
    );
    expect(match.catalogUrl, isEmpty);
    expect(match.status, contains('Aguardando'));
  });

  test('fonte OEM conhecida continua disponível', () {
    final match = OemCatalogService().match(
      Asset(id: '008-001', description: 'Retroescavadeira', brand: 'NEW HOLLAND', model: 'B110B'),
    );
    expect(match.catalogUrl, isNotEmpty);
    expect(match.provider, contains('New Holland'));
  });
}
