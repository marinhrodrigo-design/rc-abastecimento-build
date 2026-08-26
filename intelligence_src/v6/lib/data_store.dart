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

    if (assets.isEmpty) assets.addAll(_simulatorAssets());
    if (partUsages.isEmpty) partUsages.addAll(_simulatorPartEvidence());
    if (readings.isEmpty) readings.addAll(_simulatorReadings());

    _ensureConfirmedRule(
      'location:FROTAS',
      'OFICINA BANGU / BASE_OFICINA_TANQUE',
      'Regra operacional confirmada pelo administrador.',
    );
    _ensureConfirmedRule(
      'fueling:passenger_cars',
      'PLUXEE_EXTERNO',
      'Carros leves não abastecem no tanque interno.',
    );

    if (!anomalies.any((a) => a.id == 'asset:034-028:serial-conflict')) {
      anomalies.add(Anomaly(
        id: 'asset:034-028:serial-conflict',
        title: 'Série do ativo 034-028 precisa de confirmação',
        message:
            'Duas fontes apresentam séries diferentes para o 034-028: O.S. = HBZNB95CCRAH35053; relatório de estoque/PDF = HR7NB95CCRAH35053. O Intelligence não escolheu nenhuma automaticamente.',
        severity: 'alta',
        createdAt: DateTime.now(),
        assetId: '034-028',
        needsConfirmation: true,
        ruleKey: 'asset:034-028:serial',
      ));
    }
    await saveAll();
  }

  void _ensureConfirmedRule(String key, String value, String reason) {
    if (learningRules.any((r) => r.key == key)) return;
    learningRules.add(LearningRule(
      key: key,
      value: value,
      reason: reason,
      updatedAt: DateTime.now(),
      confidence: 1,
      confirmed: true,
    ));
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
      final i = assets.indexWhere(
        (x) => x.id.trim().toUpperCase() == a.id.trim().toUpperCase(),
      );
      if (i >= 0) {
        final old = assets[i];
        if (old.serial.isNotEmpty &&
            a.serial.isNotEmpty &&
            old.serial.toUpperCase() != a.serial.toUpperCase()) {
          await addAnomaly(Anomaly(
            id: 'asset:${old.id}:serial:${old.serial}:${a.serial}',
            title: 'Conflito de chassi/série',
            message:
                '${old.id}: valor atual "${old.serial}" e nova fonte "${a.serial}". Confirme manualmente antes de substituir.',
            severity: 'alta',
            createdAt: DateTime.now(),
            assetId: old.id,
            needsConfirmation: true,
            ruleKey: 'asset:${old.id}:serial',
          ));
        }
        assets[i] = Asset(
          id: old.id,
          description: a.description.isEmpty ? old.description : a.description,
          brand: a.brand.isEmpty ? old.brand : a.brand,
          model: a.model.isEmpty ? old.model : a.model,
          year: a.year.isEmpty ? old.year : a.year,
          serial: old.serial.isEmpty ? a.serial : old.serial,
          plate: a.plate.isEmpty ? old.plate : a.plate,
          meterType:
              a.meterType == 'NAO_INFORMADO' ? old.meterType : a.meterType,
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

  static List<MeterReading> _simulatorReadings() => [
        MeterReading(
          assetId: '034-020',
          date: DateTime(2025, 12, 4),
          rawValue: '1713',
          value: 1713,
          type: 'HORIMETRO',
          source: 'O.S. 3552 • Revisão preventiva 250 h',
          confidence: 1,
        ),
        MeterReading(
          assetId: '034-020',
          date: DateTime(2026, 1, 22),
          rawValue: '1748',
          value: 1748,
          type: 'HORIMETRO',
          source: 'O.S. 3692',
          confidence: 1,
        ),
        MeterReading(
          assetId: '034-020',
          date: DateTime(2026, 3, 27),
          rawValue: '1810',
          value: 1810,
          type: 'HORIMETRO',
          source: 'O.S. 3937',
          confidence: 1,
        ),
        MeterReading(
          assetId: '034-020',
          date: DateTime(2026, 4, 14),
          rawValue: '1810',
          value: 1810,
          type: 'HORIMETRO',
          source: 'O.S. 4005',
          confidence: 1,
        ),
        MeterReading(
          assetId: '034-020',
          date: DateTime(2026, 5, 20),
          rawValue: '1834',
          value: 1834,
          type: 'HORIMETRO',
          source: 'O.S. 4160',
          confidence: 1,
        ),
      ];

  static List<PartUsage> _simulatorPartEvidence() => [
        PartUsage(
          assetId: '034-024',
          date: DateTime(2025, 1, 2),
          os: '2231',
          rm: '2178/2',
          internalCode: '983',
          partName: 'FILTRO OLEO HIDRAULICO - JOHN DEERE 310K',
          reference: 'AT367840',
          quantity: 1,
          unit: 'un',
          source: 'relatorio certo desde 2025.pdf • página 5',
        ),
        PartUsage(
          assetId: '034-024',
          date: DateTime(2025, 1, 2),
          os: '2231',
          rm: '2178**/4',
          internalCode: '1702',
          partName: 'M-HIDRAULICO AW68 HLP DRUM 200L',
          reference: '122537',
          quantity: 80,
          unit: 'l',
          source: 'relatorio certo desde 2025.pdf • página 4',
        ),
        PartUsage(
          assetId: '034-020',
          date: DateTime(2025, 1, 20),
          os: '2368',
          rm: '2305/3',
          internalCode: '427',
          partName: 'FILTRO LUBRIFICANTE DO MOTOR',
          reference: '84228488',
          quantity: 1,
          unit: 'un',
          source: 'relatorio certo desde 2025.pdf • página 95',
        ),
        PartUsage(
          assetId: '034-020',
          date: DateTime(2025, 1, 20),
          os: '2368',
          rm: '2326**',
          internalCode: '1610',
          partName: 'M-DELVAC MODERN 15W40 SD V3',
          reference: '123738',
          quantity: 15,
          unit: 'l',
          source: 'relatorio certo desde 2025.pdf • página 96',
        ),
      ];

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
        Asset(id: '034-028', description: 'Retroescavadeira', brand: 'NEW HOLLAND', model: 'B95C', serial: '', meterType: 'HORIMETRO'),
        Asset(id: '034-036', description: 'Retroescavadeira', brand: 'NEW HOLLAND', model: 'B95C', serial: 'HBZNB95CTSAH38283', meterType: 'HORIMETRO'),
        Asset(id: '035-001', description: 'Escavadeira', brand: 'NEW HOLLAND', model: 'E215BLCH', serial: 'NAAA05857', meterType: 'HORIMETRO'),
        Asset(id: '033-003', description: 'Pá carregadeira', brand: 'NEW HOLLAND', model: '12C', serial: 'HBZN012CCCAE01891', meterType: 'HORIMETRO'),
        Asset(id: '033-004', description: 'Carregadeira compacta', brand: 'BOBCAT', model: 'S450', serial: 'B1ED14785', meterType: 'HORIMETRO'),
        Asset(id: '054-001', description: 'Fresadora de asfalto', brand: 'WIRTGEN', model: 'DC2000', serial: '113', meterType: 'HORIMETRO'),
        Asset(id: '044-001', description: 'Vibro acabadora', brand: 'CIBER', model: 'AF4000', serial: 'CP400155', meterType: 'HORIMETRO'),
        Asset(id: '044-003', description: 'Vibro acabadora', brand: 'LEEBOY', model: '8500', meterType: 'HORIMETRO'),
      ];
}
