class V6CatalogMatch {
  const V6CatalogMatch({
    required this.provider,
    required this.title,
    required this.catalogUrl,
    required this.compatibility,
    required this.notes,
    this.partUrl = '',
  });

  final String provider;
  final String title;
  final String catalogUrl;
  final String compatibility;
  final String notes;
  final String partUrl;

  bool get hasCatalog => catalogUrl.trim().isNotEmpty;
  bool get hasDirectPart => partUrl.trim().isNotEmpty;
}

class V6OemCatalogService {
  const V6OemCatalogService();

  static const newHollandHome =
      'https://www.mycnhstore.com/sa/pt/newhollandce/sa/cn/SA';
  static const newHollandBFamily =
      'https://www.mycnhstore.com/sa/pt/newhollandce/light-equipment/loader-backhoes/b-b/cn/SA_F_S_49_LOA_206_B_B';
  static const newHollandE215B =
      'https://www.mycnhstore.com/sa/pt/newhollandce/sa/heavy-equipment/crawler-excavators/safr24cra365eb/crawler-excavator-brazil/cn/AF07734F-E6BE-E111-9FCE-005056875BD6';
  static const newHolland12C =
      'https://www.mycnhstore.com/sa/pt/newhollandce/sa/heavy-equipment/wheel-loaders/safr90whe233c/wheel-loader-brazil/cn/E0EA724F-E6BE-E111-9FCE-005056875BD6';
  static const deereParts =
      'https://www.deere.com.br/pt/pe%C3%A7as-e-servi%C3%A7os/pe%C3%A7as/';
  static const bobcatParts =
      'https://www.bobcat.com/na/en/parts-service/parts-catalog';
  static const bobcatS450 = 'https://shop.bobcat.com/bobcat-s450';
  static const wirtgenParts =
      'https://www.wirtgen-group.com/pt-br/pecas-e-servicos/pecas-de-reposicao/';
  static const catParts = 'https://parts.cat.com/pt/catcorp/parts-diagram';
  static const vwco = 'https://www.vwco.com.br/';
  static const mercedesTrucks = 'https://www.mercedes-benz-trucks.com/';
  static const leeboyParts = 'https://leeboy.com/parts/';

