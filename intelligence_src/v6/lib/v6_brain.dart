class V6PartUsage {
  const V6PartUsage({
    required this.assetId,
    required this.date,
    required this.partName,
    required this.quantity,
    required this.unit,
    this.os = '',
    this.rm = '',
    this.internalCode = '',
    this.reference = '',
    this.source = '',
    this.defect = '',
    this.actionTaken = '',
  });

  final String assetId;
  final DateTime date;
  final String os;
  final String rm;
  final String internalCode;
  final String partName;
  final String reference;
  final double quantity;
  final String unit;
  final String source;
  final String defect;
  final String actionTaken;

  Map<String, dynamic> toJson() => {
        'assetId': assetId,
        'date': date.toIso8601String(),
        'os': os,
        'rm': rm,
        'internalCode': internalCode,
        'partName': partName,
        'reference': reference,
        'quantity': quantity,
        'unit': unit,
        'source': source,
        'defect': defect,
        'actionTaken': actionTaken,
      };

  factory V6PartUsage.fromJson(Map<String, dynamic> j) => V6PartUsage(
        assetId: '${j['assetId'] ?? ''}',
        date: DateTime.tryParse('${j['date'] ?? ''}') ?? DateTime(2000),
        os: '${j['os'] ?? ''}',
        rm: '${j['rm'] ?? ''}',
        internalCode: '${j['internalCode'] ?? ''}',
        partName: '${j['partName'] ?? ''}',
        reference: '${j['reference'] ?? ''}',
        quantity: (j['quantity'] as num?)?.toDouble() ??
            double.tryParse('${j['quantity'] ?? ''}'.replaceAll(',', '.')) ??
            0,
        unit: '${j['unit'] ?? ''}',
        source: '${j['source'] ?? ''}',
        defect: '${j['defect'] ?? ''}',
        actionTaken: '${j['actionTaken'] ?? ''}',
      );
}

class V6Anomaly {
  const V6Anomaly({
    required this.id,
    required this.title,
    required this.message,
    required this.severity,
    required this.createdAt,
    this.assetId = '',
    this.needsConfirmation = false,
    this.ruleKey = '',
    this.resolved = false,
    this.notified = false,
  });

  final String id;
  final String title;
  final String message;
  final String severity;
  final DateTime createdAt;
  final String assetId;
  final bool needsConfirmation;
  final String ruleKey;
  final bool resolved;
  final bool notified;

  V6Anomaly copyWith({bool? resolved, bool? notified}) => V6Anomaly(
        id: id,
        title: title,
        message: message,
        severity: severity,
        createdAt: createdAt,
        assetId: assetId,
        needsConfirmation: needsConfirmation,
        ruleKey: ruleKey,
        resolved: resolved ?? this.resolved,
        notified: notified ?? this.notified,
      );

  Map<String, dynamic> toJson() => {
        'id': id,
        'title': title,
        'message': message,
        'severity': severity,
        'createdAt': createdAt.toIso8601String(),
        'assetId': assetId,
        'needsConfirmation': needsConfirmation,
        'ruleKey': ruleKey,
        'resolved': resolved,
        'notified': notified,
      };

  factory V6Anomaly.fromJson(Map<String, dynamic> j) => V6Anomaly(
        id: '${j['id'] ?? ''}',
        title: '${j['title'] ?? ''}',
        message: '${j['message'] ?? ''}',
        severity: '${j['severity'] ?? 'INFO'}',
        createdAt: DateTime.tryParse('${j['createdAt'] ?? ''}') ?? DateTime.now(),
        assetId: '${j['assetId'] ?? ''}',
        needsConfirmation: j['needsConfirmation'] == true,
        ruleKey: '${j['ruleKey'] ?? ''}',
        resolved: j['resolved'] == true,
        notified: j['notified'] == true,
      );
}

class V6LearnedRule {
  const V6LearnedRule({
    required this.key,
    required this.value,
    required this.reason,
    required this.updatedAt,
    required this.confidence,
    required this.confirmed,
  });

  final String key;
  final String value;
  final String reason;
  final DateTime updatedAt;
  final double confidence;
  final bool confirmed;

