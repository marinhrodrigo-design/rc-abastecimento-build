import 'dart:typed_data';

import 'package:excel/excel.dart';

import 'models.dart';

class AssetImportResult {
  AssetImportResult(this.assets, this.conflicts, this.notes);
  final List<Asset> assets;
  final List<String> conflicts;
  final List<String> notes;
}

class DataImportService {
  static const baseLocation = 'BASE_OFICINA_TANQUE';
  static const baseAddress = 'Av. Brasil 33060, Bangu, Rio de Janeiro';

  AssetImportResult parseAssets(Uint8List bytes) {
    final excel = Excel.decodeBytes(bytes);
    final assets = <Asset>[];
    final conflicts = <String>[];
    final notes = <String>[];

    for (final entry in excel.tables.entries) {
      final rows = entry.value.rows;
      if (rows.isEmpty) continue;
      var headerIndex = -1;
      Map<String, int> headers = {};
      for (var i = 0; i < rows.length && i < 20; i++) {
        final candidate = <String, int>{};
        for (var c = 0; c < rows[i].length; c++) {
          final key = _norm(_text(rows[i][c]?.value));
          if (key.isNotEmpty) candidate[key] = c;
        }
        if (_find(candidate, ['ATIVO', 'N DO ATIVO', 'Nº DO ATIVO', 'IDENTIFICACAO']) != null) {
          headerIndex = i;
          headers = candidate;
          break;
        }
      }
      if (headerIndex < 0) continue;

      final idCol = _find(headers, ['ATIVO', 'N DO ATIVO', 'Nº DO ATIVO', 'IDENTIFICACAO']);
      if (idCol == null) continue;
      final descCol = _find(headers, ['TIPO', 'DESCRICAO', 'EQUIPAMENTO']);
      final brandCol = _find(headers, ['MARCA', 'FABRICANTE']);
      final modelCol = _find(headers, ['MODELO']);
      final yearCol = _find(headers, ['ANO']);
      final serialCol = _find(headers, ['CHASSI', 'SERIE', 'N DE SERIE', 'Nº DE SERIE', 'CHASSI SERIE']);
      final plateCol = _find(headers, ['PLACA']);

      for (var r = headerIndex + 1; r < rows.length; r++) {
        final row = rows[r];
        String at(int? c) => c == null || c >= row.length ? '' : _text(row[c]?.value).trim();
        final id = at(idCol);
        if (id.isEmpty || id.toUpperCase().contains('TOTAL')) continue;
        var brand = at(brandCol);
        var model = at(modelCol);
        final description = at(descCol);
        final combined = '$description $brand $model ${at(serialCol)}';
        if (brand.isEmpty) brand = _inferBrand(combined);
        if (model.isEmpty) model = _inferModel(combined, brand);
        final asset = Asset(
          id: id,
          description: description,
          brand: brand,
          model: model,
          year: at(yearCol),
          serial: at(serialCol),
          plate: at(plateCol),
          meterType: _inferMeter(description),
        );
        if (assets.any((a) => a.id.toUpperCase() == asset.id.toUpperCase())) {
          conflicts.add('Ativo $id repetido na importação (${entry.key}, linha ${r + 1}).');
        } else {
          assets.add(asset);
        }
      }
      if (assets.isNotEmpty) notes.add('Aba ${entry.key}: ${assets.length} ativos identificados até aqui.');
    }
    if (assets.isEmpty) conflicts.add('Nenhuma tabela de ativos reconhecida. Confira os cabeçalhos.');
    return AssetImportResult(assets, conflicts, notes);
  }

  String normalizeLocation(String raw) {
    final n = _norm(raw);
    if (n == 'FROTAS' || n.contains('OFICINA BANGU') || n.contains('AV BRASIL 33060')) {
      return baseLocation;
    }
    return raw.trim();
  }

  bool baseFuelingProvesRelease(String rawLocation) => false;

  static String _text(Object? value) => value?.toString() ?? '';

  static String _norm(String value) => value
      .toUpperCase()
      .replaceAll('Ã', 'A')
      .replaceAll('Á', 'A')
      .replaceAll('Â', 'A')
      .replaceAll('Ç', 'C')
      .replaceAll('É', 'E')
      .replaceAll('Í', 'I')
      .replaceAll('Ó', 'O')
      .replaceAll('Õ', 'O')
      .replaceAll('Ú', 'U')
      .replaceAll(RegExp(r'[^A-Z0-9 ]'), ' ')
      .replaceAll(RegExp(r'\s+'), ' ')
      .trim();

  static int? _find(Map<String, int> headers, List<String> aliases) {
    for (final alias in aliases) {
      final wanted = _norm(alias);
      for (final e in headers.entries) {
        if (e.key == wanted || e.key.contains(wanted)) return e.value;
      }
    }
    return null;
  }

  static String _inferBrand(String raw) {
    final t = raw.toUpperCase();
    const brands = [
      'NEW HOLLAND', 'JOHN DEERE', 'VOLKSWAGEN', 'MERCEDES BENZ', 'MERCEDES-BENZ',
      'BOBCAT', 'WIRTGEN', 'CIBER', 'LEEBOY', 'CATERPILLAR', 'IVECO', 'FIAT', 'FORD', 'CHEVROLET'
    ];
    for (final b in brands) {
      if (t.contains(b)) return b.replaceAll('-', ' ');
    }
    return '';
  }

  static String _inferModel(String raw, String brand) {
    final t = raw.toUpperCase();
    const models = [
      'B110BT4', 'B110B', 'B95BT4', 'B95C', 'B90B', 'E215BLCH', 'E215B', '310K',
      '12C', 'S450', 'DC2000', 'AF4000', '8500', '26.280', '26/280', '26.260', '24.280',
      '17.190', '25.360', '2729', '2726', '1719'
    ];
    for (final m in models) {
      if (t.contains(m)) return m;
    }
    return '';
  }

  static String _inferMeter(String description) {
    final d = description.toUpperCase();
    if (d.contains('CAMINH') || d.contains('AUTOM') || d.contains('MICRO') || d.contains('PICK')) return 'KM';
    if (d.contains('ESCAVA') || d.contains('RETRO') || d.contains('CARREGA') || d.contains('FRESAD') || d.contains('ACABAD')) return 'HORIMETRO';
    return 'NAO_INFORMADO';
  }
}
