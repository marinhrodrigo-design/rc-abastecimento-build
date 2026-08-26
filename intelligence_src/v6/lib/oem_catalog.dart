import 'models.dart';

class CatalogMatch {
  CatalogMatch({
    required this.provider,
    required this.title,
    required this.catalogUrl,
    required this.status,
    required this.notes,
    this.partUrl,
  });
  final String provider;
  final String title;
  final String catalogUrl;
  final String status;
  final String notes;
  final String? partUrl;
}

class OemCatalogService {
  static const _newHollandB =
      'https://www.mycnhstore.com/sa/pt/newhollandce/light-equipment/loader-backhoes/b-b/cn/SA_F_S_49_LOA_206_B_B';
  static const _newHollandE215B =
      'https://www.mycnhstore.com/sa/pt/newhollandce/sa/heavy-equipment/crawler-excavators/safr24cra365eb/crawler-excavator-brazil/cn/AF07734F-E6BE-E111-9FCE-005056875BD6';
  static const _newHolland12C =
      'https://www.mycnhstore.com/sa/pt/newhollandce/sa/heavy-equipment/wheel-loaders/safr90whe233c/wheel-loader-brazil/cn/E0EA724F-E6BE-E111-9FCE-005056875BD6';
  static const _newHollandHome =
      'https://www.mycnhstore.com/sa/pt/newhollandce/sa/cn/SA';
  static const _deere =
      'https://www.deere.com.br/pt/pe%C3%A7as-e-servi%C3%A7os/pe%C3%A7as/';
  static const _bobcat = 'https://www.bobcat.com/na/en/parts-service/parts-catalog';
  static const _bobcatS450 = 'https://shop.bobcat.com/bobcat-s450';
  static const _wirtgen =
      'https://www.wirtgen-group.com/en-us/parts-and-service/spare-parts/';
  static const _cat = 'https://parts.cat.com/pt/catcorp/parts-diagram';
  static const _vw = 'https://www.vwco.com.br/';
  static const _mercedes = 'https://www.mercedes-benz-trucks.com/';
  static const _leeboy = 'https://leeboy.com/parts/';

  CatalogMatch match(Asset asset, {String partReference = ''}) {
    final brand = asset.brand.toUpperCase();
    final model = asset.model.toUpperCase();
    final serialKnown = asset.serial.trim().isNotEmpty;
    final status = serialKnown ? 'Compatibilidade por modelo/série' : 'Compatibilidade por modelo';

    if (brand.contains('NEW HOLLAND')) {
      var url = _newHollandHome;
      var title = 'MyCNH Store - catálogo New Holland Construction';
      if (model.contains('B110B') || model.contains('B110BT4') || model.contains('B90B') || model.contains('B95B')) {
        url = _newHollandB;
        title = 'MyCNH Store - família B (retroescavadeiras)';
      } else if (model.contains('E215B')) {
        url = _newHollandE215B;
        title = 'MyCNH Store - E215B';
      } else if (model.contains('12C')) {
        url = _newHolland12C;
        title = 'MyCNH Store - 12C Turbo';
      }
      return CatalogMatch(
        provider: 'New Holland / MyCNH Store',
        title: title,
        catalogUrl: url,
        status: status,
        notes: 'Pesquisar por número de série e depois pela referência da peça para confirmar a aplicação.',
      );
    }

    if (brand.contains('JOHN DEERE') || brand == 'DEERE') {
      String? partUrl;
      if (partReference.toUpperCase() == 'AT367840') {
        partUrl =
            'https://shop.deere.com/br/pt/product/AT367840%3A-Filtro-de-%C3%93leo-Hidr%C3%A1ulico/p/AT367840';
      }
      return CatalogMatch(
        provider: 'John Deere',
        title: model.contains('310K') ? 'John Deere - peças para 310K' : 'John Deere - catálogo de peças',
        catalogUrl: _deere,
        partUrl: partUrl,
        status: status,
        notes: partUrl == null
            ? 'O portal oficial permite buscar por PIN, modelo, equipamento ou catálogo.'
            : 'Referência localizada em página oficial e compatível com 310K.',
      );
    }

    if (brand.contains('BOBCAT')) {
      return CatalogMatch(
        provider: 'Bobcat',
        title: model.contains('S450') ? 'Bobcat S450 - peças e manuais' : 'Bobcat Parts Catalog',
        catalogUrl: model.contains('S450') ? _bobcatS450 : _bobcat,
        status: status,
        notes: 'A Bobcat recomenda busca pelo número de série para maior precisão.',
      );
    }

    if (brand.contains('WIRTGEN') || brand.contains('CIBER')) {
      return CatalogMatch(
        provider: 'Wirtgen Group / WIDOS',
        title: 'Wirtgen Group - peças e documentação WIDOS',
        catalogUrl: _wirtgen,
        status: status,
        notes: 'WIDOS reúne catálogo, desenhos técnicos, instruções de operação e diagramas; parte do conteúdo exige login.',
      );
    }

    if (brand.contains('CATERPILLAR') || brand == 'CAT') {
      return CatalogMatch(
        provider: 'Caterpillar',
        title: 'Cat Parts Store - diagramas por número de série',
        catalogUrl: _cat,
        status: status,
        notes: 'Adicionar equipamento e número de série para obter diagramas e peças compatíveis.',
      );
    }

    if (brand.contains('VOLKSWAGEN') || brand == 'VW') {
      return CatalogMatch(
        provider: 'Volkswagen Caminhões e Ônibus',
        title: 'Portal oficial Volkswagen Caminhões e Ônibus',
        catalogUrl: _vw,
        status: 'Fonte OEM identificada; catálogo detalhado pode exigir rede/concessionário',
        notes: 'Manter modelo, chassi e referência da peça para conferência de aplicação.',
      );
    }

    if (brand.contains('MERCEDES')) {
      return CatalogMatch(
        provider: 'Mercedes-Benz Trucks',
        title: 'Portal oficial Mercedes-Benz Trucks',
        catalogUrl: _mercedes,
        status: 'Fonte OEM identificada; catálogo detalhado pode exigir acesso autorizado',
        notes: 'Usar VIN/chassi como identificador principal de aplicação.',
      );
    }

    if (brand.contains('LEEBOY')) {
      return CatalogMatch(
        provider: 'LeeBoy',
        title: 'LeeBoy Parts',
        catalogUrl: _leeboy,
        status: status,
        notes: 'Confirmar pelo modelo e número de série antes de classificar como peça OEM compatível.',
      );
    }

    return CatalogMatch(
      provider: 'OEM não identificado automaticamente',
      title: 'Pesquisa OEM necessária',
      catalogUrl: '',
      status: 'Aguardando fonte oficial',
      notes: 'O Intelligence não deve inventar catálogo ou intervalo de revisão.',
    );
  }
}
