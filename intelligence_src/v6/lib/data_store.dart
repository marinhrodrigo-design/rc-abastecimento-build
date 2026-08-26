import 'package:shared_preferences/shared_preferences.dart';

import 'models.dart';

class DataStore {
  static const _assetsKey = 'v6_assets';
  static const _partsKey = 'v6_part_usages';
  static const _readingsKey = 'v6_meter_readings';
  static const _anomaliesKey = 'v6_anomalies';
  static const _rulesKey = 'v6_learning_rules';

  final List<Asset> assets = [];
  final List<PartUsage> partUsages = [];
  final List<MeterReading> readings = [];
  final List<Anomaly> anomalies = [];
  final List<LearningRule> learningRules = [];

  Future<void> load() async {
    final p = await SharedPreferences.getInstance();
    assets
      ..clear()
      ..addAll(decodeList(p.getString(_assetsKey)).map(Asset.fromJson));
    partUsages
      ..clear()
      ..addAll(decodeList(p.getString(_partsKey)).map(PartUsage.fromJson));
    readings
      ..clear()
      ..addAll(decodeList(p.getString(_readingsKey)).map(MeterReading.fromJson));
    anomalies
      ..clear()
      ..addAll(decodeList(p.getString(_anomaliesKey)).map(Anomaly.fromJson));
    learningRules
      ..clear()
      ..addAll(decodeList(p.getString(_rulesKey)).map(LearningRule.fromJson));
    if (assets.isEmpty) {
      assets.addAll(_simulatorAssets());
      learningRules.add(LearningRule(
        key: 'location:FROTAS',
        value: 'OFICINA BANGU / BASE_OFICINA_TANQUE',
        reason: 'Regra operacional confirmada pelo administrador.',
        updatedAt: DateTime.now(),
        confidence: 1,
        confirmed: true,
      ));
      learningRules.add(LearningRule(
        key: 'fueling:passenger_cars',
        value: 'PLUXEE_EXTERNO',
        reason: 'Carros leves não abastecem no tanque interno.',
        updatedAt: DateTime.now(),
        confidence: 1,
        confirmed: true,
      ));
      await saveAll();
    }
  }

  Future<void> saveAll() async {
    final p = await SharedPreferences.getInstance();
    await p.setString(_assetsKey, encodeList(assets, (e) => e.toJson()));
    await p.setString(_partsKey, encodeList(partUsages, (e) => e.toJson()));
    await p.setString(_readingsKey, encodeList(readings, (e) => e.toJson()));
    await p.setString(_anomaliesKey, encodeList(anomalies, (e) => e.toJson()));
    await p.setString(_rulesKey, encodeList(learningRules, (e) => e.toJson()));
  }

  Future<void> importAssetsBatch(List<Asset> incoming) async {
    for (final a in incoming) {
      final i = assets.indexWhere((x) => x.id.trim().toUpperCase() == a.id.trim().toUpperCase());
      if (i >= 0) {
        final old = assets[i];
        assets[i] = Asset(
          id: old.id,
          description: a.description.isEmpty ? old.description : a.description,
          brand: a.brand.isEmpty ? old.brand : a.brand,
          model: a.model.isEmpty ? old.model : a.model,
          year: a.year.isEmpty ? old.year : a.year,
          serial: a.serial.isEmpty ? old.serial : a.serial,
          plate: a.plate.isEmpty ? old.plate : a.plate,
          meterType: a.meterType == 'NAO_INFORMADO' ? old.meterType : a.meterType,
        );
      } else {
        assets.add(a);
      }
    }
    await saveAll();
  }

  Future<void> updateAsset(Asset updated) async {
    final i = assets.indexWhere((a) => a.id == updated.id);
    if (i < 0) {
      assets.add(updated);
    } else {
      assets[i] = updated;
    }
    await saveAll();
  }

  Future<void> addPartUsages(List<PartUsage> values) async {
    for (final value in values) {
      final exists = partUsages.any((p) =>
          p.assetId == value.assetId &&
          p.date == value.date &&
          p.os == value.os &&
          p.rm == value.rm &&
          p.reference == value.reference &&
          p.partName == value.partName &&
          p.quantity == value.quantity);
      if (!exists) partUsages.add(value);
    }
    await saveAll();
  }

  Future<void> addReadings(List<MeterReading> values) async {
    for (final value in values) {
      final exists = readings.any((r) =>
          r.assetId == value.assetId &&
          r.date == value.date &&
          r.rawValue == value.rawValue &&
          r.source == value.source);
      if (!exists) readings.add(value);
    }
    await saveAll();
  }

  Future<void> addAnomaly(Anomaly value) async {
    if (!anomalies.any((a) => a.id == value.id)) anomalies.add(value);
    await saveAll();
  }