  V6CatalogMatch match({
    required String manufacturer,
    required String model,
    required String serial,
    String partReference = '',
  }) {
    final brand = _n(manufacturer);
    final mdl = _n(model);
    final serialKnown = serial.trim().isNotEmpty;
    final compatibility = serialKnown
        ? 'Modelo identificado; série/chassi disponível para validação fina.'
        : 'Modelo identificado; série/chassi ainda precisa ser informado.';

    if (brand.contains('NEW HOLLAND')) {
      var url = newHollandHome;
      var title = 'MyCNH Store • New Holland Construction';
      if (mdl.contains('B110B') ||
          mdl.contains('B110BT4') ||
          mdl.contains('B90B') ||
          mdl.contains('B95B') ||
          mdl.contains('B95C')) {
        url = newHollandBFamily;
        title = 'MyCNH Store • família de retroescavadeiras B';
      } else if (mdl.contains('E215B')) {
        url = newHollandE215B;
        title = 'MyCNH Store • E215B';
      } else if (mdl.contains('12C')) {
        url = newHolland12C;
        title = 'MyCNH Store • 12C';
      }
      return V6CatalogMatch(
        provider: 'New Holland / MyCNH Store',
        title: title,
        catalogUrl: url,
        compatibility: compatibility,
        notes:
            'Priorizar a seleção por número de série e confirmar a referência no desenho/grupo funcional. O catálogo de peças não substitui o manual de manutenção para intervalos e capacidades.',
      );
    }

    if (brand.contains('JOHN DEERE') || brand == 'DEERE') {
      final ref = partReference.trim().toUpperCase();
      var partUrl = '';
      if (ref == 'AT367840') {
        partUrl =
            'https://shop.deere.com/br/pt/product/AT367840%3A-Filtro-de-%C3%93leo-Hidr%C3%A1ulico/p/AT367840';
      }
      return V6CatalogMatch(
        provider: 'John Deere',
        title: mdl.contains('310K')
            ? 'John Deere • peças para 310K'
            : 'John Deere • peças e catálogos',
        catalogUrl: deereParts,
        partUrl: partUrl,
        compatibility: compatibility,
        notes: partUrl.isNotEmpty
            ? 'A referência AT367840 possui página oficial e a John Deere lista o 310K entre os equipamentos compatíveis.'
            : 'Usar PIN/chassi, modelo e referência para confirmar aplicação antes de classificar a peça como compatível.',
      );
    }

    if (brand.contains('BOBCAT')) {
      return V6CatalogMatch(
        provider: 'Bobcat',
        title: mdl.contains('S450')
            ? 'Bobcat S450 • peças, acessórios e manuais'
            : 'Bobcat Parts Catalog',
        catalogUrl: mdl.contains('S450') ? bobcatS450 : bobcatParts,
        compatibility: compatibility,
        notes:
            'O catálogo oficial permite busca por série, modelo ou peça; a própria Bobcat informa que o número de série é a forma mais precisa.',
      );
    }

    if (brand.contains('WIRTGEN') || brand.contains('CIBER')) {
      return V6CatalogMatch(
        provider: 'Wirtgen Group / WIDOS',
        title: 'Wirtgen Group • Parts / WIDOS',
        catalogUrl: wirtgenParts,
        compatibility: compatibility,
        notes:
            'WIDOS reúne catálogo completo de peças, desenhos técnicos, manual de operação e diagramas hidráulicos/elétricos. Algumas funções exigem login no portal.',
      );
    }

    if (brand.contains('CATERPILLAR') || brand == 'CAT') {
      return V6CatalogMatch(
        provider: 'Caterpillar',
        title: 'Cat Parts Store • diagramas por equipamento/série',
        catalogUrl: catParts,
        compatibility: compatibility,
        notes:
            'O Cat Parts Store solicita equipamento e número de série para mostrar diagramas precisos e peças compatíveis.',
      );
    }

    if (brand.contains('VOLKSWAGEN') || brand == 'VW') {
      return V6CatalogMatch(
        provider: 'Volkswagen Caminhões e Ônibus',
        title: 'Portal oficial Volkswagen Caminhões e Ônibus',
        catalogUrl: vwco,
        compatibility: 'Fonte OEM identificada; catálogo técnico detalhado pode exigir rede/concessionário.',
        notes: 'Usar modelo e chassi como identificadores principais; não inventar referência quando o portal público não confirmar.',
      );
    }

    if (brand.contains('MERCEDES')) {
      return V6CatalogMatch(
        provider: 'Mercedes-Benz Trucks',
        title: 'Portal oficial Mercedes-Benz Trucks',
        catalogUrl: mercedesTrucks,
        compatibility: 'Fonte OEM identificada; catálogo técnico detalhado pode exigir acesso autorizado.',
        notes: 'Usar VIN/chassi para confirmar aplicação e documentação da configuração exata.',
      );
    }

    if (brand.contains('LEEBOY')) {
      return V6CatalogMatch(
        provider: 'LeeBoy',
        title: 'LeeBoy Parts',
        catalogUrl: leeboyParts,
        compatibility: compatibility,
        notes: 'Confirmar modelo e série antes de classificar uma referência como OEM compatível.',
      );
    }

    return const V6CatalogMatch(
      provider: 'OEM ainda não mapeado',
      title: 'Pesquisa OEM necessária',
      catalogUrl: '',
      compatibility: 'Não confirmado',
      notes:
          'O Intelligence mantém a regra interna e não inventa catálogo, intervalo ou compatibilidade. A fonte oficial precisa ser localizada e validada.',
    );
  }

  String _n(String value) => value
      .toUpperCase()
      .replaceAll('Á', 'A')
      .replaceAll('À', 'A')
      .replaceAll('Â', 'A')
      .replaceAll('Ã', 'A')
      .replaceAll('É', 'E')
      .replaceAll('Ê', 'E')
      .replaceAll('Í', 'I')
      .replaceAll('Ó', 'O')
      .replaceAll('Ô', 'O')
      .replaceAll('Õ', 'O')
      .replaceAll('Ú', 'U')
      .replaceAll('Ç', 'C')
      .trim();
}
