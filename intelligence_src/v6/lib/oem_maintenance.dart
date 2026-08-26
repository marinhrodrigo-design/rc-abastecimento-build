import 'dart:math';

import 'models.dart';

class OemMaintenanceRule {
  const OemMaintenanceRule({
    required this.id,
    required this.brandContains,
    required this.modelContains,
    required this.serviceName,
    required this.interval,
    required this.unit,
    required this.sourceTitle,
    required this.sourceUrl,
    required this.evidence,
    this.fullPreventive = false,
    this.confidence = 1,
  });

  final String id;
  final String brandContains;
  final String modelContains;
  final String serviceName;
  final double interval;
  final String unit;
  final String sourceTitle;
  final String sourceUrl;
  final String evidence;
  final bool fullPreventive;
  final double confidence;

  bool matches(Asset asset) {
    final brand = asset.brand.toUpperCase();
    final model = asset.model.toUpperCase();
    return brand.contains(brandContains.toUpperCase()) &&
        model.contains(modelContains.toUpperCase());
  }
}

class OemMaintenanceForecast {
  const OemMaintenanceForecast({
    required this.rule,
    required this.latestKnownMeter,
    required this.latestReadingDate,
    required this.estimatedCurrentMeter,
    required this.currentMeterEstimated,
    required this.nextTarget,
    required this.remaining,
    required this.baselineConfirmed,
    required this.levelCode,
    required this.levelLabel,
    required this.levelEmoji,
    this.estimatedDate,
  });

  final OemMaintenanceRule rule;
  final double latestKnownMeter;
  final DateTime latestReadingDate;
  final double estimatedCurrentMeter;
  final bool currentMeterEstimated;
  final double nextTarget;
  final double remaining;
  final bool baselineConfirmed;
  final String levelCode;
  final String levelLabel;
  final String levelEmoji;
  final DateTime? estimatedDate;

  String get unitLabel => rule.unit == 'H' ? 'h' : 'km';

  String get targetText => '${_fmt(nextTarget)} $unitLabel';

  String get remainingText => remaining < 0
      ? '${_fmt(remaining.abs())} $unitLabel ultrapassadas'
      : '${_fmt(remaining)} $unitLabel';

  String get estimatedDateText {
    final d = estimatedDate;
    if (d == null) return 'dados insuficientes para estimar a data';
    return '${d.day.toString().padLeft(2, '0')}/${d.month.toString().padLeft(2, '0')}/${d.year}';
  }

  String get userMessage {
    if (rule.fullPreventive) {
      return 'De acordo com a regra OEM, a próxima revisão preventiva deve ser em $targetText. '
          'A estimativa para a revisão de acordo com a OEM é $estimatedDateText.';
    }
    return 'De acordo com a regra OEM, ${rule.serviceName} deve ocorrer em $targetText. '
        'A estimativa é $estimatedDateText.';
  }

  static String _fmt(double value) {
    if ((value - value.roundToDouble()).abs() < .05) return value.round().toString();
    return value.toStringAsFixed(1).replaceAll('.', ',');
  }
}

class OemMaintenanceService {
  OemMaintenanceService({List<OemMaintenanceRule>? rules})
      : rules = rules ?? verifiedRules;

  final List<OemMaintenanceRule> rules;

  // Somente regras com evidência OEM pública/confirmada entram aqui.
  // Uma regra de item isolado não é promovida automaticamente a revisão completa.
  static const verifiedRules = <OemMaintenanceRule>[
    OemMaintenanceRule(
      id: 'nh_b110b_engine_oil_500h',
      brandContains: 'NEW HOLLAND',
      modelContains: 'B110B',
      serviceName: 'Troca do óleo do motor',
      interval: 500,
      unit: 'H',
      sourceTitle: 'New Holland Construction - folheto oficial Série B',
      sourceUrl:
          'https://construction.cdn.newholland.com/lar/pt/Gallery/Documents/Retroescavadeiras/B5-0008-19-NHCE_Folheto_Retros_B90B_B95B_B110B_PO.pdf',
      evidence:
          'O material oficial informa intervalo de 500 horas para troca do óleo do motor.',
      fullPreventive: false,
    ),
  ];

