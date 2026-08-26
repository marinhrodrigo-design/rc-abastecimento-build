import 'package:flutter_test/flutter_test.dart';
import 'package:rc_intelligence/models.dart';
import 'package:rc_intelligence/oem_catalog.dart';

void main() {
  test('New Holland B110BT4 aponta para MyCNH Store', () {
    final service = OemCatalogService();
    final match = service.match(Asset(
      id: '034-020',
      description: 'Retroescavadeira',
      brand: 'NEW HOLLAND',
      model: 'B110BT4',
      serial: 'HBZN110BCDAH09625',
    ));
    expect(match.provider, contains('New Holland'));
    expect(match.catalogUrl, contains('mycnhstore.com'));
    expect(match.status, contains('série'));
  });

  test('John Deere AT367840 abre pagina oficial da peca', () {
    final service = OemCatalogService();
    final match = service.match(
      Asset(id: '034-024', description: 'Retroescavadeira', brand: 'JOHN DEERE', model: '310K', serial: 'IT0310KXPDC251347'),
      partReference: 'AT367840',
    );
    expect(match.partUrl, isNotNull);
    expect(match.partUrl, contains('shop.deere.com'));
  });

  test('Wirtgen usa WIDOS/portal oficial', () {
    final match = OemCatalogService().match(Asset(id: '054-001', description: 'Fresadora', brand: 'WIRTGEN', model: 'DC2000', serial: '113'));
    expect(match.catalogUrl, contains('wirtgen-group.com'));
  });
}