  Map<String, dynamic> toJson() => {
        'key': key,
        'value': value,
        'reason': reason,
        'updatedAt': updatedAt.toIso8601String(),
        'confidence': confidence,
        'confirmed': confirmed,
      };

  factory V6LearnedRule.fromJson(Map<String, dynamic> j) => V6LearnedRule(
        key: '${j['key'] ?? ''}',
        value: '${j['value'] ?? ''}',
        reason: '${j['reason'] ?? ''}',
        updatedAt: DateTime.tryParse('${j['updatedAt'] ?? ''}') ?? DateTime.now(),
        confidence: (j['confidence'] as num?)?.toDouble() ?? .5,
        confirmed: j['confirmed'] == true,
      );
}

class V6InferenceResult {
  const V6InferenceResult({
    required this.statement,
    required this.confidence,
    required this.evidence,
  });
  final String statement;
  final String confidence;
  final List<String> evidence;
}

class V6Brain {
  const V6Brain();

  String classifySystem(String text) {
    final t = _normalize(text);
    if (t.contains('DIRECAO') ||
        t.contains('TERMINAL DIRE') ||
        t.contains('BARRA DIRE') ||
        t.contains('CAIXA DIRE')) return 'DIREÇÃO';
    if (t.contains('FREIO') ||
        t.contains('SAPATA') ||
        t.contains('TAMBOR') ||
        t.contains('PASTILHA')) return 'FREIO';
    if (t.contains('HIDRAUL') ||
        t.contains('MANGUEIRA') ||
        t.contains('CILINDRO HIDR')) return 'HIDRÁULICO';
    if (t.contains('MOTOR') ||
        t.contains('LUBRIFICANTE') ||
        t.contains('15W40') ||
        t.contains('5W30') ||
        t.contains('10W40')) return 'MOTOR/LUBRIFICAÇÃO';
    if (t.contains('COMBUST') || t.contains('RACOR') || t.contains('INJECAO')) {
      return 'COMBUSTÍVEL/INJEÇÃO';
    }
    if (t.contains('TRANSM') ||
        t.contains('CAIXA') ||
        t.contains('80W90') ||
        t.contains('85W140') ||
        t.contains('ECOFLUID')) return 'TRANSMISSÃO';
    if (t.contains('CORREIA') || t.contains('POLIA')) return 'ACIONAMENTO';
    if (t.contains('BATERIA') ||
        t.contains('LAMP') ||
        t.contains('FUSIVEL') ||
        t.contains('ELETR')) return 'ELÉTRICO';
    if (t.contains('PNEU') ||
        t.contains('RODA') ||
        t.contains('ROLAMENTO')) return 'RODAGEM';
    if (t.contains('ARREFEC') || t.contains('RADIADOR') || t.contains('COOLANT')) {
      return 'ARREFECIMENTO';
    }
    if (t.contains('FILTRO')) return 'FILTRAGEM';
    return 'OUTROS';
  }