  List<OemMaintenanceRule> rulesFor(Asset asset) =>
      rules.where((r) => r.matches(asset)).toList(growable: false);

  OemMaintenanceRule? fullPreventiveRuleFor(Asset asset) {
    for (final rule in rules) {
      if (rule.fullPreventive && rule.matches(asset)) return rule;
    }
    return null;
  }

  OemMaintenanceForecast? forecastFullPreventive({
    required Asset asset,
    required List<MeterReading> readings,
    required double averagePerDay,
    double? lastCompletedMeter,
    DateTime? now,
  }) {
    final rule = fullPreventiveRuleFor(asset);
    if (rule == null) return null;
    return forecastRule(
      asset: asset,
      rule: rule,
      readings: readings,
      averagePerDay: averagePerDay,
      lastCompletedMeter: lastCompletedMeter,
      now: now,
    );
  }

  OemMaintenanceForecast? forecastRule({
    required Asset asset,
    required OemMaintenanceRule rule,
    required List<MeterReading> readings,
    required double averagePerDay,
    double? lastCompletedMeter,
    DateTime? now,
  }) {
    final expectedType = rule.unit == 'H' ? 'HORIMETRO' : 'KM';
    final valid = readings
        .where((r) =>
            r.assetId == asset.id &&
            r.confidence >= .6 &&
            r.type.toUpperCase() == expectedType)
        .toList()
      ..sort((a, b) => a.date.compareTo(b.date));
    if (valid.isEmpty || rule.interval <= 0) return null;

    final latest = valid.last;
    final referenceNow = now ?? DateTime.now();
    var estimatedCurrent = latest.value;
    var estimated = false;

    if (averagePerDay > 0 && referenceNow.isAfter(latest.date)) {
      final elapsedDays = max(0, referenceNow.difference(latest.date).inDays);
      if (elapsedDays > 0) {
        estimatedCurrent += averagePerDay * elapsedDays;
        estimated = true;
      }
    }

    final baselineConfirmed = lastCompletedMeter != null;
    var nextTarget = baselineConfirmed
        ? lastCompletedMeter + rule.interval
        : (estimatedCurrent / rule.interval).ceil() * rule.interval;
    if (!baselineConfirmed && (nextTarget - estimatedCurrent).abs() < .0001) {
      nextTarget += rule.interval;
    }

    final remaining = nextTarget - estimatedCurrent;
    final level = levelForRemaining(remaining);

    DateTime? estimatedDate;
    if (averagePerDay > 0 && remaining >= 0) {
      final days = max(0, remaining / averagePerDay).ceil();
      estimatedDate = referenceNow.add(Duration(days: days));
    }

    return OemMaintenanceForecast(
      rule: rule,
      latestKnownMeter: latest.value,
      latestReadingDate: latest.date,
      estimatedCurrentMeter: estimatedCurrent,
      currentMeterEstimated: estimated,
      nextTarget: nextTarget,
      remaining: remaining,
      baselineConfirmed: baselineConfirmed,
      levelCode: level.code,
      levelLabel: level.label,
      levelEmoji: level.emoji,
      estimatedDate: estimatedDate,
    );
  }

  OemAlertLevel levelForRemaining(double remaining) {
    if (remaining < 0) {
      return const OemAlertLevel('OVERDUE', 'Vencida', '⚫');
    }
    if (remaining <= 10) {
      return const OemAlertLevel('VERY_CLOSE', 'Muito próxima', '🔴');
    }
    if (remaining <= 50) {
      return const OemAlertLevel('SCHEDULE', 'Programar manutenção', '🟠');
    }
    if (remaining <= 100) {
      return const OemAlertLevel('ATTENTION', 'Atenção', '🟡');
    }
    if (remaining <= 250) {
      return const OemAlertLevel('PLANNING', 'Planejamento', '🔵');
    }
    return const OemAlertLevel('MONITOR', 'Acompanhamento', '');
  }
}

class OemAlertLevel {
  const OemAlertLevel(this.code, this.label, this.emoji);
  final String code;
  final String label;
  final String emoji;
}
