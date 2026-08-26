import 'dart:convert';

class Asset {
  Asset({
    required this.id,
    required this.description,
    this.brand = '',
    this.model = '',
    this.year = '',
    this.serial = '',
    this.plate = '',
    this.meterType = 'NAO_INFORMADO',
  });

  final String id;
  final String description;
  final String brand;
  final String model;
  final String year;
  final String serial;
  final String plate;
  final String meterType;

  Asset copyWith({
    String? description,
    String? brand,
    String? model,
    String? year,
    String? serial,
    String? plate,
    String? meterType,
  }) =>
      Asset(
        id: id,
        description: description ?? this.description,
        brand: brand ?? this.brand,
        model: model ?? this.model,
        year: year ?? this.year,
        serial: serial ?? this.serial,
        plate: plate ?? this.plate,
        meterType: meterType ?? this.meterType,
      );

  Map<String, dynamic> toJson() => {
        'id': id,
        'description': description,
        'brand': brand,
        'model': model,
        'year': year,
        'serial': serial,
        'plate': plate,
        'meterType': meterType,
      };

  factory Asset.fromJson(Map<String, dynamic> j) => Asset(
        id: '${j['id'] ?? ''}',
        description: '${j['description'] ?? ''}',
        brand: '${j['brand'] ?? ''}',
        model: '${j['model'] ?? ''}',
        year: '${j['year'] ?? ''}',
        serial: '${j['serial'] ?? ''}',
        plate: '${j['plate'] ?? ''}',
        meterType: '${j['meterType'] ?? 'NAO_INFORMADO'}',
      );
}

class PartUsage {
  PartUsage({
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
      };

  factory PartUsage.fromJson(Map<String, dynamic> j) => PartUsage(
        assetId: '${j['assetId'] ?? ''}',
        date: DateTime.tryParse('${j['date'] ?? ''}') ?? DateTime(2000),
        os: '${j['os'] ?? ''}',
        rm: '${j['rm'] ?? ''}',
        internalCode: '${j['internalCode'] ?? ''}',
        partName: '${j['partName'] ?? ''}',
        reference: '${j['reference'] ?? ''}',
        quantity: (j['quantity'] as num?)?.toDouble() ?? 0,
        unit: '${j['unit'] ?? ''}',
        source: '${j['source'] ?? ''}',
      );
}

class MeterReading {
  MeterReading({
    required this.assetId,
    required this.date,
    required this.rawValue,
    required this.value,
    required this.type,
    required this.source,
    this.confidence = 1,
  });
  final String assetId;
  final DateTime date;
  final String rawValue;
  final double value;
  final String type;
  final String source;
  final double confidence;

  Map<String, dynamic> toJson() => {
        'assetId': assetId,
        'date': date.toIso8601String(),
        'rawValue': rawValue,
        'value': value,
        'type': type,
        'source': source,
        'confidence': confidence,
      };

  factory MeterReading.fromJson(Map<String, dynamic> j) => MeterReading(
        assetId: '${j['assetId'] ?? ''}',
        date: DateTime.tryParse('${j['date'] ?? ''}') ?? DateTime(2000),
        rawValue: '${j['rawValue'] ?? ''}',
        value: (j['value'] as num?)?.toDouble() ?? 0,
        type: '${j['type'] ?? ''}',
        source: '${j['source'] ?? ''}',
        confidence: (j['confidence'] as num?)?.toDouble() ?? 1,
      );
}

class Anomaly {
  Anomaly({
    required this.id,
    required this.title,
    required this.message,
    required this.severity,
    required this.createdAt,
    this.assetId = '',
    this.needsConfirmation = false,
    this.resolved = false,
    this.ruleKey = '',
  });
  final String id;
  final String title;
  final String message;
  final String severity;
  final DateTime createdAt;
  final String assetId;
  final bool needsConfirmation;
  final bool resolved;
  final String ruleKey;

  Anomaly copyWith({bool? resolved}) => Anomaly(
        id: id,
        title: title,
        message: message,
        severity: severity,
        createdAt: createdAt,
        assetId: assetId,
        needsConfirmation: needsConfirmation,
        resolved: resolved ?? this.resolved,
        ruleKey: ruleKey,
      );

  Map<String, dynamic> toJson() => {
        'id': id,
        'title': title,
        'message': message,
        'severity': severity,
        'createdAt': createdAt.toIso8601String(),
        'assetId': assetId,
        'needsConfirmation': needsConfirmation,
        'resolved': resolved,
        'ruleKey': ruleKey,
      };

  factory Anomaly.fromJson(Map<String, dynamic> j) => Anomaly(
        id: '${j['id'] ?? ''}',
        title: '${j['title'] ?? ''}',
        message: '${j['message'] ?? ''}',
        severity: '${j['severity'] ?? 'info'}',
        createdAt: DateTime.tryParse('${j['createdAt'] ?? ''}') ?? DateTime.now(),
        assetId: '${j['assetId'] ?? ''}',
        needsConfirmation: j['needsConfirmation'] == true,
        resolved: j['resolved'] == true,
        ruleKey: '${j['ruleKey'] ?? ''}',
      );
}

class LearningRule {
  LearningRule({
    required this.key,
    required this.value,
    required this.reason,
    required this.updatedAt,
    this.confidence = .5,
    this.confirmed = false,
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

  factory LearningRule.fromJson(Map<String, dynamic> j) => LearningRule(
        key: '${j['key'] ?? ''}',
        value: '${j['value'] ?? ''}',
        reason: '${j['reason'] ?? ''}',
        updatedAt: DateTime.tryParse('${j['updatedAt'] ?? ''}') ?? DateTime.now(),
        confidence: (j['confidence'] as num?)?.toDouble() ?? .5,
        confirmed: j['confirmed'] == true,
      );
}

String encodeList<T>(List<T> data, Map<String, dynamic> Function(T) f) =>
    jsonEncode(data.map(f).toList());

List<Map<String, dynamic>> decodeList(String? raw) {
  if (raw == null || raw.trim().isEmpty) return [];
  final v = jsonDecode(raw);
  if (v is! List) return [];
  return v.whereType<Map>().map((e) => Map<String, dynamic>.from(e)).toList();
}