  V6InferenceResult inferIntervention(V6PartUsage usage) {
    final system = classifySystem('${usage.partName} ${usage.reference}');
    final evidence = <String>[
      'Peça/material registrado: ${usage.partName}',
      if (usage.reference.trim().isNotEmpty) 'Referência: ${usage.reference}',
      if (usage.rm.trim().isNotEmpty) 'RM: ${usage.rm}',
      if (usage.os.trim().isNotEmpty) 'O.S.: ${usage.os}',
      'Data: ${_date(usage.date)}',
    ];
    final defectSystem = classifySystem(usage.defect);
    final actionSystem = classifySystem(usage.actionTaken);
    final actionHasEvidence = usage.actionTaken.trim().isNotEmpty &&
        (actionSystem == system ||
            _normalize(usage.actionTaken).contains(_normalize(usage.reference)) ||
            _tokensOverlap(usage.actionTaken, usage.partName));
    final defectAligned = usage.defect.trim().isNotEmpty && defectSystem == system;

    if (actionHasEvidence && defectAligned) {
      evidence.add('Queixa/defeito e providência convergem com o mesmo sistema.');
      return V6InferenceResult(
        statement: 'Intervenção no sistema $system fortemente sustentada pelas fontes. A causa específica ainda depende do texto técnico da O.S.',
        confidence: 'ALTA',
        evidence: evidence,
      );
    }
    if (actionHasEvidence) {
      evidence.add('Providência tomada converge com a peça/material.');
      return V6InferenceResult(
        statement: 'Intervenção no sistema $system sustentada pela providência registrada.',
        confidence: 'ALTA',
        evidence: evidence,
      );
    }
    if (defectAligned) {
      evidence.add('Queixa/defeito converge com o sistema da peça.');
      return V6InferenceResult(
        statement: 'Intervenção provável no sistema $system. A peça usada reforça a queixa, mas não prova sozinha que o componente anterior estava quebrado.',
        confidence: 'MÉDIA',
        evidence: evidence,
      );
    }
    return V6InferenceResult(
      statement: 'Intervenção provável no sistema $system. O uso da peça é evidência de intervenção, não prova isolada de componente quebrado.',
      confidence: 'MÉDIA',
      evidence: evidence,
    );
  }

  List<V6Anomaly> analyzePartHistory(List<V6PartUsage> usages) {
    final out = <V6Anomaly>[];
    final sorted = [...usages]..sort((a, b) => a.date.compareTo(b.date));
    const meaningfulSystems = {
      'DIREÇÃO',
      'FREIO',
      'HIDRÁULICO',
      'MOTOR/LUBRIFICAÇÃO',
      'COMBUSTÍVEL/INJEÇÃO',
      'TRANSMISSÃO',
      'ACIONAMENTO',
      'ELÉTRICO',
      'RODAGEM',
      'ARREFECIMENTO',
    };

    for (var i = 0; i < sorted.length; i++) {
      final first = sorted[i];
      for (var j = i + 1; j < sorted.length; j++) {
        final next = sorted[j];
        final days = next.date.difference(first.date).inDays;
        if (days > 180) break;
        if (first.assetId != next.assetId) continue;
        final sameReference = first.reference.trim().isNotEmpty &&
            _normalize(first.reference) == _normalize(next.reference);
        final system = classifySystem(first.partName);
        final sameSystem = meaningfulSystems.contains(system) &&
            system == classifySystem(next.partName);
        if (!sameReference && !sameSystem) continue;
        final label = sameReference
            ? 'a mesma referência ${first.reference}'
            : 'o sistema $system';
        out.add(V6Anomaly(
          id: 'repeat:${first.assetId}:${first.date.toIso8601String()}:${next.date.toIso8601String()}:$label',
          title: 'Possível reincidência de manutenção',
          message:
              '${first.assetId}: $label voltou a aparecer após $days dias. Cruzar O.S., providência, Horímetro/Km e operação antes de concluir falha repetida.',
          severity: days <= 30 ? 'ALTA' : 'MÉDIA',
          createdAt: DateTime.now(),
          assetId: first.assetId,
        ));
      }
    }

    final byRm = <String, List<V6PartUsage>>{};
    for (final usage in usages) {
      final rm = rmFamily(usage.rm);
      if (rm.isEmpty) continue;
      byRm.putIfAbsent(rm, () => []).add(usage);
    }
    for (final entry in byRm.entries) {
      final osSet = entry.value.map((e) => e.os.trim()).where((e) => e.isNotEmpty).toSet();
      final assetSet = entry.value.map((e) => e.assetId.trim()).where((e) => e.isNotEmpty).toSet();
      if (osSet.length > 1 && assetSet.length > 1) {
        out.add(V6Anomaly(
          id: 'rm:${entry.key}:multi-os-asset',
          title: 'RM vinculada a O.S./ativos diferentes',
          message:
              'RM-base ${entry.key}: aparecem O.S. ${osSet.join(', ')} e ativos ${assetSet.join(', ')}. Como uma O.S. pode ter várias RMs, o conflito só é aberto quando a mesma RM-base cruza O.S. e ativos diferentes.',
          severity: 'ALTA',
          createdAt: DateTime.now(),
          needsConfirmation: true,
          ruleKey: 'rm:${entry.key}:vinculo',
        ));
      }
    }

    for (final usage in usages) {
      if (isFluid(usage.partName) && usage.unit.trim().toLowerCase() == 'un') {
        out.add(V6Anomaly(
          id: 'fluid-unit:${usage.assetId}:${usage.date.toIso8601String()}:${usage.rm}:${usage.internalCode}:${usage.reference}',
          title: 'Unidade de fluido precisa de contexto',
          message:
              '${usage.assetId}: ${usage.partName} está como ${_qty(usage.quantity)} ${usage.unit}. Pode representar embalagem ou unidade comercial; não converter para litros sem conhecer a embalagem.',
          severity: 'MÉDIA',
          createdAt: DateTime.now(),
          assetId: usage.assetId,
          needsConfirmation: true,
          ruleKey: 'package:${usage.internalCode.isNotEmpty ? usage.internalCode : usage.reference}',
        ));
      }
    }

    return _dedupe(out);
  }