  Future<void> resolveAnomaly(String id) async {
    final i = anomalies.indexWhere((a) => a.id == id);
    if (i >= 0) anomalies[i] = anomalies[i].copyWith(resolved: true);
    await saveAll();
  }

  Future<void> learn(LearningRule rule) async {
    final i = learningRules.indexWhere((r) => r.key == rule.key);
    if (i >= 0) {
      learningRules[i] = rule;
    } else {
      learningRules.add(rule);
    }
    await saveAll();
  }

  LearningRule? rule(String key) {
    for (final r in learningRules) {
      if (r.key == key) return r;
    }
    return null;
  }

  static List<Asset> _simulatorAssets() => [
        Asset(id: '034-012', description: 'Retroescavadeira', brand: 'NEW HOLLAND', model: 'B90B', serial: 'HBZNB90BPCAH03860', meterType: 'HORIMETRO'),
        Asset(id: '034-014', description: 'Retroescavadeira', brand: 'NEW HOLLAND', model: 'B110BT4', serial: 'HBZN110BCDAH09466', meterType: 'HORIMETRO'),
        Asset(id: '034-015', description: 'Retroescavadeira', brand: 'NEW HOLLAND', model: 'B110BT4', serial: 'HBZN110BCDAH09468', meterType: 'HORIMETRO'),
        Asset(id: '034-016', description: 'Retroescavadeira', brand: 'NEW HOLLAND', model: 'B110BT4', serial: 'HBZN110BCDAH09469', meterType: 'HORIMETRO'),
        Asset(id: '034-017', description: 'Retroescavadeira', brand: 'NEW HOLLAND', model: 'B110BT4', serial: 'HBZN110BCDAH09506', meterType: 'HORIMETRO'),
        Asset(id: '034-018', description: 'Retroescavadeira', brand: 'NEW HOLLAND', model: 'B110BT4', serial: 'HBZN110BCDAH09507', meterType: 'HORIMETRO'),
        Asset(id: '034-019', description: 'Retroescavadeira', brand: 'NEW HOLLAND', model: 'B110BT4', serial: 'HBZN110BCDAH09624', meterType: 'HORIMETRO'),
        Asset(id: '034-020', description: 'Retroescavadeira', brand: 'NEW HOLLAND', model: 'B110BT4', serial: 'HBZN110BCDAH09625', meterType: 'HORIMETRO'),
        Asset(id: '034-022', description: 'Retroescavadeira', brand: 'JOHN DEERE', model: '310K', serial: 'IT0310KXHDC249866', meterType: 'HORIMETRO'),
        Asset(id: '034-024', description: 'Retroescavadeira', brand: 'JOHN DEERE', model: '310K', serial: 'IT0310KXPDC251347', meterType: 'HORIMETRO'),
        Asset(id: '034-025', description: 'Retroescavadeira', brand: 'NEW HOLLAND', model: 'B95BT4', serial: 'HBZNB95BJEAH11696', meterType: 'HORIMETRO'),
        Asset(id: '034-027', description: 'Retroescavadeira', brand: 'NEW HOLLAND', model: 'B95BT4', serial: 'HBZNB95BKEAH11681', meterType: 'HORIMETRO'),
        Asset(id: '034-028', description: 'Retroescavadeira', brand: 'NEW HOLLAND', model: 'B95C', serial: 'HR7NB95CCRAH35053', meterType: 'HORIMETRO'),
        Asset(id: '034-036', description: 'Retroescavadeira', brand: 'NEW HOLLAND', model: 'B95C', serial: 'HBZNB95CTSAH38283', meterType: 'HORIMETRO'),
        Asset(id: '035-001', description: 'Escavadeira', brand: 'NEW HOLLAND', model: 'E215BLCH', serial: 'NAAA05857', meterType: 'HORIMETRO'),
        Asset(id: '033-003', description: 'Pá carregadeira', brand: 'NEW HOLLAND', model: '12C', serial: 'HBZN012CCCAE01891', meterType: 'HORIMETRO'),
        Asset(id: '033-004', description: 'Carregadeira compacta', brand: 'BOBCAT', model: 'S450', serial: 'B1ED14785', meterType: 'HORIMETRO'),
        Asset(id: '054-001', description: 'Fresadora de asfalto', brand: 'WIRTGEN', model: 'DC2000', serial: '113', meterType: 'HORIMETRO'),
        Asset(id: '044-001', description: 'Vibro acabadora', brand: 'CIBER', model: 'AF4000', serial: 'CP400155', meterType: 'HORIMETRO'),
        Asset(id: '044-003', description: 'Vibro acabadora', brand: 'LEEBOY', model: '8500', meterType: 'HORIMETRO'),
      ];
}