  V6Anomaly? meterConflict({
    required String assetId,
    required String sourceA,
    required String rawA,
    required String sourceB,
    required String rawB,
    required DateTime date,
    required String meterType,
  }) {
    if (_normalize(rawA) == _normalize(rawB)) return null;
    return V6Anomaly(
      id: 'meter-conflict:$assetId:${date.toIso8601String()}:$sourceA:$sourceB',
      title: 'Conflito de Horímetro/Km para correção',
      message:
          '$assetId em ${_date(date)}: $sourceA = "$rawA"; $sourceB = "$rawB" ($meterType). Os dois valores originais ficam preservados e nenhum é escolhido automaticamente.',
      severity: 'ALTA',
      createdAt: DateTime.now(),
      assetId: assetId,
      needsConfirmation: true,
      ruleKey: 'meter:$assetId:${date.toIso8601String()}',
    );
  }

  String rmFamily(String raw) {
    var value = raw.trim().toUpperCase();
    if (value.isEmpty) return '';
    value = value.replaceAll('*', '').replaceAll(' ', '');
    value = value.replaceAll(RegExp(r'\.+$'), '');
    value = value.replaceAll(RegExp(r'/\d+$'), '');
    value = value.replaceAll(RegExp(r'\.+$'), '');
    return value;
  }

  bool isFluid(String text) => RegExp(
        r'OLEO|ÓLEO|LUBRIFICANTE|HIDRAUL|HYDRO|COOLANT|ADITIVO|15W|10W|5W|80W|85W|SAE|ATF|ECOFLUID',
        caseSensitive: false,
      ).hasMatch(text);

  bool descriptionNumberIsQuantity(String description) {
    // Números presentes no nome técnico não são quantidade por si só.
    // Ex.: "PROPULSORA PNEUMÁTICA TAMBOR GRAXA 170/200KG" descreve
    // a faixa do tambor compatível; a quantidade vem do campo Quantidade.
    return false;
  }

  List<V6Anomaly> _dedupe(List<V6Anomaly> values) {
    final seen = <String>{};
    return values.where((e) => seen.add(e.id)).toList();
  }

  String _normalize(String input) => input
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
      .replaceAll(RegExp(r'[^A-Z0-9]+'), ' ')
      .trim();

  bool _tokensOverlap(String a, String b) {
    final aa = _normalize(a).split(' ').where((e) => e.length >= 4).toSet();
    final bb = _normalize(b).split(' ').where((e) => e.length >= 4).toSet();
    if (aa.isEmpty || bb.isEmpty) return false;
    return aa.intersection(bb).length >= 2;
  }

  String _date(DateTime d) =>
      '${d.day.toString().padLeft(2, '0')}/${d.month.toString().padLeft(2, '0')}/${d.year}';

  String _qty(double value) => value == value.roundToDouble()
      ? value.toInt().toString()
      : value.toStringAsFixed(3).replaceFirst(RegExp(r'0+$'), '').replaceFirst(RegExp(r'\.$'), '');
}
