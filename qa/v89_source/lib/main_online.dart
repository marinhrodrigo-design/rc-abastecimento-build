import 'dart:async';
import 'dart:convert';
import 'dart:io';
import 'dart:isolate';
import 'dart:math';
import 'dart:ui' as ui;

import 'package:flutter/material.dart';
import 'package:flutter/rendering.dart';
import 'package:flutter/services.dart';
import 'package:connectivity_plus/connectivity_plus.dart';
import 'package:crypto/crypto.dart' as crypto;
import 'package:image_picker/image_picker.dart';
import 'package:geolocator/geolocator.dart';
import 'package:geocoding/geocoding.dart';
import 'package:path_provider/path_provider.dart';
import 'package:pdf/pdf.dart';
import 'package:pdf/widgets.dart' as pw;
import 'package:printing/printing.dart';
import 'package:supabase_flutter/supabase_flutter.dart';

part 'v29_features.dart';
part 'v30_features.dart';
part 'v31_features.dart';

const _supabaseUrl = 'https://zitwhbfplafvarivgzdr.supabase.co';
const _supabaseKey = String.fromEnvironment('SUPABASE_KEY');
const _blue = Color(0xFF0B4EA2);
const _deviceChannelV42 = MethodChannel('rc.abastecimento/device');
final GlobalKey<ScaffoldMessengerState> _syncMessengerKeyV84 =
    GlobalKey<ScaffoldMessengerState>();

String _randomSaltV69() {
  final r = Random.secure();
  final bytes = List<int>.generate(16, (_) => r.nextInt(256), growable: false);
  return base64UrlEncode(bytes);
}

String _pbkdf2Sha256V69(String secret, String saltB64, int iterations) {
  final salt = base64Url.decode(base64Url.normalize(saltB64));
  final hmac = crypto.Hmac(crypto.sha256, utf8.encode(secret));
  final block = Uint8List(salt.length + 4)..setRange(0, salt.length, salt);
  block[salt.length] = 0;
  block[salt.length + 1] = 0;
  block[salt.length + 2] = 0;
  block[salt.length + 3] = 1;
  var u = Uint8List.fromList(hmac.convert(block).bytes);
  final out = Uint8List.fromList(u);
  for (var i = 1; i < iterations; i++) {
    u = Uint8List.fromList(hmac.convert(u).bytes);
    for (var j = 0; j < out.length; j++) {
      out[j] ^= u[j];
    }
  }
  return base64UrlEncode(out);
}

Future<String> _stableDeviceIdV42() async {
  if (Platform.isAndroid) {
    try {
      final raw =
          (await _deviceChannelV42.invokeMethod<String>('androidId'))?.trim() ??
              '';
      if (raw.isNotEmpty) return 'android-$raw';
    } catch (_) {}
  }
  return offlineStore.ensureDeviceIdV39();
}

const _ink = Color(0xFF12325A);
const _fuelTypes = <String>[
  'Diesel',
  'Arla 32',
  'Diesel S10',
  'Gasolina comum',
  'GNV',
  'Etanol',
  'Gasolina aditivada',
  'Etanol aditivado',
];

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  await SystemChrome.setPreferredOrientations([DeviceOrientation.portraitUp]);
  await Supabase.initialize(url: _supabaseUrl, anonKey: _supabaseKey);
  await offlineStore.init();
  runApp(const RcAbastecimentoOnlineApp());
}

class RcAbastecimentoOnlineApp extends StatelessWidget {
  const RcAbastecimentoOnlineApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      scaffoldMessengerKey: _syncMessengerKeyV84,
      debugShowCheckedModeBanner: false,
      title: 'R&C Abastecimento',
      theme: ThemeData(
        useMaterial3: true,
        colorScheme: ColorScheme.fromSeed(seedColor: _blue),
        scaffoldBackgroundColor: const Color(0xFFF4F7FB),
        inputDecorationTheme: InputDecorationTheme(
          filled: true,
          fillColor: Colors.white,
          border: OutlineInputBorder(borderRadius: BorderRadius.circular(14)),
        ),
        cardTheme: CardThemeData(
          elevation: 0,
          color: Colors.white,
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(18),
            side: const BorderSide(color: Color(0xFFE2E8F0)),
          ),
        ),
      ),
      home: const AuthGate(),
    );
  }
}

void _showSyncMessageV84(String message) {
  final messenger = _syncMessengerKeyV84.currentState;
  if (messenger == null || message.trim().isEmpty) return;
  messenger.hideCurrentSnackBar();
  messenger.showSnackBar(SnackBar(
    content: Text(message),
    duration: const Duration(seconds: 6),
  ));
}

String _syncResultMessageV84(Map<String, dynamic> result,
    {bool automatic = false}) {
  final synced = _intOrNull(result['synced']) ?? 0;
  final after = _intOrNull(result['after']) ?? 0;
  final conflicts = _intOrNull(result['conflicts']) ?? 0;
  final reason = '${result['error'] ?? ''}'.trim();
  final prefix = automatic ? 'Internet restabelecida. ' : '';
  if (after == 0) {
    return synced > 0
        ? '${prefix}Sincronização concluída com sucesso. $synced registro(s) enviado(s).'
        : '${prefix}Não há registros pendentes para sincronizar.';
  }
  if (synced > 0) {
    if (conflicts > 0) {
      return '${prefix}$synced registro(s) sincronizado(s). $conflicts conflito(s) aguardam análise.';
    }
    if (reason.isNotEmpty) {
      return '${prefix}$synced registro(s) sincronizado(s). $after ainda pendente(s). Motivo: $reason';
    }
    return '${prefix}$synced registro(s) sincronizado(s). $after ainda pendente(s).';
  }
  if (conflicts > 0) {
    return '${prefix}Não foi possível concluir toda a sincronização. $conflicts conflito(s) aguardam análise.';
  }
  if (reason.isNotEmpty) {
    return '${prefix}Não foi possível sincronizar: $reason';
  }
  return '${prefix}Nenhum registro foi sincronizado. Os dados continuam salvos no aparelho.';
}

Map<String, dynamic> _map(dynamic value) {
  if (value is Map<String, dynamic>) return value;
  if (value is Map) return value.map((k, v) => MapEntry(k.toString(), v));
  return <String, dynamic>{};
}

List<Map<String, dynamic>> _rows(dynamic value) {
  if (value is! List) return <Map<String, dynamic>>[];
  return value.map(_map).toList();
}

double _num(dynamic value) {
  if (value is num) return value.toDouble();
  return double.tryParse('$value') ?? 0;
}

int? _intOrNull(dynamic value) {
  if (value == null) return null;
  if (value is int) return value;
  return int.tryParse('$value');
}

String _fmtLiters(dynamic value) => '${_num(value).toStringAsFixed(1)} L';
String _fmtMoney(dynamic value) =>
    'R\$ ${_num(value).toStringAsFixed(2).replaceAll('.', ',')}';

String _authPasswordForLogin(String value) =>
    value.length >= 6 ? value : 'RcPin#$value#Fuel';

String _unitPrefix(dynamic value) {
  final raw =
      '${value ?? ''}'.toUpperCase().replaceAll(RegExp(r'[^A-Z0-9]'), '');
  return raw.replaceAll(RegExp(r'[0-9]'), '');
}

int _unitNumber(dynamic value) {
  final raw = '${value ?? ''}';
  final matches = RegExp(r'[0-9]+').allMatches(raw).toList();
  return matches.isEmpty ? 0 : int.tryParse(matches.last.group(0) ?? '') ?? 0;
}

List<Map<String, dynamic>> _sortedFuelUnits(dynamic value) {
  final list = _rows(value);
  list.sort((a, b) {
    final prefix = _unitPrefix(a['code']).compareTo(_unitPrefix(b['code']));
    if (prefix != 0) return prefix;
    final number = _unitNumber(a['code']).compareTo(_unitNumber(b['code']));
    if (number != 0) return number;
    return '${a['code'] ?? ''}'.compareTo('${b['code'] ?? ''}');
  });
  return list;
}

String _fmtDate(dynamic value) {
  final d = DateTime.tryParse('$value')?.toLocal();
  if (d == null) return '-';
  String two(int x) => x.toString().padLeft(2, '0');
  return '${two(d.day)}/${two(d.month)}/${d.year} ${two(d.hour)}:${two(d.minute)}';
}

String _movementLabel(String type) {
  switch (type) {
    case 'refinery_entry':
      return 'Entrada da refinaria';
    case 'tank_transfer':
      return 'Transferência';
    case 'fueling':
      return 'Abastecimento';
    case 'reversal':
      return 'Estorno';
    case 'adjustment':
      return 'Ajuste';
    default:
      return type;
  }
}

String _movementLabelForItem(Map<String, dynamic> item) {
  if ('${item['type']}' == 'fueling' && item['lubricated'] == true) {
    return 'Abastecimento/Lubrificação';
  }
  return _movementLabel('${item['type']}');
}

bool _hasValue(dynamic value) {
  if (value == null) return false;
  final s = '$value'.trim();
  return s.isNotEmpty && s != '-' && s.toLowerCase() != 'null';
}

String _plateDescriptionLabel(dynamic plate, dynamic description) {
  final parts = <String>[];
  if (_hasValue(plate)) parts.add('$plate'.trim());
  if (_hasValue(description)) parts.add('$description'.trim());
  return parts.isEmpty ? '-' : parts.join(' • ');
}

Future<void> _logoutToLogin(
    BuildContext context, Future<void> Function() onLogout) async {
  try {
    await onLogout();
  } catch (e) {
    if (context.mounted)
      ScaffoldMessenger.of(context)
          .showSnackBar(SnackBar(content: Text(_friendlyError(e))));
    return;
  }
  if (!context.mounted) return;
  Navigator.of(context, rootNavigator: true).pushAndRemoveUntil(
      MaterialPageRoute(builder: (_) => const AuthGate()), (_) => false);
}

bool _isNetworkError(Object e) {
  final s = e.toString().toLowerCase();
  return s.contains('socketexception') ||
      s.contains('failed host lookup') ||
      s.contains('connection refused') ||
      s.contains('connection reset') ||
      s.contains('network is unreachable') ||
      s.contains('network error') ||
      s.contains('timed out') ||
      s.contains('timeout');
}

class OfflineStore {
  final ValueNotifier<bool> online = ValueNotifier(true);
  final ValueNotifier<int> pendingCount = ValueNotifier(0);
  final ValueNotifier<bool> syncing = ValueNotifier(false);
  final ValueNotifier<int> syncRevision = ValueNotifier(0);
  final Connectivity _connectivity = Connectivity();
  File? _stateFile;
  Directory? _evidenceDir;
  Map<String, dynamic> _state = <String, dynamic>{'queue': <dynamic>[]};
  Future<void> _writeChain = Future<void>.value();
  bool _syncing = false;
  bool _reconnectSyncingV84 = false;
  String? _sessionLoginV84;
  String? _sessionCredentialV84;

  List<Map<String, dynamic>> get _queue => _rows(_state['queue']);
  List<Map<String, dynamic>> get _auditEventsV87 =>
      _rows(_state['audit_events_v87']);

  List<Map<String, dynamic>> _auditEventsForActiveUserV87() {
    final uid = _activeUserKeyV78;
    if (uid == null) return const <Map<String, dynamic>>[];
    return _auditEventsV87
        .where((e) => '${e['user_id'] ?? ''}'.trim() == uid)
        .toList();
  }

  bool get hasPendingAuditEventsV87 =>
      _auditEventsForActiveUserV87().isNotEmpty;

  String _eventHashV87(String previousHash, Map<String, dynamic> event) {
    final canonical = jsonEncode({
      'prev_hash': previousHash,
      'event_id': event['event_id'],
      'event_type': event['event_type'],
      'session_id': event['session_id'],
      'device_id': event['device_id'],
      'tank_id': event['tank_id'],
      'fueling_event_id': event['fueling_event_id'],
      'occurred_at': event['occurred_at'],
      'online': event['online'],
      'payload': event['payload'],
    });
    return crypto.sha256.convert(utf8.encode(canonical)).toString();
  }

  Future<void> recordEventV87(
    String eventType, {
    Map<String, dynamic>? payload,
    int? tankId,
    String? fuelingEventId,
    DateTime? occurredAt,
  }) async {
    final uid = _activeUserKeyV78;
    if (uid == null || uid.isEmpty) return;
    final sessionId =
        appSessionIdV30 ?? await ensureAppSessionIdV30(renew: false);
    final deviceId = await ensureDeviceIdV39();
    final events = _auditEventsV87;
    var previousHash = '';
    for (var i = events.length - 1; i >= 0; i--) {
      final e = events[i];
      if ('${e['user_id'] ?? ''}' == uid &&
          '${e['session_id'] ?? ''}' == '$sessionId') {
        previousHash = '${e['event_hash'] ?? ''}';
        break;
      }
    }
    final event = <String, dynamic>{
      'event_id': _newOfflineEventIdV58(),
      'event_type': eventType.trim().toLowerCase(),
      'session_id': sessionId,
      'device_id': deviceId,
      'user_id': uid,
      'tank_id': tankId ?? lastTankId,
      'fueling_event_id': fuelingEventId,
      'occurred_at': (occurredAt ?? DateTime.now()).toUtc().toIso8601String(),
      'online': backendReadyV81,
      'prev_hash': previousHash,
      'payload': payload ?? <String, dynamic>{},
    };
    event['event_hash'] = _eventHashV87(previousHash, event);
    events.add(event);
    _state['audit_events_v87'] = events;
    await _persist();
    syncRevision.value++;
    if (backendReadyV81 && events.length >= 25) {
      unawaited(syncAuditEventsV87());
    }
  }

  Future<Map<String, dynamic>> syncAuditEventsV87() async {
    if (!backendReadyV81) {
      return {'ok': false, 'synced': 0, 'pending': hasPendingAuditEventsV87};
    }
    final uid = Supabase.instance.client.auth.currentUser?.id;
    if (uid == null) return {'ok': false, 'synced': 0};
    final mine = _auditEventsForActiveUserV87().take(200).toList();
    if (mine.isEmpty) return {'ok': true, 'synced': 0};
    final ids = mine.map((e) => '${e['event_id']}').toSet();
    try {
      final result = _map(await Supabase.instance.client
          .rpc('rca_sync_app_events_v87', params: {'p_events': mine}));
      if (result['ok'] != true) {
        throw Exception(
            '${result['message'] ?? 'Falha ao sincronizar auditoria'}');
      }
      final remaining = _auditEventsV87
          .where((e) => !('${e['user_id'] ?? ''}' == uid &&
              ids.contains('${e['event_id']}')))
          .toList();
      _state['audit_events_v87'] = remaining;
      await _persist();
      syncRevision.value++;
      return {
        ...result,
        'synced': mine.length,
        'remaining':
            remaining.where((e) => '${e['user_id'] ?? ''}' == uid).length,
      };
    } catch (e) {
      if (_isNetworkError(e)) markOffline();
      rethrow;
    }
  }

  Map<String, dynamic>? get cachedProfile =>
      _state['profile'] is Map ? _map(_state['profile']) : null;
  String? get _activeUserKeyV78 {
    final v =
        (activeUserIdV62 ?? Supabase.instance.client.auth.currentUser?.id ?? '')
            .trim();
    return v.isEmpty ? null : v;
  }

  Map<String, dynamic>? get _baseReferenceDataV69 {
    final uid = _activeUserKeyV78;
    final byUser = _state['reference_data_by_user_v78'];
    if (uid != null && byUser is Map) {
      final item = _map(byUser)[uid];
      return item is Map ? _map(item) : null;
    }
    return _state['reference_data'] is Map
        ? _map(_state['reference_data'])
        : null;
  }

  Map<String, dynamic>? get cachedReferenceData =>
      _referenceWithPendingOverlayV69();
  int? get lastTankId {
    final uid = _activeUserKeyV78;
    final byUser = _state['last_tank_by_user_v78'];
    if (uid != null && byUser is Map) {
      return _intOrNull(_map(byUser)[uid]);
    }
    return _intOrNull(_state['last_tank_id']);
  }

  Map<String, dynamic>? get _sequenceSnapshotV74 =>
      _state['sequence_snapshot_v74'] is Map
          ? _map(_state['sequence_snapshot_v74'])
          : null;

  int _lastKnownSequenceV74(int tankId) {
    var last = 0;
    for (final item in _rows(_sequenceSnapshotV74?['items'])) {
      if (_intOrNull(item['tank_id']) == tankId) {
        last = max(last, _intOrNull(item['last_sequence']) ?? 0);
      }
    }
    for (final q in _queue) {
      if (q['sync_rejected'] == true || !_fuelingRpc('${q['rpc'] ?? ''}')) {
        continue;
      }
      final params = _map(q['params']);
      if (_intOrNull(params['p_source_tank_id']) != tankId) continue;
      final local = _intOrNull(q['offline_sequence_v74']);
      if (local != null) last = max(last, local);
    }
    return last;
  }

  String _sourceCodeV74(int tankId) {
    for (final tank in _rows(_baseReferenceDataV69?['tanks'])) {
      if (_intOrNull(tank['id']) == tankId) {
        final code = '${tank['code'] ?? tank['name'] ?? ''}'.trim();
        if (code.isNotEmpty && code != 'null') return code;
      }
    }
    for (final item in _rows(_sequenceSnapshotV74?['items'])) {
      if (_intOrNull(item['tank_id']) == tankId) {
        final code = '${item['source_code'] ?? ''}'.trim();
        if (code.isNotEmpty && code != 'null') return code;
      }
    }
    return 'UNIDADE';
  }

  String _offlineCodeV74(int tankId, int sequence) =>
      '${_sourceCodeV74(tankId)}-${sequence.toString().padLeft(6, '0')}';

  void _backfillPendingSequencesV74() {
    final queue = _queue;
    final nextByTank = <int, int>{};
    for (final item in _rows(_sequenceSnapshotV74?['items'])) {
      final tankId = _intOrNull(item['tank_id']);
      if (tankId != null) {
        nextByTank[tankId] = _intOrNull(item['last_sequence']) ?? 0;
      }
    }
    for (final q in queue) {
      if (q['sync_rejected'] == true || !_fuelingRpc('${q['rpc'] ?? ''}')) {
        continue;
      }
      final tankId = _intOrNull(_map(q['params'])['p_source_tank_id']);
      if (tankId == null) continue;
      final existing = _intOrNull(q['offline_sequence_v74']);
      if (existing != null) {
        nextByTank[tankId] = max(nextByTank[tankId] ?? 0, existing);
        q['offline_code_v74'] ??= _offlineCodeV74(tankId, existing);
        continue;
      }
      final next = (nextByTank[tankId] ?? 0) + 1;
      nextByTank[tankId] = next;
      q['offline_sequence_v74'] = next;
      q['offline_code_v74'] = _offlineCodeV74(tankId, next);
    }
    _state['queue'] = queue;
  }

  Future<void> refreshSequenceSnapshotV74() async {
    if (!online.value || Supabase.instance.client.auth.currentUser == null) {
      return;
    }
    final value =
        _map(await Supabase.instance.client.rpc('rca_sequence_snapshot_v74'));
    _state['sequence_snapshot_v74'] = value;
    _backfillPendingSequencesV74();
    await _persist();
    syncRevision.value++;
  }

  Future<void> _learnSequenceFromResultV74(
      Map<String, dynamic> result, Map<String, dynamic> params) async {
    final tankId = _intOrNull(params['p_source_tank_id']);
    if (tankId == null) return;
    final code = '${result['code'] ?? result['movement_code'] ?? ''}'.trim();
    final match = RegExp(r'(\d+)$').firstMatch(code);
    final sequence = int.tryParse(match?.group(1) ?? '');
    if (sequence == null) return;
    final snapshot = _sequenceSnapshotV74 ?? <String, dynamic>{};
    final items = _rows(snapshot['items']);
    var found = false;
    for (final item in items) {
      if (_intOrNull(item['tank_id']) == tankId) {
        item['last_sequence'] =
            max(_intOrNull(item['last_sequence']) ?? 0, sequence);
        item['source_code'] ??= _sourceCodeV74(tankId);
        found = true;
        break;
      }
    }
    if (!found) {
      items.add({
        'tank_id': tankId,
        'source_code': _sourceCodeV74(tankId),
        'last_sequence': sequence
      });
    }
    snapshot['items'] = items;
    snapshot['captured_at'] = DateTime.now().toUtc().toIso8601String();
    _state['sequence_snapshot_v74'] = snapshot;
    await _persist();
  }

  Map<String, dynamic>? _referenceWithPendingOverlayV69() {
    final raw = _baseReferenceDataV69;
    if (raw == null) return null;
    final ref = _map(jsonDecode(jsonEncode(raw)));
    final tanks = _rows(ref['tanks']);
    final reserved = <int, double>{};
    final incoming = <int, double>{};
    // Physical stock is shared by every user on this device. Personal history
    // remains user-scoped elsewhere, but every pending operation must reserve
    // the same physical fuel so a user switch cannot overbook a tank.
    for (final q in _queue) {
      if (q['sync_rejected'] == true) continue;
      if (q['sync_blocked'] == true && q['sync_conflict'] != true) continue;
      final rpc = '${q['rpc'] ?? ''}';
      final params = _map(q['params']);
      final liters = _num(params['p_liters']);
      if (liters <= 0) continue;
      if (_fuelingRpc(rpc)) {
        final id = _intOrNull(params['p_source_tank_id']);
        if (id != null) reserved[id] = (reserved[id] ?? 0) + liters;
      } else if (rpc == 'rca_record_transfer') {
        final sId = _intOrNull(params['p_source_tank_id']),
            dId = _intOrNull(params['p_destination_tank_id']);
        if (sId != null) reserved[sId] = (reserved[sId] ?? 0) + liters;
        if (dId != null) incoming[dId] = (incoming[dId] ?? 0) + liters;
      } else if (rpc == 'rca_record_refinery_entry') {
        final id = _intOrNull(params['p_tank_id']);
        if (id != null) incoming[id] = (incoming[id] ?? 0) + liters;
      }
    }
    for (final t in tanks) {
      final id = _intOrNull(t['id']);
      if (id == null) continue;
      final confirmed = _num(t['current_balance_liters']);
      final out = reserved[id] ?? 0;
      final inc = incoming[id] ?? 0;
      t['confirmed_balance_liters'] = confirmed;
      t['pending_reserved_liters'] = out;
      t['pending_incoming_liters'] = inc;
      final available = confirmed - out + inc;
      t['current_balance_liters'] = available < 0 ? 0.0 : available;
    }
    ref['tanks'] = tanks;
    return ref;
  }

  bool get hasCachedCanFuelV68 => _state.containsKey('can_fueling_create_v68');
  bool get cachedCanFuelV68 => _state['can_fueling_create_v68'] == true;
  Map<String, dynamic>? get abandonedSessionV68 =>
      _state['abandoned_session_v68'] is Map
          ? _map(_state['abandoned_session_v68'])
          : null;
  bool _belongsToActiveUserV78(Map<String, dynamic> q,
      {bool allowLegacy = true}) {
    final uid = _activeUserKeyV78;
    final owner = '${q['user_id'] ?? ''}'.trim();
    if (owner.isEmpty) return allowLegacy;
    return uid != null && owner == uid;
  }

  int _pendingQueueCountV68() => _queue.where((q) {
        if (q['sync_rejected'] == true) return false;
        if (!_fuelingRpc('${q['rpc'] ?? ''}')) return false;
        return _belongsToActiveUserV78(q);
      }).length;

  bool _hasSyncWorkV78() =>
      hasPendingAuditEventsV87 ||
      _queue.any((q) {
        if (q['sync_rejected'] == true) return false;
        return _belongsToActiveUserV78(q, allowLegacy: false);
      });
  Future<void> cacheFuelingPermissionV68(bool allowed) async {
    _state['can_fueling_create_v68'] = allowed;
    await _persist();
  }

  Future<void> beginSessionMarkerV68() async {
    final uid =
        activeUserIdV62 ?? Supabase.instance.client.auth.currentUser?.id;
    if (uid == null || uid.isEmpty) return;
    _state['session_marker_v68'] = {
      'user_id': uid,
      'session_id': appSessionIdV30,
      'tank_id': lastTankId,
      'started_at': DateTime.now().toUtc().toIso8601String(),
      'last_seen_at': DateTime.now().toUtc().toIso8601String()
    };
    await _persist();
  }

  Future<void> clearSessionMarkerV68() async {
    _state.remove('session_marker_v68');
    await _persist();
  }

  Future<void> reconcileAbandonedSessionV68() async {
    final old = abandonedSessionV68;
    if (old == null) return;
    final uid =
        Supabase.instance.client.auth.currentUser?.id ?? activeUserIdV62;
    final owner = '${old['user_id'] ?? ''}'.trim();
    if (uid == null || uid.isEmpty || owner.isEmpty || uid != owner) return;
    final sid = '${old['session_id'] ?? ''}'.trim();
    final tank = _intOrNull(old['tank_id']);
    final occurred = DateTime.tryParse(
            '${old['last_seen_at'] ?? old['started_at'] ?? ''}') ??
        DateTime.now().toUtc();
    try {
      if (online.value) {
        await Supabase.instance.client.rpc('rca_offline_logout_v62', params: {
          'p_session_id': sid.isEmpty ? null : sid,
          'p_tank_id': tank,
          'p_occurred_at': occurred.toUtc().toIso8601String()
        });
      } else {
        await queueOfflineLogoutV62(
            sessionId: sid.isEmpty ? null : sid,
            tankId: tank,
            occurredAt: occurred);
      }
      _state.remove('abandoned_session_v68');
      await _persist();
    } catch (e) {
      if (_isNetworkError(e)) {
        markOffline();
        await queueOfflineLogoutV62(
            sessionId: sid.isEmpty ? null : sid,
            tankId: tank,
            occurredAt: occurred);
        _state.remove('abandoned_session_v68');
        await _persist();
      }
    }
  }

  String? get activeUserIdV62 {
    final v = '${_state['active_user_id_v62'] ?? ''}'.trim();
    return v.isEmpty ? Supabase.instance.client.auth.currentUser?.id : v;
  }

  bool get appLoggedOutV62 => _state['app_logged_out_v62'] == true;
  bool get backendReadyV81 =>
      online.value && Supabase.instance.client.auth.currentUser != null;
  bool get onlineReauthRequiredV81 =>
      online.value &&
      !appLoggedOutV62 &&
      activeUserIdV62 != null &&
      Supabase.instance.client.auth.currentUser == null;
  Map<String, dynamic> get _offlineUsersV62 =>
      _state['offline_users_v62'] is Map
          ? _map(_state['offline_users_v62'])
          : <String, dynamic>{};
  String _offlineKeyV62(String username) => username.trim().toLowerCase();
  void _rememberSessionCredentialV84(String username, String password) {
    _sessionLoginV84 = _offlineKeyV62(username);
    _sessionCredentialV84 = password;
  }

  String _offlineHashV62(String username, String password) {
    final device = '${_state['device_id_v39'] ?? 'rc-device'}';
    return crypto.sha256
        .convert(utf8.encode('$device|${_offlineKeyV62(username)}|$password'))
        .toString();
  }

  String _offlineSecretV69(String username, String password) {
    final device = '${_state['device_id_v39'] ?? 'rc-device'}';
    return '$device|${_offlineKeyV62(username)}|$password';
  }

  Future<Map<String, dynamic>> _credentialV69(
      String username, String password) async {
    const iterations = 60000;
    final salt = _randomSaltV69();
    final secret = _offlineSecretV69(username, password);
    final hash =
        await Isolate.run(() => _pbkdf2Sha256V69(secret, salt, iterations));
    return {
      'kdf': 'pbkdf2-sha256',
      'iterations': iterations,
      'salt': salt,
      'hash': hash
    };
  }

  Future<bool> _verifyCredentialV69(
      Map<String, dynamic> item, String username, String password) async {
    if ('${item['kdf'] ?? ''}' == 'pbkdf2-sha256') {
      final salt = '${item['salt'] ?? ''}';
      final iterations = _intOrNull(item['iterations']) ?? 60000;
      if (salt.isEmpty) return false;
      final expected = '${item['hash'] ?? ''}';
      final secret = _offlineSecretV69(username, password);
      final actual =
          await Isolate.run(() => _pbkdf2Sha256V69(secret, salt, iterations));
      return actual == expected;
    }
    return '${item['hash'] ?? ''}' == _offlineHashV62(username, password);
  }

  Future<void> cacheOfflineLoginV62(
      String username, String password, Map<String, dynamic> profile) async {
    _rememberSessionCredentialV84(username, password);
    final key = _offlineKeyV62(username);
    final users = _offlineUsersV62;
    final uid =
        '${profile['user_id'] ?? profile['id'] ?? Supabase.instance.client.auth.currentUser?.id ?? ''}'
            .trim();
    final credential = await _credentialV69(username, password);
    users[key] = <String, dynamic>{
      ...credential,
      'profile': profile,
      'user_id': uid,
      'updated_at': DateTime.now().toUtc().toIso8601String()
    };
    _state['offline_users_v62'] = users;
    _state['profile'] = profile;
    _state['active_user_id_v62'] = uid;
    _state['app_logged_out_v62'] = false;
    pendingCount.value = _pendingQueueCountV68();
    await _persist();
  }

  Future<Map<String, dynamic>> offlineLoginV62(
      String username, String password) async {
    final key = _offlineKeyV62(username), users = _offlineUsersV62;
    final raw = users[key];
    if (raw is! Map)
      throw Exception(
          'Este usuário ainda não foi habilitado para acesso offline neste aparelho. Conecte-se à internet e entre uma vez.');
    final item = _map(raw);
    if (!await _verifyCredentialV69(item, username, password))
      throw Exception('Usuário ou senha/PIN inválidos.');
    _rememberSessionCredentialV84(username, password);
    if ('${item['kdf'] ?? ''}' != 'pbkdf2-sha256') {
      final upgraded = await _credentialV69(username, password);
      item.addAll(upgraded);
      users[key] = item;
      _state['offline_users_v62'] = users;
    }
    final p = _map(item['profile']);
    if (p.isEmpty)
      throw Exception('Dados offline deste usuário não estão disponíveis.');
    final uid = '${item['user_id'] ?? p['user_id'] ?? p['id'] ?? ''}'.trim();
    final perUserRef = _state['reference_data_by_user_v78'];
    if (uid.isNotEmpty &&
        perUserRef is Map &&
        !_map(perUserRef).containsKey(uid)) {
      throw Exception(
          'Este usuário precisa entrar online uma vez nesta versão para atualizar as unidades e permissões offline deste aparelho.');
    }
    _state['profile'] = p;
    _state['active_user_id_v62'] = uid;
    _state['app_logged_out_v62'] = false;
    pendingCount.value = _pendingQueueCountV68();
    await _persist();
    return p;
  }

  String? get activeLoginV83 {
    final uid = activeUserIdV62;
    if (uid == null || uid.isEmpty) return null;
    for (final entry in _offlineUsersV62.entries) {
      final raw = entry.value;
      if (raw is! Map) continue;
      final item = _map(raw);
      final itemUid =
          '${item['user_id'] ?? _map(item['profile'])['user_id'] ?? _map(item['profile'])['id'] ?? ''}'
              .trim();
      if (itemUid == uid) return entry.key.trim().toLowerCase();
    }
    return null;
  }

  Future<void> reauthenticateOnlineForSyncV83(String password) async {
    if (!online.value) {
      throw Exception('Sem internet. Conecte o aparelho e tente novamente.');
    }
    final username = activeLoginV83;
    if (username == null || username.isEmpty) {
      throw Exception(
          'Não foi possível identificar o usuário desta sessão offline. Saia e entre novamente com internet.');
    }
    final raw = _offlineUsersV62[username];
    if (raw is! Map) {
      throw Exception(
          'Este usuário não possui credencial offline válida neste aparelho.');
    }
    final item = _map(raw);
    if (!await _verifyCredentialV69(item, username, password)) {
      throw Exception('Usuário ou senha/PIN inválidos.');
    }

    final client = Supabase.instance.client;
    final expectedUid = activeUserIdV62;
    final loginPassword = _authPasswordForLogin(password);
    try {
      try {
        await client.auth.signOut(scope: SignOutScope.local);
      } catch (_) {}
      var signedIn = false;
      if (username.contains('@')) {
        await client.auth
            .signInWithPassword(email: username, password: loginPassword);
        signedIn = true;
      } else if (username == 'admin' || username == 'adminfuel') {
        for (final email in const [
          'marinhrodrigo@gmail.com',
          'adminfuel@rccombustivel.app'
        ]) {
          try {
            await client.auth
                .signInWithPassword(email: email, password: loginPassword);
            signedIn = true;
            break;
          } catch (_) {}
        }
      } else {
        try {
          await client.auth.signInWithPassword(
              email: '$username@rccombustivel.app', password: loginPassword);
          signedIn = true;
        } catch (_) {}
        if (!signedIn) {
          await client.auth.signInWithPassword(
              email: '$username@rcmanutencao.app', password: loginPassword);
          signedIn = true;
        }
      }
      if (!signedIn || client.auth.currentUser == null) {
        throw Exception('Usuário ou senha/PIN inválidos.');
      }
      final signedUid = client.auth.currentUser!.id;
      if (expectedUid != null &&
          expectedUid.isNotEmpty &&
          signedUid != expectedUid) {
        await client.auth.signOut(scope: SignOutScope.local);
        throw Exception(
            'A credencial informada pertence a outro usuário. Confirme a senha/PIN do usuário que iniciou esta sessão offline.');
      }

      final sid = await ensureAppSessionIdV30(renew: true);
      final dev = await _stableDeviceIdV42();
      final claim =
          _map(await client.rpc('rca_session_resume_offline_v88', params: {
        'p_session_id': sid,
        'p_device_id': dev,
      }));
      if (claim['ok'] == false) {
        await client.auth.signOut(scope: SignOutScope.local);
        throw Exception(
            '${claim['message'] ?? 'Não foi possível validar esta sessão para sincronização.'}');
      }

      final profile = _map(await client.rpc('rca_profile'));
      markOnline();
      await cacheProfile(profile);
      await cacheFuelingPermissionV68(profile['can_fueling_create'] == true);
      await cacheOfflineLoginV62(username, password, profile);
      try {
        final ref = _map(await client.rpc('rca_reference_data_v33'));
        await cacheReferenceData(ref);
      } catch (_) {}
      await markAppLoggedInV62(signedUid);
      await beginSessionMarkerV68();
    } catch (e) {
      if (_isNetworkError(e)) {
        markOffline();
        throw Exception(
            'A conexão caiu durante a validação. Tente sincronizar novamente quando a internet estiver estável.');
      }
      rethrow;
    }
  }

  Future<void> markAppLoggedOutV62() async {
    _sessionLoginV84 = null;
    _sessionCredentialV84 = null;
    _state['app_logged_out_v62'] = true;
    _state.remove('active_user_id_v62');
    _state.remove('profile');
    pendingCount.value = 0;
    await _persist();
  }

  Future<void> markAppLoggedInV62([String? uid]) async {
    _state['app_logged_out_v62'] = false;
    if (uid != null && uid.isNotEmpty) _state['active_user_id_v62'] = uid;
    pendingCount.value = _pendingQueueCountV68();
    await _persist();
  }

  Future<void> queueOfflineLogoutV62(
      {required String? sessionId,
      required int? tankId,
      required DateTime occurredAt}) async {
    final owner = activeUserIdV62;
    if (owner == null || owner.isEmpty)
      throw Exception(
          'Não foi possível identificar o usuário para registrar a saída offline.');
    final queue = _queue;
    queue.add(<String, dynamic>{
      'id': '${DateTime.now().microsecondsSinceEpoch}',
      'rpc': 'rca_offline_logout_v62',
      'params': {
        'p_session_id': sessionId,
        'p_tank_id': tankId,
        'p_occurred_at': occurredAt.toUtc().toIso8601String()
      },
      'created_at': occurredAt.toUtc().toIso8601String(),
      'user_id': owner
    });
    _state['queue'] = queue;
    pendingCount.value = _pendingQueueCountV68();
    await _persist();
    syncRevision.value++;
  }

  Future<void> queueOfflineReleaseV62(
      {required int? tankId, required DateTime occurredAt}) async {
    final owner = activeUserIdV62;
    if (owner == null || owner.isEmpty) return;
    final queue = _queue;
    queue.add(<String, dynamic>{
      'id': '${DateTime.now().microsecondsSinceEpoch}',
      'rpc': 'rca_offline_release_unit_v62',
      'params': {
        'p_tank_id': tankId,
        'p_occurred_at': occurredAt.toUtc().toIso8601String()
      },
      'created_at': occurredAt.toUtc().toIso8601String(),
      'user_id': owner
    });
    _state['queue'] = queue;
    pendingCount.value = _pendingQueueCountV68();
    await _persist();
    syncRevision.value++;
  }

  bool _fuelingRpc(String rpc) => rpc.startsWith('rca_record_fueling');

  Map<String, dynamic> _offlineFuelingReportSnapshotV73(
      Map<String, dynamic> params,
      {String? currentQueueId}) {
    final ref = cachedReferenceData ?? const <String, dynamic>{};
    final baseRef = _baseReferenceDataV69 ?? ref;
    final machines = _rows(ref['machines']);
    final works = _rows(ref['works']);
    final tanks = _rows(baseRef['tanks']);
    final thirdParty = _rows(ref['third_party_vehicles']);
    final institutional = _map(ref['institutional_company']);
    final institutionalName = '${institutional['company_name'] ?? ''}'.trim();
    String? firstText(Iterable<dynamic> values) {
      for (final value in values) {
        if (_hasValue(value)) return '$value'.trim();
      }
      return null;
    }

    final machineId = _intOrNull(params['p_machine_id']);
    final workId = _intOrNull(params['p_work_id']);
    final tankId = _intOrNull(params['p_source_tank_id']);
    final thirdId = _intOrNull(params['p_third_party_vehicle_id']);

    Map<String, dynamic>? machine, work, tank, third;
    for (final x in machines) {
      if (_intOrNull(x['id']) == machineId) {
        machine = x;
        break;
      }
    }
    for (final x in works) {
      if (_intOrNull(x['id']) == workId) {
        work = x;
        break;
      }
    }
    for (final x in tanks) {
      if (_intOrNull(x['id']) == tankId) {
        tank = x;
        break;
      }
    }
    for (final x in thirdParty) {
      if (_intOrNull(x['id']) == thirdId) {
        third = x;
        break;
      }
    }

    final buyer = firstText([
      work?['company_name'],
      work?['client_name'],
      params['p_receiver_company']
    ]);
    final seller = institutionalName.isNotEmpty ? institutionalName : null;
    final thirdOwner =
        firstText([third?['company_name'], params['p_third_party_company']]);
    final owner = machineId != null ? seller : thirdOwner;

    String measurement =
        '${machine?['measurement_type'] ?? ''}'.trim().toLowerCase();
    if (measurement.isEmpty) {
      final hasKm = params['p_km_value'] != null;
      final hasHour = params['p_hourmeter_value'] != null;
      measurement = hasKm && hasHour
          ? 'both'
          : hasHour
              ? 'hourmeter'
              : hasKm
                  ? 'km'
                  : 'none';
    }

    double opening = _num(tank?['accounting_meter']);
    for (final q in _queue) {
      if (currentQueueId != null && '${q['id']}' == currentQueueId) break;
      if (q['sync_rejected'] == true) continue;
      if (q['sync_blocked'] == true && q['sync_conflict'] != true) continue;
      if (!_fuelingRpc('${q['rpc'] ?? ''}')) continue;
      final qp = _map(q['params']);
      if (_intOrNull(qp['p_source_tank_id']) == tankId) {
        opening += _num(qp['p_liters']);
      }
    }
    final liters = _num(params['p_liters']);
    final closing = tankId == null ? null : opening + liters;
    final profile = _map(_state['profile']);
    final operator = firstText(
        [profile['display_name'], profile['name'], profile['username']]);

    return <String, dynamic>{
      'institutional_company': institutional,
      'company_name': seller,
      'empresa': seller,
      'empresa_fornecedora_vendedora': seller,
      'empresa_recebedora_compradora': buyer,
      'obra': work?['name'],
      'responsavel_obra': work?['responsible'],
      'proprietario_equipamento': owner,
      'origem': tank?['code'] ?? tank?['name'],
      'work_company_name': buyer,
      'work_responsible': work?['responsible'],
      'measurement_type': measurement,
      'asset_number': machine?['numeroAtivo'],
      'asset_plate': machine?['placa'],
      'asset_model':
          [machine?['marca'], machine?['modelo']].where(_hasValue).join(' '),
      'third_party_company': thirdOwner,
      'operator': operator,
      'opening_meter': tankId == null ? null : opening,
      'closing_meter': closing,
      'totalizer': closing,
    };
  }

  List<Map<String, dynamic>> pendingFuelingsForCurrentUser(
      {bool includeLegacy = true}) {
    final uid = activeUserIdV62;
    final ref = cachedReferenceData;
    final machines = _rows(ref?['machines']);
    final works = _rows(ref?['works']);
    final tanks = _rows(ref?['tanks']);
    final out = <Map<String, dynamic>>[];
    for (final q in _queue) {
      final rpc = '${q['rpc'] ?? ''}';
      if (!_fuelingRpc(rpc)) continue;
      final owner = '${q['user_id'] ?? ''}'.trim();
      final legacy = owner.isEmpty;
      if (!legacy && uid != null && owner != uid) continue;
      if (legacy && !includeLegacy) continue;
      final params = _map(q['params']);
      final resolved = q['resolved_params'] is Map
          ? _map(q['resolved_params'])
          : const <String, dynamic>{};
      final snapshot = q['report_snapshot_v73'] is Map
          ? _map(q['report_snapshot_v73'])
          : _offlineFuelingReportSnapshotV73(params,
              currentQueueId: '${q['id']}');
      dynamic mediaParam(String key) {
        final original = params[key];
        if (original is String && original.startsWith('offline://')) {
          try {
            final file = File(original.substring('offline://'.length));
            if (file.existsSync()) return original;
          } catch (_) {}
        }
        return resolved[key] ?? original;
      }

      final machineId = _intOrNull(params['p_machine_id']);
      final workId = _intOrNull(params['p_work_id']);
      final tankId = _intOrNull(params['p_source_tank_id']);
      Map<String, dynamic>? machine, work, tank;
      for (final x in machines) {
        if (_intOrNull(x['id']) == machineId) {
          machine = x;
          break;
        }
      }
      for (final x in works) {
        if (_intOrNull(x['id']) == workId) {
          work = x;
          break;
        }
      }
      for (final x in tanks) {
        if (_intOrNull(x['id']) == tankId) {
          tank = x;
          break;
        }
      }
      final third = '${params['p_third_party_plate'] ?? ''}'.trim();
      final profile = _map(_state['profile']);
      final price = _num(params['p_sale_price_per_liter']);
      final litersValue = _num(params['p_liters']);
      out.add(<String, dynamic>{
        'offline_pending': true,
        'offline_legacy_owner': legacy,
        'queue_id': '${q['id']}',
        'id': null,
        'code': q['sync_rejected'] == true
            ? 'REJEITADO • LOCAL ${(_intOrNull(q['offline_sequence_v74']) ?? 0).toString().padLeft(4, '0')}'
            : q['offline_code_v74'] ?? 'PENDENTE (OFFLINE)',
        'offline_sequence_v74': q['offline_sequence_v74'],
        'offline_sequence_provisional_v74': q['offline_sequence_v74'] != null,
        'type': 'fueling',
        'status': q['sync_rejected'] == true
            ? 'rejected'
            : q['sync_conflict'] == true
                ? 'pending_review'
                : 'pending_offline',
        'asset_id': machineId,
        'asset_number': snapshot['asset_number'] ??
            machine?['numeroAtivo'] ??
            (third.isNotEmpty ? third : '-'),
        'asset_plate': snapshot['asset_plate'] ?? machine?['placa'],
        'asset_model': snapshot['asset_model'] ??
            [machine?['marca'], machine?['modelo']]
                .where((v) => _hasValue(v))
                .join(' '),
        'third_party_vehicle_id':
            _intOrNull(params['p_third_party_vehicle_id']),
        'third_party_plate': third.isEmpty ? null : third,
        'third_party_description': params['p_third_party_description'],
        'work_id': workId,
        'work': snapshot['obra'] ?? work?['name'] ?? 'Sem obra',
        'work_responsible': snapshot['work_responsible'],
        'work_company_name': snapshot['work_company_name'],
        'liters': params['p_liters'],
        'fuel_type': params['p_fuel_type'] ?? 'Combustível',
        'source_tank_id': tankId,
        'source_tank':
            snapshot['origem'] ?? tank?['code'] ?? tank?['name'] ?? '-',
        'source_tank_name': tank?['name'],
        'source_tank_type': tank?['tank_type'],
        'occurred_at': params['p_occurred_at'] ?? q['created_at'],
        'created_at': params['p_occurred_at'] ?? q['created_at'],
        'km_value': params['p_km_value'],
        'hourmeter_value': params['p_hourmeter_value'],
        'km_hourmeter': params['p_hourmeter_value'] ?? params['p_km_value'],
        'measurement_type': snapshot['measurement_type'],
        'receiver': params['p_receiver_name'],
        'receiver_company': snapshot['empresa_recebedora_compradora'],
        'operator': snapshot['operator'] ??
            profile['display_name'] ??
            profile['name'] ??
            profile['username'] ??
            'Usuário offline',
        'buyer_company_name_snapshot':
            snapshot['empresa_recebedora_compradora'],
        'seller_company_name_snapshot':
            snapshot['empresa_fornecedora_vendedora'],
        'equipment_owner_name_snapshot': snapshot['proprietario_equipamento'],
        'institutional_company': snapshot['institutional_company'],
        'report_context': {
          'institutional_company': snapshot['institutional_company'],
          'empresa': snapshot['empresa'],
          'empresa_fornecedora_vendedora':
              snapshot['empresa_fornecedora_vendedora'],
          'empresa_recebedora_compradora':
              snapshot['empresa_recebedora_compradora'],
          'obra': snapshot['obra'],
          'responsavel_obra': snapshot['responsavel_obra'],
          'proprietario_equipamento': snapshot['proprietario_equipamento'],
          'origem': snapshot['origem'],
        },
        'notes': params['p_notes'],
        'location_address': params['p_location_address'],
        'latitude': params['p_latitude'],
        'longitude': params['p_longitude'],
        'location_captured_at': params['p_location_captured_at'],
        'location_accuracy_m': params['p_location_accuracy_m'],
        'sale_price_per_liter': price > 0 ? price : null,
        'total_value': price > 0 ? price * litersValue : null,
        'opening_meter': snapshot['opening_meter'],
        'closing_meter': snapshot['closing_meter'],
        'totalizer': snapshot['totalizer'],
        'meter_photo_path': mediaParam('p_meter_photo_path'),
        'totalizer_evidence_photo_path': mediaParam('p_totalizer_photo_path'),
        'totalizer_photo_before_path': mediaParam('p_totalizer_photo_path'),
        'totalizer_photo_before_captured_at':
            params['p_totalizer_before_captured_at'],
        'identity_evidence_photo_path': mediaParam('p_identity_photo_path'),
        'identity_evidence_kind': params['p_identity_evidence_kind'],
        'extra_evidence_photo_path': mediaParam('p_extra_photo_path'),
        'receiver_signature_path': mediaParam('p_receiver_signature_path'),
        'operator_signature_path': mediaParam('p_operator_signature_path'),
        'photo_paths': [
          mediaParam('p_meter_photo_path'),
          mediaParam('p_totalizer_photo_path'),
          mediaParam('p_identity_photo_path'),
          mediaParam('p_extra_photo_path')
        ].where((v) => _hasValue(v)).toList(),
        'sync_error': q['sync_error'],
        'sync_conflict': q['sync_conflict'] == true,
        'sync_status': q['sync_status'],
        'sync_rejected': q['sync_rejected'] == true,
        'last_sync_attempt': q['last_sync_attempt'],
      });
    }
    out.sort((a, b) =>
        '${b['occurred_at'] ?? ''}'.compareTo('${a['occurred_at'] ?? ''}'));
    return out;
  }

  Future<void> claimLegacyPending(String queueId) async {
    final uid = Supabase.instance.client.auth.currentUser?.id;
    if (uid == null)
      throw Exception(
          'Entre com o mesmo usuário que realizou o abastecimento.');
    final queue = _queue;
    for (final q in queue) {
      if ('${q['id']}' == queueId) {
        if ('${q['user_id'] ?? ''}'.trim().isNotEmpty &&
            '${q['user_id']}' != uid)
          throw Exception('Este registro pertence a outro usuário.');
        q['user_id'] = uid;
        q.remove('sync_error');
        q.remove('sync_blocked');
      }
    }
    _state['queue'] = queue;
    await _persist();
    syncRevision.value++;
  }

  Future<void> reconcileServerQueueV78() async {
    if (!online.value || Supabase.instance.client.auth.currentUser == null) {
      return;
    }
    final eventIds = <String>[];
    for (final q in _queue) {
      if (!_fuelingRpc('${q['rpc'] ?? ''}')) continue;
      if (!_belongsToActiveUserV78(q)) continue;
      final eventId = '${_map(q['params'])['p_offline_event_id'] ?? ''}'.trim();
      if (eventId.isNotEmpty && !eventIds.contains(eventId))
        eventIds.add(eventId);
    }
    if (eventIds.isEmpty) return;

    final rows = await api.offlineEventStatusesV78(eventIds);
    if (rows.isEmpty) return;
    final byEvent = <String, Map<String, dynamic>>{
      for (final row in rows)
        if ('${row['offline_event_id'] ?? ''}'.trim().isNotEmpty)
          '${row['offline_event_id']}': row
    };

    final queue = _queue;
    final removeIds = <String>{};
    var changed = false;
    for (final q in queue) {
      if (!_fuelingRpc('${q['rpc'] ?? ''}')) continue;
      final eventId = '${_map(q['params'])['p_offline_event_id'] ?? ''}'.trim();
      final server = byEvent[eventId];
      if (server == null) continue;
      if (_intOrNull(server['movement_id']) != null) {
        removeIds.add('${q['id']}');
        changed = true;
        continue;
      }
      final status = '${server['conflict_status'] ?? ''}'.trim().toLowerCase();
      final notes = '${server['review_notes'] ?? ''}'.trim();
      if (status == 'rejected') {
        q['sync_conflict'] = false;
        q['sync_rejected'] = true;
        q['sync_blocked'] = true;
        q['sync_status'] = 'rejected';
        q['sync_error'] = notes.isEmpty
            ? 'Rejeitado na análise administrativa.'
            : 'Rejeitado na análise: $notes';
        q['reviewed_at_v77'] = server['reviewed_at'];
        q['review_status_v77'] = 'rejected';
        changed = true;
      } else if (status == 'approved') {
        q['sync_conflict'] = false;
        q.remove('sync_rejected');
        q.remove('sync_blocked');
        q.remove('sync_error');
        q['sync_status'] = 'approved_retry';
        q['reviewed_at_v77'] = server['reviewed_at'];
        q['review_status_v77'] = 'approved';
        changed = true;
      } else if (status == 'pending_review') {
        q['sync_conflict'] = true;
        q['sync_blocked'] = true;
        q['sync_status'] = 'pending_review';
        q['sync_error'] =
            '${server['reason'] ?? 'CONFLITO • AGUARDANDO ANÁLISE'}';
        changed = true;
      }
    }
    if (!changed) return;
    _state['queue'] = removeIds.isEmpty
        ? queue
        : queue.where((q) => !removeIds.contains('${q['id']}')).toList();
    pendingCount.value = _pendingQueueCountV68();
    await _persist();
    syncRevision.value++;
  }

  Future<void> reconcileReviewedConflictsV77() async {
    if (!online.value || Supabase.instance.client.auth.currentUser == null) {
      return;
    }
    final eventIds = <String>[];
    for (final q in _queue) {
      if (q['sync_conflict'] != true) continue;
      final eventId = '${_map(q['params'])['p_offline_event_id'] ?? ''}'.trim();
      if (eventId.isNotEmpty && !eventIds.contains(eventId)) {
        eventIds.add(eventId);
      }
    }
    if (eventIds.isEmpty) return;

    final rows = await api.offlineConflictStatusesV77(eventIds);
    if (rows.isEmpty) return;
    final byEvent = <String, Map<String, dynamic>>{
      for (final row in rows)
        if ('${row['offline_event_id'] ?? ''}'.trim().isNotEmpty)
          '${row['offline_event_id']}': row
    };

    final queue = _queue;
    var changed = false;
    for (final q in queue) {
      if (q['sync_conflict'] != true) continue;
      final eventId = '${_map(q['params'])['p_offline_event_id'] ?? ''}'.trim();
      final review = byEvent[eventId];
      if (review == null) continue;
      final status = '${review['status'] ?? ''}'.trim().toLowerCase();
      final notes = '${review['review_notes'] ?? ''}'.trim();
      if (status == 'rejected') {
        q['sync_conflict'] = false;
        q['sync_rejected'] = true;
        q['sync_blocked'] = true;
        q['sync_status'] = 'rejected';
        q['sync_error'] = notes.isEmpty
            ? 'Rejeitado na análise administrativa.'
            : 'Rejeitado na análise: $notes';
        q['reviewed_at_v77'] = review['reviewed_at'];
        q['review_status_v77'] = 'rejected';
        changed = true;
      } else if (status == 'approved') {
        q['sync_conflict'] = false;
        q.remove('sync_rejected');
        q.remove('sync_blocked');
        q.remove('sync_error');
        q['sync_status'] = 'approved_retry';
        q['reviewed_at_v77'] = review['reviewed_at'];
        q['review_status_v77'] = 'approved';
        changed = true;
      }
    }
    if (!changed) return;
    _state['queue'] = queue;
    pendingCount.value = _pendingQueueCountV68();
    await _persist();
    syncRevision.value++;
  }

  Future<void> applyConflictReviewV77(
      String offlineEventId, String decision, String notes) async {
    final eventId = offlineEventId.trim();
    if (eventId.isEmpty) return;
    final normalized = decision.trim().toLowerCase();
    final queue = _queue;
    var changed = false;
    for (final q in queue) {
      final localEvent =
          '${_map(q['params'])['p_offline_event_id'] ?? ''}'.trim();
      if (localEvent != eventId) continue;
      if (normalized == 'reject' || normalized == 'rejected') {
        q['sync_conflict'] = false;
        q['sync_rejected'] = true;
        q['sync_blocked'] = true;
        q['sync_status'] = 'rejected';
        q['sync_error'] = notes.trim().isEmpty
            ? 'Rejeitado na análise administrativa.'
            : 'Rejeitado na análise: ${notes.trim()}';
        q['review_status_v77'] = 'rejected';
      } else if (normalized == 'approve' || normalized == 'approved') {
        q['sync_conflict'] = false;
        q.remove('sync_rejected');
        q.remove('sync_blocked');
        q.remove('sync_error');
        q['sync_status'] = 'approved_retry';
        q['review_status_v77'] = 'approved';
      }
      q['reviewed_at_v77'] = DateTime.now().toUtc().toIso8601String();
      changed = true;
    }
    if (!changed) return;
    _state['queue'] = queue;
    pendingCount.value = _pendingQueueCountV68();
    await _persist();
    syncRevision.value++;
  }

  Future<void> retryPending() async {
    final queue = _queue;
    for (final q in queue) {
      if (q['sync_rejected'] == true || q['sync_conflict'] == true) continue;
      q.remove('sync_blocked');
      q.remove('sync_error');
      q.remove('sync_status');
    }
    _state['queue'] = queue;
    pendingCount.value = _pendingQueueCountV68();
    await _persist();
    syncRevision.value++;
    await syncPending(force: true);
  }

  Future<void> setLastTankId(int? value) async {
    final uid = _activeUserKeyV78;
    final previous = lastTankId;
    final byUser = _state['last_tank_by_user_v78'] is Map
        ? _map(_state['last_tank_by_user_v78'])
        : <String, dynamic>{};
    if (uid != null) {
      if (value == null) {
        byUser.remove(uid);
      } else {
        byUser[uid] = value;
      }
      _state['last_tank_by_user_v78'] = byUser;
    }
    if (value == null) {
      _state.remove('last_tank_id');
    } else {
      _state['last_tank_id'] = value;
    }
    if (_state['session_marker_v68'] is Map) {
      final m = _map(_state['session_marker_v68']);
      m['tank_id'] = value;
      m['last_seen_at'] = DateTime.now().toUtc().toIso8601String();
      _state['session_marker_v68'] = m;
    }
    await _persist();
    if (previous != value) {
      final type = value == null
          ? 'unit_released'
          : previous == null
              ? 'unit_selected'
              : 'unit_switched';
      await recordEventV87(type,
          tankId: value ?? previous,
          payload: {'previous_tank_id': previous, 'new_tank_id': value});
    }
  }

  Future<Map<String, dynamic>?> _readStateCandidateV73(File file) async {
    if (!await file.exists()) return null;
    final raw = await file.readAsString();
    if (raw.trim().isEmpty) return null;
    final decoded = jsonDecode(raw);
    if (decoded is! Map) return null;
    final state = _map(decoded);
    final queue = state['queue'];
    if (queue != null && queue is! List) return null;
    state['queue'] ??= <dynamic>[];
    return state;
  }

  Future<void> _loadDurableStateV73() async {
    final file = _stateFile!;
    final tmp = File('${file.path}.tmp');
    final bak = File('${file.path}.bak');
    final candidates = <File>[file, tmp, bak];
    var hadStoredData = false;
    Object? lastError;

    for (final candidate in candidates) {
      try {
        if (await candidate.exists() && await candidate.length() > 0) {
          hadStoredData = true;
        }
        final recovered = await _readStateCandidateV73(candidate);
        if (recovered == null) continue;
        _state = recovered;
        if (candidate.path != file.path) {
          _state['storage_recovered_v73'] =
              candidate.path.endsWith('.tmp') ? 'tmp' : 'backup';
          final recovery = File('${file.path}.recovery');
          await recovery.writeAsString(jsonEncode(_state), flush: true);
          // Keep the previous primary as a forensic copy when it was corrupt.
          if (await file.exists()) {
            final corrupt = File(
                '${file.path}.corrupt_${DateTime.now().millisecondsSinceEpoch}');
            try {
              await file.rename(corrupt.path);
            } catch (_) {
              try {
                await file.copy(corrupt.path);
              } catch (_) {}
              try {
                await file.delete();
              } catch (_) {}
            }
          }
          await recovery.rename(file.path);
          if (await tmp.exists()) {
            try {
              await tmp.delete();
            } catch (_) {}
          }
        }
        return;
      } catch (e) {
        lastError = e;
      }
    }

    _state = <String, dynamic>{'queue': <dynamic>[]};
    if (hadStoredData) {
      // Never silently discard evidence of a damaged queue. Invalid source files
      // are left untouched and the marker survives the next successful write.
      _state['storage_recovery_failed_v73'] = true;
      _state['storage_recovery_error_v73'] = '${lastError ?? 'invalid_state'}';
    }
  }

  Future<void> init() async {
    final dir = await getApplicationSupportDirectory();
    _stateFile = File('${dir.path}/rc_abastecimento_offline.json');
    _evidenceDir = Directory('${dir.path}/offline_evidence');
    await _evidenceDir!.create(recursive: true);
    await _loadDurableStateV73();
    _state['queue'] ??= <dynamic>[];
    _state['audit_events_v87'] ??= <dynamic>[];
    unawaited(_pruneOfflineMediaCacheV72());
    if (_state['balance_model_v69'] != true) {
      final ref = _baseReferenceDataV69;
      if (ref != null) {
        final tanks = _rows(ref['tanks']);
        void change(int? id, double delta) {
          if (id == null) return;
          for (final t in tanks) {
            if (_intOrNull(t['id']) == id) {
              t['current_balance_liters'] =
                  _num(t['current_balance_liters']) + delta;
              return;
            }
          }
        }

        for (final q in _queue) {
          final rpc = '${q['rpc'] ?? ''}';
          final params = _map(q['params']);
          final liters = _num(params['p_liters']);
          if (liters <= 0) continue;
          if (_fuelingRpc(rpc)) {
            final id = _intOrNull(params['p_source_tank_id']);
            change(id, liters);
            for (final t in tanks) {
              if (_intOrNull(t['id']) == id) {
                t['accounting_meter'] =
                    max(0, _num(t['accounting_meter']) - liters);
                break;
              }
            }
          } else if (rpc == 'rca_record_transfer') {
            change(_intOrNull(params['p_source_tank_id']), liters);
            change(_intOrNull(params['p_destination_tank_id']), -liters);
          } else if (rpc == 'rca_record_refinery_entry') {
            change(_intOrNull(params['p_tank_id']), -liters);
          }
        }
        ref['tanks'] = tanks;
        _state['reference_data'] = ref;
      }
      _state['balance_model_v69'] = true;
      await _persist();
    }
    if (_state['reference_data_by_user_v78'] is! Map &&
        _state['reference_data'] is Map) {
      final profile = _state['profile'] is Map
          ? _map(_state['profile'])
          : <String, dynamic>{};
      final uid =
          '${profile['user_id'] ?? profile['id'] ?? _state['active_user_id_v62'] ?? ''}'
              .trim();
      if (uid.isNotEmpty) {
        _state['reference_data_by_user_v78'] = {
          uid: _map(_state['reference_data'])
        };
        await _persist();
      }
    }
    if (_state['session_marker_v68'] is Map &&
        _state['app_logged_out_v62'] != true) {
      final abandoned = _map(_state['session_marker_v68']);
      _state['abandoned_session_v68'] = abandoned;
      _state.remove('session_marker_v68');
      await _persist();
      final abandonedOwner = '${abandoned['user_id'] ?? ''}'.trim();
      if (abandonedOwner.isNotEmpty) {
        _state['active_user_id_v62'] ??= abandonedOwner;
        await recordEventV87('app_session_abandoned',
            tankId: _intOrNull(abandoned['tank_id']),
            payload: {'previous_session': abandoned});
      }
    }
    pendingCount.value = _pendingQueueCountV68();
    await _refreshOnlineState();
    _connectivity.onConnectivityChanged
        .listen((_) => unawaited(_refreshOnlineState()));
    Timer.periodic(
        const Duration(seconds: 12), (_) => unawaited(_refreshOnlineState()));
  }

  Future<void> _syncImmediatelyAfterReconnectV84() async {
    if (_reconnectSyncingV84 || !online.value || !_hasSyncWorkV78()) return;
    _reconnectSyncingV84 = true;
    final before = pendingCount.value;
    try {
      var needsReauth = Supabase.instance.client.auth.currentUser == null;
      if (!needsReauth) {
        final sid = appSessionIdV30;
        if (sid == null || sid.isEmpty) {
          needsReauth = true;
        } else {
          try {
            final valid = await Supabase.instance.client
                .rpc('rca_session_valid_v30', params: {'p_session_id': sid});
            needsReauth = valid != true;
          } catch (e) {
            if (_isNetworkError(e)) rethrow;
            needsReauth = true;
          }
        }
      }
      if (needsReauth) {
        final activeLogin = activeLoginV83;
        final rememberedLogin = _sessionLoginV84;
        final credential = _sessionCredentialV84;
        if (activeLogin == null ||
            rememberedLogin == null ||
            credential == null ||
            credential.isEmpty ||
            activeLogin != rememberedLogin) {
          throw Exception(
              'A internet voltou, mas não foi possível validar automaticamente a sessão offline. Toque em Sincronizar pendentes e informe sua senha/PIN.');
        }
        await reauthenticateOnlineForSyncV83(credential);
      }
      await reconcileAbandonedSessionV68();
      final result = await syncPendingManualV74();
      if (before > 0) {
        _showSyncMessageV84(_syncResultMessageV84(result, automatic: true));
      }
    } catch (e) {
      if (before > 0) {
        _showSyncMessageV84(
            'Internet restabelecida. Não foi possível sincronizar: ${_friendlyError(e)}');
      }
    } finally {
      _reconnectSyncingV84 = false;
    }
  }

  Future<void> _refreshOnlineState() async {
    var reachable = false;
    try {
      final states = await _connectivity.checkConnectivity();
      if (states.any((x) => x != ConnectivityResult.none)) {
        final http = HttpClient()
          ..connectionTimeout = const Duration(seconds: 4);
        try {
          final req = await http
              .getUrl(Uri.parse(_supabaseUrl))
              .timeout(const Duration(seconds: 4));
          final res = await req.close().timeout(const Duration(seconds: 4));
          await res.drain();
          reachable = true;
        } finally {
          http.close(force: true);
        }
      }
    } catch (_) {}
    final changed = online.value != reachable;
    online.value = reachable;
    if (reachable) {
      if (changed && _hasSyncWorkV78()) {
        unawaited(_syncImmediatelyAfterReconnectV84());
        return;
      }
      try {
        await reconcileAbandonedSessionV68();
      } catch (_) {}
      if (_hasSyncWorkV78()) unawaited(syncPending(force: changed));
    }
  }

  void markOffline() => online.value = false;
  void markOnline() {
    final changed = !online.value;
    online.value = true;
    if (changed && _hasSyncWorkV78()) unawaited(syncPending(force: true));
  }

  Future<void> cacheProfile(Map<String, dynamic> value) async {
    _state['profile'] = value;
    final uid =
        '${value['user_id'] ?? value['id'] ?? Supabase.instance.client.auth.currentUser?.id ?? ''}'
            .trim();
    if (uid.isNotEmpty) _state['active_user_id_v62'] = uid;
    pendingCount.value = _pendingQueueCountV68();
    await _persist();
  }

  Future<void> clearProfile() async {
    _state.remove('profile');
    await _persist();
  }

  Future<void> cacheReferenceData(Map<String, dynamic> value) async {
    _state['reference_data'] = value;
    final uid = _activeUserKeyV78;
    if (uid != null) {
      final byUser = _state['reference_data_by_user_v78'] is Map
          ? _map(_state['reference_data_by_user_v78'])
          : <String, dynamic>{};
      byUser[uid] = Map<String, dynamic>.from(value);
      _state['reference_data_by_user_v78'] = byUser;
    }
    _state['balance_model_v69'] = true;
    await _persist();
  }

  Future<String> saveEvidence(Uint8List bytes, String kind, String mime) async {
    final ext = mime.contains('jpeg') || mime.contains('jpg')
        ? 'jpg'
        : mime.contains('webp')
            ? 'webp'
            : 'png';
    final file = File(
        '${_evidenceDir!.path}/${DateTime.now().microsecondsSinceEpoch}_$kind.$ext');
    await file.writeAsBytes(bytes, flush: true);
    return 'offline://${file.path}';
  }

  String? _offlineRemoteLocalNameV72(String remotePath) {
    final name = remotePath.split('/').last;
    final match = RegExp(r'^offline_\d+_(.+)$').firstMatch(name);
    return match?.group(1);
  }

  Future<Uint8List?> readOfflineMediaCacheV72(String remotePath) async {
    final dir = _evidenceDir;
    final localName = _offlineRemoteLocalNameV72(remotePath);
    if (dir == null || localName == null || localName.isEmpty) return null;
    try {
      final file = File('${dir.path}/$localName');
      if (!await file.exists()) return null;
      return await file.readAsBytes();
    } catch (_) {
      return null;
    }
  }

  Future<void> mirrorOfflineMediaV72(String remotePath, Uint8List bytes) async {
    final dir = _evidenceDir;
    final localName = _offlineRemoteLocalNameV72(remotePath);
    if (dir == null || localName == null || localName.isEmpty) return;
    try {
      final file = File('${dir.path}/$localName');
      if (!await file.exists()) await file.writeAsBytes(bytes, flush: true);
    } catch (_) {}
  }

  Future<void> _pruneOfflineMediaCacheV72() async {
    final dir = _evidenceDir;
    if (dir == null || !await dir.exists()) return;
    final protected = <String>{};
    void collect(dynamic value) {
      if (value is String && value.startsWith('offline://')) {
        protected.add(value.substring('offline://'.length));
      } else if (value is List) {
        for (final x in value) collect(x);
      } else if (value is Map) {
        for (final x in value.values) collect(x);
      }
    }

    for (final q in _queue) collect(q['params']);

    final candidates = <File>[];
    await for (final entity in dir.list()) {
      if (entity is File && !protected.contains(entity.path)) {
        candidates.add(entity);
      }
    }
    candidates.sort((a, b) {
      try {
        return a.lastModifiedSync().compareTo(b.lastModifiedSync());
      } catch (_) {
        return 0;
      }
    });
    final now = DateTime.now();
    var totalBytes = 0;
    for (final file in candidates) {
      try {
        totalBytes += await file.length();
      } catch (_) {}
    }
    const maxBytes = 512 * 1024 * 1024;
    for (final file in List<File>.from(candidates)) {
      try {
        final age = now.difference(await file.lastModified());
        if (age > const Duration(days: 30)) {
          totalBytes -= await file.length();
          await file.delete();
          candidates.remove(file);
        }
      } catch (_) {}
    }
    for (final file in candidates) {
      if (totalBytes <= maxBytes) break;
      try {
        totalBytes -= await file.length();
        await file.delete();
      } catch (_) {}
    }
  }

  bool _containsLocal(dynamic value) {
    if (value is String) return value.startsWith('offline://');
    if (value is List) return value.any(_containsLocal);
    if (value is Map) return value.values.any(_containsLocal);
    return false;
  }

  double _balance(int? tankId) {
    for (final t in _rows(cachedReferenceData?['tanks'])) {
      if (_intOrNull(t['id']) == tankId)
        return _num(t['current_balance_liters']);
    }
    return 0;
  }

  Future<Map<String, dynamic>> executeOrQueue(
      String rpc, Map<String, dynamic> params) async {
    if (!backendReadyV81 || _containsLocal(params))
      return _queueAndResult(rpc, params);
    try {
      final result =
          _map(await Supabase.instance.client.rpc(rpc, params: params));
      markOnline();
      if (_fuelingRpc(rpc)) {
        await _learnSequenceFromResultV74(result, params);
      }
      return result;
    } catch (e) {
      if (_isNetworkError(e)) {
        markOffline();
        return _queueAndResult(rpc, params);
      }
      rethrow;
    }
  }

  String newTraceIdV87() => _newOfflineEventIdV58();

  String _newOfflineEventIdV58() {
    final uid = (activeUserIdV62 ?? '00000000-0000-0000-0000-000000000000')
        .replaceAll('-', '');
    final time = DateTime.now()
        .microsecondsSinceEpoch
        .toRadixString(16)
        .padLeft(16, '0');
    final raw =
        (uid.substring(0, 16) + time).padRight(32, '0').substring(0, 32);
    return '${raw.substring(0, 8)}-${raw.substring(8, 12)}-${raw.substring(12, 16)}-${raw.substring(16, 20)}-${raw.substring(20, 32)}';
  }

  Future<Map<String, dynamic>> _queueAndResult(
      String rpc, Map<String, dynamic> params) async {
    int? offlineSequenceV74;
    String? offlineCodeV74;
    if (_fuelingRpc(rpc)) {
      if (!hasCachedCanFuelV68 || !cachedCanFuelV68)
        throw Exception(
            'Seu acesso para registrar abastecimentos offline não está autorizado. Conecte-se à internet para atualizar as permissões.');
      params = Map<String, dynamic>.from(params);
      final liters = _num(params['p_liters']);
      final price = _num(params['p_sale_price_per_liter']);
      final tankId = _intOrNull(params['p_source_tank_id']);
      if (liters <= 0)
        throw Exception('Preenchimento obrigatório: Quantidade (L)');
      if (price <= 0)
        throw Exception('Preenchimento obrigatório: Preço por litro');
      if (tankId == null) throw Exception('Unidade de abastecimento inválida.');
      for (final q in _queue) {
        if (q['sync_conflict'] == true &&
            q['sync_rejected'] != true &&
            _intOrNull(_map(q['params'])['p_source_tank_id']) == tankId)
          throw Exception(
              'Existe um abastecimento desta unidade em CONFLITO • AGUARDANDO ANÁLISE. Resolva o conflito antes de registrar outro abastecimento offline.');
      }
      final available = _balance(tankId);
      if (liters > available + 0.000001)
        throw Exception(
            'Saldo insuficiente para abastecimento offline. Disponível: ${_fmtLiters(available)}.');
      params['p_is_offline'] = true;
      params['p_offline_event_id'] ??= _newOfflineEventIdV58();
      offlineSequenceV74 = _lastKnownSequenceV74(tankId) + 1;
      offlineCodeV74 = _offlineCodeV74(tankId, offlineSequenceV74);
    }
    final queue = _queue;
    final reportSnapshot =
        _fuelingRpc(rpc) ? _offlineFuelingReportSnapshotV73(params) : null;
    queue.add(<String, dynamic>{
      'id': '${DateTime.now().microsecondsSinceEpoch}',
      'rpc': rpc,
      'params': params,
      if (offlineSequenceV74 != null)
        'offline_sequence_v74': offlineSequenceV74,
      if (offlineCodeV74 != null) 'offline_code_v74': offlineCodeV74,
      if (reportSnapshot != null) 'report_snapshot_v73': reportSnapshot,
      'created_at': DateTime.now().toUtc().toIso8601String(),
      'user_id': activeUserIdV62,
    });
    _state['queue'] = queue;
    pendingCount.value = _pendingQueueCountV68();
    await _persist();
    syncRevision.value++;
    if (_fuelingRpc(rpc)) {
      await recordEventV87('fueling_queued',
          tankId: _intOrNull(params['p_source_tank_id']),
          fuelingEventId: '${params['p_offline_event_id'] ?? ''}',
          payload: {
            'rpc': rpc,
            'offline_sequence': offlineSequenceV74,
            'offline_code': offlineCodeV74,
            'params': params,
          });
    }

    if (rpc == 'rca_record_transfer') {
      return <String, dynamic>{
        'queued': true,
        'code': 'PENDENTE (OFFLINE)',
        'source_balance': _balance(_intOrNull(params['p_source_tank_id'])),
        'destination_balance':
            _balance(_intOrNull(params['p_destination_tank_id'])),
      };
    }
    final tankId = rpc == 'rca_record_refinery_entry'
        ? _intOrNull(params['p_tank_id'])
        : _intOrNull(params['p_source_tank_id']);
    return <String, dynamic>{
      'queued': true,
      'code': offlineCodeV74 ?? 'PENDENTE (OFFLINE)',
      'offline_sequence_v74': offlineSequenceV74,
      'liters': params['p_liters'],
      'balance_after': _balance(tankId),
    };
  }

  Future<dynamic> _resolveLocal(dynamic value, String queueId) async {
    if (value is String && value.startsWith('offline://')) {
      final localPath = value.substring('offline://'.length);
      final local = File(localPath);
      if (!await local.exists())
        throw Exception('Arquivo offline não encontrado: $localPath');
      final uid = Supabase.instance.client.auth.currentUser?.id;
      if (uid == null)
        throw Exception('Sessão necessária para sincronizar dados pendentes.');
      final name = localPath.split('/').last;
      final remote = '$uid/offline_${queueId}_$name';
      final lower = name.toLowerCase();
      final mime = lower.endsWith('.jpg') || lower.endsWith('.jpeg')
          ? 'image/jpeg'
          : lower.endsWith('.webp')
              ? 'image/webp'
              : 'image/png';
      await Supabase.instance.client.storage.from('fuel-evidence').uploadBinary(
            remote,
            await local.readAsBytes(),
            fileOptions: FileOptions(contentType: mime, upsert: true),
          );
      return remote;
    }
    if (value is List) {
      final out = <dynamic>[];
      for (final item in value) {
        out.add(await _resolveLocal(item, queueId));
      }
      return out;
    }
    if (value is Map) {
      final out = <String, dynamic>{};
      for (final entry in value.entries) {
        out['${entry.key}'] = await _resolveLocal(entry.value, queueId);
      }
      return out;
    }
    return value;
  }

  void _deleteLocalRefs(dynamic value) {
    if (value is String && value.startsWith('offline://')) {
      final file = File(value.substring('offline://'.length));
      if (file.existsSync()) file.deleteSync();
    } else if (value is List) {
      for (final item in value) {
        _deleteLocalRefs(item);
      }
    } else if (value is Map) {
      for (final item in value.values) {
        _deleteLocalRefs(item);
      }
    }
  }

  Future<void> _cleanupUnlinkedRemoteEvidenceV69(
      dynamic value, String queueId) async {
    final uid = Supabase.instance.client.auth.currentUser?.id;
    if (uid == null) return;
    final paths = <String>[];
    void collect(dynamic v) {
      if (v is String && v.startsWith('$uid/offline_${queueId}_')) {
        paths.add(v);
      } else if (v is List) {
        for (final x in v) {
          collect(x);
        }
      } else if (v is Map) {
        for (final x in v.values) {
          collect(x);
        }
      }
    }

    collect(value);
    if (paths.isEmpty) return;
    try {
      await Supabase.instance.client.storage
          .from('fuel-evidence')
          .remove(paths.toSet().toList());
    } catch (_) {}
  }

  Future<void> _refreshReferenceAfterSyncV69() async {
    if (!online.value || Supabase.instance.client.auth.currentUser == null)
      return;
    try {
      final fresh =
          _map(await Supabase.instance.client.rpc('rca_reference_data_v33'));
      await cacheReferenceData(fresh);
      try {
        await refreshSequenceSnapshotV74();
      } catch (_) {}
    } catch (_) {}
  }

  Future<void> syncPending({bool force = false}) async {
    if (_syncing || !online.value || !_hasSyncWorkV78()) return;
    final uid = Supabase.instance.client.auth.currentUser?.id;
    if (uid == null) return;
    _syncing = true;
    syncing.value = true;
    try {
      if (!appLoggedOutV62 &&
          activeUserIdV62 == uid &&
          appSessionIdV30 == null) {
        try {
          final sid = await ensureAppSessionIdV30(renew: true);
          final dev = await _stableDeviceIdV42();
          await Supabase.instance.client.rpc('rca_session_claim_v42', params: {
            'p_session_id': sid,
            'p_device_id': dev,
            'p_explicit_login': false
          });
        } catch (e) {
          if (_isNetworkError(e)) {
            markOffline();
            return;
          }
        }
      }
      try {
        await reconcileServerQueueV78();
        await reconcileReviewedConflictsV77();
      } catch (e) {
        if (_isNetworkError(e)) {
          markOffline();
          return;
        }
      }
      if (force) {
        final queue = _queue;
        var claimedLegacy = false;
        for (final q in queue) {
          final rpc = '${q['rpc'] ?? ''}';
          final owner = '${q['user_id'] ?? ''}'.trim();
          if (_fuelingRpc(rpc) && owner.isEmpty && q['sync_rejected'] != true) {
            // "Sincronizar pendentes" is an explicit confirmation by the
            // authenticated user. Older app versions could save a fueling
            // without user_id, making it visible but impossible to send.
            q['user_id'] = uid;
            q['legacy_claimed_at_v75'] =
                DateTime.now().toUtc().toIso8601String();
            claimedLegacy = true;
          }
        }
        if (claimedLegacy) {
          _state['queue'] = queue;
          await _persist();
          syncRevision.value++;
        }
      }
      final snapshot = List<Map<String, dynamic>>.from(_queue);
      for (final queued in snapshot) {
        final owner = '${queued['user_id'] ?? ''}'.trim();
        if (owner.isEmpty) continue;
        if (owner != uid) continue;
        if (queued['sync_rejected'] == true)
          continue; // estado final: nunca tenta novamente.
        if (queued['sync_conflict'] == true)
          continue; // conflito já separado: não bloqueia nem é reenviado em loop.
        if (queued['sync_blocked'] == true)
          continue; // erro determinístico não trava os demais registros.
        if (_fuelingRpc('${queued['rpc'] ?? ''}')) {
          unawaited(recordEventV87('fueling_sync_started',
              tankId: _intOrNull(_map(queued['params'])['p_source_tank_id']),
              fuelingEventId:
                  '${_map(queued['params'])['p_offline_event_id'] ?? ''}',
              payload: {
                'queue_id': '${queued['id']}',
                'offline_code': queued['offline_code_v74'],
              }));
        }
        try {
          final original = _map(queued['params']);
          final rpc = '${queued['rpc']}';
          final isOfflineV68 = _fuelingRpc(rpc) &&
              original['p_is_offline'] == true &&
              (rpc == 'rca_record_fueling_v68' ||
                  rpc == 'rca_record_fueling_v71');
          if (_fuelingRpc(rpc) && !isOfflineV68) {
            final tankId = _intOrNull(original['p_source_tank_id']);
            if (tankId != null) {
              await Supabase.instance.client
                  .rpc('rca_claim_unit_v31', params: {'p_tank_id': tankId});
              await setLastTankId(tankId);
            }
          }
          final base = queued['resolved_params'] is Map
              ? _map(queued['resolved_params'])
              : original;
          final params = _map(await _resolveLocal(base, '${queued['id']}'));
          if (queued['resolved_params'] is! Map && _containsLocal(original)) {
            final queue = _queue;
            for (final q in queue) {
              if ('${q['id']}' == '${queued['id']}')
                q['resolved_params'] = params;
            }
            _state['queue'] = queue;
            await _persist();
          }
          final response =
              _map(await Supabase.instance.client.rpc(rpc, params: params));
          final status = '${response['status'] ?? ''}'.trim().toLowerCase();
          if (status == 'rejected') {
            final queue = _queue;
            for (final q in queue) {
              if ('${q['id']}' == '${queued['id']}') {
                q['sync_error'] =
                    '${response['message'] ?? 'Abastecimento rejeitado.'}';
                q['sync_blocked'] = true;
                q['sync_conflict'] = false;
                q['sync_status'] = 'rejected';
                q['sync_rejected'] = true;
                q['last_sync_attempt'] =
                    DateTime.now().toUtc().toIso8601String();
              }
            }
            _state['queue'] = queue;
            if (!_fuelingRpc(rpc)) _deleteLocalRefs(original);
            pendingCount.value = _pendingQueueCountV68();
            await _persist();
            syncRevision.value++;
            if (_fuelingRpc(rpc)) {
              await recordEventV87('fueling_sync_failed',
                  tankId: _intOrNull(original['p_source_tank_id']),
                  fuelingEventId: '${original['p_offline_event_id'] ?? ''}',
                  payload: {
                    'queue_id': '${queued['id']}',
                    'status': 'rejected',
                    'error': response['message'],
                  });
            }
            continue;
          }
          if (response['conflict'] == true || response['ok'] == false) {
            final queue = _queue;
            for (final q in queue) {
              if ('${q['id']}' == '${queued['id']}') {
                q['sync_error'] =
                    '${response['message'] ?? 'CONFLITO • AGUARDANDO ANÁLISE'}';
                q['sync_blocked'] = true;
                q['sync_conflict'] = response['conflict'] == true;
                q['sync_status'] = response['status'];
                q['last_sync_attempt'] =
                    DateTime.now().toUtc().toIso8601String();
              }
            }
            _state['queue'] = queue;
            if (!_fuelingRpc(rpc)) _deleteLocalRefs(original);
            pendingCount.value = _pendingQueueCountV68();
            await _persist();
            syncRevision.value++;
            if (_fuelingRpc(rpc)) {
              await recordEventV87('fueling_sync_conflict',
                  tankId: _intOrNull(original['p_source_tank_id']),
                  fuelingEventId: '${original['p_offline_event_id'] ?? ''}',
                  payload: {
                    'queue_id': '${queued['id']}',
                    'status': response['status'],
                    'message': response['message'],
                  });
            }
            continue;
          }
          if (!_fuelingRpc(rpc)) _deleteLocalRefs(original);
          final remaining =
              _queue.where((x) => '${x['id']}' != '${queued['id']}').toList();
          _state['queue'] = remaining;
          pendingCount.value = _pendingQueueCountV68();
          syncRevision.value++;
          await _persist();
          unawaited(_pruneOfflineMediaCacheV72());
          await _refreshReferenceAfterSyncV69();
          if (_fuelingRpc(rpc)) {
            await recordEventV87('fueling_sync_succeeded',
                tankId: _intOrNull(original['p_source_tank_id']),
                fuelingEventId: '${original['p_offline_event_id'] ?? ''}',
                payload: {
                  'queue_id': '${queued['id']}',
                  'movement_id': response['movement_id'] ?? response['id'],
                  'movement_code':
                      response['code'] ?? response['movement_code'],
                });
          }
        } catch (e) {
          if (_isNetworkError(e)) {
            markOffline();
            break;
          }
          final queue = _queue;
          Map<String, dynamic>? uploaded;
          for (final q in queue) {
            if ('${q['id']}' == '${queued['id']}') {
              uploaded = q['resolved_params'] is Map
                  ? _map(q['resolved_params'])
                  : null;
              q['sync_error'] = _friendlyError(e);
              q['sync_blocked'] = true;
              q['sync_conflict'] = false;
              q['sync_status'] = 'error';
              q['last_sync_attempt'] = DateTime.now().toUtc().toIso8601String();
              q.remove('resolved_params');
            }
          }
          if (uploaded != null)
            await _cleanupUnlinkedRemoteEvidenceV69(
                uploaded, '${queued['id']}');
          _state['queue'] = queue;
          pendingCount.value = _pendingQueueCountV68();
          await _persist();
          syncRevision.value++;
          if (_fuelingRpc('${queued['rpc'] ?? ''}')) {
            final originalForAudit = _map(queued['params']);
            await recordEventV87('fueling_sync_failed',
                tankId: _intOrNull(originalForAudit['p_source_tank_id']),
                fuelingEventId:
                    '${originalForAudit['p_offline_event_id'] ?? ''}',
                payload: {
                  'queue_id': '${queued['id']}',
                  'status': 'error',
                  'error': _friendlyError(e),
                });
          }
          continue;
        }
      }
      if (backendReadyV81 && hasPendingAuditEventsV87) {
        try {
          await syncAuditEventsV87();
        } catch (_) {}
      }
      if (online.value &&
          !_hasSyncWorkV78() &&
          Supabase.instance.client.auth.currentUser != null) {
        try {
          final fresh = _map(
              await Supabase.instance.client.rpc('rca_reference_data_v33'));
          await cacheReferenceData(fresh);
        } catch (_) {}
      }
    } finally {
      _syncing = false;
      syncing.value = false;
    }
  }

  Future<Map<String, dynamic>> syncPendingManualV74() async {
    if (!online.value) {
      throw Exception('Sem internet. Conecte o aparelho e tente novamente.');
    }
    final uid = Supabase.instance.client.auth.currentUser?.id;
    if (uid == null) {
      throw Exception(
          'Internet disponível, mas esta sessão foi iniciada offline. Toque em Sincronizar pendentes e confirme sua senha/PIN para validar a sessão.');
    }
    if (_syncing) {
      throw Exception('A sincronização já está em andamento.');
    }
    final before = pendingCount.value;
    var auditSynced = 0;
    if (hasPendingAuditEventsV87) {
      try {
        final ar = await syncAuditEventsV87();
        auditSynced = _intOrNull(ar['synced']) ?? 0;
      } catch (_) {}
    }
    if (before == 0) {
      return {
        'before': 0,
        'synced': 0,
        'after': 0,
        'audit_synced': auditSynced,
      };
    }
    await retryPending();
    final after = pendingCount.value;
    final conflicts = _queue.where((q) {
      final owner = '${q['user_id'] ?? ''}'.trim();
      return q['sync_conflict'] == true &&
          q['sync_rejected'] != true &&
          (owner.isEmpty || owner == uid);
    }).length;
    String? firstError;
    for (final q in _queue) {
      final owner = '${q['user_id'] ?? ''}'.trim();
      if (owner.isNotEmpty && owner != uid) continue;
      final value = '${q['sync_error'] ?? ''}'.trim();
      if (value.isNotEmpty) {
        firstError = value;
        break;
      }
    }
    try {
      await refreshSequenceSnapshotV74();
    } catch (_) {}
    return {
      'before': before,
      'synced': max(0, before - after),
      'after': after,
      'conflicts': conflicts,
      'audit_synced': auditSynced,
      if (firstError != null) 'error': firstError,
    };
  }

  Future<void> _persist() {
    _writeChain = _writeChain.catchError((_) {}).then((_) async {
      final file = _stateFile;
      if (file == null) return;
      final tmp = File('${file.path}.tmp');
      final bak = File('${file.path}.bak');
      final payload = jsonEncode(_state);

      await tmp.writeAsString(payload, flush: true);
      final verified = await _readStateCandidateV73(tmp);
      if (verified == null) {
        throw const FormatException(
            'Falha ao validar a fila offline temporária');
      }

      if (await file.exists()) {
        // Preserve the last known primary before replacement. If Android closes
        // the process during the swap, init() can recover from tmp or backup.
        await file.copy(bak.path);
      }
      try {
        await tmp.rename(file.path);
      } on FileSystemException {
        if (await file.exists()) await file.delete();
        await tmp.rename(file.path);
      }

      final primary = await _readStateCandidateV73(file);
      if (primary == null) {
        throw const FormatException('Falha ao validar a fila offline gravada');
      }
    });
    return _writeChain;
  }
}

final offlineStore = OfflineStore();

Future<String?> _requestSyncCredentialV83(BuildContext context) async {
  final controller = TextEditingController();
  final value = await showDialog<String>(
      context: context,
      barrierDismissible: false,
      builder: (ctx) => AlertDialog(
            title: const Text('Validar sessão para sincronizar'),
            content: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text(
                    'A internet voltou, mas esta sessão foi iniciada offline. Informe sua senha/PIN uma vez para validar a sessão e enviar os registros pendentes.'),
                const SizedBox(height: 14),
                TextField(
                  controller: controller,
                  autofocus: true,
                  obscureText: true,
                  decoration: const InputDecoration(
                      labelText: 'Senha/PIN',
                      prefixIcon: Icon(Icons.lock_outline_rounded)),
                  onSubmitted: (value) {
                    if (value.trim().isNotEmpty) Navigator.pop(ctx, value);
                  },
                ),
              ],
            ),
            actions: [
              TextButton(
                  onPressed: () => Navigator.pop(ctx),
                  child: const Text('Cancelar')),
              FilledButton(
                  onPressed: () {
                    final value = controller.text;
                    if (value.trim().isNotEmpty) Navigator.pop(ctx, value);
                  },
                  child: const Text('Validar e sincronizar')),
            ],
          ));
  controller.dispose();
  return value;
}

Future<void> _syncPendingWithFeedbackV74(BuildContext context) async {
  try {
    if (offlineStore.onlineReauthRequiredV81) {
      final credential = await _requestSyncCredentialV83(context);
      if (credential == null || credential.trim().isEmpty) return;
      if (!context.mounted) return;
      await offlineStore.reauthenticateOnlineForSyncV83(credential);
      if (!context.mounted) return;
    }
    final result = await offlineStore.syncPendingManualV74();
    if (!context.mounted) return;
    final message = _syncResultMessageV84(result);
    ScaffoldMessenger.of(context)
        .showSnackBar(SnackBar(content: Text(message)));
  } catch (e) {
    if (!context.mounted) return;
    ScaffoldMessenger.of(context)
        .showSnackBar(SnackBar(content: Text(_friendlyError(e))));
  }
}

class FuelApi {
  SupabaseClient get client => Supabase.instance.client;

  Future<Map<String, dynamic>> profile() async =>
      _map(await client.rpc('rca_profile'));
  Future<Map<String, dynamic>> referenceData() async {
    try {
      final value = _map(await client.rpc('rca_reference_data_v33'));
      offlineStore.markOnline();
      await offlineStore.cacheReferenceData(value);
      try {
        await offlineStore.refreshSequenceSnapshotV74();
      } catch (_) {}
      return value;
    } catch (e) {
      if (_isNetworkError(e)) offlineStore.markOffline();
      final cached = offlineStore.cachedReferenceData;
      if (cached != null) return cached;
      rethrow;
    }
  }

  Future<List<Map<String, dynamic>>> recent({int limit = 40}) async => _rows(
      await client.rpc('rca_recent_movements', params: {'p_limit': limit}));

  Future<List<Map<String, dynamic>>> adminSearch({
    DateTime? start,
    DateTime? end,
    int? workId,
    String? asset,
    String? plate,
    String? operatorName,
    String? type,
    int limit = 200,
  }) async {
    final data = await client.rpc('rca_admin_search', params: {
      'p_start': start?.toUtc().toIso8601String(),
      'p_end': end?.toUtc().toIso8601String(),
      'p_work_id': workId,
      'p_asset_query': asset,
      'p_plate': plate,
      'p_operator': operatorName,
      'p_type': type,
      'p_limit': limit,
    });
    return _rows(data);
  }

  Future<Map<String, dynamic>> refineryEntry({
    required int tankId,
    required double liters,
    required String supplier,
    String? document,
    String? batch,
    double? unitCost,
    List<String> photos = const [],
    String? notes,
  }) async {
    return offlineStore.executeOrQueue('rca_record_refinery_entry', {
      'p_tank_id': tankId,
      'p_liters': liters,
      'p_supplier_name': supplier,
      'p_document': document,
      'p_batch': batch,
      'p_unit_cost': unitCost,
      'p_photo_paths': photos,
      'p_notes': notes,
    });
  }

  Future<Map<String, dynamic>> transfer({
    required int sourceTankId,
    required int destinationTankId,
    required double liters,
    String? notes,
  }) async {
    return offlineStore.executeOrQueue('rca_record_transfer', {
      'p_source_tank_id': sourceTankId,
      'p_destination_tank_id': destinationTankId,
      'p_liters': liters,
      'p_notes': notes,
    });
  }

  Future<Map<String, dynamic>> fueling({
    required int sourceTankId,
    int? workId,
    int? machineId,
    int? thirdPartyVehicleId,
    String? thirdPartyPlate,
    String? thirdPartyCompany,
    String? thirdPartyDescription,
    required double liters,
    double? meter,
    required bool meterUnavailable,
    String? meterObservation,
    List<String> meterDamagePhotos = const [],
    required String receiverName,
    String? receiverCompany,
    required String receiverSignature,
    required String operatorSignature,
    List<String> photos = const [],
    String? notes,
    bool lubricated = false,
    double? latitude,
    double? longitude,
    String? kmPhotoBefore,
    String? kmPhotoAfter,
    String? totalizerPhotoBefore,
    String? totalizerPhotoAfter,
    String? platePhotoBefore,
    String? platePhotoAfter,
    required String fuelType,
    required String locationAddress,
  }) async {
    return offlineStore.executeOrQueue('rca_record_fueling_v14', {
      'p_source_tank_id': sourceTankId,
      'p_work_id': workId,
      'p_machine_id': machineId,
      'p_third_party_vehicle_id': thirdPartyVehicleId,
      'p_third_party_plate': thirdPartyPlate,
      'p_third_party_company': thirdPartyCompany,
      'p_third_party_description': thirdPartyDescription,
      'p_liters': liters,
      'p_km_hourmeter': meter,
      'p_km_unavailable': meterUnavailable,
      'p_km_observation': meterObservation,
      'p_km_damage_photo_paths': meterDamagePhotos,
      'p_receiver_name': receiverName,
      'p_receiver_company': receiverCompany,
      'p_receiver_signature_path': receiverSignature,
      'p_operator_signature_path': operatorSignature,
      'p_photo_paths': photos,
      'p_notes': notes,
      'p_lubricated': lubricated,
      'p_latitude': latitude,
      'p_longitude': longitude,
      'p_km_photo_before_path': kmPhotoBefore,
      'p_km_photo_after_path': kmPhotoAfter,
      'p_totalizer_photo_before_path': totalizerPhotoBefore,
      'p_totalizer_photo_after_path': totalizerPhotoAfter,
      'p_plate_photo_before_path': platePhotoBefore,
      'p_plate_photo_after_path': platePhotoAfter,
      'p_fuel_type': fuelType,
      'p_location_address': locationAddress,
    });
  }

  Future<Map<String, dynamic>> refineryLoadV22({
    required int truckTankId,
    required double liters,
    required String supplier,
    required String invoice,
    required double unitCost,
    required String fuelType,
    required String truckPlatePhoto,
    required String invoicePhoto,
    String? batch,
    String? notes,
  }) async =>
      _map(await client.rpc('rca_record_refinery_load_v22', params: {
        'p_truck_tank_id': truckTankId,
        'p_liters': liters,
        'p_supplier_name': supplier,
        'p_invoice_number': invoice,
        'p_batch_number': batch,
        'p_unit_cost': unitCost,
        'p_fuel_type': fuelType,
        'p_photo_paths': <String>[truckPlatePhoto, invoicePhoto],
        'p_notes': notes,
      }));
  Future<Map<String, dynamic>> refineryToTeV22(
          {required int truckTankId,
          required int teTankId,
          int? lotId,
          required double liters,
          String? notes}) async =>
      _map(await client.rpc('rca_record_refinery_to_te_v22', params: {
        'p_truck_tank_id': truckTankId,
        'p_te_tank_id': teTankId,
        'p_lot_id': lotId,
        'p_liters': liters,
        'p_notes': notes
      }));
  Future<Map<String, dynamic>> transferV22(
          {required int sourceTankId,
          required int destinationTankId,
          required double liters,
          required String donor,
          required String receiver,
          required String donorSignature,
          required String receiverSignature,
          int? lotId,
          String? notes}) async =>
      _map(await client.rpc('rca_record_transfer_v22', params: {
        'p_source_tank_id': sourceTankId,
        'p_destination_tank_id': destinationTankId,
        'p_liters': liters,
        'p_donor_responsible': donor,
        'p_receiver_responsible': receiver,
        'p_donor_signature_path': donorSignature,
        'p_receiver_signature_path': receiverSignature,
        'p_lot_id': lotId,
        'p_notes': notes
      }));
  Future<Map<String, dynamic>> fuelingV71(
          {required int sourceTankId,
          int? workId,
          int? machineId,
          int? thirdId,
          String? thirdPartyPlate,
          String? thirdPartyDescription,
          required double liters,
          double? km,
          double? hourmeter,
          String? responsible,
          required String receiver,
          required String receiverSignature,
          required String operatorSignature,
          String? meterPhoto,
          required String totalizerPhoto,
          required DateTime totalizerBeforeCapturedAt,
          required String identityPhoto,
          required String identityKind,
          String? extraPhoto,
          required double salePrice,
          String? notes,
          required bool lubricated,
          required String fuelingEventId,
          required String fuelType,
          required String location,
          double? latitude,
          double? longitude,
          DateTime? locationCapturedAt,
          double? locationAccuracyM,
          required DateTime occurredAt}) async =>
      offlineStore.executeOrQueue('rca_record_fueling_v71', {
        'p_source_tank_id': sourceTankId,
        'p_work_id': workId,
        'p_machine_id': machineId,
        'p_third_party_vehicle_id': thirdId,
        'p_third_party_plate': thirdPartyPlate,
        'p_third_party_company': null,
        'p_third_party_description': thirdPartyDescription,
        'p_liters': liters,
        'p_km_value': km,
        'p_hourmeter_value': hourmeter,
        'p_responsible_name': responsible,
        'p_receiver_name': receiver,
        'p_receiver_company': null,
        'p_receiver_signature_path': receiverSignature,
        'p_operator_signature_path': operatorSignature,
        'p_meter_photo_path': meterPhoto,
        'p_totalizer_photo_path': totalizerPhoto,
        'p_identity_photo_path': identityPhoto,
        'p_identity_evidence_kind': identityKind,
        'p_extra_photo_path': extraPhoto,
        'p_sale_price_per_liter': salePrice,
        'p_notes': notes,
        'p_lubricated': lubricated,
        'p_latitude': latitude,
        'p_longitude': longitude,
        'p_fuel_type': fuelType,
        'p_location_address': location,
        'p_location_captured_at': locationCapturedAt?.toUtc().toIso8601String(),
        'p_location_accuracy_m': locationAccuracyM,
        'p_totalizer_before_captured_at':
            totalizerBeforeCapturedAt.toUtc().toIso8601String(),
        'p_occurred_at': occurredAt.toUtc().toIso8601String(),
        'p_offline_event_id': fuelingEventId,
        'p_is_offline': false
      });
  Future<List<Map<String, dynamic>>> offlineUnitUseConflictsV87() async =>
      _rows(await client.rpc('rca_offline_unit_use_conflicts_v87'));
  Future<Map<String, dynamic>> reviewOfflineUnitUseConflictV87(
          int conflictId, String notes) async =>
      _map(await client.rpc('rca_review_offline_unit_use_conflict_v87',
          params: {'p_conflict_id': conflictId, 'p_notes': notes}));
  Future<Map<String, dynamic>> cancelFuelingV87(
          int movementId, String reason) async =>
      _map(await client.rpc('rca_cancel_fueling_v87', params: {
        'p_movement_id': movementId,
        'p_reason': reason,
      }));

  Future<Map<String, dynamic>> pdfSaleV41(int movementId) async =>
      _map(await client
          .rpc('rca_pdf_sale_v41', params: {'p_movement_id': movementId}));
  Future<Map<String, dynamic>> dashboardV22() async =>
      _map(await client.rpc('rca_fuel_dashboard_v22', params: {'p_days': 7}));
  Future<Map<String, dynamic>> dailyFuelV22(DateTime d) async {
    final day =
        '${d.year.toString().padLeft(4, '0')}-${d.month.toString().padLeft(2, '0')}-${d.day.toString().padLeft(2, '0')}';
    return _map(
        await client.rpc('rca_daily_fuel_report_v22', params: {'p_date': day}));
  }

  Future<Map<String, dynamic>> traceV22(int lotId) async =>
      _map(await client.rpc('rca_nf_trace_v22', params: {'p_lot_id': lotId}));
  Future<List<Map<String, dynamic>>> compareV22(
          List<int> machines, List<int> thirds) async =>
      _rows(await client.rpc('rca_compare_equipment_v22', params: {
        'p_machine_ids': machines,
        'p_third_party_ids': thirds,
        'p_start': null,
        'p_end': null
      }));

  Future<List<Map<String, dynamic>>> offlineConflictsV58() async =>
      _rows(await client.rpc('rca_offline_conflicts_v58'));
  Future<List<Map<String, dynamic>>> offlineConflictStatusesV77(
          List<String> offlineEventIds) async =>
      offlineEventIds.isEmpty
          ? <Map<String, dynamic>>[]
          : _rows(await client.rpc('rca_offline_conflict_statuses_v77',
              params: {'p_offline_event_ids': offlineEventIds}));
  Future<List<Map<String, dynamic>>> offlineEventStatusesV78(
          List<String> offlineEventIds) async =>
      offlineEventIds.isEmpty
          ? <Map<String, dynamic>>[]
          : _rows(await client.rpc('rca_offline_event_statuses_v78',
              params: {'p_offline_event_ids': offlineEventIds}));
  Future<Map<String, dynamic>> reviewOfflineConflictV58(int id, String decision,
          {String? notes}) async =>
      _map(await client.rpc('rca_review_offline_conflict_v58', params: {
        'p_conflict_id': id,
        'p_decision': decision,
        'p_notes': notes
      }));
  Future<Map<String, dynamic>> correctOfflineConflictV89(
          int id, Map<String, dynamic> changes, String reason) async =>
      _map(await client.rpc('rca_correct_offline_conflict_v89', params: {
        'p_conflict_id': id,
        'p_changes': changes,
        'p_reason': reason,
      }));
  Future<Map<String, dynamic>> operationAuditFiltersV59() async =>
      _map(await client.rpc('rc_web_operation_audit_filters_v59'));
  Future<List<Map<String, dynamic>>> operationAuditV59(
          {String? userId,
          int? tankId,
          String? eventType,
          DateTime? start,
          DateTime? end,
          String? query}) async =>
      _rows(await client.rpc('rc_web_operation_audit_v59', params: {
        'p_user_id': userId,
        'p_user_name': null,
        'p_tank_id': tankId,
        'p_event_type': eventType,
        'p_start': start?.toUtc().toIso8601String(),
        'p_end': end?.toUtc().toIso8601String(),
        'p_query': query,
        'p_limit': 1000
      }));

  Future<Map<String, dynamic>> dashboardKpisV28() async =>
      _map(await client.rpc('rca_dashboard_kpis_v28'));
  Future<List<Map<String, dynamic>>> worksCatalogV28() async =>
      _rows(await client.rpc('rca_works_catalog_v28'));
  Future<Map<String, dynamic>> workDetailV28(int workId) async => _map(
      await client.rpc('rca_work_detail_v28', params: {'p_work_id': workId}));
  Future<Map<String, dynamic>> restoreWorkV28(int workId) async => _map(
      await client.rpc('rca_restore_work_v28', params: {'p_work_id': workId}));
  Future<Map<String, dynamic>> purgeWorkV28(int workId) async => _map(
      await client.rpc('rca_purge_work_v28', params: {'p_work_id': workId}));
  Future<List<Map<String, dynamic>>> auditHistoryV28(
          {String? query, int limit = 200}) async =>
      _rows(await client.rpc('rca_audit_history_v60',
          params: {'p_query': query, 'p_limit': limit}));
  Future<Map<String, dynamic>> globalSearchV28(String query,
          {int limit = 20}) async =>
      _map(await client.rpc('rca_global_search_v28',
          params: {'p_query': query, 'p_limit': limit}));
  Future<Map<String, dynamic>> generalRecordsV28({
    DateTime? start,
    DateTime? end,
    int? workId,
    String? asset,
    String? plate,
    String? operatorName,
    String? type,
    String? query,
    String? sourceCode,
    String? invoice,
    String? responsible,
    int? companyId,
    String? fuelType,
    int limit = 500,
  }) async =>
      _map(await client.rpc('rca_general_records_v71', params: {
        'p_start': start?.toUtc().toIso8601String(),
        'p_end': end?.toUtc().toIso8601String(),
        'p_work_id': workId,
        'p_asset_query': asset,
        'p_plate': plate,
        'p_operator': operatorName,
        'p_type': type,
        'p_query': query,
        'p_source_code': sourceCode,
        'p_invoice': invoice,
        'p_responsible': responsible,
        'p_company_id': companyId,
        'p_fuel_type': fuelType,
        'p_limit': limit,
      }));
  Future<Map<String, dynamic>> deleteWorkV25(int workId) async => _map(
      await client.rpc('rca_delete_work_v25', params: {'p_work_id': workId}));
  Future<List<Map<String, dynamic>>> worksCatalogV23() async =>
      _rows(await client.rpc('rca_works_catalog_v23'));
  Future<Map<String, dynamic>> workFinalReportDataV23(int workId) async =>
      _map(await client.rpc('rca_work_final_report_data_v23',
          params: {'p_work_id': workId}));
  Future<Map<String, dynamic>> finalizeWorkV23(
          int workId, String pdfPath) async =>
      _map(await client.rpc('rca_finalize_work_v23',
          params: {'p_work_id': workId, 'p_pdf_path': pdfPath}));
  Future<List<Map<String, dynamic>>> generatedReportsSearchV23(
      {String? workName,
      String? responsible,
      DateTime? start,
      DateTime? end,
      String? asset}) async {
    String? day(DateTime? d) => d == null
        ? null
        : '${d.year.toString().padLeft(4, '0')}-${d.month.toString().padLeft(2, '0')}-${d.day.toString().padLeft(2, '0')}';
    return _rows(await client.rpc('rca_generated_reports_search_v23', params: {
      'p_work_name': workName,
      'p_responsible': responsible,
      'p_start': day(start),
      'p_end': day(end),
      'p_asset': asset
    }));
  }

  Future<Map<String, dynamic>> generatedReportDetailV23(int reportId) async =>
      _map(await client.rpc('rca_generated_report_detail_v23',
          params: {'p_report_id': reportId}));
  Future<List<Map<String, dynamic>>> lotsCatalogV23() async =>
      _rows(await client.rpc('rca_lots_catalog_v23'));
  Future<Map<String, dynamic>> traceV23(int lotId) async =>
      _map(await client.rpc('rca_nf_trace_v23', params: {'p_lot_id': lotId}));
  Future<Map<String, dynamic>> movementTraceV23(int movementId) async =>
      _map(await client.rpc('rca_movement_trace_v23',
          params: {'p_movement_id': movementId}));
  Future<Map<String, dynamic>> reportContextV23(int movementId) async =>
      _map(await client.rpc('rca_report_context_v23',
          params: {'p_movement_id': movementId}));
  Future<Map<String, dynamic>> userActionMap(Map<String, dynamic> body) async {
    final r = await client.functions.invoke('fuel-users', body: body);
    final m = _map(r.data);
    if (r.status < 200 || r.status >= 300 || m['error'] != null)
      throw Exception(m['error'] ?? 'Falha ao gerenciar usuario.');
    return m;
  }

  Future<Map<String, dynamic>> dailyStockReport(
      {required int tankId, DateTime? date}) async {
    final d = date ?? DateTime.now();
    final day =
        '${d.year.toString().padLeft(4, '0')}-${d.month.toString().padLeft(2, '0')}-${d.day.toString().padLeft(2, '0')}';
    return _map(await client.rpc('rca_daily_stock_report',
        params: {'p_tank_id': tankId, 'p_date': day}));
  }

  Future<Map<String, dynamic>> reportCompany() async =>
      _map(await client.rpc('rca_report_company'));

  Future<void> saveReportCompany(
      {required String companyName,
      required String companySubtitle,
      required String document,
      required String address}) async {
    await client.rpc('rca_save_report_company', params: {
      'p_company_name': companyName,
      'p_company_subtitle': companySubtitle,
      'p_document': document,
      'p_address': address,
    });
  }

  Future<List<Map<String, dynamic>>> listDrivers() async =>
      _rows(await client.rpc('rca_list_drivers'));

  Future<void> deleteDriverUser(String userId) async {
    await client.rpc('rca_delete_driver_user', params: {'p_user_id': userId});
  }

  Future<Map<String, dynamic>> adminUpdateMovementCode(
      {required int movementId, required String code}) async {
    return _map(await client.rpc('rca_admin_update_movement_code', params: {
      'p_movement_id': movementId,
      'p_code': code,
    }));
  }

  Future<Map<String, dynamic>> adminEditFuelingV47({
    required int movementId,
    required String code,
    int? workId,
    int? machineId,
    int? thirdPartyVehicleId,
    double? kmValue,
    double? hourmeterValue,
    String? receiverName,
    String? responsibleName,
    String? notes,
    String? locationAddress,
  }) async =>
      _map(await client.rpc('rca_admin_edit_fueling_v47', params: {
        'p_movement_id': movementId,
        'p_code': code,
        'p_work_id': workId,
        'p_machine_id': machineId,
        'p_third_party_vehicle_id': thirdPartyVehicleId,
        'p_km_value': kmValue,
        'p_hourmeter_value': hourmeterValue,
        'p_receiver_name': receiverName,
        'p_responsible_name': responsibleName,
        'p_notes': notes,
        'p_location_address': locationAddress,
      }));

  Future<Map<String, dynamic>> meterStatusV48(int machineId) async =>
      _map(await client
          .rpc('rca_meter_status_v48', params: {'p_machine_id': machineId}));
  Future<Map<String, dynamic>> meterCheckV48(int machineId,
          {double? km, double? hourmeter}) async =>
      _map(await client.rpc('rca_meter_check_v48', params: {
        'p_machine_id': machineId,
        'p_km': km,
        'p_hourmeter': hourmeter
      }));
  Future<Map<String, dynamic>> replaceHourmeterV48(
          {required int machineId,
          required double brokenReading,
          double newInitialReading = 0,
          required String reason,
          String? oldPhotoPath,
          String? newPhotoPath,
          DateTime? replacedAt}) async =>
      _map(await client.rpc('rca_admin_replace_hourmeter_v48', params: {
        'p_machine_id': machineId,
        'p_broken_reading': brokenReading,
        'p_new_initial_reading': newInitialReading,
        'p_reason': reason,
        'p_old_photo_path': oldPhotoPath,
        'p_new_photo_path': newPhotoPath,
        'p_replaced_at':
            (replacedAt ?? DateTime.now().toUtc()).toIso8601String(),
      }));
  Future<Map<String, dynamic>> adminEditFuelingV48({
    required int movementId,
    required String code,
    required int sourceTankId,
    int? workId,
    int? machineId,
    int? thirdPartyVehicleId,
    required double liters,
    required String fuelType,
    double? kmValue,
    double? hourmeterValue,
    String? receiverName,
    String? receiverCompany,
    String? responsibleName,
    String? operatorName,
    String? notes,
    String? locationAddress,
    double? latitude,
    double? longitude,
    DateTime? locationCapturedAt,
    double? locationAccuracyM,
    double? salePrice,
    bool lubricated = false,
    String? meterPhotoPath,
    String? totalizerPhotoPath,
    String? identityPhotoPath,
    String? identityKind,
    String? extraPhotoPath,
    String? receiverSignaturePath,
    String? operatorSignaturePath,
    DateTime? occurredAt,
    required String reason,
  }) async =>
      _map(await client.rpc('rca_admin_edit_fueling_v48', params: {
        'p_movement_id': movementId,
        'p_code': code,
        'p_source_tank_id': sourceTankId,
        'p_work_id': workId,
        'p_machine_id': machineId,
        'p_third_party_vehicle_id': thirdPartyVehicleId,
        'p_liters': liters,
        'p_fuel_type': fuelType,
        'p_km_value': kmValue,
        'p_hourmeter_value': hourmeterValue,
        'p_receiver_name': receiverName,
        'p_receiver_company': receiverCompany,
        'p_responsible_name': responsibleName,
        'p_operator_name': operatorName,
        'p_notes': notes,
        'p_location_address': locationAddress,
        'p_latitude': latitude,
        'p_longitude': longitude,
        'p_location_captured_at': locationCapturedAt?.toUtc().toIso8601String(),
        'p_location_accuracy_m': locationAccuracyM,
        'p_sale_price_per_liter': salePrice,
        'p_lubricated': lubricated,
        'p_meter_photo_path': meterPhotoPath,
        'p_totalizer_photo_path': totalizerPhotoPath,
        'p_identity_photo_path': identityPhotoPath,
        'p_identity_evidence_kind': identityKind,
        'p_extra_photo_path': extraPhotoPath,
        'p_receiver_signature_path': receiverSignaturePath,
        'p_operator_signature_path': operatorSignaturePath,
        'p_occurred_at': occurredAt?.toUtc().toIso8601String(),
        'p_reason': reason,
      }));

  Future<void> invokeUserAction(Map<String, dynamic> body) async {
    final res = await client.functions.invoke('fuel-users', body: body);
    if (res.status < 200 || res.status >= 300) {
      final m = _map(res.data);
      throw Exception(m['error'] ?? 'Falha ao gerenciar usuário.');
    }
    final m = _map(res.data);
    if (m['error'] != null) throw Exception(m['error']);
  }

  Future<List<Map<String, dynamic>>> managedCompanies() async =>
      _rows(await client.rpc('rca_managed_companies'));
  Future<List<Map<String, dynamic>>> companiesByRole(String role) async =>
      _rows(
          await client.rpc('rca_companies_by_role', params: {'p_role': role}));

  Future<void> saveManagedCompany({
    int? id,
    required String name,
    String? subtitle,
    String? document,
    String? zipCode,
    String? street,
    String? streetNumber,
    String? complement,
    String? neighborhood,
    String? city,
    String? state,
    bool active = true,
    required bool isClient,
    required bool isEquipmentOwner,
    required bool isFuelSupplier,
  }) async {
    await client.rpc('rca_save_managed_company_v2', params: {
      'p_id': id,
      'p_name': name,
      'p_subtitle': subtitle,
      'p_document': document,
      'p_zip_code': zipCode,
      'p_street': street,
      'p_street_number': streetNumber,
      'p_complement': complement,
      'p_neighborhood': neighborhood,
      'p_city': city,
      'p_state': state,
      'p_active': active,
      'p_is_client': isClient,
      'p_is_equipment_owner': isEquipmentOwner,
      'p_is_fuel_supplier': isFuelSupplier,
    });
  }

  Future<void> saveWork(
      {int? id,
      required String name,
      String? location,
      String? responsible,
      int? companyId,
      bool active = true}) async {
    await client.rpc('rca_save_work_v2', params: {
      'p_id': id,
      'p_name': name,
      'p_location': location,
      'p_company_id': companyId,
      'p_active': active,
      'p_responsible': responsible,
    });
  }

  Future<int?> saveMachine({
    int? id,
    required String assetNumber,
    String? model,
    String? plate,
    String? type,
    String? location,
    bool active = true,
    double? comboioCapacityLiters,
    double? fuelTankCapacityLiters,
    required String measurementType,
  }) async {
    final value = await client.rpc('rca_save_machine_v33', params: {
      'p_id': id,
      'p_asset_number': assetNumber,
      'p_model': model,
      'p_plate': plate,
      'p_type': type,
      'p_location': location,
      'p_active': active,
      'p_comboio_capacity_liters': comboioCapacityLiters,
      'p_fuel_tank_capacity_liters': fuelTankCapacityLiters,
      'p_measurement_type': measurementType,
    });
    return _intOrNull(value);
  }

  Future<void> saveThirdParty({
    int? id,
    String? plate,
    String? company,
    String? description,
    String? driverName,
    bool active = true,
  }) async {
    await client.rpc('rca_save_third_party_vehicle', params: {
      'p_id': id,
      'p_plate': plate,
      'p_company_name': company,
      'p_description': description,
      'p_driver_name': driverName,
      'p_active': active,
    });
  }

  Future<void> archiveManagedCompany(Map<String, dynamic> x) async {
    await saveManagedCompany(
      id: _intOrNull(x['id']),
      name: '${x['name'] ?? ''}',
      subtitle: '${x['subtitle'] ?? ''}',
      document: '${x['document'] ?? ''}',
      zipCode: '${x['zip_code'] ?? ''}',
      street: '${x['street'] ?? ''}',
      streetNumber: '${x['street_number'] ?? ''}',
      complement: '${x['complement'] ?? ''}',
      neighborhood: '${x['neighborhood'] ?? ''}',
      city: '${x['city'] ?? ''}',
      state: '${x['state'] ?? ''}',
      active: false,
      isClient: x['is_client'] == true,
      isEquipmentOwner: x['is_equipment_owner'] == true,
      isFuelSupplier: x['is_fuel_supplier'] == true,
    );
  }

  Future<void> archiveMachine(Map<String, dynamic> x) async {
    final id = _intOrNull(x['id']);
    if (id == null) throw Exception('Ativo inválido');
    await client.rpc('rca_archive_machine_v68', params: {'p_id': id});
  }

  Future<void> archiveThirdParty(Map<String, dynamic> x) async {
    await saveThirdParty(
        id: _intOrNull(x['id']),
        plate: '${x['plate'] ?? ''}',
        company: '${x['company_name'] ?? x['company'] ?? ''}',
        description: '${x['description'] ?? ''}',
        driverName: '${x['driver_name'] ?? ''}',
        active: false);
  }

  Future<List<Map<String, dynamic>>> truckRoles() async =>
      _rows(await client.rpc('rca_truck_roles'));
  Future<int?> saveTruckRole(
      {int? tankId,
      required int machineId,
      required double capacityLiters,
      bool active = true}) async {
    final value = await client.rpc('rca_save_truck_role', params: {
      'p_tank_id': tankId,
      'p_machine_id': machineId,
      'p_capacity_liters': capacityLiters,
      'p_active': active
    });
    return _intOrNull(value);
  }

  Future<Map<String, dynamic>> removeTruckRole(int tankId) async => _map(
      await client.rpc('rca_remove_truck_role', params: {'p_tank_id': tankId}));

  Future<void> saveTank({
    int? id,
    required String code,
    required String name,
    required String tankType,
    required double capacityLiters,
  }) async {
    await client.rpc('rca_save_tank', params: {
      'p_id': id,
      'p_code': code,
      'p_name': name,
      'p_tank_type': tankType,
      'p_capacity_liters': capacityLiters,
    });
  }

  Future<Map<String, dynamic>> removeTank(int tankId) async {
    return _map(await client
        .rpc('rca_admin_remove_tank', params: {'p_tank_id': tankId}));
  }

  Future<String> uploadBytes(Uint8List bytes, String kind,
      {String mime = 'image/png'}) async {
    if (!offlineStore.backendReadyV81)
      return offlineStore.saveEvidence(bytes, kind, mime);
    try {
      final uid = client.auth.currentUser?.id;
      if (uid == null)
        throw Exception(
            'Sessão expirada. Entre novamente para registrar o lançamento.');
      final stamp = DateTime.now().microsecondsSinceEpoch;
      final ext = mime.contains('pdf')
          ? 'pdf'
          : mime.contains('jpeg')
              ? 'jpg'
              : mime.contains('webp')
                  ? 'webp'
                  : 'png';
      final path = '$uid/${stamp}_$kind.$ext';
      await client.storage
          .from('fuel-evidence')
          .uploadBinary(
            path,
            bytes,
            fileOptions: FileOptions(contentType: mime, upsert: false),
          )
          .timeout(const Duration(seconds: 45));
      offlineStore.markOnline();
      return path;
    } catch (e) {
      if (_isNetworkError(e)) {
        offlineStore.markOffline();
        return offlineStore.saveEvidence(bytes, kind, mime);
      }
      rethrow;
    }
  }

  Future<Uint8List?> downloadMedia(String? path) async {
    if (path == null || path.trim().isEmpty) return null;
    final value = path.trim();
    if (value.startsWith('offline://')) {
      try {
        final file = File(value.substring('offline://'.length));
        return await file.exists() ? await file.readAsBytes() : null;
      } catch (_) {
        return null;
      }
    }
    final cached = await offlineStore.readOfflineMediaCacheV72(value);
    if (cached != null) return cached;
    try {
      final bytes = await client.storage.from('fuel-evidence').download(value);
      await offlineStore.mirrorOfflineMediaV72(value, bytes);
      return bytes;
    } catch (_) {
      return null;
    }
  }
}

final api = FuelApi();

class AuthGate extends StatefulWidget {
  const AuthGate({super.key});
  @override
  State<AuthGate> createState() => _AuthGateState();
}

class _AuthGateState extends State<AuthGate> with WidgetsBindingObserver {
  bool loading = true, _checkingSessionV30 = false, _closingV38 = false;
  Map<String, dynamic>? profile;
  String? error;
  Timer? _sessionGuardV30;
  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addObserver(this);
    _restore();
  }

  @override
  void dispose() {
    WidgetsBinding.instance.removeObserver(this);
    _sessionGuardV30?.cancel();
    super.dispose();
  }

  @override
  void didChangeAppLifecycleState(AppLifecycleState state) {
    if (state == AppLifecycleState.resumed) {
      unawaited(offlineStore.recordEventV87('app_resumed'));
      _startSessionGuardV30();
      unawaited(_checkSessionV30());
      return;
    }
    // paused/inactive/hidden = minimizado: mantém tela, sessão e unidade reservada.
    unawaited(offlineStore
        .recordEventV87('app_lifecycle', payload: {'state': state.name}));
    if (state == AppLifecycleState.detached) {
      unawaited(_closeAppV38());
    }
  }

  Future<void> _closeAppV38() async {
    if (_closingV38 || profile == null) return;
    _closingV38 = true;
    _sessionGuardV30?.cancel();
    final id = offlineStore.appSessionIdV30;
    final tankId = offlineStore.lastTankId;
    final occurred = DateTime.now().toUtc();
    try {
      await offlineStore.recordEventV87('app_closed',
          tankId: tankId, occurredAt: occurred);
      if (offlineStore.backendReadyV81) {
        try {
          await offlineStore
              .syncAuditEventsV87()
              .timeout(const Duration(seconds: 1));
        } catch (_) {}
      }
      if (offlineStore.online.value) {
        await Supabase.instance.client.rpc('rca_offline_logout_v62', params: {
          'p_session_id': id,
          'p_tank_id': tankId,
          'p_occurred_at': occurred.toIso8601String()
        }).timeout(const Duration(seconds: 2));
      } else {
        await offlineStore.queueOfflineLogoutV62(
            sessionId: id, tankId: tankId, occurredAt: occurred);
      }
    } catch (e) {
      if (_isNetworkError(e)) {
        try {
          offlineStore.markOffline();
          await offlineStore.queueOfflineLogoutV62(
              sessionId: id, tankId: tankId, occurredAt: occurred);
        } catch (_) {}
      }
    }
    try {
      await offlineStore.clearSessionMarkerV68();
      await offlineStore.clearProfile();
      await offlineStore.setLastTankId(null);
      await offlineStore.clearAppSessionIdV30();
    } catch (_) {}
    try {
      await Supabase.instance.client.auth
          .signOut(scope: SignOutScope.local)
          .timeout(const Duration(seconds: 1));
    } catch (_) {}
  }

  Future<Map<String, dynamic>> _claimSessionV42(
      {required bool explicitLogin}) async {
    final id = await offlineStore.ensureAppSessionIdV30(renew: false);
    final deviceId = await _stableDeviceIdV42();
    return api.sessionClaimV42(id, deviceId, explicitLogin: explicitLogin);
  }

  void _startSessionGuardV30() {
    _sessionGuardV30?.cancel();
    _sessionGuardV30 = Timer.periodic(
        const Duration(seconds: 10), (_) => unawaited(_checkSessionV30()));
  }

  Future<void> _checkSessionV30() async {
    if (_checkingSessionV30 || !offlineStore.online.value || profile == null)
      return;
    final id = offlineStore.appSessionIdV30;
    if (id == null) return;
    _checkingSessionV30 = true;
    try {
      if (!await api.sessionValidV30(id))
        await _forcedLocalLogoutV30(
            'Sua sessão foi desconectada pelo administrador.');
    } catch (e) {
      if (!_isNetworkError(e))
        await _forcedLocalLogoutV30('Sua sessão não está mais ativa.');
    } finally {
      _checkingSessionV30 = false;
    }
  }

  Future<void> _forcedLocalLogoutV30(String message) async {
    _sessionGuardV30?.cancel();
    await offlineStore.clearSessionMarkerV68();
    await offlineStore.clearProfile();
    await offlineStore.setLastTankId(null);
    await offlineStore.clearAppSessionIdV30();
    await offlineStore.markAppLoggedOutV62();
    try {
      await Supabase.instance.client.auth.signOut(scope: SignOutScope.local);
    } catch (_) {}
    if (mounted)
      setState(() {
        profile = null;
        loading = false;
        error = message;
      });
  }

  Future<void> _restore() async {
    final cached = offlineStore.cachedProfile;
    if (offlineStore.appLoggedOutV62) {
      if (mounted) setState(() => loading = false);
      return;
    }
    if (Supabase.instance.client.auth.currentSession == null) {
      if (!offlineStore.online.value && cached != null) {
        await offlineStore
            .cacheFuelingPermissionV68(cached['can_fueling_create'] == true);
        await offlineStore.reconcileAbandonedSessionV68();
        await offlineStore.beginSessionMarkerV68();
        if (mounted)
          setState(() {
            profile = cached;
            loading = false;
          });
      } else if (mounted) setState(() => loading = false);
      return;
    }
    try {
      if (offlineStore.online.value) {
        await offlineStore.reconcileAbandonedSessionV68();
        final claim = await _claimSessionV42(explicitLogin: false);
        if (claim['ok'] != true) {
          await _forcedLocalLogoutV30(
              '${claim['message'] ?? 'Sua sessão não está mais ativa. Entre novamente para continuar.'}');
          return;
        }
      }
      final p = await api.profile();
      offlineStore.markOnline();
      await offlineStore.cacheProfile(p);
      await offlineStore
          .cacheFuelingPermissionV68(p['can_fueling_create'] == true);
      try {
        await api.referenceData();
      } catch (_) {}
      await offlineStore
          .markAppLoggedInV62(Supabase.instance.client.auth.currentUser?.id);
      await offlineStore.beginSessionMarkerV68();
      if (mounted)
        setState(() {
          profile = p;
          loading = false;
        });
      _startSessionGuardV30();
      unawaited(offlineStore.syncPending(force: true));
    } catch (e) {
      if (_isNetworkError(e) && cached != null) {
        offlineStore.markOffline();
        await offlineStore
            .cacheFuelingPermissionV68(cached['can_fueling_create'] == true);
        await offlineStore.reconcileAbandonedSessionV68();
        await offlineStore.beginSessionMarkerV68();
        if (mounted)
          setState(() {
            profile = cached;
            loading = false;
          });
      } else {
        await _forcedLocalLogoutV30(_friendlyError(e));
      }
    }
  }

  Future<void> _login(String username, String password) async {
    setState(() {
      loading = true;
      error = null;
    });
    final client = Supabase.instance.client;
    final normalized = username.trim().toLowerCase();
    if (!offlineStore.online.value) {
      try {
        final p = await offlineStore.offlineLoginV62(normalized, password);
        await offlineStore
            .cacheFuelingPermissionV68(p['can_fueling_create'] == true);
        await offlineStore.reconcileAbandonedSessionV68();
        await offlineStore.beginSessionMarkerV68();
        await offlineStore.recordEventV87('login', payload: {
          'mode': 'offline',
          'username': normalized,
          'role': p['role'],
        });
        if (mounted)
          setState(() {
            profile = p;
            loading = false;
            error = null;
          });
        return;
      } catch (e) {
        if (mounted)
          setState(() {
            loading = false;
            error = _friendlyError(e);
          });
        return;
      }
    }
    try {
      final loginPassword = _authPasswordForLogin(password);
      var signedIn = false;
      if (normalized.contains('@')) {
        await client.auth
            .signInWithPassword(email: normalized, password: loginPassword);
        signedIn = true;
      } else if (normalized == 'admin' || normalized == 'adminfuel') {
        for (final email in const [
          'marinhrodrigo@gmail.com',
          'adminfuel@rccombustivel.app'
        ]) {
          try {
            await client.auth
                .signInWithPassword(email: email, password: loginPassword);
            signedIn = true;
            break;
          } catch (_) {}
        }
        if (!signedIn) throw Exception('Usuário ou senha inválidos.');
      } else {
        try {
          await client.auth.signInWithPassword(
              email: '$normalized@rccombustivel.app', password: loginPassword);
          signedIn = true;
        } catch (_) {}
        if (!signedIn) {
          await client.auth.signInWithPassword(
              email: '$normalized@rcmanutencao.app', password: loginPassword);
          signedIn = true;
        }
      }
      await offlineStore.reconcileAbandonedSessionV68();
      final claim = await _claimSessionV42(explicitLogin: true);
      if (claim['ok'] != true)
        throw Exception(
            '${claim['message'] ?? 'Não foi possível registrar esta sessão.'}');
      final p = await api.profile();
      offlineStore.markOnline();
      await offlineStore.cacheProfile(p);
      await offlineStore
          .cacheFuelingPermissionV68(p['can_fueling_create'] == true);
      await offlineStore.cacheOfflineLoginV62(normalized, password, p);
      await api.referenceData();
      await offlineStore.beginSessionMarkerV68();
      await offlineStore.recordEventV87('login', payload: {
        'mode': 'online',
        'username': normalized,
        'role': p['role'],
      });
      unawaited(offlineStore.syncAuditEventsV87());
      if (mounted)
        setState(() {
          profile = p;
          loading = false;
        });
      _startSessionGuardV30();
      unawaited(offlineStore.syncPending(force: true));
    } catch (e) {
      if (_isNetworkError(e)) {
        offlineStore.markOffline();
        try {
          final p = await offlineStore.offlineLoginV62(normalized, password);
          await offlineStore
              .cacheFuelingPermissionV68(p['can_fueling_create'] == true);
          await offlineStore.reconcileAbandonedSessionV68();
          await offlineStore.beginSessionMarkerV68();
          await offlineStore.recordEventV87('login', payload: {
            'mode': 'offline_after_network_loss',
            'username': normalized,
            'role': p['role'],
          });
          if (mounted)
            setState(() {
              profile = p;
              loading = false;
              error = null;
            });
          return;
        } catch (_) {}
      }
      _sessionGuardV30?.cancel();
      await offlineStore.clearAppSessionIdV30();
      try {
        await client.auth.signOut();
      } catch (_) {}
      if (mounted)
        setState(() {
          loading = false;
          error = _friendlyError(e);
        });
    }
  }

  Future<void> _logout() async {
    final id = offlineStore.appSessionIdV30;
    final tankId = offlineStore.lastTankId;
    final occurred = DateTime.now();
    _sessionGuardV30?.cancel();
    await offlineStore.recordEventV87('logout',
        tankId: tankId, occurredAt: occurred, payload: {'explicit': true});
    if (offlineStore.backendReadyV81) {
      try {
        await offlineStore.syncAuditEventsV87();
      } catch (_) {}
    }
    if (!offlineStore.online.value) {
      await offlineStore.queueOfflineLogoutV62(
          sessionId: id, tankId: tankId, occurredAt: occurred);
      await offlineStore.clearSessionMarkerV68();
      await offlineStore.setLastTankId(null);
      await offlineStore.clearAppSessionIdV30();
      await offlineStore.markAppLoggedOutV62();
      if (mounted) setState(() => profile = null);
      return;
    }
    if (id != null && Supabase.instance.client.auth.currentUser != null) {
      try {
        await api.logoutV30(id);
      } catch (e) {
        if (_isNetworkError(e)) {
          try {
            await offlineStore.queueOfflineLogoutV62(
                sessionId: id, tankId: tankId, occurredAt: occurred);
          } catch (_) {}
        }
      }
    }
    if (mounted) setState(() => profile = null);
    await offlineStore.clearSessionMarkerV68();
    await offlineStore.clearProfile();
    await offlineStore.setLastTankId(null);
    await offlineStore.clearAppSessionIdV30();
    await offlineStore.markAppLoggedOutV62();
    await Supabase.instance.client.auth
        .signOut(scope: SignOutScope.local)
        .timeout(const Duration(seconds: 2));
  }

  @override
  Widget build(BuildContext context) {
    if (loading)
      return const Scaffold(body: Center(child: CircularProgressIndicator()));
    if (profile == null) return LoginScreen(onLogin: _login, error: error);
    final staff = profile!['is_admin'] == true ||
        profile!['is_manager'] == true ||
        profile!['is_supervisor'] == true;
    if (staff) return AdminHomeScreen(profile: profile!, onLogout: _logout);
    final role = '${profile!['role'] ?? ''}'.trim().toLowerCase();
    final operational =
        role == 'fuel_driver' || role == 'operator' || role == 'operational';
    if (operational)
      return OperationalHomeV31Screen(profile: profile!, onLogout: _logout);
    final lastTankId = offlineStore.lastTankId;
    if (lastTankId != null)
      return FieldHomeScreen(
          profile: profile!, tankId: lastTankId, onLogout: _logout);
    return UnitSelectionScreen(profile: profile!, onLogout: _logout);
  }
}

String _friendlyError(Object e) {
  var s = e.toString().replaceFirst('Exception: ', '');
  final pg =
      RegExp(r'PostgrestException\(message:\s*(.*?),\s*code:', dotAll: true)
          .firstMatch(s);
  if (pg != null) s = (pg.group(1) ?? '').trim();
  if (s.toLowerCase().contains('permission denied for function'))
    return 'Não foi possível acessar esta função com a sessão atual. Entre novamente com internet e tente de novo.';
  if (s.contains('Localização GPS obrigatória no momento do abastecimento') ||
      s.contains('Informe a localização do abastecimento'))
    return 'Informe a localização do abastecimento. Se o GPS não estiver disponível, preencha o endereço manualmente.';
  if (s.contains('Invalid login credentials') ||
      s.contains('invalid_credentials') ||
      s.contains('FunctionsHttpException(status: 401') ||
      s.contains('Unauthorized')) {
    return 'Usuário ou senha inválidos.';
  }
  if (_isNetworkError(e))
    return 'Sem conexão com a internet. Use um usuário que já tenha acessado este aparelho online para entrar offline.';
  if (s.contains('Sessão desconectada pelo administrador') ||
      s.contains('Usuário desconectado pelo administrador'))
    return 'Sua sessão foi desconectada pelo administrador.';
  if (s.contains('Selecione esta unidade antes de registrar o abastecimento'))
    return 'Selecione a unidade de abastecimento antes de continuar.';
  if (s.contains('record "old" has no field "id"'))
    return 'Falha interna no cadastro do motorista.';
  if (s.contains('password_too_short'))
    return 'A senha/PIN deve ter pelo menos 4 caracteres.';
  if (s.contains('invalid_input'))
    return 'Confira os campos obrigatórios e as unidades permitidas.';
  if (s.contains('Entrada excede a capacidade do tanque') ||
      s.contains('Valor excede volume máximo do tanque'))
    return 'Valor excede volume máximo do tanque.';
  if (s.contains('Transferência excede a capacidade do comboio'))
    return 'Valor excede volume máximo do comboio.';
  if (s.contains('managed_account_use_current_username_and_password'))
    return 'Use o usuário e a senha/PIN definidos pelo administrador.';
  if (s.contains('recovery_email_in_use'))
    return 'O e-mail de segurança já está vinculado a outra conta.';
  if (s.contains('admin_only'))
    return 'Somente o Admin pode alterar esta configuração.';
  if (s.contains('otp') || s.contains('nonce') || s.contains('reauth'))
    return 'PIN inválido ou expirado. Solicite um novo código e tente novamente.';
  return s;
}

class BrandHeader extends StatelessWidget {
  final bool compact;
  const BrandHeader({super.key, this.compact = false});

  @override
  Widget build(BuildContext context) => Column(
        children: [
          Container(
            width: compact ? 58 : 82,
            height: compact ? 58 : 82,
            decoration:
                const BoxDecoration(color: _blue, shape: BoxShape.circle),
            child: Icon(Icons.local_gas_station_rounded,
                color: Colors.white, size: compact ? 32 : 46),
          ),
          SizedBox(height: compact ? 8 : 14),
          Text('R&C Abastecimento',
              style: Theme.of(context)
                  .textTheme
                  .headlineSmall
                  ?.copyWith(fontWeight: FontWeight.w900, color: _ink)),
          const SizedBox(height: 3),
          const Text('HYDRA EQUIPAMENTOS',
              style: TextStyle(
                  fontWeight: FontWeight.w800,
                  letterSpacing: 1.2,
                  color: Color(0xFF60758D))),
          const SizedBox(height: 6),
          const OnlineBadge(),
        ],
      );
}

class OnlineBadge extends StatelessWidget {
  const OnlineBadge({super.key});
  @override
  Widget build(BuildContext context) => ValueListenableBuilder<bool>(
        valueListenable: offlineStore.online,
        builder: (_, isOnline, __) {
          final reauth = isOnline && offlineStore.onlineReauthRequiredV81;
          final color = !isOnline
              ? Colors.red
              : reauth
                  ? Colors.orange
                  : Colors.green;
          final label = !isOnline
              ? 'OFFLINE'
              : reauth
                  ? 'ONLINE • VALIDAR'
                  : 'ONLINE';
          return Container(
            padding: const EdgeInsets.symmetric(horizontal: 7, vertical: 3),
            decoration: BoxDecoration(
                color: color.shade50,
                borderRadius: BorderRadius.circular(30),
                border: Border.all(color: color.shade200)),
            child: Text(label,
                maxLines: 1,
                softWrap: false,
                style: TextStyle(
                    color: color.shade800,
                    fontWeight: FontWeight.w900,
                    fontSize: 9)),
          );
        },
      );
}

class GreetingLine extends StatelessWidget {
  final String name;
  const GreetingLine({super.key, required this.name});
  @override
  Widget build(BuildContext context) => Row(children: [
        Expanded(
            child: SizedBox(
                height: 34,
                child: FittedBox(
                  fit: BoxFit.scaleDown,
                  alignment: Alignment.centerLeft,
                  child: Text('Olá, $name',
                      maxLines: 1,
                      softWrap: false,
                      style: Theme.of(context)
                          .textTheme
                          .headlineSmall
                          ?.copyWith(fontWeight: FontWeight.w900)),
                ))),
        const SizedBox(width: 8),
        const OnlineBadge(),
      ]);
}

class LoginScreen extends StatefulWidget {
  final Future<void> Function(String, String) onLogin;
  final String? error;
  const LoginScreen({super.key, required this.onLogin, this.error});

  @override
  State<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen> {
  final user = TextEditingController();
  final pass = TextEditingController();
  bool obscure = true;
  bool busy = false;

  @override
  void dispose() {
    user.dispose();
    pass.dispose();
    super.dispose();
  }

  Future<void> submit() async {
    if (user.text.trim().isEmpty || pass.text.isEmpty) return;
    setState(() => busy = true);
    await widget.onLogin(user.text, pass.text);
    if (mounted) setState(() => busy = false);
  }

  Future<void> recoverAdmin() async {
    if (!offlineStore.online.value) {
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(
          content:
              Text('Conecte-se à internet para recuperar o acesso do Admin.')));
      return;
    }

    Future<Map<String, dynamic>> requestCode() async {
      final res = await Supabase.instance.client.functions
          .invoke('admin-recovery', body: {'action': 'request_recovery'});
      final data = _map(res.data);
      if (res.status < 200 || res.status >= 300 || data['ok'] != true) {
        throw Exception(
            '${data['error'] ?? 'Não foi possível gerar o código de recuperação.'}');
      }
      return data;
    }

    Map<String, dynamic> challenge;
    setState(() => busy = true);
    try {
      challenge = await requestCode();
    } catch (e) {
      if (mounted) {
        final msg = e.toString().replaceFirst('Exception: ', '');
        ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(content: Text('Não foi possível enviar o código: $msg')));
      }
      return;
    } finally {
      if (mounted) setState(() => busy = false);
    }

    final code = TextEditingController(),
        next = TextEditingController(),
        confirm = TextEditingController();
    bool saving = false, requesting = false, hide = true;
    int challengeId = int.tryParse('${challenge['challenge_id']}') ?? 0;
    DateTime deadline =
        DateTime.tryParse('${challenge['expires_at']}')?.toUtc() ??
            DateTime.now().toUtc().add(const Duration(minutes: 3));
    Timer? ticker;

    int remainingSeconds() {
      final n = deadline.difference(DateTime.now().toUtc()).inSeconds;
      if (n < 0) return 0;
      if (n > 180) return 180;
      return n;
    }

    String clock() {
      final total = remainingSeconds();
      final mm = (total ~/ 60).toString().padLeft(2, '0');
      final ss = (total % 60).toString().padLeft(2, '0');
      return '$mm:$ss';
    }

    try {
      await showDialog<void>(
          context: context,
          barrierDismissible: false,
          builder: (dialogContext) => StatefulBuilder(builder: (ctx, setLocal) {
                ticker ??= Timer.periodic(const Duration(seconds: 1), (_) {
                  if (!ctx.mounted) return;
                  setLocal(() {});
                  if (remainingSeconds() <= 0) {
                    ticker?.cancel();
                    ticker = null;
                  }
                });
                final expired = remainingSeconds() <= 0;
                return AlertDialog(
                  title: const Text('Recuperar acesso do Admin'),
                  content: SizedBox(
                      width: 420,
                      child: SingleChildScrollView(
                          child: Column(
                              mainAxisSize: MainAxisSize.min,
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                            const Text(
                                'Um novo código foi enviado para o e-mail de segurança. Somente o código mais recente é válido.'),
                            const SizedBox(height: 8),
                            const Text('marinhrodrigo@gmail.com',
                                style: TextStyle(fontWeight: FontWeight.w800)),
                            const SizedBox(height: 12),
                            Container(
                              width: double.infinity,
                              padding: const EdgeInsets.symmetric(
                                  horizontal: 14, vertical: 12),
                              decoration: BoxDecoration(
                                  borderRadius: BorderRadius.circular(12),
                                  color: expired
                                      ? Colors.red.withValues(alpha: .08)
                                      : _blue.withValues(alpha: .08)),
                              child: Row(children: [
                                Icon(
                                    expired
                                        ? Icons.timer_off_outlined
                                        : Icons.timer_outlined,
                                    color: expired ? Colors.red : _blue),
                                const SizedBox(width: 10),
                                Expanded(
                                    child: Text(
                                        expired
                                            ? 'Código expirado'
                                            : 'Código expira em ${clock()}',
                                        style: TextStyle(
                                            fontWeight: FontWeight.w900,
                                            color:
                                                expired ? Colors.red : _blue))),
                              ]),
                            ),
                            const SizedBox(height: 10),
                            TextButton.icon(
                              onPressed: requesting || saving
                                  ? null
                                  : () async {
                                      setLocal(() => requesting = true);
                                      try {
                                        final fresh = await requestCode();
                                        challengeId = int.tryParse(
                                                '${fresh['challenge_id']}') ??
                                            0;
                                        deadline = DateTime.tryParse(
                                                    '${fresh['expires_at']}')
                                                ?.toUtc() ??
                                            DateTime.now().toUtc().add(
                                                const Duration(minutes: 3));
                                        code.clear();
                                        ticker?.cancel();
                                        ticker = null;
                                        if (ctx.mounted) {
                                          setLocal(() => requesting = false);
                                          ScaffoldMessenger.of(context)
                                              .showSnackBar(const SnackBar(
                                                  content: Text(
                                                      'Novo código enviado. O prazo de 3 minutos foi reiniciado.')));
                                        }
                                      } catch (e) {
                                        if (ctx.mounted) {
                                          setLocal(() => requesting = false);
                                          final msg = e
                                              .toString()
                                              .replaceFirst('Exception: ', '');
                                          ScaffoldMessenger.of(context)
                                              .showSnackBar(SnackBar(
                                                  content: Text(
                                                      'Não foi possível gerar um novo código: $msg')));
                                        }
                                      }
                                    },
                              icon: requesting
                                  ? const SizedBox(
                                      width: 18,
                                      height: 18,
                                      child: CircularProgressIndicator(
                                          strokeWidth: 2))
                                  : const Icon(Icons.refresh_rounded),
                              label: Text(expired
                                  ? 'Gerar novo código'
                                  : 'Gerar outro código'),
                            ),
                            const SizedBox(height: 6),
                            TextField(
                                controller: code,
                                keyboardType: TextInputType.number,
                                inputFormatters: [
                                  FilteringTextInputFormatter.digitsOnly
                                ],
                                maxLength: 6,
                                decoration: const InputDecoration(
                                    labelText: 'Código de 6 dígitos *',
                                    prefixIcon: Icon(Icons.pin_outlined))),
                            const SizedBox(height: 8),
                            TextField(
                                controller: next,
                                obscureText: hide,
                                decoration: InputDecoration(
                                    labelText: 'Nova senha / PIN do Admin *',
                                    prefixIcon: const Icon(Icons.lock_outline),
                                    suffixIcon: IconButton(
                                        onPressed: () =>
                                            setLocal(() => hide = !hide),
                                        icon: Icon(hide
                                            ? Icons.visibility_outlined
                                            : Icons.visibility_off_outlined)))),
                            const SizedBox(height: 10),
                            TextField(
                                controller: confirm,
                                obscureText: hide,
                                decoration: const InputDecoration(
                                    labelText: 'Confirmar nova senha / PIN *',
                                    prefixIcon:
                                        Icon(Icons.lock_reset_outlined))),
                          ]))),
                  actions: [
                    TextButton(
                        onPressed: saving || requesting
                            ? null
                            : () => Navigator.pop(ctx),
                        child: const Text('Cancelar')),
                    FilledButton(
                        onPressed: saving || requesting || expired
                            ? null
                            : () async {
                                final pin = code.text.trim(),
                                    password = next.text,
                                    again = confirm.text;
                                if (pin.length != 6) {
                                  ScaffoldMessenger.of(context).showSnackBar(
                                      const SnackBar(
                                          content: Text(
                                              'Informe o código de 6 dígitos recebido por e-mail.')));
                                  return;
                                }
                                if (password.length < 4) {
                                  ScaffoldMessenger.of(context).showSnackBar(
                                      const SnackBar(
                                          content: Text(
                                              'A nova senha/PIN deve ter pelo menos 4 caracteres.')));
                                  return;
                                }
                                if (password != again) {
                                  ScaffoldMessenger.of(context).showSnackBar(
                                      const SnackBar(
                                          content: Text(
                                              'A confirmação da nova senha não confere.')));
                                  return;
                                }
                                setLocal(() => saving = true);
                                try {
                                  final res = await Supabase
                                      .instance.client.functions
                                      .invoke('admin-recovery', body: {
                                    'action': 'complete_recovery',
                                    'challenge_id': challengeId,
                                    'code': pin,
                                    'password': password
                                  });
                                  final data = _map(res.data);
                                  if (res.status < 200 ||
                                      res.status >= 300 ||
                                      data['ok'] != true)
                                    throw Exception(
                                        '${data['error'] ?? 'Não foi possível recuperar o Admin.'}');
                                  ticker?.cancel();
                                  ticker = null;
                                  if (ctx.mounted) Navigator.pop(ctx);
                                  user.text = 'admin';
                                  pass.clear();
                                  if (mounted)
                                    await showDialog<void>(
                                        context: context,
                                        builder: (okCtx) => AlertDialog(
                                                title: const Text(
                                                    'Acesso recuperado ✓'),
                                                content: const Text(
                                                    'A senha do Admin foi redefinida com sucesso. Agora entre com o usuário admin e a nova senha escolhida.'),
                                                actions: [
                                                  FilledButton(
                                                      onPressed: () =>
                                                          Navigator.pop(okCtx),
                                                      child: const Text('OK'))
                                                ]));
                                } catch (e) {
                                  final msg = e
                                      .toString()
                                      .replaceFirst('Exception: ', '');
                                  String friendly = msg;
                                  if (msg.contains('invalid_recovery_code'))
                                    friendly =
                                        'Código inválido. Confira o e-mail e tente novamente.';
                                  if (msg.contains('recovery_expired'))
                                    friendly =
                                        'Este código expirou. Toque em Gerar novo código.';
                                  if (msg.contains('recovery_locked'))
                                    friendly =
                                        'Recuperação bloqueada após várias tentativas inválidas. Gere um novo código.';
                                  if (mounted)
                                    ScaffoldMessenger.of(context).showSnackBar(
                                        SnackBar(content: Text(friendly)));
                                  if (ctx.mounted)
                                    setLocal(() => saving = false);
                                }
                              },
                        child: saving
                            ? const SizedBox(
                                width: 18,
                                height: 18,
                                child:
                                    CircularProgressIndicator(strokeWidth: 2))
                            : const Text('Redefinir senha')),
                  ],
                );
              }));
    } finally {
      ticker?.cancel();
      code.dispose();
      next.dispose();
      confirm.dispose();
    }
  }

  @override
  Widget build(BuildContext context) => Scaffold(
        body: SafeArea(
          child: Center(
            child: SingleChildScrollView(
              padding: const EdgeInsets.all(24),
              child: ConstrainedBox(
                constraints: const BoxConstraints(maxWidth: 430),
                child: Column(
                  children: [
                    const BrandHeader(),
                    const SizedBox(height: 26),
                    Card(
                      child: Padding(
                        padding: const EdgeInsets.all(20),
                        child: Column(
                          children: [
                            TextField(
                                controller: user,
                                textInputAction: TextInputAction.next,
                                decoration: const InputDecoration(
                                    labelText: 'Usuário',
                                    prefixIcon:
                                        Icon(Icons.person_outline_rounded))),
                            const SizedBox(height: 14),
                            TextField(
                              controller: pass,
                              obscureText: obscure,
                              onSubmitted: (_) => submit(),
                              decoration: InputDecoration(
                                labelText: 'Senha / PIN',
                                prefixIcon:
                                    const Icon(Icons.lock_outline_rounded),
                                suffixIcon: IconButton(
                                    onPressed: () =>
                                        setState(() => obscure = !obscure),
                                    icon: Icon(obscure
                                        ? Icons.visibility
                                        : Icons.visibility_off)),
                              ),
                            ),
                            if (widget.error != null) ...[
                              const SizedBox(height: 12),
                              Text(widget.error!,
                                  style: TextStyle(
                                      color:
                                          Theme.of(context).colorScheme.error)),
                            ],
                            const SizedBox(height: 18),
                            SizedBox(
                              width: double.infinity,
                              height: 52,
                              child: FilledButton.icon(
                                onPressed: busy ? null : submit,
                                icon: busy
                                    ? const SizedBox.square(
                                        dimension: 20,
                                        child: CircularProgressIndicator(
                                            strokeWidth: 2))
                                    : const Icon(Icons.login_rounded),
                                label: const Text('Entrar'),
                              ),
                            ),
                            const SizedBox(height: 8),
                            TextButton.icon(
                                onPressed: busy ? null : recoverAdmin,
                                icon: const Icon(
                                    Icons.admin_panel_settings_outlined),
                                label: const Text('Recuperar acesso do Admin')),
                          ],
                        ),
                      ),
                    ),
                    const SizedBox(height: 14),
                    const Text(
                        'Use o usuário e a senha cadastrados pelo administrador.',
                        textAlign: TextAlign.center,
                        style: TextStyle(
                            fontWeight: FontWeight.w700,
                            color: Color(0xFF60758D))),
                    const SizedBox(height: 10),
                    const Align(
                      alignment: Alignment.centerRight,
                      child: Text('v89',
                          style: TextStyle(
                              fontSize: 11,
                              color: Color(0xFF8A98A8),
                              fontWeight: FontWeight.w500)),
                    ),
                  ],
                ),
              ),
            ),
          ),
        ),
      );
}

class UnitSelectionScreen extends StatefulWidget {
  final Map<String, dynamic> profile;
  final Future<void> Function() onLogout;
  const UnitSelectionScreen(
      {super.key, required this.profile, required this.onLogout});

  @override
  State<UnitSelectionScreen> createState() => _UnitSelectionScreenState();
}

class _UnitSelectionScreenState extends State<UnitSelectionScreen> {
  Map<String, dynamic>? data;
  List<Map<String, dynamic>> statuses = [];
  String? error;
  Timer? timer;
  bool refreshing = false;

  @override
  void initState() {
    super.initState();
    refresh();
    timer = Timer.periodic(
        const Duration(seconds: 3), (_) => refresh(silent: true));
  }

  @override
  void dispose() {
    timer?.cancel();
    super.dispose();
  }

  Map<String, dynamic>? statusFor(int id) {
    for (final x in statuses) {
      if (_intOrNull(x['tank_id']) == id) return x;
    }
    return null;
  }

  Future<void> refresh({bool silent = false}) async {
    if (refreshing) return;
    refreshing = true;
    try {
      final d = await api.referenceData();
      List<Map<String, dynamic>> st = [];
      if (offlineStore.online.value) {
        try {
          st = await api.unitStatusV30();
        } catch (_) {}
      }
      if (mounted)
        setState(() {
          data = d;
          statuses = st;
          error = null;
        });
    } catch (e) {
      if (mounted && !silent) setState(() => error = _friendlyError(e));
    } finally {
      refreshing = false;
    }
  }

  @override
  Widget build(BuildContext context) {
    final tanks = _sortedFuelUnits(data?['tanks']);
    return Scaffold(
      appBar: AppBar(
        actions: [
          IconButton(
              onPressed: () async {
                await _logoutToLogin(context, widget.onLogout);
              },
              tooltip: 'Sair',
              icon: const Icon(Icons.logout_rounded))
        ],
      ),
      body: data == null
          ? Center(
              child: error == null
                  ? const CircularProgressIndicator()
                  : Text(error!))
          : RefreshIndicator(
              onRefresh: refresh,
              child: ListView(
                padding: const EdgeInsets.all(22),
                children: [
                  const BrandHeader(compact: true),
                  const SizedBox(height: 24),
                  SizedBox(
                      height: 34,
                      child: FittedBox(
                          fit: BoxFit.scaleDown,
                          alignment: Alignment.centerLeft,
                          child: Text('Olá, ${widget.profile['display_name']}',
                              maxLines: 1,
                              softWrap: false,
                              style: Theme.of(context)
                                  .textTheme
                                  .headlineSmall
                                  ?.copyWith(fontWeight: FontWeight.w900)))),
                  const SizedBox(height: 6),
                  const Text(
                      'Unidades em uso ficam bloqueadas imediatamente e só voltam a ficar disponíveis após liberação ou troca.'),
                  const SizedBox(height: 18),
                  ...tanks.map((tank) {
                    final authorized = tank['authorized'] != false;
                    final tankId = _intOrNull(tank['id']);
                    final st = tankId == null ? null : statusFor(tankId);
                    final mine = st?['is_mine'] == true;
                    final inUse = st?['in_use'] == true;
                    final blocked = inUse && !mine;
                    final owner = '${st?['user_name'] ?? ''}'.trim();
                    final typeLabel = tank['tank_type'] == 'stationary'
                        ? 'Tanque estacionário'
                        : tank['tank_type'] == 'truck'
                            ? 'Caminhão-tanque'
                            : 'Comboio';
                    final subtitle = blocked
                        ? '$typeLabel • Em uso por ${owner.isEmpty ? 'outro usuário' : owner}'
                        : '$typeLabel • Saldo disponível: ${_fmtLiters(tank['current_balance_liters'])}${authorized ? '' : '\nSomente visualização'}';
                    return Card(
                      child: ListTile(
                        contentPadding: const EdgeInsets.all(14),
                        leading: Icon(
                            tank['tank_type'] == 'stationary'
                                ? Icons.oil_barrel_outlined
                                : tank['tank_type'] == 'truck'
                                    ? Icons.local_shipping_rounded
                                    : Icons.local_shipping_outlined,
                            color: blocked ? Colors.black38 : _blue),
                        title: Text('${tank['code']} • ${tank['name']}',
                            style:
                                const TextStyle(fontWeight: FontWeight.w900)),
                        subtitle: Text(subtitle),
                        isThreeLine: !authorized,
                        trailing: mine
                            ? const Icon(Icons.check_circle_rounded,
                                color: Colors.green)
                            : blocked
                                ? const Icon(Icons.lock_outline_rounded)
                                : Icon(authorized
                                    ? Icons.chevron_right_rounded
                                    : Icons.visibility_outlined),
                        onTap: blocked
                            ? () => ScaffoldMessenger.of(context).showSnackBar(
                                SnackBar(
                                    content: Text(
                                        'Esta unidade já está sendo usada por ${owner.isEmpty ? 'outro usuário' : owner}.')))
                            : authorized
                                ? () async {
                                    if (tankId == null) {
                                      ScaffoldMessenger.of(context)
                                          .showSnackBar(const SnackBar(
                                              content:
                                                  Text('Unidade inválida.')));
                                      return;
                                    }
                                    if (!offlineStore.online.value) {
                                      await offlineStore.setLastTankId(tankId);
                                      if (context.mounted)
                                        ScaffoldMessenger.of(context)
                                            .showSnackBar(const SnackBar(
                                                content: Text(
                                                    'Unidade selecionada offline. A validação será feita quando a internet voltar.')));
                                    } else {
                                      try {
                                        final claim =
                                            await api.claimUnitV31(tankId);
                                        if (claim['ok'] != true) {
                                          if (context.mounted)
                                            ScaffoldMessenger.of(context)
                                                .showSnackBar(SnackBar(
                                                    content: Text(
                                                        '${claim['message'] ?? 'Esta unidade já está em uso.'}')));
                                          await refresh(silent: true);
                                          return;
                                        }
                                      } catch (e) {
                                        if (context.mounted)
                                          ScaffoldMessenger.of(context)
                                              .showSnackBar(SnackBar(
                                                  content:
                                                      Text(_friendlyError(e))));
                                        return;
                                      }
                                    }
                                    await offlineStore.setLastTankId(tankId);
                                    if (!context.mounted) return;
                                    Navigator.pushReplacement(
                                        context,
                                        MaterialPageRoute(
                                            builder: (_) => FieldHomeScreen(
                                                profile: widget.profile,
                                                tankId: tankId,
                                                onLogout: widget.onLogout)));
                                  }
                                : () => ScaffoldMessenger.of(context)
                                    .showSnackBar(const SnackBar(
                                        content: Text(
                                            'Esta unidade não foi liberada para operação deste usuário.'))),
                      ),
                    );
                  }),
                  if (tanks.isEmpty)
                    const Padding(
                        padding: EdgeInsets.all(24),
                        child: Text('Nenhuma unidade cadastrada no sistema.',
                            textAlign: TextAlign.center)),
                ],
              ),
            ),
    );
  }
}

class FieldHomeScreen extends StatefulWidget {
  final Map<String, dynamic> profile;
  final int tankId;
  final Future<void> Function() onLogout;
  const FieldHomeScreen(
      {super.key,
      required this.profile,
      required this.tankId,
      required this.onLogout});

  @override
  State<FieldHomeScreen> createState() => _FieldHomeScreenState();
}

class _FieldHomeScreenState extends State<FieldHomeScreen> {
  Map<String, dynamic>? ref;
  Timer? timer;
  bool refreshing = false;

  @override
  void initState() {
    super.initState();
    refresh();
    timer = Timer.periodic(
        const Duration(seconds: 8), (_) => refresh(silent: true));
  }

  @override
  void dispose() {
    timer?.cancel();
    super.dispose();
  }

  Future<void> refresh({bool silent = false}) async {
    if (refreshing) return;
    refreshing = true;
    try {
      final d = await api.referenceData();
      if (mounted) setState(() => ref = d);
    } catch (_) {
    } finally {
      refreshing = false;
    }
  }

  Map<String, dynamic>? get tank {
    for (final t in _rows(ref?['tanks'])) {
      if (_intOrNull(t['id']) == widget.tankId) return t;
    }
    return null;
  }

  Future<void> open(Widget page) async {
    timer?.cancel();
    try {
      await Navigator.push(context, MaterialPageRoute(builder: (_) => page));
    } finally {
      if (mounted) {
        await refresh();
        timer?.cancel();
        timer = Timer.periodic(
            const Duration(seconds: 8), (_) => refresh(silent: true));
      }
    }
  }

  Future<void> openStationaryDestination(
      Map<String, dynamic> sourceTank) async {
    final choice = await showModalBottomSheet<String>(
      context: context,
      builder: (ctx) => SafeArea(
        child: Wrap(children: [
          const Padding(
            padding: EdgeInsets.fromLTRB(18, 16, 18, 8),
            child: Text('Selecione o destino',
                style: TextStyle(fontWeight: FontWeight.w900, fontSize: 18)),
          ),
          ListTile(
            leading: const Icon(Icons.local_shipping_outlined),
            title: const Text('Comboio'),
            subtitle: const Text(
                'Transferir estoque do tanque estacionário para um comboio'),
            onTap: () => Navigator.pop(ctx, 'comboio'),
          ),
          ListTile(
            leading: const Icon(Icons.precision_manufacturing_outlined),
            title: const Text('Ativo próprio ou terceiro'),
            subtitle: const Text(
                'Abastecer equipamento, caminhão ou veículo alugado'),
            onTap: () => Navigator.pop(ctx, 'fueling'),
          ),
        ]),
      ),
    );
    if (!mounted || choice == null) return;
    if (choice == 'comboio') {
      await open(
          TransferOnlineScreen(sourceTank: sourceTank, referenceData: ref!));
    } else {
      await open(
          FuelingOnlineScreen(sourceTank: sourceTank, referenceData: ref!));
    }
  }

  @override
  Widget build(BuildContext context) {
    final t = tank;
    final tankType = '${t?['tank_type'] ?? ''}';
    final stationary = tankType == 'stationary',
        truck = tankType == 'truck',
        comboio = tankType == 'comboio';
    return Scaffold(
      appBar: AppBar(
        title: const Text('R&C Abastecimento',
            style: TextStyle(fontWeight: FontWeight.w900)),
        actions: [
          PopupMenuButton<String>(
            onSelected: (v) async {
              if (v == 'unit') {
                timer?.cancel();
                if (!context.mounted) return;
                Navigator.pushReplacement(
                    context,
                    MaterialPageRoute(
                        builder: (_) => UnitSelectionScreen(
                            profile: widget.profile,
                            onLogout: widget.onLogout)));
              }
              if (v == 'logout') {
                await _logoutToLogin(context, widget.onLogout);
              }
            },
            itemBuilder: (_) => const [
              PopupMenuItem(value: 'unit', child: Text('Trocar unidade')),
              PopupMenuItem(value: 'logout', child: Text('Sair'))
            ],
          ),
        ],
      ),
      body: ref == null || t == null
          ? const Center(child: CircularProgressIndicator())
          : RefreshIndicator(
              onRefresh: refresh,
              child: ListView(
                padding: const EdgeInsets.all(20),
                children: [
                  GreetingLine(name: '${widget.profile['display_name']}'),
                  const SizedBox(height: 4),
                  Text('${t['code']} • ${t['name']}'),
                  const SizedBox(height: 14),
                  BalanceCard(tank: t),
                  const SizedBox(height: 12),
                  const Card(
                      child: ListTile(
                          leading: Icon(Icons.location_on_outlined,
                              color: Colors.orange),
                          title: Text('Localização deve estar ativada',
                              style: TextStyle(fontWeight: FontWeight.w900)),
                          subtitle: Text(
                              'O ponto exato do abastecimento será capturado automaticamente ao concluir.'))),
                  const SizedBox(height: 12),
                  if (truck) ...[
                    HomeActionCard(
                        icon: Icons.receipt_long_rounded,
                        title: 'Entrada da refinaria / NF',
                        subtitle:
                            'Registrar a carga e criar o lote da Nota Fiscal',
                        onTap: () => open(RefineryLoadV23Screen(truck: t))),
                    const SizedBox(height: 12),
                    HomeActionCard(
                        icon: Icons.oil_barrel_outlined,
                        title: 'Descarregar no T.E.',
                        subtitle: 'Caminhão-tanque → Tanque estacionário',
                        onTap: () =>
                            open(RefineryToTeV23Screen(truck: t, ref: ref!))),
                    const SizedBox(height: 12),
                    HomeActionCard(
                        icon: Icons.swap_horiz_rounded,
                        title: 'Transferir',
                        subtitle: 'Caminhão-tanque → Comboio',
                        onTap: () => open(TransferV23Screen(
                            source: t, ref: ref!, profile: widget.profile))),
                    const SizedBox(height: 12),
                    HomeActionCard(
                        icon: Icons.local_gas_station_rounded,
                        title: 'Novo abastecimento',
                        subtitle:
                            'Usar o caminhão-tanque para abastecer diretamente ativos e equipamentos',
                        onTap: () => open(FuelingV23Screen(
                            source: t, ref: ref!, profile: widget.profile))),
                  ] else if (comboio) ...[
                    HomeActionCard(
                        icon: Icons.local_gas_station_rounded,
                        title: 'Novo abastecimento',
                        subtitle: 'Ativo próprio ou equipamento de terceiros',
                        onTap: () => open(FuelingV23Screen(
                            source: t, ref: ref!, profile: widget.profile))),
                    const SizedBox(height: 12),
                    HomeActionCard(
                        icon: Icons.swap_horiz_rounded,
                        title: 'Transferir',
                        subtitle: 'Comboio → Comboio',
                        onTap: () => open(TransferV23Screen(
                            source: t, ref: ref!, profile: widget.profile))),
                  ] else if (stationary) ...[
                    HomeActionCard(
                        icon: Icons.local_gas_station_rounded,
                        title: 'Novo abastecimento',
                        subtitle:
                            'T.E. → Ativo próprio ou equipamento de terceiros',
                        onTap: () => open(FuelingV23Screen(
                            source: t, ref: ref!, profile: widget.profile))),
                  ],
                  const SizedBox(height: 12),
                  HomeActionCard(
                      icon: Icons.calendar_month_outlined,
                      title: 'Registro diário de estoque',
                      subtitle:
                          'Saldo anterior, entradas, abastecimentos e saldo final do dia',
                      onTap: () => open(DailyStockReportScreen(tank: t))),
                  const SizedBox(height: 12),
                  HomeActionCard(
                      icon: Icons.receipt_long_rounded,
                      title: 'Meus registros',
                      subtitle: 'Movimentações registradas por este usuário',
                      onTap: () => open(const MyOnlineMovementsScreen())),
                ],
              ),
            ),
    );
  }
}

class BalanceCard extends StatelessWidget {
  final Map<String, dynamic> tank;
  const BalanceCard({super.key, required this.tank});

  @override
  Widget build(BuildContext context) {
    final balance = _num(tank['current_balance_liters']);
    final capacity = _num(tank['capacity_liters']);
    final ratio =
        capacity <= 0 ? 0.0 : (balance / capacity).clamp(0.0, 1.0).toDouble();
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child:
            Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
          Row(children: [
            const Icon(Icons.local_gas_station_rounded, color: _blue),
            const SizedBox(width: 10),
            Expanded(
                child: Text('Combustível disponível • ${tank['code']}',
                    style: const TextStyle(
                        fontWeight: FontWeight.w900, fontSize: 16))),
            Text(_fmtLiters(balance),
                style:
                    const TextStyle(fontWeight: FontWeight.w900, fontSize: 18)),
          ]),
          const SizedBox(height: 8),
          Text('Capacidade: ${_fmtLiters(capacity)}'),
          const SizedBox(height: 8),
          LinearProgressIndicator(
              value: ratio,
              minHeight: 8,
              borderRadius: BorderRadius.circular(10)),
          const SizedBox(height: 6),
          ValueListenableBuilder<bool>(
            valueListenable: offlineStore.online,
            builder: (_, isOnline, __) => ValueListenableBuilder<int>(
              valueListenable: offlineStore.pendingCount,
              builder: (_, pending, __) => ValueListenableBuilder<bool>(
                valueListenable: offlineStore.syncing,
                builder: (_, isSyncing, __) => Column(
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: [
                    Text(
                      isOnline
                          ? (pending > 0
                              ? 'Online • $pending lançamento(s) aguardando sincronização.'
                              : 'Atualização automática online a cada poucos segundos.')
                          : (pending > 0
                              ? 'Offline • $pending lançamento(s) salvo(s) no aparelho.'
                              : 'Offline • os próximos lançamentos serão salvos no aparelho.'),
                      style:
                          const TextStyle(fontSize: 12, color: Colors.black54),
                    ),
                    if (pending > 0) ...[
                      const SizedBox(height: 8),
                      OutlinedButton.icon(
                        onPressed: !isOnline || isSyncing
                            ? null
                            : () => _syncPendingWithFeedbackV74(context),
                        icon: Icon(isSyncing
                            ? Icons.sync_rounded
                            : Icons.cloud_upload_outlined),
                        label: Text(isSyncing
                            ? 'Sincronizando...'
                            : isOnline
                                ? 'Sincronizar pendentes'
                                : 'Sem internet para sincronizar'),
                      ),
                    ],
                  ],
                ),
              ),
            ),
          ),
        ]),
      ),
    );
  }
}

class DailyStockReportScreen extends StatefulWidget {
  final Map<String, dynamic> tank;
  const DailyStockReportScreen({super.key, required this.tank});
  @override
  State<DailyStockReportScreen> createState() => _DailyStockReportScreenState();
}

class _DailyStockReportScreenState extends State<DailyStockReportScreen> {
  DateTime date = DateTime.now();
  Map<String, dynamic>? data;
  bool busy = false;

  @override
  void initState() {
    super.initState();
    load();
  }

  Future<void> load() async {
    final id = _intOrNull(widget.tank['id']);
    if (id == null) return;
    setState(() => busy = true);
    try {
      final value = await api.dailyStockReport(tankId: id, date: date);
      if (mounted) setState(() => data = value);
    } catch (e) {
      if (mounted)
        ScaffoldMessenger.of(context)
            .showSnackBar(SnackBar(content: Text(_friendlyError(e))));
    } finally {
      if (mounted) setState(() => busy = false);
    }
  }

  Future<void> chooseDate() async {
    final d = await showDatePicker(
        context: context,
        initialDate: date,
        firstDate: DateTime(2024),
        lastDate: DateTime.now());
    if (d == null) return;
    setState(() => date = d);
    await load();
  }

  String dayLabel() =>
      '${date.day.toString().padLeft(2, '0')}/${date.month.toString().padLeft(2, '0')}/${date.year}';

  @override
  Widget build(BuildContext context) {
    final d = data;
    final movements = _rows(d?['movements']);
    final transferred = _num(d?['transferred_out_liters']);
    return Scaffold(
      appBar: AppBar(title: Text('Registro diário • ${widget.tank['code']}')),
      body: RefreshIndicator(
        onRefresh: load,
        child: ListView(
          padding: const EdgeInsets.fromLTRB(16, 16, 16, 150),
          children: [
            OutlinedButton.icon(
                onPressed: busy ? null : chooseDate,
                icon: const Icon(Icons.calendar_today_outlined),
                label: Text(dayLabel())),
            const SizedBox(height: 12),
            if (busy && d == null)
              const Center(
                  child: Padding(
                      padding: EdgeInsets.all(30),
                      child: CircularProgressIndicator())),
            if (d != null) ...[
              Card(
                  child: Padding(
                padding: const EdgeInsets.all(16),
                child: Column(
                    crossAxisAlignment: CrossAxisAlignment.stretch,
                    children: [
                      Text('${d['code']} • ${d['name']}',
                          style: const TextStyle(
                              fontWeight: FontWeight.w900, fontSize: 18)),
                      const SizedBox(height: 14),
                      _DailyValue(
                          label: 'Saldo anterior',
                          value: _fmtLiters(d['opening_balance'])),
                      _DailyValue(
                          label: '+ Entradas no dia',
                          value: _fmtLiters(d['received_liters'])),
                      const Divider(height: 20),
                      _DailyValue(
                          label: 'Saldo disponível',
                          value: _fmtLiters(d['available_liters']),
                          strong: true),
                      const SizedBox(height: 8),
                      _DailyValue(
                          label: 'Total abastecido',
                          value: _fmtLiters(d['fueled_liters'])),
                      if (transferred > 0)
                        _DailyValue(
                            label: 'Transferido para comboios',
                            value: _fmtLiters(transferred)),
                      const Divider(height: 20),
                      _DailyValue(
                          label: 'Saldo final',
                          value: _fmtLiters(d['closing_balance']),
                          strong: true),
                      const SizedBox(height: 8),
                      const Text(
                          'O saldo final deste dia é usado como saldo anterior do dia seguinte.',
                          style:
                              TextStyle(color: Colors.black54, fontSize: 12)),
                    ]),
              )),
              const SizedBox(height: 16),
              Text('Movimentações do dia',
                  style: Theme.of(context)
                      .textTheme
                      .titleMedium
                      ?.copyWith(fontWeight: FontWeight.w900)),
              const SizedBox(height: 8),
              if (movements.isEmpty)
                const Card(
                    child: Padding(
                        padding: EdgeInsets.all(18),
                        child: Text('Nenhuma movimentação nesta data.',
                            textAlign: TextAlign.center)))
              else
                ...movements.map((m) {
                  final type = _movementLabelForItem(m);
                  final asset = m['asset_number'] ??
                      m['third_party_plate'] ??
                      m['destination_tank'] ??
                      m['source_tank'] ??
                      '';
                  final entry = m['direction'] == 'entry';
                  return Card(
                      child: ListTile(
                    leading: Icon(
                        entry
                            ? Icons.add_circle_outline
                            : Icons.remove_circle_outline,
                        color: _blue),
                    title: Text('$type${_hasValue(asset) ? ' • $asset' : ''}',
                        style: const TextStyle(fontWeight: FontWeight.w800)),
                    subtitle: Text(
                        '${_fmtDate(m['created_at'])}\n${entry ? 'Entrada' : 'Saída'} • ${_fmtLiters(m['liters'])}'),
                    isThreeLine: false,
                  ));
                }),
            ],
          ],
        ),
      ),
    );
  }
}

class _DailyValue extends StatelessWidget {
  final String label;
  final String value;
  final bool strong;
  const _DailyValue(
      {required this.label, required this.value, this.strong = false});
  @override
  Widget build(BuildContext context) => Padding(
        padding: const EdgeInsets.symmetric(vertical: 5),
        child: Row(children: [
          Expanded(
              child: Text(label,
                  style: TextStyle(
                      fontWeight: strong ? FontWeight.w900 : FontWeight.w700))),
          Text(value,
              style: TextStyle(
                  fontWeight: strong ? FontWeight.w900 : FontWeight.w600,
                  fontSize: strong ? 17 : 15)),
        ]),
      );
}

class HomeActionCard extends StatelessWidget {
  final IconData icon;
  final String title;
  final String subtitle;
  final VoidCallback onTap;
  const HomeActionCard(
      {super.key,
      required this.icon,
      required this.title,
      required this.subtitle,
      required this.onTap});

  @override
  Widget build(BuildContext context) => Card(
        child: ListTile(
          contentPadding: const EdgeInsets.all(16),
          leading: Icon(icon, color: _blue, size: 34),
          title:
              Text(title, style: const TextStyle(fontWeight: FontWeight.w900)),
          trailing: const Icon(Icons.chevron_right_rounded),
          onTap: onTap,
        ),
      );
}

class RefineryLoadV23Screen extends StatefulWidget {
  final Map<String, dynamic> truck;
  const RefineryLoadV23Screen({super.key, required this.truck});
  @override
  State<RefineryLoadV23Screen> createState() => _RefineryLoadV23ScreenState();
}

class _RefineryLoadV23ScreenState extends State<RefineryLoadV23Screen> {
  final nf = TextEditingController(),
      liters = TextEditingController(),
      cost = TextEditingController(),
      batch = TextEditingController(),
      notes = TextEditingController();
  String fuel = 'Diesel';
  XFile? truckPlatePhoto, invoicePhoto;
  List<Map<String, dynamic>> suppliers = [];
  Map<String, dynamic> buyerCompany = {};
  int? supplierId;
  bool busy = false, loadingRefs = true;
  String step = 'Salvar recebimento';

  @override
  void initState() {
    super.initState();
    loadRefs();
  }

  Future<void> loadRefs() async {
    try {
      final r = await Future.wait<dynamic>(
          [api.companiesByRole('fuel_supplier'), api.reportCompany()]);
      if (mounted)
        setState(() {
          suppliers = List<Map<String, dynamic>>.from(
              r[0] as List<Map<String, dynamic>>);
          buyerCompany = _map(r[1]);
          supplierId =
              suppliers.length == 1 ? _intOrNull(suppliers.first['id']) : null;
          loadingRefs = false;
        });
    } catch (e) {
      if (mounted) {
        setState(() => loadingRefs = false);
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(
            content: Text('Erro ao carregar empresas: ${_friendlyError(e)}')));
      }
    }
  }

  String supplierName() {
    for (final x in suppliers) {
      if (_intOrNull(x['id']) == supplierId) return '${x['name']}';
    }
    return '';
  }

  Future<XFile?> camera() => ImagePicker()
      .pickImage(source: ImageSource.camera, imageQuality: 78, maxWidth: 1800);
  void message(String value) => ScaffoldMessenger.of(context)
      .showSnackBar(SnackBar(content: Text(value)));

  Future<void> submit() async {
    if (busy) return;
    final volume = double.tryParse(liters.text.trim().replaceAll(',', '.'));
    final unitCost = double.tryParse(cost.text.trim().replaceAll(',', '.'));
    final supplier = supplierName();
    if (nf.text.trim().isEmpty) {
      message('Preenchimento obrigatório: Número da Nota Fiscal');
      return;
    }
    if (supplierId == null || supplier.isEmpty) {
      message('Preenchimento obrigatório: Fornecedor do combustível');
      return;
    }
    if (volume == null || volume <= 0) {
      message('Preenchimento obrigatório: Volume recebido');
      return;
    }
    if (unitCost == null || unitCost < 0) {
      message('Preenchimento obrigatório: Preço de compra por litro');
      return;
    }
    if (truckPlatePhoto == null) {
      message('Foto da placa do caminhão-tanque obrigatória');
      return;
    }
    if (invoicePhoto == null) {
      message('Foto legível da Nota Fiscal obrigatória');
      return;
    }
    final ok = await showDialog<bool>(
        context: context,
        builder: (ctx) => AlertDialog(
              title: const Text('Confirmar recebimento de combustível?'),
              content: Column(
                  mainAxisSize: MainAxisSize.min,
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                        'Empresa compradora: ${buyerCompany['company_name'] ?? '-'}',
                        style: const TextStyle(fontWeight: FontWeight.w700)),
                    Text('Fornecedor do combustível: $supplier'),
                    const SizedBox(height: 8),
                    Text(
                        'Caminhão-tanque: ${widget.truck['code']} • ${widget.truck['name']}'),
                    Text('Nota Fiscal: ${nf.text.trim()}'),
                    Text('Combustível: $fuel'),
                    Text('Volume recebido: ${_fmtLiters(volume)}'),
                    Text('Preço de compra/L: ${_fmtMoney(unitCost)}'),
                    const SizedBox(height: 8),
                    const Text(
                        'A data e a hora da chegada serão registradas automaticamente pelo app.'),
                  ]),
              actions: [
                TextButton(
                    onPressed: () => Navigator.pop(ctx, false),
                    child: const Text('Cancelar')),
                FilledButton(
                    onPressed: () => Navigator.pop(ctx, true),
                    child: const Text('Confirmar recebimento'))
              ],
            ));
    if (ok != true || !mounted) return;
    setState(() {
      busy = true;
      step = 'Enviando fotos obrigatórias...';
    });
    try {
      Future<String> up(XFile f, String kind) async =>
          api.uploadBytes(await f.readAsBytes(), kind,
              mime: f.mimeType ?? 'image/jpeg');
      final photos = await Future.wait<String>([
        up(truckPlatePhoto!, 'placa_caminhao_tanque'),
        up(invoicePhoto!, 'nota_fiscal_legivel')
      ]);
      if (!mounted) return;
      setState(() => step = 'Registrando NF e lote...');
      final r = await api.refineryLoadV22(
          truckTankId: _intOrNull(widget.truck['id'])!,
          liters: volume,
          supplier: supplier,
          invoice: nf.text.trim(),
          unitCost: unitCost,
          fuelType: fuel,
          truckPlatePhoto: photos[0],
          invoicePhoto: photos[1],
          batch: batch.text.trim(),
          notes: notes.text.trim());
      if (!mounted) return;
      message(
          'NF ${r['invoice_number']} registrada com sucesso ✓ • ${_fmtLiters(r['liters'])}');
      Navigator.pop(context, true);
    } catch (e) {
      if (mounted)
        message('Erro ao registrar recebimento: ${_friendlyError(e)}');
    } finally {
      if (mounted)
        setState(() {
          busy = false;
          step = 'Salvar recebimento';
        });
    }
  }

  @override
  void dispose() {
    for (final c in [nf, liters, cost, batch, notes]) {
      c.dispose();
    }
    super.dispose();
  }

  @override
  Widget build(BuildContext c) => Scaffold(
        appBar: AppBar(title: const Text('Recebimento de combustível / NF')),
        body: loadingRefs
            ? const Center(child: CircularProgressIndicator())
            : ListView(padding: const EdgeInsets.all(18), children: [
                Card(
                    child: ListTile(
                        leading:
                            const Icon(Icons.business_rounded, color: _blue),
                        title: const Text('Empresa compradora'),
                        subtitle: Text(
                            '${buyerCompany['company_name'] ?? '-'}\nSua empresa operadora recebe o combustível e o incorpora ao estoque.'))),
                const SizedBox(height: 8),
                Text('${widget.truck['code']} • ${widget.truck['name']}',
                    style: Theme.of(c)
                        .textTheme
                        .titleLarge
                        ?.copyWith(fontWeight: FontWeight.w900)),
                const SizedBox(height: 5),
                const Text(
                    'Toda chegada entra primeiro pela Nota Fiscal. O fornecedor é selecionado do cadastro “Empresas” e deve estar marcado como “Fornecedor de combustível”.'),
                const SizedBox(height: 14),
                DropdownButtonFormField<int>(
                    initialValue: supplierId,
                    isExpanded: true,
                    decoration: const InputDecoration(
                        labelText: 'Fornecedor do combustível *'),
                    items: suppliers
                        .map((x) => DropdownMenuItem(
                            value: _intOrNull(x['id']),
                            child: Text('${x['name']}')))
                        .toList(),
                    onChanged:
                        busy ? null : (v) => setState(() => supplierId = v)),
                if (suppliers.isEmpty)
                  const Padding(
                      padding: EdgeInsets.only(top: 8),
                      child: Card(
                          child: ListTile(
                              leading: Icon(Icons.warning_amber_rounded,
                                  color: Colors.orange),
                              title: Text('Nenhum fornecedor cadastrado'),
                              subtitle: Text(
                                  'O Admin deve abrir Cadastros > Empresas e marcar uma empresa como “Fornecedor de combustível”.')))),
                const SizedBox(height: 8),
                TextField(
                    controller: nf,
                    enabled: !busy,
                    decoration: const InputDecoration(
                        labelText: 'Número da Nota Fiscal *')),
                const SizedBox(height: 8),
                TextField(
                    controller: batch,
                    enabled: !busy,
                    decoration:
                        const InputDecoration(labelText: 'Lote / remessa')),
                const SizedBox(height: 8),
                DropdownButtonFormField<String>(
                    initialValue: fuel,
                    decoration:
                        const InputDecoration(labelText: 'Combustível *'),
                    items: _fuelTypes
                        .map((x) => DropdownMenuItem(value: x, child: Text(x)))
                        .toList(),
                    onChanged: busy
                        ? null
                        : (v) => setState(() => fuel = v ?? 'Diesel')),
                const SizedBox(height: 8),
                TextField(
                    controller: liters,
                    enabled: !busy,
                    keyboardType:
                        const TextInputType.numberWithOptions(decimal: true),
                    decoration: const InputDecoration(
                        labelText: 'Volume recebido (L) *')),
                const SizedBox(height: 8),
                TextField(
                    controller: cost,
                    enabled: !busy,
                    keyboardType:
                        const TextInputType.numberWithOptions(decimal: true),
                    decoration: const InputDecoration(
                        labelText: 'Preço de compra/L *')),
                const SizedBox(height: 8),
                TextField(
                    controller: notes,
                    enabled: !busy,
                    maxLines: 3,
                    decoration:
                        const InputDecoration(labelText: 'Observações')),
                const SizedBox(height: 12),
                OutlinedButton.icon(
                    onPressed: busy
                        ? null
                        : () async {
                            final x = await camera();
                            if (x != null) setState(() => truckPlatePhoto = x);
                          },
                    icon: const Icon(Icons.local_shipping_outlined),
                    label: Text(truckPlatePhoto == null
                        ? 'Foto da placa do caminhão-tanque *'
                        : 'Foto da placa do caminhão-tanque ✓')),
                const SizedBox(height: 6),
                OutlinedButton.icon(
                    onPressed: busy
                        ? null
                        : () async {
                            final x = await camera();
                            if (x != null) setState(() => invoicePhoto = x);
                          },
                    icon: const Icon(Icons.receipt_long_outlined),
                    label: Text(invoicePhoto == null
                        ? 'Foto legível da Nota Fiscal *'
                        : 'Foto legível da Nota Fiscal ✓')),
                const SizedBox(height: 8),
                const Card(
                    child: ListTile(
                        leading: Icon(Icons.schedule_rounded, color: _blue),
                        title: Text('Data e hora da chegada'),
                        subtitle: Text(
                            'Registradas automaticamente no momento em que a carga é confirmada.'))),
                const SizedBox(height: 14),
                FilledButton.icon(
                    onPressed: busy || suppliers.isEmpty ? null : submit,
                    icon: busy
                        ? const SizedBox(
                            width: 18,
                            height: 18,
                            child: CircularProgressIndicator(strokeWidth: 2))
                        : const Icon(Icons.check_rounded),
                    label: Text(busy ? step : 'Salvar recebimento')),
              ]),
      );
}

class RefineryToTeV23Screen extends StatefulWidget {
  final Map<String, dynamic> truck, ref;
  const RefineryToTeV23Screen(
      {super.key, required this.truck, required this.ref});
  @override
  State<RefineryToTeV23Screen> createState() => _RefineryToTeV23ScreenState();
}

class _RefineryToTeV23ScreenState extends State<RefineryToTeV23Screen> {
  int? te, lot;
  final liters = TextEditingController();
  bool busy = false;
  @override
  void dispose() {
    liters.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext c) {
    final tes = _rows(widget.ref['tanks'])
            .where((x) => x['tank_type'] == 'stationary')
            .toList(),
        lots = _rows(widget.ref['open_lots']);
    Map<String, dynamic>? target() {
      for (final x in tes) {
        if (_intOrNull(x['id']) == te) return x;
      }
      return null;
    }

    Future<void> submit() async {
      final v = double.tryParse(liters.text.trim().replaceAll(',', '.'));
      if (te == null) {
        ScaffoldMessenger.of(c).showSnackBar(const SnackBar(
            content: Text('Preenchimento obrigatório: T.E. recebedor')));
        return;
      }
      if (v == null || v <= 0) {
        ScaffoldMessenger.of(c).showSnackBar(const SnackBar(
            content:
                Text('Preenchimento obrigatório: Volume da transferência')));
        return;
      }
      final t = target();
      final ok = await showDialog<bool>(
          context: c,
          builder: (ctx) => AlertDialog(
                  title: const Text('Confirmar transferência?'),
                  content: Column(
                      mainAxisSize: MainAxisSize.min,
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                            'Origem: ${widget.truck['code']} • ${widget.truck['name']}'),
                        Text('Destino: ${t?['code']} • ${t?['name']}'),
                        Text('Volume: ${_fmtLiters(v)}'),
                        const SizedBox(height: 8),
                        const Text(
                            'Tipo de movimento: Transferência interna — sem venda')
                      ]),
                  actions: [
                    TextButton(
                        onPressed: () => Navigator.pop(ctx, false),
                        child: const Text('Cancelar')),
                    FilledButton(
                        onPressed: () => Navigator.pop(ctx, true),
                        child: const Text('Confirmar transferência'))
                  ]));
      if (ok != true || !mounted) return;
      setState(() => busy = true);
      try {
        await api.refineryToTeV22(
            truckTankId: _intOrNull(widget.truck['id'])!,
            teTankId: te!,
            lotId: lot,
            liters: v);
        if (mounted) {
          ScaffoldMessenger.of(c).showSnackBar(const SnackBar(
              content: Text('Transferência registrada com sucesso ✓')));
          Navigator.pop(c, true);
        }
      } catch (e) {
        if (mounted)
          ScaffoldMessenger.of(c).showSnackBar(SnackBar(
              content: Text(
                  'Erro ao registrar transferência: ${_friendlyError(e)}')));
      } finally {
        if (mounted) setState(() => busy = false);
      }
    }

    return Scaffold(
        appBar: AppBar(title: const Text('Caminhão-tanque → T.E.')),
        body: ListView(padding: const EdgeInsets.all(18), children: [
          const Card(
              child: ListTile(
                  leading: Icon(Icons.swap_horiz_rounded, color: _blue),
                  title: Text('Transferência interna — sem venda'),
                  subtitle: Text(
                      'O combustível muda de local, mas continua vinculado à mesma NF/lote.'))),
          DropdownButtonFormField<int>(
              initialValue: te,
              decoration: const InputDecoration(labelText: 'T.E. recebedor *'),
              items: tes
                  .map((x) => DropdownMenuItem(
                      value: _intOrNull(x['id']),
                      child: Text('${x['code']} • ${x['name']}')))
                  .toList(),
              onChanged: busy ? null : (v) => setState(() => te = v)),
          const SizedBox(height: 8),
          DropdownButtonFormField<int?>(
              initialValue: lot,
              decoration:
                  const InputDecoration(labelText: 'NF/lote (vazio = FIFO)'),
              items: [
                const DropdownMenuItem<int?>(
                    value: null, child: Text('FIFO automático')),
                ...lots.map((x) => DropdownMenuItem<int?>(
                    value: _intOrNull(x['id']),
                    child: Text(
                        'NF ${x['invoice_number']} • ${_fmtLiters(x['remaining_liters'])}')))
              ],
              onChanged: busy ? null : (v) => setState(() => lot = v)),
          const SizedBox(height: 8),
          TextField(
              controller: liters,
              enabled: !busy,
              keyboardType:
                  const TextInputType.numberWithOptions(decimal: true),
              decoration: const InputDecoration(labelText: 'Volume (L) *')),
          const SizedBox(height: 16),
          FilledButton.icon(
              onPressed: busy ? null : submit,
              icon: busy
                  ? const SizedBox(
                      width: 18,
                      height: 18,
                      child: CircularProgressIndicator(strokeWidth: 2))
                  : const Icon(Icons.swap_horiz_rounded),
              label: Text(busy ? 'Registrando...' : 'Registrar descarga')),
        ]));
  }
}

class TransferV23Screen extends StatefulWidget {
  final Map<String, dynamic> source, ref, profile;
  const TransferV23Screen(
      {super.key,
      required this.source,
      required this.ref,
      required this.profile});
  @override
  State<TransferV23Screen> createState() => _TransferV23ScreenState();
}

class _TransferV23ScreenState extends State<TransferV23Screen> {
  int? dest;
  final liters = TextEditingController(),
      donor = TextEditingController(),
      receiver = TextEditingController();
  Uint8List? ds, rs;
  bool saving = false;
  String step = 'Concluir transferência';
  @override
  void initState() {
    super.initState();
    donor.text = '${widget.profile['display_name'] ?? ''}'.trim();
  }

  Future<Uint8List?> sign(String t) => Navigator.push<Uint8List>(
      context,
      MaterialPageRoute(
          builder: (_) => SignatureCaptureOnlineScreen(title: t),
          fullscreenDialog: true));
  Map<String, dynamic>? destinationOf(List<Map<String, dynamic>> a) {
    for (final x in a) {
      if (_intOrNull(x['id']) == dest) return x;
    }
    return null;
  }

  Future<void> submit(List<Map<String, dynamic>> dests) async {
    if (saving) return;
    final sourceId = _intOrNull(widget.source['id']);
    final v = _num(liters.text.replaceAll(',', '.'));
    final target = destinationOf(dests);
    if (sourceId == null ||
        dest == null ||
        target == null ||
        v <= 0 ||
        donor.text.trim().isEmpty ||
        receiver.text.trim().isEmpty ||
        ds == null ||
        rs == null) {
      if (mounted)
        ScaffoldMessenger.of(context).showSnackBar(const SnackBar(
            content: Text('Preencha os dados e as duas assinaturas.')));
      return;
    }
    final confirmed = await showDialog<bool>(
        context: context,
        builder: (ctx) => AlertDialog(
              title: const Text('Confirmar transferência?'),
              content: Column(
                  mainAxisSize: MainAxisSize.min,
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                        'Origem: ${widget.source['code']} • ${widget.source['name']}',
                        style: const TextStyle(fontWeight: FontWeight.w700)),
                    const SizedBox(height: 8),
                    Text('Destino: ${target['code']} • ${target['name']}',
                        style: const TextStyle(fontWeight: FontWeight.w700)),
                    const SizedBox(height: 8),
                    Text('Volume: ${_fmtLiters(v)}'),
                    const SizedBox(height: 8),
                    Text('Responsável doador: ${donor.text.trim()}'),
                    Text('Responsável recebedor: ${receiver.text.trim()}'),
                    const SizedBox(height: 10),
                    const Text(
                        'Confira os dados antes de confirmar. Depois da confirmação a movimentação será registrada.'),
                  ]),
              actions: [
                TextButton(
                    onPressed: () => Navigator.pop(ctx, false),
                    child: const Text('Cancelar')),
                FilledButton(
                    onPressed: () => Navigator.pop(ctx, true),
                    child: const Text('Confirmar transferência'))
              ],
            ));
    if (confirmed != true || !mounted) return;
    setState(() {
      saving = true;
      step = 'Enviando assinaturas...';
    });
    try {
      final paths = await Future.wait<String>([
        api.uploadBytes(ds!, 'transfer_doador'),
        api.uploadBytes(rs!, 'transfer_recebedor')
      ]);
      if (!mounted) return;
      setState(() => step = 'Registrando transferência...');
      await api.transferV22(
          sourceTankId: sourceId,
          destinationTankId: dest!,
          liters: v,
          donor: donor.text.trim(),
          receiver: receiver.text.trim(),
          donorSignature: paths[0],
          receiverSignature: paths[1]);
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(
          content: Text('Transferência registrada com sucesso ✓')));
      Navigator.pop(context, true);
    } catch (e) {
      if (mounted)
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(
            content:
                Text('Erro ao registrar transferência: ${_friendlyError(e)}')));
    } finally {
      if (mounted)
        setState(() {
          saving = false;
          step = 'Concluir transferência';
        });
    }
  }

  @override
  void dispose() {
    liters.dispose();
    donor.dispose();
    receiver.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext c) {
    final sourceId = _intOrNull(widget.source['id']);
    final dests = _rows(widget.ref['comboio_destinations'])
        .where((x) => _intOrNull(x['id']) != sourceId)
        .toList();
    return Scaffold(
        appBar: AppBar(title: const Text('Transferir')),
        body: ListView(padding: const EdgeInsets.all(18), children: [
          Text('Doador: ${widget.source['code']} • ${widget.source['name']}',
              style: Theme.of(c)
                  .textTheme
                  .titleLarge
                  ?.copyWith(fontWeight: FontWeight.w900)),
          const SizedBox(height: 12),
          DropdownButtonFormField<int>(
              initialValue: dest,
              decoration: const InputDecoration(labelText: 'CB recebedor *'),
              items: dests
                  .map((x) => DropdownMenuItem(
                      value: _intOrNull(x['id']),
                      child: Text('${x['code']} • ${x['name']}')))
                  .toList(),
              onChanged: saving ? null : (v) => setState(() => dest = v)),
          const SizedBox(height: 8),
          TextField(
              controller: donor,
              readOnly: true,
              decoration: const InputDecoration(
                  labelText: 'Responsável doador • identificado pelo login',
                  prefixIcon: Icon(Icons.verified_user_outlined))),
          const SizedBox(height: 8),
          TextField(
              controller: receiver,
              enabled: !saving,
              decoration:
                  const InputDecoration(labelText: 'Responsável recebedor *')),
          const SizedBox(height: 8),
          TextField(
              controller: liters,
              enabled: !saving,
              keyboardType:
                  const TextInputType.numberWithOptions(decimal: true),
              decoration: const InputDecoration(labelText: 'Volume (L) *')),
          const SizedBox(height: 10),
          OutlinedButton(
              onPressed: saving
                  ? null
                  : () async {
                      final b = await sign('Assinatura responsável doador');
                      if (b != null) setState(() => ds = b);
                    },
              child: Text(
                  ds == null ? 'Assinatura doador *' : 'Assinatura doador ✓')),
          OutlinedButton(
              onPressed: saving
                  ? null
                  : () async {
                      final b = await sign('Assinatura responsável recebedor');
                      if (b != null) setState(() => rs = b);
                    },
              child: Text(rs == null
                  ? 'Assinatura recebedor *'
                  : 'Assinatura recebedor ✓')),
          const SizedBox(height: 12),
          FilledButton.icon(
              onPressed: saving ? null : () => submit(dests),
              icon: saving
                  ? const SizedBox(
                      width: 18,
                      height: 18,
                      child: CircularProgressIndicator(strokeWidth: 2))
                  : const Icon(Icons.swap_horiz_rounded),
              label: Text(saving ? step : 'Concluir transferência')),
        ]));
  }
}

class FuelingV23Screen extends StatefulWidget {
  final Map<String, dynamic> source, ref, profile;
  const FuelingV23Screen(
      {super.key,
      required this.source,
      required this.ref,
      required this.profile});
  @override
  State<FuelingV23Screen> createState() => _FuelingV23ScreenState();
}

class _FuelingV23ScreenState extends State<FuelingV23Screen> {
  int? work, machine, third;
  String fuel = 'Diesel';
  final liters = TextEditingController(),
      km = TextEditingController(),
      hour = TextEditingController(),
      receiver = TextEditingController(),
      observation = TextEditingController(),
      location = TextEditingController(),
      sale = TextEditingController(),
      thirdDescription = TextEditingController(),
      thirdPlate = TextEditingController();
  XFile? meter, totalizer, identity, extra;
  Uint8List? rs, os;
  Position? capturedPosition;
  DateTime? locationCapturedAt;
  DateTime? totalizerBeforeCapturedAtV71;
  double? locationAccuracyM;
  bool manualLocationV44 = false;
  bool autoLocationAttemptedV44 = false;
  int locationAttemptsV52 = 0;
  bool locating = false, saving = false;
  bool lubricated = false;
  late final String fuelingTraceIdV87;
  final Map<String, Timer> _fieldAuditTimersV87 = <String, Timer>{};
  final Map<String, String> _lastFieldValuesV87 = <String, String>{};
  String savingStep = 'Concluir abastecimento';
  final Map<int, String> measurementOverridesV51 = <int, String>{};

  @override
  void initState() {
    super.initState();
    fuelingTraceIdV87 = offlineStore.newTraceIdV87();
    final tracked = <String, TextEditingController>{
      'liters': liters,
      'km': km,
      'hourmeter': hour,
      'receiver': receiver,
      'observation': observation,
      'location': location,
      'sale_price_per_liter': sale,
      'third_party_description': thirdDescription,
      'third_party_plate': thirdPlate,
    };
    for (final entry in tracked.entries) {
      entry.value
          .addListener(() => _auditFieldV87(entry.key, entry.value.text));
    }
    unawaited(offlineStore.recordEventV87('fueling_started',
        tankId: _intOrNull(widget.source['id']),
        fuelingEventId: fuelingTraceIdV87,
        payload: {
          'source_code': widget.source['code'],
          'source_name': widget.source['name'],
          'source_type': widget.source['tank_type'],
        }));
  }

  void _auditFieldV87(String field, dynamic value, {bool immediate = false}) {
    final text = value == null ? '' : '$value';
    if (_lastFieldValuesV87[field] == text) return;
    _lastFieldValuesV87[field] = text;
    _fieldAuditTimersV87[field]?.cancel();
    void send() {
      unawaited(offlineStore.recordEventV87('fueling_field_changed',
          tankId: _intOrNull(widget.source['id']),
          fuelingEventId: fuelingTraceIdV87,
          payload: {'field': field, 'value': value}));
    }

    if (immediate) {
      send();
    } else {
      _fieldAuditTimersV87[field] =
          Timer(const Duration(milliseconds: 300), send);
    }
  }

  Future<void> _auditEvidenceV87(String kind, XFile file) async {
    try {
      final bytes = await file.readAsBytes();
      await offlineStore.recordEventV87('fueling_evidence_captured',
          tankId: _intOrNull(widget.source['id']),
          fuelingEventId: fuelingTraceIdV87,
          payload: {
            'kind': kind,
            'file_name': file.name,
            'size_bytes': bytes.length,
            'sha256': crypto.sha256.convert(bytes).toString(),
          });
    } catch (_) {}
  }

  Future<void> _auditSignatureV87(String kind, Uint8List bytes) async {
    await offlineStore.recordEventV87('fueling_signature_captured',
        tankId: _intOrNull(widget.source['id']),
        fuelingEventId: fuelingTraceIdV87,
        payload: {
          'kind': kind,
          'size_bytes': bytes.length,
          'sha256': crypto.sha256.convert(bytes).toString(),
        });
  }

  Future<void> captureTotalizerBeforeV70() async {
    if (saving) return;
    final x = await cam();
    if (x == null || !mounted) return;
    setState(() {
      totalizer = x;
      totalizerBeforeCapturedAtV71 = DateTime.now().toUtc();
    });
    unawaited(_auditEvidenceV87('totalizer_before', x));
    unawaited(offlineStore.recordEventV87('fueling_totalizer_before',
        tankId: _intOrNull(widget.source['id']),
        fuelingEventId: fuelingTraceIdV87,
        occurredAt: totalizerBeforeCapturedAtV71,
        payload: {'captured_before_fueling': true}));
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (mounted) unawaited(attemptLocationV52(automatic: true));
    });
  }

  bool get financial => true;
  Future<XFile?> cam() => ImagePicker()
      .pickImage(source: ImageSource.camera, imageQuality: 75, maxWidth: 1600);
  Future<Uint8List?> sign(String t) => Navigator.push<Uint8List>(
      context,
      MaterialPageRoute(
          builder: (_) => SignatureCaptureOnlineScreen(title: t),
          fullscreenDialog: true));
  Map<String, dynamic>? selected(List<Map<String, dynamic>> a, int? id) {
    if (id == null) return null;
    for (final x in a) {
      if (_intOrNull(x['id']) == id) return x;
    }
    return null;
  }

  bool vehicleLike(Map<String, dynamic> x, {bool thirdParty = false}) {
    final raw =
        '${x['tipo'] ?? x['type'] ?? ''} ${x['modelo'] ?? x['model'] ?? ''} ${x['description'] ?? ''}'
            .toLowerCase();
    const vehicleTerms = [
      'automóvel',
      'automovel',
      'caminhão',
      'caminhao',
      'microonibus',
      'micro-ônibus',
      'microônibus',
      'ônibus',
      'onibus',
      'cavalo mecânico',
      'cavalo mecanico',
      'pickup',
      'pick up',
      'van',
      'veículo',
      'veiculo',
      'carro'
    ];
    if (vehicleTerms.any(raw.contains)) return true;
    const machineTerms = [
      'retroescavadeira',
      'escavadeira',
      'carregadeira',
      'fresadora',
      'rolo ',
      'rolo compactador',
      'motoniveladora',
      'vibro acabadora',
      'máquina',
      'maquina',
      'trator',
      'gerador',
      'extrusora'
    ];
    if (machineTerms.any(raw.contains)) return false;
    final plate = thirdParty ? x['plate'] : x['placa'];
    return _hasValue(plate);
  }

  bool munckLikeV51(Map<String, dynamic> x) {
    final raw =
        '${x['tipo'] ?? x['type'] ?? ''} ${x['modelo'] ?? x['model'] ?? ''}'
            .toLowerCase();
    return raw.contains('munck') || raw.contains('guindauto');
  }

  Future<void> refreshMeasurementV51(int? machineId) async {
    if (machineId == null) return;
    try {
      final fresh = await api.referenceData();
      for (final x in _rows(fresh['machines'])) {
        if (_intOrNull(x['id']) != machineId) continue;
        final mt = '${x['measurement_type'] ?? ''}'.trim().toLowerCase();
        if (mt.isNotEmpty) {
          measurementOverridesV51[machineId] = mt;
          if (mounted) setState(() {});
        }
        break;
      }
    } catch (_) {}
  }

  Set<String> metricKinds() {
    final out = <String>{};
    final ms = _rows(widget.ref['machines']),
        ts = _rows(widget.ref['third_party_vehicles']);
    final sm = selected(ms, machine), st = selected(ts, third);
    if (sm != null) {
      final id = _intOrNull(sm['id']);
      final rawMeasurement = id == null
          ? sm['measurement_type']
          : (measurementOverridesV51[id] ?? sm['measurement_type']);
      final configured = '${rawMeasurement ?? ''}'.trim().toLowerCase();
      if (configured == 'both' || munckLikeV51(sm)) {
        out.addAll(const ['km', 'hour']);
      } else if (configured == 'km')
        out.add('km');
      else if (configured == 'hourmeter')
        out.add('hour');
      else if (configured == 'none') {
      } else
        out.add(vehicleLike(sm) ? 'km' : 'hour');
    }
    if (st != null) out.add(vehicleLike(st, thirdParty: true) ? 'km' : 'hour');
    return out;
  }

  String sourceTypeLabel() {
    switch ('${widget.source['tank_type']}') {
      case 'stationary':
        return 'T.E.';
      case 'truck':
        return 'Caminhão-tanque';
      default:
        return 'Comboio';
    }
  }

  String sourceDisplayLabelV80() {
    final code = '${widget.source['code'] ?? ''}'.trim();
    final asset = '${widget.source['machine_asset_number'] ?? ''}'.trim();
    final name = '${widget.source['name'] ?? ''}'.trim();
    final identity = asset.isNotEmpty ? asset : name;
    return [code, identity, sourceTypeLabel()]
        .where((x) => x.trim().isNotEmpty)
        .join(' • ');
  }

  String metricPhotoLabel(Set<String> kinds) {
    if (kinds.length > 1) return 'Foto do KM/Horímetro *';
    if (kinds.contains('km')) return 'Foto do KM *';
    if (kinds.contains('hour')) return 'Foto do Horímetro *';
    return 'Foto do KM/Horímetro *';
  }

  Future<Position?> currentPosition() async {
    try {
      if (!await Geolocator.isLocationServiceEnabled()) return null;
      var permission = await Geolocator.checkPermission();
      if (permission == LocationPermission.denied)
        permission = await Geolocator.requestPermission();
      if (permission == LocationPermission.denied ||
          permission == LocationPermission.deniedForever) return null;
      Position? best;
      final deadline = DateTime.now().add(const Duration(seconds: 20));
      while (DateTime.now().isBefore(deadline)) {
        final remaining = deadline.difference(DateTime.now());
        if (remaining <= Duration.zero) break;
        final slice = remaining > const Duration(seconds: 5)
            ? const Duration(seconds: 5)
            : remaining;
        try {
          final p = await Geolocator.getCurrentPosition(
              locationSettings: LocationSettings(
                  accuracy: LocationAccuracy.bestForNavigation,
                  timeLimit: slice));
          if (best == null || p.accuracy < best.accuracy) best = p;
          if (p.accuracy <= 20) return p;
        } catch (_) {}
        if (DateTime.now().isBefore(deadline))
          await Future<void>.delayed(const Duration(milliseconds: 500));
      }
      return best != null && best.accuracy <= 20 ? best : null;
    } catch (_) {
      return null;
    }
  }

  String formatPlacemark(Placemark p) {
    final road = [p.thoroughfare, p.subThoroughfare]
        .where((v) => v != null && v.trim().isNotEmpty)
        .map((v) => v!.trim())
        .join(', ');
    final street = road.isNotEmpty ? road : (p.street ?? '').trim();
    final district = (p.subLocality ?? '').trim();
    final city = [p.locality, p.administrativeArea]
        .where((v) => v != null && v.trim().isNotEmpty)
        .map((v) => v!.trim())
        .join(' - ');
    final tail = [district, city, p.postalCode, p.country]
        .where((v) => v != null && v.trim().isNotEmpty)
        .map((v) => v!.trim())
        .join(', ');
    return [street, tail].where((v) => v.trim().isNotEmpty).join(', ');
  }

  Future<bool> attemptLocationV52({bool automatic = false}) async {
    if (locating || manualLocationV44) return false;
    if (mounted) setState(() => locating = true);
    try {
      locationAttemptsV52++;
      autoLocationAttemptedV44 = true;
      final pos = await currentPosition();
      if (pos == null) {
        capturedPosition = null;
        locationAccuracyM = null;
        location.clear();
        if (locationAttemptsV52 >= 2) manualLocationV44 = true;
        if (mounted) {
          setState(() {});
          final msg = locationAttemptsV52 >= 2
              ? 'Não foi possível obter a localização automaticamente. Informe o endereço manualmente para continuar.'
              : 'Não foi possível obter a localização. Toque no campo Localização para tentar novamente.';
          ScaffoldMessenger.of(context)
              .showSnackBar(SnackBar(content: Text(msg)));
        }
        return false;
      }
      String value = '';
      for (var attempt = 0; attempt < 2 && value.trim().isEmpty; attempt++) {
        try {
          final places =
              await placemarkFromCoordinates(pos.latitude, pos.longitude);
          if (places.isNotEmpty) value = formatPlacemark(places.first);
        } catch (_) {}
        if (value.trim().isEmpty && attempt == 0)
          await Future<void>.delayed(const Duration(milliseconds: 500));
      }
      if (value.trim().isEmpty) {
        // O GPS funcionou: preserve as coordenadas originais mesmo se o endereço
        // não puder ser resolvido sem internet. O usuário digita apenas o endereço.
        capturedPosition = pos;
        locationCapturedAt = DateTime.now().toUtc();
        locationAccuracyM = pos.accuracy;
        location.clear();
        manualLocationV44 = true;
        if (mounted) {
          setState(() {});
          ScaffoldMessenger.of(context).showSnackBar(const SnackBar(
              content: Text(
                  'GPS capturado. Informe apenas o endereço manualmente.')));
        }
        return false;
      }
      manualLocationV44 = false;
      capturedPosition = pos;
      locationCapturedAt = DateTime.now().toUtc();
      locationAccuracyM = pos.accuracy;
      location.text = value;
      if (mounted) setState(() {});
      return true;
    } finally {
      if (mounted) setState(() => locating = false);
    }
  }

  Future<bool> captureLocationForSubmission() async {
    if (locating) return false;
    if (mounted) setState(() => locating = true);
    try {
      final manualAddress = location.text.trim();
      final pos =
          await currentPosition(); // nova leitura no exato fluxo de conclusão; tolerância de 20 m.
      if (pos == null) {
        capturedPosition = null;
        locationAccuracyM = null;
        locationCapturedAt = DateTime.now().toUtc();
        manualLocationV44 = true;
        if (manualAddress.isEmpty) {
          location.clear();
          if (mounted) {
            setState(() {});
            ScaffoldMessenger.of(context).showSnackBar(const SnackBar(
                content: Text(
                    'GPS indisponível no momento da conclusão. Informe o endereço manualmente.')));
          }
          return false;
        }
        location.text = manualAddress;
        if (mounted) setState(() {});
        await offlineStore.recordEventV87('fueling_location_captured',
            tankId: _intOrNull(widget.source['id']),
            fuelingEventId: fuelingTraceIdV87,
            payload: {
              'address': location.text.trim(),
              'manual': true,
              'latitude': null,
              'longitude': null,
              'accuracy_m': null,
            });
        return true;
      }
      capturedPosition = pos;
      locationCapturedAt = DateTime.now().toUtc();
      locationAccuracyM = pos.accuracy;
      String resolved = '';
      try {
        final places =
            await placemarkFromCoordinates(pos.latitude, pos.longitude);
        if (places.isNotEmpty) resolved = formatPlacemark(places.first);
      } catch (_) {}
      if (resolved.trim().isNotEmpty) {
        location.text = resolved.trim();
        manualLocationV44 = false;
      } else if (manualAddress.isNotEmpty) {
        location.text = manualAddress;
        manualLocationV44 = true;
      } else {
        manualLocationV44 = true;
        location.clear();
        if (mounted) {
          setState(() {});
          ScaffoldMessenger.of(context).showSnackBar(const SnackBar(
              content: Text(
                  'GPS capturado, mas o endereço não pôde ser identificado. Informe o endereço manualmente.')));
        }
        return false;
      }
      if (mounted) setState(() {});
      await offlineStore.recordEventV87('fueling_location_captured',
          tankId: _intOrNull(widget.source['id']),
          fuelingEventId: fuelingTraceIdV87,
          payload: {
            'address': location.text.trim(),
            'manual': manualLocationV44,
            'latitude': capturedPosition?.latitude,
            'longitude': capturedPosition?.longitude,
            'accuracy_m': locationAccuracyM,
          });
      return true;
    } finally {
      if (mounted) setState(() => locating = false);
    }
  }

  String locationMeta() {
    if (locationCapturedAt == null)
      return 'Será capturada no momento em que o abastecimento for registrado.';
    final d = locationCapturedAt!.toLocal();
    final hh = d.hour.toString().padLeft(2, '0'),
        mm = d.minute.toString().padLeft(2, '0'),
        ss = d.second.toString().padLeft(2, '0');
    final accuracy = locationAccuracyM == null
        ? ''
        : ' • precisão aproximada ±${locationAccuracyM!.round()} m';
    return 'Capturada às $hh:$mm:$ss$accuracy';
  }

  Future<bool> confirmFueling(double v, double? k, double? h) async {
    final ms = _rows(widget.ref['machines']),
        ts = _rows(widget.ref['third_party_vehicles']);
    final sm = selected(ms, machine), st = selected(ts, third);
    final targets = <String>[];
    if (sm != null) targets.add('${sm['numeroAtivo']} • ${sm['modelo'] ?? ''}');
    if (st != null)
      targets.add(_plateDescriptionLabel(st['plate'], st['description']));
    if (st == null && thirdPlate.text.trim().isNotEmpty)
      targets
          .add('${thirdPlate.text.trim()} • ${thirdDescription.text.trim()}');
    return await showDialog<bool>(
            context: context,
            builder: (ctx) => AlertDialog(
                    title: const Text('Confirmar abastecimento?'),
                    content: SingleChildScrollView(
                        child: Column(
                            mainAxisSize: MainAxisSize.min,
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                          Text(
                              'Origem: ${widget.source['code']} • ${widget.source['name']}',
                              style:
                                  const TextStyle(fontWeight: FontWeight.w700)),
                          const SizedBox(height: 8),
                          Text('Ativo/equipamento: ${targets.join(' + ')}'),
                          const SizedBox(height: 8),
                          Text('Combustível: $fuel'),
                          Text('Volume: ${_fmtLiters(v)}'),
                          Text('Lubrificou? ${lubricated ? 'Sim' : 'Não'}'),
                          const Text(
                              'Totalizador antes do abastecimento: foto registrada ✓',
                              style: TextStyle(fontWeight: FontWeight.w700)),
                          Text(
                              'Preço por litro: ${_fmtMoney(_num(sale.text.replaceAll(',', '.')))}'),
                          Text(
                              'Valor total: ${_fmtMoney(v * _num(sale.text.replaceAll(',', '.')))}',
                              style:
                                  const TextStyle(fontWeight: FontWeight.w700)),
                          if (k != null)
                            Text(
                                'KM: ${k.toStringAsFixed(k.truncateToDouble() == k ? 0 : 1)}'),
                          if (h != null)
                            Text(
                                'Horímetro: ${h.toStringAsFixed(h.truncateToDouble() == h ? 0 : 1)}'),
                          Text(
                              'Responsável pelo recebimento do abastecimento: ${receiver.text.trim()}'),
                          if (observation.text.trim().isNotEmpty)
                            Text('Observação: ${observation.text.trim()}'),
                          const SizedBox(height: 8),
                          Text(
                              'Endereço do abastecimento: ${location.text.trim()}',
                              style:
                                  const TextStyle(fontWeight: FontWeight.w700)),
                          Text(
                              manualLocationV44
                                  ? 'Localização informada manualmente'
                                  : 'Localização obtida automaticamente',
                              style: const TextStyle(
                                  fontSize: 12, color: Colors.black54)),
                          if (capturedPosition != null)
                            Text(
                                'Coordenadas: ${capturedPosition!.latitude.toStringAsFixed(6)}, ${capturedPosition!.longitude.toStringAsFixed(6)}',
                                style: const TextStyle(
                                    fontSize: 12, color: Colors.black54)),
                          if (capturedPosition != null)
                            Text(locationMeta(),
                                style: const TextStyle(
                                    fontSize: 12, color: Colors.black54)),
                          const SizedBox(height: 10),
                          const Text(
                              'Confira os dados antes de confirmar. Depois da confirmação o registro será processado.')
                        ])),
                    actions: [
                      TextButton(
                          onPressed: () => Navigator.pop(ctx, false),
                          child: const Text('Cancelar')),
                      FilledButton(
                          onPressed: () => Navigator.pop(ctx, true),
                          child: const Text('Confirmar abastecimento'))
                    ])) ??
        false;
  }

  Future<void> submit(bool hasPlate) async {
    if (saving || locating) return;
    final v = _num(liters.text.replaceAll(',', '.'));
    final kinds = metricKinds();
    double? k, h;
    void requiredMessage(String field) {
      if (mounted)
        ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(content: Text('Preenchimento obrigatório: $field')));
    }

    if (v <= 0) {
      requiredMessage('Quantidade (L)');
      return;
    }
    final saleValue = double.tryParse(sale.text.trim().replaceAll(',', '.'));
    if (saleValue == null || saleValue <= 0) {
      requiredMessage('Preço por litro');
      return;
    }
    final needsWork =
        const ['comboio', 'truck'].contains('${widget.source['tank_type']}');
    if (needsWork && work == null) {
      requiredMessage('Obra');
      return;
    }
    final manualThird = machine == null && third == -1;
    if (machine == null && third == null) {
      requiredMessage('Ativo ou Equipamento de terceiros');
      return;
    }
    if (manualThird && thirdPlate.text.trim().isEmpty) {
      requiredMessage('Placa/Identificação do equipamento não cadastrado');
      return;
    }
    if (manualThird && thirdPlate.text.trim().isEmpty) {
      requiredMessage('Placa/Identificação');
      return;
    }
    if (manualThird) {
      k = double.tryParse(km.text.trim().replaceAll(',', '.'));
      h = double.tryParse(hour.text.trim().replaceAll(',', '.'));
      if (k != null && k < 0) {
        requiredMessage('KM');
        return;
      }
      if (h != null && h < 0) {
        requiredMessage('Horímetro');
        return;
      }
      if (k == null && h == null) {
        requiredMessage('KM ou Horímetro');
        return;
      }
    } else {
      if (kinds.contains('km')) {
        k = double.tryParse(km.text.trim().replaceAll(',', '.'));
        if (k == null || k < 0) {
          requiredMessage('KM');
          return;
        }
      }
      if (kinds.contains('hour')) {
        h = double.tryParse(hour.text.trim().replaceAll(',', '.'));
        if (h == null || h < 0) {
          requiredMessage('Horímetro');
          return;
        }
      }
    }
    if (receiver.text.trim().isEmpty) {
      requiredMessage('Responsável pelo recebimento do abastecimento');
      return;
    }
    if ((kinds.isNotEmpty || manualThird) && meter == null) {
      requiredMessage(kinds.length > 1
          ? 'Foto de KM/Horímetro'
          : kinds.contains('km')
              ? 'Foto do KM'
              : kinds.contains('hour')
                  ? 'Foto do Horímetro'
                  : 'Foto de KM/Horímetro');
      return;
    }
    if (totalizer == null || totalizerBeforeCapturedAtV71 == null) {
      requiredMessage('Foto do totalizador antes do abastecimento');
      return;
    }
    if (identity == null) {
      requiredMessage('Foto da placa ou identificação');
      return;
    }
    if (rs == null) {
      requiredMessage('Assinatura de quem recebeu');
      return;
    }
    if (os == null) {
      requiredMessage('Assinatura de quem abasteceu');
      return;
    }
    if (machine != null && !offlineStore.backendReadyV81) {
      final sm = selected(_rows(widget.ref['machines']), machine);
      if (sm != null) {
        final configured =
            '${sm['measurement_type'] ?? ''}'.trim().toLowerCase();
        final lastKmRaw = sm['kmHorimetro'];
        final lastHourRaw = sm['meter_physical_value'];
        final lastKm = lastKmRaw == null
            ? null
            : (lastKmRaw is num
                ? lastKmRaw.toDouble()
                : double.tryParse('$lastKmRaw'));
        final lastHour = lastHourRaw == null
            ? null
            : (lastHourRaw is num
                ? lastHourRaw.toDouble()
                : double.tryParse('$lastHourRaw'));
        String? regressionMessage;
        if ((configured == 'km' || kinds.contains('km')) &&
            k != null &&
            lastKm != null &&
            k < lastKm) {
          regressionMessage =
              'KM inferior ao último registro conhecido no aparelho (${lastKm.toStringAsFixed(1)} km).';
        } else if ((configured == 'hourmeter' || kinds.contains('hour')) &&
            h != null &&
            lastHour != null &&
            h < lastHour) {
          regressionMessage =
              'Horímetro inferior ao último registro conhecido no aparelho (${lastHour.toStringAsFixed(1)} h).';
        }
        if (regressionMessage != null) {
          if (mounted) {
            await showDialog<void>(
                context: context,
                builder: (ctx) => AlertDialog(
                        title: const Text('Leitura inválida'),
                        content: Text(
                            '$regressionMessage\n\nComo o aparelho está offline, a última leitura conhecida foi usada para impedir que um valor regressivo seja salvo por engano.'),
                        actions: [
                          FilledButton(
                              onPressed: () => Navigator.pop(ctx),
                              child: const Text('Corrigir valor'))
                        ]));
          }
          return;
        }
      }
    }
    if (machine != null && offlineStore.backendReadyV81) {
      try {
        final check = await api.meterCheckV48(machine!, km: k, hourmeter: h);
        if (check['regression'] == true) {
          final msg =
              '${check['message'] ?? 'Valor inferior ao último registro.'}';
          if (mounted)
            await showDialog<void>(
                context: context,
                builder: (ctx) => AlertDialog(
                        title: const Text('KM/Horímetro inválido'),
                        content: Text(msg),
                        actions: [
                          FilledButton(
                              onPressed: () => Navigator.pop(ctx),
                              child: const Text('Corrigir valor'))
                        ]));
          return;
        }
        if (check['large_jump'] == true && mounted) {
          final lastK = check['last_km'], lastH = check['last_hourmeter'];
          final ok = await showDialog<bool>(
                  context: context,
                  builder: (ctx) => AlertDialog(
                          title: const Text(
                              'Valor muito acima do último registro'),
                          content: Text(
                              'Último KM: ${lastK ?? '-'}\nÚltimo horímetro: ${lastH ?? '-'}\n\nO valor informado teve um aumento fora do normal. Confirme somente se conferiu a leitura no equipamento.'),
                          actions: [
                            TextButton(
                                onPressed: () => Navigator.pop(ctx, false),
                                child: const Text('Voltar')),
                            FilledButton(
                                onPressed: () => Navigator.pop(ctx, true),
                                child: const Text('Valor conferido'))
                          ])) ??
              false;
          if (!ok) return;
        }
      } catch (e) {
        if (_isNetworkError(e)) {
          offlineStore.markOffline();
        } else {
          if (mounted)
            ScaffoldMessenger.of(context)
                .showSnackBar(SnackBar(content: Text(_friendlyError(e))));
          return;
        }
      }
    }
    if (!await captureLocationForSubmission() || !mounted) return;
    if (!await confirmFueling(v, k, h) || !mounted) return;
    final occurredAt = DateTime.now().toUtc();
    final tankIdV87 = _intOrNull(widget.source['id'])!;
    final expectedSequenceV87 =
        offlineStore._lastKnownSequenceV74(tankIdV87) + 1;
    await offlineStore.recordEventV87('fueling_confirmed',
        tankId: tankIdV87,
        fuelingEventId: fuelingTraceIdV87,
        occurredAt: occurredAt,
        payload: {
          'source_code': widget.source['code'],
          'expected_sequence': expectedSequenceV87,
          'expected_code':
              offlineStore._offlineCodeV74(tankIdV87, expectedSequenceV87),
          'work_id': work,
          'machine_id': machine,
          'third_party_vehicle_id': third == -1 ? null : third,
          'third_party_plate': third == -1 ? thirdPlate.text.trim() : null,
          'third_party_description':
              third == -1 ? thirdDescription.text.trim() : null,
          'fuel_type': fuel,
          'liters': v,
          'sale_price_per_liter': saleValue,
          'total_price': v * saleValue,
          'km': k,
          'hourmeter': h,
          'receiver': receiver.text.trim(),
          'notes': observation.text.trim(),
          'lubricated': lubricated,
          'location': location.text.trim(),
          'latitude': capturedPosition?.latitude,
          'longitude': capturedPosition?.longitude,
          'location_accuracy_m': locationAccuracyM,
          'totalizer_before_captured_at':
              totalizerBeforeCapturedAtV71?.toIso8601String(),
          'has_meter_photo': meter != null,
          'has_totalizer_photo': totalizer != null,
          'has_identity_photo': identity != null,
          'has_extra_photo': extra != null,
          'has_receiver_signature': rs != null,
          'has_operator_signature': os != null,
        });
    setState(() {
      saving = true;
      savingStep = 'Enviando evidências...';
    });
    try {
      Future<String> up(XFile x, String kind) async =>
          api.uploadBytes(await x.readAsBytes(), kind,
              mime: x.mimeType ?? 'image/jpeg');
      final u = await Future.wait<String?>([
        meter == null
            ? Future<String?>.value(null)
            : up(meter!, 'km_horimetro'),
        up(totalizer!, 'totalizador_antes'),
        up(identity!, 'placa_identificacao'),
        extra == null
            ? Future<String?>.value(null)
            : up(extra!, 'abastecimento_extra'),
        api.uploadBytes(rs!, 'assinatura_recebedor'),
        api.uploadBytes(os!, 'assinatura_abastecedor')
      ]);
      if (!mounted) return;
      setState(() => savingStep = 'Finalizando abastecimento...');
      final manualThird = machine == null && third == -1;
      final r = await api.fuelingV71(
          sourceTankId: _intOrNull(widget.source['id'])!,
          workId: work,
          machineId: machine,
          thirdId: manualThird ? null : third,
          thirdPartyPlate: manualThird ? thirdPlate.text.trim() : null,
          thirdPartyDescription:
              manualThird && thirdDescription.text.trim().isNotEmpty
                  ? thirdDescription.text.trim()
                  : null,
          liters: v,
          km: k,
          hourmeter: h,
          responsible: null,
          receiver: receiver.text.trim(),
          receiverSignature: u[4]!,
          operatorSignature: u[5]!,
          meterPhoto: u[0],
          totalizerPhoto: u[1]!,
          totalizerBeforeCapturedAt: totalizerBeforeCapturedAtV71!,
          identityPhoto: u[2]!,
          identityKind: (hasPlate || manualThird) ? 'plate' : 'side',
          extraPhoto: u[3],
          salePrice: saleValue,
          notes:
              observation.text.trim().isEmpty ? null : observation.text.trim(),
          lubricated: lubricated,
          fuelingEventId: fuelingTraceIdV87,
          fuelType: fuel,
          location: location.text.trim(),
          latitude: capturedPosition?.latitude,
          longitude: capturedPosition?.longitude,
          locationCapturedAt: locationCapturedAt,
          locationAccuracyM: locationAccuracyM,
          occurredAt: occurredAt);
      if (!mounted) return;
      await offlineStore.recordEventV87(
          r['queued'] == true ? 'fueling_saved_offline' : 'fueling_registered',
          tankId: tankIdV87,
          fuelingEventId: fuelingTraceIdV87,
          payload: {
            'queued': r['queued'] == true,
            'movement_id': r['movement_id'] ?? r['id'],
            'movement_code': r['code'] ?? r['movement_code'],
            'offline_sequence': r['offline_sequence_v74'],
            'liters': v,
            'price_per_liter': saleValue,
            'total_price': v * saleValue,
          });
      if (offlineStore.backendReadyV81) {
        unawaited(offlineStore.syncAuditEventsV87());
      }
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(
          content: Text(r['queued'] == true
              ? 'Abastecimento salvo no aparelho ✓. Aguardando sincronização.'
              : 'Abastecimento registrado com sucesso ✓')));
      Navigator.pop(context, true);
    } catch (e) {
      await offlineStore.recordEventV87('fueling_submit_failed',
          tankId: _intOrNull(widget.source['id']),
          fuelingEventId: fuelingTraceIdV87,
          payload: {'error': _friendlyError(e)});
      if (mounted)
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(
            content:
                Text('Erro ao registrar abastecimento: ${_friendlyError(e)}')));
    } finally {
      if (mounted)
        setState(() {
          saving = false;
          savingStep = 'Concluir abastecimento';
        });
    }
  }

  @override
  void dispose() {
    for (final timer in _fieldAuditTimersV87.values) {
      timer.cancel();
    }
    for (final c in [
      liters,
      km,
      hour,
      receiver,
      observation,
      location,
      sale,
      thirdDescription,
      thirdPlate
    ]) {
      c.dispose();
    }
    super.dispose();
  }

  @override
  Widget build(BuildContext c) {
    final ms = _rows(widget.ref['machines']),
        ts = _rows(widget.ref['third_party_vehicles']),
        ws = _rows(widget.ref['works']);
    final sm = selected(ms, machine),
        st = selected(ts, third),
        manualThird = machine == null && third == -1,
        hasPlate = _hasValue(sm?['placa']) ||
            _hasValue(st?['plate']) ||
            (manualThird && _hasValue(thirdPlate.text));
    final needsWork =
        const ['comboio', 'truck'].contains('${widget.source['tank_type']}');
    final kinds = metricKinds(),
        needsKm = kinds.contains('km'),
        needsHour = kinds.contains('hour');
    dynamic rawSmMeasurement;
    if (sm != null) {
      final smId = _intOrNull(sm['id']);
      rawSmMeasurement = smId == null
          ? sm['measurement_type']
          : (measurementOverridesV51[smId] ?? sm['measurement_type']);
    }
    final smMeasurement = '${rawSmMeasurement ?? ''}'.trim().toLowerCase();
    final measurementNotApplicable =
        sm != null && st == null && smMeasurement == 'none';
    const title = 'Novo abastecimento';
    if (totalizer == null) {
      return Scaffold(
          appBar: AppBar(title: Text(title)),
          body: SafeArea(
              child: ListView(padding: const EdgeInsets.all(20), children: [
            Card(
                child: Padding(
                    padding: const EdgeInsets.all(18),
                    child: Column(
                        crossAxisAlignment: CrossAxisAlignment.stretch,
                        children: [
                          const Icon(Icons.camera_alt_rounded,
                              size: 52, color: _blue),
                          const SizedBox(height: 12),
                          const Text('Foto obrigatória antes de iniciar',
                              textAlign: TextAlign.center,
                              style: TextStyle(
                                  fontSize: 20, fontWeight: FontWeight.w900)),
                          const SizedBox(height: 16),
                          InputDecorator(
                              decoration: const InputDecoration(
                                  labelText: 'Origem do combustível'),
                              child: Text(sourceDisplayLabelV80(),
                                  style: const TextStyle(
                                      fontWeight: FontWeight.w800))),
                          const SizedBox(height: 16),
                          FilledButton.icon(
                              onPressed: captureTotalizerBeforeV70,
                              icon: const Icon(Icons.photo_camera_rounded),
                              label: const Text(
                                  'Tirar foto do totalizador antes do abastecimento')),
                          const SizedBox(height: 8),
                          TextButton(
                              onPressed: () async {
                                await offlineStore.recordEventV87(
                                    'fueling_form_cancelled',
                                    tankId: _intOrNull(widget.source['id']),
                                    fuelingEventId: fuelingTraceIdV87,
                                    payload: {'stage': 'before_form'});
                                if (context.mounted) Navigator.pop(context);
                              },
                              child: const Text('Cancelar abastecimento')),
                        ]))),
          ])));
    }
    return Scaffold(
        appBar: AppBar(title: Text(title)),
        body: SafeArea(
            child: ListView(
                padding: const EdgeInsets.fromLTRB(18, 18, 18, 36),
                children: [
              const Card(
                  child: ListTile(
                      leading:
                          Icon(Icons.verified_rounded, color: Colors.green),
                      title: Text(
                          'Totalizador antes do abastecimento registrado ✓',
                          style: TextStyle(fontWeight: FontWeight.w900)),
                      subtitle: Text(
                          'A foto foi capturada antes do início deste registro e será preservada no histórico e no PDF.'))),
              const SizedBox(height: 12),
              const Card(
                  child: ListTile(
                      leading: Icon(Icons.location_on_outlined,
                          color: Colors.orange),
                      title: Text('Localização deve estar ativada',
                          style: TextStyle(fontWeight: FontWeight.w900)))),
              const SizedBox(height: 12),
              InputDecorator(
                  decoration: const InputDecoration(
                      labelText: 'Origem do combustível',
                      prefixIcon: Icon(Icons.local_gas_station_outlined)),
                  child: Text(sourceDisplayLabelV80(),
                      style: const TextStyle(fontWeight: FontWeight.w800))),
              const SizedBox(height: 10),
              if (needsWork)
                DropdownButtonFormField<int>(
                    initialValue: work,
                    decoration: const InputDecoration(labelText: 'Obra *'),
                    items: ws
                        .map((x) => DropdownMenuItem(
                            value: _intOrNull(x['id']),
                            child: Text('${x['name']}')))
                        .toList(),
                    onChanged: saving
                        ? null
                        : (v) {
                            setState(() => work = v);
                            _auditFieldV87('work_id', v, immediate: true);
                          }),
              const SizedBox(height: 12),
              Text('Destino do abastecimento *',
                  style: Theme.of(c)
                      .textTheme
                      .titleSmall
                      ?.copyWith(fontWeight: FontWeight.w900)),
              const SizedBox(height: 8),
              DropdownButtonFormField<int?>(
                  initialValue: machine,
                  isExpanded: true,
                  decoration: const InputDecoration(labelText: 'Ativo próprio'),
                  items: [
                    const DropdownMenuItem<int?>(
                        value: null, child: Text('Nenhum')),
                    ...ms.map((x) {
                      final parts = <String>['${x['numeroAtivo'] ?? '-'}'];
                      if (_hasValue(x['placa'])) parts.add('${x['placa']}');
                      parts.add('${x['modelo'] ?? '-'}');
                      final label = parts.join(' • ');
                      return DropdownMenuItem<int?>(
                          value: _intOrNull(x['id']),
                          child: Text(label,
                              maxLines: 1, overflow: TextOverflow.ellipsis));
                    })
                  ],
                  onChanged: (saving || third != null)
                      ? null
                      : (v) {
                          setState(() {
                            machine = v;
                            if (v != null) {
                              third = null;
                              thirdPlate.clear();
                              thirdDescription.clear();
                            }
                          });
                          _auditFieldV87('machine_id', v, immediate: true);
                          unawaited(refreshMeasurementV51(v));
                        }),
              const SizedBox(height: 8),
              DropdownButtonFormField<int?>(
                  initialValue: third,
                  isExpanded: true,
                  decoration: const InputDecoration(
                      labelText: 'Equipamento de terceiros'),
                  items: [
                    const DropdownMenuItem<int?>(
                        value: null, child: Text('Nenhum')),
                    const DropdownMenuItem<int?>(
                        value: -1, child: Text('Não cadastrado')),
                    ...ts.map((x) => DropdownMenuItem<int?>(
                        value: _intOrNull(x['id']),
                        child: Text(
                            _plateDescriptionLabel(
                                x['plate'], x['description']),
                            maxLines: 1,
                            overflow: TextOverflow.ellipsis)))
                  ],
                  onChanged: (saving || machine != null)
                      ? null
                      : (v) {
                          setState(() {
                            third = v;
                            if (v != null) machine = null;
                          });
                          final t = v == -1 ? null : selected(ts, v);
                          if (t != null) {
                            thirdPlate.text = '${t['plate'] ?? ''}';
                            thirdDescription.text = '${t['description'] ?? ''}';
                          } else {
                            thirdPlate.clear();
                            thirdDescription.clear();
                          }
                          _auditFieldV87('third_party_vehicle_id', v,
                              immediate: true);
                        }),
              if (manualThird) ...[
                const SizedBox(height: 8),
                TextField(
                    controller: thirdDescription,
                    enabled: !saving,
                    onChanged: (_) => setState(() {}),
                    decoration: const InputDecoration(
                        labelText: 'Descrição do equipamento')),
                const SizedBox(height: 8),
                TextField(
                    controller: thirdPlate,
                    enabled: !saving,
                    onChanged: (_) => setState(() {}),
                    decoration: const InputDecoration(
                        labelText: 'Placa/Identificação *')),
                const Padding(
                    padding: EdgeInsets.only(top: 6, bottom: 10),
                    child: Text(
                        'Informe a descrição e a placa ou identificação do equipamento não cadastrado.',
                        style: TextStyle(fontSize: 12, color: Colors.black54))),
              ],
              const SizedBox(height: 18),
              DropdownButtonFormField<String>(
                  initialValue: fuel,
                  decoration: const InputDecoration(labelText: 'Combustível'),
                  items: _fuelTypes
                      .map((x) => DropdownMenuItem(value: x, child: Text(x)))
                      .toList(),
                  onChanged: saving
                      ? null
                      : (v) {
                          setState(() => fuel = v ?? 'Diesel');
                          _auditFieldV87('fuel_type', fuel, immediate: true);
                        }),
              const SizedBox(height: 8),
              TextField(
                  controller: liters,
                  enabled: !saving,
                  keyboardType:
                      const TextInputType.numberWithOptions(decimal: true),
                  onChanged: (_) {
                    if (mounted) setState(() {});
                  },
                  decoration:
                      const InputDecoration(labelText: 'Quantidade (L) *')),
              if (financial) ...[
                const SizedBox(height: 8),
                TextField(
                    controller: sale,
                    enabled: !saving,
                    keyboardType:
                        const TextInputType.numberWithOptions(decimal: true),
                    onChanged: (_) => setState(() {}),
                    decoration:
                        const InputDecoration(labelText: 'Preço por litro *')),
                const SizedBox(height: 6),
                InputDecorator(
                    decoration: const InputDecoration(
                        labelText:
                            'Preço total • automático e somente leitura'),
                    child: Text(
                        _fmtMoney(_num(liters.text.replaceAll(',', '.')) *
                            _num(sale.text.replaceAll(',', '.'))),
                        style: const TextStyle(fontWeight: FontWeight.w900)))
              ],
              const SizedBox(height: 10),
              if (manualThird)
                Row(children: [
                  Expanded(
                      child: TextField(
                          controller: km,
                          enabled: !saving,
                          keyboardType: const TextInputType.numberWithOptions(
                              decimal: true),
                          decoration: const InputDecoration(labelText: 'KM'))),
                  const SizedBox(width: 8),
                  Expanded(
                      child: TextField(
                          controller: hour,
                          enabled: !saving,
                          keyboardType: const TextInputType.numberWithOptions(
                              decimal: true),
                          decoration:
                              const InputDecoration(labelText: 'Horímetro')))
                ])
              else if (needsKm && needsHour)
                Row(children: [
                  Expanded(
                      child: TextField(
                          controller: km,
                          enabled: !saving,
                          keyboardType: const TextInputType.numberWithOptions(
                              decimal: true),
                          decoration:
                              const InputDecoration(labelText: 'KM *'))),
                  const SizedBox(width: 8),
                  Expanded(
                      child: TextField(
                          controller: hour,
                          enabled: !saving,
                          keyboardType: const TextInputType.numberWithOptions(
                              decimal: true),
                          decoration:
                              const InputDecoration(labelText: 'Horímetro *')))
                ])
              else if (needsKm)
                TextField(
                    controller: km,
                    enabled: !saving,
                    keyboardType:
                        const TextInputType.numberWithOptions(decimal: true),
                    decoration: const InputDecoration(labelText: 'KM *'))
              else if (needsHour)
                TextField(
                    controller: hour,
                    enabled: !saving,
                    keyboardType:
                        const TextInputType.numberWithOptions(decimal: true),
                    decoration: const InputDecoration(labelText: 'Horímetro *'))
              else if (!measurementNotApplicable)
                const Text(
                    'O campo de KM ou Horímetro será definido depois que o destino for selecionado.',
                    style: TextStyle(fontSize: 12, color: Colors.black54)),
              if (manualThird)
                const Padding(
                    padding: EdgeInsets.only(top: 5),
                    child: Text(
                        'Para equipamento de terceiros preenchido manualmente, informe KM ou Horímetro conforme o equipamento.',
                        style: TextStyle(fontSize: 12, color: Colors.black54)))
              else if (kinds.isNotEmpty)
                const Padding(
                    padding: EdgeInsets.only(top: 5),
                    child: Text(
                        'O sistema solicita a medição configurada no cadastro do ativo.',
                        style: TextStyle(fontSize: 12, color: Colors.black54))),
              const SizedBox(height: 10),
              TextField(
                  controller: receiver,
                  enabled: !saving,
                  decoration: const InputDecoration(
                      labelText:
                          'Responsável pelo recebimento do abastecimento *')),
              const SizedBox(height: 10),
              TextField(
                  controller: observation,
                  enabled: !saving,
                  maxLines: 3,
                  textCapitalization: TextCapitalization.sentences,
                  decoration: const InputDecoration(labelText: 'Observação')),
              const SizedBox(height: 10),
              if (manualLocationV44)
                TextField(
                    controller: location,
                    enabled: !saving,
                    maxLines: 2,
                    textCapitalization: TextCapitalization.words,
                    decoration: InputDecoration(
                        labelText: 'Localização do abastecimento *',
                        prefixIcon: const Icon(Icons.location_on_outlined),
                        helperText: capturedPosition != null
                            ? 'GPS capturado. Informe apenas o endereço manualmente.'
                            : 'Localização automática indisponível. Informe o endereço manualmente.'))
              else
                GestureDetector(
                  onTap: (saving || locating || location.text.trim().isNotEmpty)
                      ? null
                      : () => attemptLocationV52(),
                  child: InputDecorator(
                    decoration: const InputDecoration(
                        labelText: 'Localização do abastecimento',
                        prefixIcon: Icon(Icons.location_on_outlined)),
                    child: Text(
                      locating
                          ? 'Buscando localização...'
                          : location.text.trim().isNotEmpty
                              ? location.text.trim()
                              : locationAttemptsV52 == 1
                                  ? 'Toque para tentar buscar a localização novamente.'
                                  : 'Buscando localização automaticamente...',
                      softWrap: true,
                    ),
                  ),
                ),
              const SizedBox(height: 12),
              SwitchListTile.adaptive(
                  contentPadding: EdgeInsets.zero,
                  title: const Text('Lubrificou?',
                      style: TextStyle(fontWeight: FontWeight.w800)),
                  subtitle: Text(lubricated ? 'Sim' : 'Não'),
                  value: lubricated,
                  onChanged: saving
                      ? null
                      : (v) {
                          setState(() => lubricated = v);
                          _auditFieldV87('lubricated', v, immediate: true);
                        }),
              const SizedBox(height: 4),
              if (kinds.isNotEmpty || manualThird)
                OutlinedButton(
                    onPressed: saving
                        ? null
                        : () async {
                            final x = await cam();
                            if (x != null) {
                              setState(() => meter = x);
                              unawaited(_auditEvidenceV87('meter', x));
                            }
                          },
                    child: Text(meter == null
                        ? metricPhotoLabel(kinds)
                        : 'Medição registrada ✓')),
              OutlinedButton(
                  onPressed: saving
                      ? null
                      : () async {
                          final x = await cam();
                          if (x != null) {
                            setState(() => identity = x);
                            unawaited(_auditEvidenceV87('identity', x));
                          }
                        },
                  child: Text(identity == null
                      ? 'Foto da placa ou identificação *'
                      : 'Foto da placa ou identificação ✓')),
              OutlinedButton(
                  onPressed: saving
                      ? null
                      : () async {
                          final x = await cam();
                          if (x != null) {
                            setState(() => extra = x);
                            unawaited(_auditEvidenceV87('extra', x));
                          }
                        },
                  child: Text(extra == null
                      ? '4ª foto (opcional)'
                      : '4ª foto registrada ✓')),
              OutlinedButton(
                  onPressed: saving
                      ? null
                      : () async {
                          final x = await sign(
                              'Assinatura do responsável pelo recebimento');
                          if (x != null) {
                            setState(() => rs = x);
                            unawaited(_auditSignatureV87('receiver', x));
                          }
                        },
                  child: Text(rs == null
                      ? 'Assinatura do responsável pelo recebimento *'
                      : 'Assinatura do responsável pelo recebimento ✓')),
              OutlinedButton(
                  onPressed: saving
                      ? null
                      : () async {
                          final x = await sign('Assinatura de quem abasteceu');
                          if (x != null) {
                            setState(() => os = x);
                            unawaited(_auditSignatureV87('operator', x));
                          }
                        },
                  child: Text(os == null
                      ? 'Assinatura de quem abasteceu *'
                      : 'Assinatura de quem abasteceu ✓')),
              const SizedBox(height: 12),
              FilledButton.icon(
                  onPressed: saving || locating ? null : () => submit(hasPlate),
                  icon: (saving || locating)
                      ? const SizedBox(
                          width: 18,
                          height: 18,
                          child: CircularProgressIndicator(strokeWidth: 2))
                      : const Icon(Icons.check_rounded),
                  label: Text(locating
                      ? 'Capturando localização atual...'
                      : saving
                          ? savingStep
                          : 'Concluir abastecimento')),
              if (saving)
                const Padding(
                    padding: EdgeInsets.only(top: 8),
                    child: Text(
                        'Não feche esta tela. O app está concluindo o registro.',
                        textAlign: TextAlign.center,
                        style: TextStyle(fontSize: 12, color: Colors.black54)))
            ])));
  }
}

class FuelDashboardV23Screen extends StatefulWidget {
  final Map<String, dynamic> profile, ref;
  const FuelDashboardV23Screen(
      {super.key, required this.profile, required this.ref});
  @override
  State<FuelDashboardV23Screen> createState() => _FuelDashboardV23ScreenState();
}

class _FuelDashboardV23ScreenState extends State<FuelDashboardV23Screen> {
  Map<String, dynamic>? d;
  @override
  void initState() {
    super.initState();
    load();
  }

  Future<void> load() async {
    try {
      final x = await api.dashboardV22();
      if (mounted) setState(() => d = x);
    } catch (e) {
      if (mounted)
        ScaffoldMessenger.of(context)
            .showSnackBar(SnackBar(content: Text(_friendlyError(e))));
    }
  }

  Widget tile(String a, String b) => Card(
      child: ListTile(
          title: Text(a),
          trailing:
              Text(b, style: const TextStyle(fontWeight: FontWeight.w900))));
  @override
  Widget build(BuildContext c) {
    final x = d;
    return Scaffold(
        appBar: AppBar(title: const Text('Painel de combustível')),
        body: x == null
            ? const Center(child: CircularProgressIndicator())
            : ListView(padding: const EdgeInsets.all(16), children: [
                tile('Estoque atual', _fmtLiters(x['stock_liters'])),
                tile('Consumo médio/dia',
                    _fmtLiters(x['daily_consumption_liters'])),
                tile(
                    'Autonomia',
                    x['autonomy_days'] == null
                        ? '-'
                        : '${_num(x['autonomy_days']).toStringAsFixed(1)} dias'),
                tile('Previsão de término',
                    '${x['estimated_depletion_date'] ?? '-'}'),
                tile('Total de NFs', _fmtLiters(x['total_nf_liters'])),
                tile('Total abastecido', _fmtLiters(x['total_fueled_liters'])),
                if (x['financial_visible'] == true) ...[
                  tile('Custo médio de compra/L',
                      _fmtMoney(x['weighted_purchase_cost_per_liter'])),
                  tile('Média de venda/L',
                      _fmtMoney(x['weighted_sale_price_per_liter'])),
                  tile('Lucro total', _fmtMoney(x['total_profit']))
                ],
                const SizedBox(height: 10),
                HomeActionCard(
                    icon: Icons.description_outlined,
                    title: 'Relatório diário',
                    subtitle: 'Resumo completo do combustível em PDF',
                    onTap: () => Navigator.push(
                        c,
                        MaterialPageRoute(
                            builder: (_) => const DailyFuelV23Screen()))),
                const SizedBox(height: 10),
                HomeActionCard(
                    icon: Icons.route_outlined,
                    title: 'Rastrear NF',
                    subtitle: 'Veja onde está e para onde foi cada litro',
                    onTap: () => Navigator.push(
                        c,
                        MaterialPageRoute(
                            builder: (_) => NfTraceV23Screen(ref: widget.ref))))
              ]));
  }
}

class DailyFuelV23Screen extends StatefulWidget {
  const DailyFuelV23Screen({super.key});
  @override
  State<DailyFuelV23Screen> createState() => _DailyFuelV23ScreenState();
}

class _DailyFuelV23ScreenState extends State<DailyFuelV23Screen> {
  Map<String, dynamic>? d;
  DateTime date = DateTime.now();
  @override
  void initState() {
    super.initState();
    load();
  }

  Future<void> load() async {
    final x = await api.dailyFuelV22(date);
    if (mounted) setState(() => d = x);
  }

  @override
  Widget build(BuildContext c) {
    final x = d, s = _map(x?['summary']);
    return Scaffold(
        appBar: AppBar(title: const Text('Relatório diário')),
        body: x == null
            ? const Center(child: CircularProgressIndicator())
            : ListView(padding: const EdgeInsets.all(16), children: [
                ListTile(
                    title: const Text('Entradas por NF'),
                    trailing: Text(_fmtLiters(s['nf_liters']))),
                ListTile(
                    title: const Text('Transferências'),
                    trailing: Text(_fmtLiters(s['transfer_liters']))),
                ListTile(
                    title: const Text('Abastecimentos'),
                    trailing: Text(
                        '${s['fueling_count']} • ${_fmtLiters(s['fueling_liters'])}')),
                ListTile(
                    title: const Text('Estoque final'),
                    trailing: Text(_fmtLiters(s['closing_stock_liters']))),
                if (x['financial_visible'] == true)
                  ListTile(
                      title: const Text('Lucro do dia'),
                      trailing: Text(_fmtMoney(s['profit_total']))),
                ..._rows(x['movements']).map((m) => Card(
                    child: ListTile(
                        title: Text(
                            '${_movementLabel('${m['type']}')} • ${_fmtLiters(m['liters'])}'),
                        subtitle: Text(
                            '${_fmtDate(m['created_at'])} • ${m['source'] ?? ''}${m['destination'] != null ? ' → ${m['destination']}' : ''}'))))
              ]));
  }
}

class NfTraceV23Screen extends StatefulWidget {
  final Map<String, dynamic> ref;
  const NfTraceV23Screen({super.key, required this.ref});
  @override
  State<NfTraceV23Screen> createState() => _NfTraceV23ScreenState();
}

class _NfTraceV23ScreenState extends State<NfTraceV23Screen> {
  List<Map<String, dynamic>>? lots;
  int? id;
  Map<String, dynamic>? data;
  bool loading = false;
  final search = TextEditingController();
  @override
  void initState() {
    super.initState();
    loadLots();
  }

  @override
  void dispose() {
    search.dispose();
    super.dispose();
  }

  Future<void> loadLots() async {
    setState(() => loading = true);
    try {
      final x = await api.lotsCatalogV23();
      if (mounted) setState(() => lots = x);
    } catch (e) {
      if (mounted)
        ScaffoldMessenger.of(context)
            .showSnackBar(SnackBar(content: Text(_friendlyError(e))));
    } finally {
      if (mounted) setState(() => loading = false);
    }
  }

  Future<void> trace(int value) async {
    setState(() => loading = true);
    try {
      final x = await api.traceV23(value);
      if (mounted)
        setState(() {
          id = value;
          data = x;
        });
    } catch (e) {
      if (mounted)
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(
            content: Text('Erro ao rastrear NF: ${_friendlyError(e)}')));
    } finally {
      if (mounted) setState(() => loading = false);
    }
  }

  @override
  Widget build(BuildContext c) {
    final q = search.text.trim().toLowerCase();
    final visible = (lots ?? const <Map<String, dynamic>>[])
        .where((x) =>
            q.isEmpty ||
            '${x['invoice_number']} ${x['supplier_name']} ${x['fuel_type']}'
                .toLowerCase()
                .contains(q))
        .toList();
    final d = data, lot = _map(d?['lot']), summary = _map(d?['summary']);
    return Scaffold(
        appBar: AppBar(title: const Text('Rastreabilidade por Nota Fiscal')),
        body: ListView(padding: const EdgeInsets.all(16), children: [
          const Card(
              child: ListTile(
                  leading: Icon(Icons.route_outlined, color: _blue),
                  title: Text('Rastreabilidade completa'),
                  subtitle: Text(
                      'Acompanhe a NF da entrada na refinaria até transferências, estoques e abastecimentos finais. NFs já esgotadas também permanecem disponíveis.'))),
          TextField(
              controller: search,
              onChanged: (_) => setState(() {}),
              decoration: const InputDecoration(
                  labelText: 'Pesquisar NF, fornecedor ou combustível',
                  prefixIcon: Icon(Icons.search_rounded))),
          const SizedBox(height: 10),
          DropdownButtonFormField<int>(
              initialValue: id,
              isExpanded: true,
              decoration:
                  const InputDecoration(labelText: 'Nota Fiscal / lote'),
              items: visible
                  .map((x) => DropdownMenuItem(
                      value: _intOrNull(x['id']),
                      child: Text(
                          'NF ${x['invoice_number']} • ${x['supplier_name'] ?? '-'} • ${x['status'] == 'exhausted' ? 'Esgotada' : _fmtLiters(x['remaining_liters'])}')))
                  .toList(),
              onChanged: loading
                  ? null
                  : (v) {
                      if (v != null) trace(v);
                    }),
          if (loading)
            const Padding(
                padding: EdgeInsets.only(top: 10),
                child: LinearProgressIndicator()),
          if (d != null) ...[
            const SizedBox(height: 14),
            Text('NF ${lot['invoice_number']}',
                style: Theme.of(c)
                    .textTheme
                    .titleLarge
                    ?.copyWith(fontWeight: FontWeight.w900)),
            Card(
                child: Column(children: [
              ListTile(
                  title: const Text('Fornecedor do combustível'),
                  subtitle: Padding(
                      padding: const EdgeInsets.only(top: 4),
                      child: Text('${lot['supplier_name'] ?? '-'}',
                          style:
                              const TextStyle(fontWeight: FontWeight.w700)))),
              ListTile(
                  title: const Text('Volume original'),
                  trailing: Text(_fmtLiters(lot['total_liters']))),
              ListTile(
                  title: const Text('Volume consumido'),
                  trailing: Text(_fmtLiters(lot['consumed_liters']))),
              ListTile(
                  title: const Text('Saldo atual da NF'),
                  trailing: Text(_fmtLiters(lot['remaining_liters']))),
              ListTile(
                  title: const Text('Recebida em'),
                  trailing: Text(_fmtDate(lot['received_at']))),
              if (lot['exhausted_at'] != null)
                ListTile(
                    title: const Text('NF esgotada em'),
                    trailing: Text(_fmtDate(lot['exhausted_at']))),
              if (lot['unit_cost'] != null)
                ListTile(
                    title: const Text('Custo de compra/L'),
                    trailing: Text(_fmtMoney(lot['unit_cost']))),
              ListTile(
                  title: const Text('Abastecimentos finais'),
                  trailing: Text(
                      '${summary['final_fueling_count'] ?? 0} • ${_fmtLiters(summary['final_fueling_liters'])}')),
              if (summary['profit_total'] != null)
                ListTile(
                    title: const Text('Lucro total associado'),
                    trailing: Text(_fmtMoney(summary['profit_total']))),
            ])),
            const SizedBox(height: 10),
            const Text('Onde ainda existe saldo',
                style: TextStyle(fontSize: 17, fontWeight: FontWeight.w900)),
            if (_rows(d['positions']).isEmpty)
              const Card(
                  child: ListTile(
                      title: Text('Sem saldo em estruturas'),
                      subtitle: Text(
                          'Todo o volume desta NF já saiu do estoque ou foi consumido.'))),
            ..._rows(d['positions']).map((p) => Card(
                child: ListTile(
                    title: Text('${p['code']} • ${p['name']}'),
                    subtitle: Text('${p['tank_type']}'),
                    trailing: Text(_fmtLiters(p['remaining_liters']),
                        style: const TextStyle(fontWeight: FontWeight.w900))))),
            const SizedBox(height: 10),
            const Text('Caminho do combustível',
                style: TextStyle(fontSize: 17, fontWeight: FontWeight.w900)),
            ..._rows(d['movements']).map((m) {
              final route = [m['source'], m['destination']]
                  .where((v) => _hasValue(v))
                  .join(' → ');
              final target = m['asset_number'] ?? m['third_party'];
              return Card(
                  child: ListTile(
                      title: Text(
                          '${_movementLabel('${m['type']}')} • ${_fmtLiters(m['liters'])}',
                          style: const TextStyle(fontWeight: FontWeight.w900)),
                      subtitle: Text(
                          '${_fmtDate(m['created_at'])}${route.isNotEmpty ? '\n$route' : ''}${_hasValue(target) ? '\nEquipamento: $target' : ''}${_hasValue(m['work']) ? '\nObra: ${m['work']} • Responsável: ${m['work_responsible'] ?? '-'}' : ''}${m['unit_cost'] != null ? '\nCusto/L: ${_fmtMoney(m['unit_cost'])}' : ''}${m['sale_price_per_liter'] != null ? ' • Venda/L: ${_fmtMoney(m['sale_price_per_liter'])}' : ''}')));
            }),
          ],
        ]));
  }
}

String _permissionLabelV23(String key) {
  const labels = <String, String>{
    'movements.view': 'Visualizar registros',
    'movements.correct': 'Corrigir registros',
    'pdf.export': 'Exportar PDF',
    'nf.view': 'Visualizar Notas Fiscais',
    'nf.create': 'Cadastrar Nota Fiscal',
    'nf.edit': 'Editar/corrigir Nota Fiscal',
    'financial.view': 'Visualizar financeiro',
    'stock.view': 'Visualizar estoque',
    'autonomy.view': 'Visualizar autonomia',
    'comparisons.view': 'Comparar equipamentos',
    'reports.view': 'Visualizar relatórios',
    'reports.export': 'Exportar relatórios',
    'works.finalize': 'Finalizar obra e gerar Relatório Final',
    'fueling.create': 'Registrar abastecimentos',
    'transfer.create': 'Registrar transferências',
    'refinery.receive': 'Receber carga da refinaria',
    'refinery.unload': 'Descarregar caminhão-tanque no T.E.',
    'audit.view': 'Visualizar auditoria',
    'operators.manage': 'Gerenciar operadores',
    'units.manage': 'Gerenciar estruturas',
    'users.create': 'Cadastrar usuários',
    'users.edit': 'Editar usuários',
    'users.enable': 'Habilitar usuários',
    'users.disable': 'Desabilitar usuários',
    'users.delete': 'Excluir/remover acesso',
    'intelligence.view': 'Visualizar Intelligence',
    'intelligence.manage': 'Gerenciar Intelligence',
  };
  return labels[key] ?? key;
}

class StaffPermissionsV23Screen extends StatefulWidget {
  const StaffPermissionsV23Screen({super.key});
  @override
  State<StaffPermissionsV23Screen> createState() =>
      _StaffPermissionsV23ScreenState();
}

class _StaffPermissionsV23ScreenState extends State<StaffPermissionsV23Screen> {
  List<Map<String, dynamic>> users = [];
  List<String> keys = [];
  List<Map<String, dynamic>> defaults = [];
  bool loading = true, busy = false;
  String? error;
  @override
  void initState() {
    super.initState();
    load();
  }

  Map<String, bool> roleDefaults(String role) {
    final out = <String, bool>{for (final k in keys) k: false};
    for (final d in defaults) {
      if ('${d['role']}' == role)
        out['${d['permission_key']}'] = d['allowed'] == true;
    }
    return out;
  }

  Future<void> load() async {
    if (mounted)
      setState(() {
        loading = true;
        error = null;
      });
    try {
      final result = await Future.wait<Map<String, dynamic>>([
        api.userActionMap({'action': 'list_managers'}).timeout(
            const Duration(seconds: 15)),
        api.userActionMap({'action': 'permission_catalog'}).timeout(
            const Duration(seconds: 15)),
      ]);
      if (mounted) {
        setState(() {
          users = _rows(result[0]['users']);
          keys = (result[1]['keys'] as List? ?? []).map((e) => '$e').toList()
            ..sort();
          defaults = _rows(result[1]['defaults']);
          loading = false;
        });
      }
    } catch (e) {
      if (mounted)
        setState(() {
          loading = false;
          error = _friendlyError(e);
        });
    }
  }

  Future<void> editUser([Map<String, dynamic>? item]) async {
    final creating = item == null;
    final name = TextEditingController(text: '${item?['name'] ?? ''}');
    final username = TextEditingController(text: '${item?['username'] ?? ''}');
    final password = TextEditingController();
    String role = '${item?['role'] ?? 'supervisor'}';
    if (!['supervisor', 'manager'].contains(role)) role = 'supervisor';
    bool active = item?['active'] != false;
    Map<String, bool> permissions = creating
        ? roleDefaults(role)
        : <String, bool>{
            for (final k in keys) k: _map(item['permissions'])[k] == true
          };
    final ok = await showDialog<bool>(
        context: context,
        builder: (ctx) => StatefulBuilder(
            builder: (ctx, setD) => AlertDialog(
                  title: Text(creating
                      ? 'Cadastrar supervisor/gerente'
                      : 'Editar supervisor/gerente'),
                  content: SizedBox(
                      width: 560,
                      child: SingleChildScrollView(
                          child:
                              Column(mainAxisSize: MainAxisSize.min, children: [
                        TextField(
                            controller: name,
                            decoration:
                                const InputDecoration(labelText: 'Nome *')),
                        const SizedBox(height: 8),
                        TextField(
                            controller: username,
                            decoration: const InputDecoration(
                                labelText: 'Usuário / login *')),
                        const SizedBox(height: 8),
                        TextField(
                            controller: password,
                            obscureText: true,
                            decoration: InputDecoration(
                                labelText: creating
                                    ? 'Senha inicial *'
                                    : 'Nova senha (deixe em branco para manter)')),
                        const SizedBox(height: 8),
                        DropdownButtonFormField<String>(
                            initialValue: role,
                            decoration:
                                const InputDecoration(labelText: 'Perfil *'),
                            items: const [
                              DropdownMenuItem(
                                  value: 'supervisor',
                                  child: Text('Supervisor')),
                              DropdownMenuItem(
                                  value: 'manager', child: Text('Gerente'))
                            ],
                            onChanged: (v) {
                              if (v == null) return;
                              setD(() {
                                role = v;
                                if (creating) permissions = roleDefaults(role);
                              });
                            }),
                        SwitchListTile(
                            contentPadding: EdgeInsets.zero,
                            title: const Text('Acesso ativo'),
                            value: active,
                            onChanged: (v) => setD(() => active = v)),
                        const Divider(),
                        Row(children: [
                          Expanded(
                              child: Text('Hall de permissões',
                                  style: Theme.of(ctx)
                                      .textTheme
                                      .titleMedium
                                      ?.copyWith(fontWeight: FontWeight.w900))),
                          TextButton(
                              onPressed: () =>
                                  setD(() => permissions = roleDefaults(role)),
                              child: const Text('Usar padrão'))
                        ]),
                        ...keys.map((k) => SwitchListTile(
                            contentPadding: EdgeInsets.zero,
                            title: Text(_permissionLabelV23(k)),
                            subtitle:
                                Text(k, style: const TextStyle(fontSize: 11)),
                            value: permissions[k] == true,
                            onChanged: (v) => setD(() => permissions[k] = v))),
                      ]))),
                  actions: [
                    TextButton(
                        onPressed: () => Navigator.pop(ctx, false),
                        child: const Text('Cancelar')),
                    FilledButton(
                        onPressed: () => Navigator.pop(ctx, true),
                        child: const Text('Salvar'))
                  ],
                )));
    if (ok != true) {
      name.dispose();
      username.dispose();
      password.dispose();
      return;
    }
    if (name.text.trim().isEmpty ||
        username.text.trim().isEmpty ||
        (creating && password.text.trim().length < 4)) {
      if (mounted)
        ScaffoldMessenger.of(context).showSnackBar(const SnackBar(
            content: Text(
                'Preencha nome, usuário e uma senha inicial de pelo menos 4 caracteres.')));
      name.dispose();
      username.dispose();
      password.dispose();
      return;
    }
    setState(() => busy = true);
    try {
      String userId = '${item?['user_id'] ?? ''}';
      if (creating) {
        final r = await api.userActionMap({
          'action': 'create_manager',
          'name': name.text.trim(),
          'username': username.text.trim(),
          'password': password.text,
          'role': role
        });
        userId = '${r['user_id'] ?? ''}';
      } else {
        await api.userActionMap({
          'action': 'update_manager',
          'user_id': userId,
          'name': name.text.trim(),
          'username': username.text.trim(),
          'password': password.text,
          'role': role
        });
      }
      if (userId.isEmpty) throw Exception('Usuário salvo sem identificador.');
      for (final k in keys) {
        await api.userActionMap({
          'action': 'set_permission',
          'user_id': userId,
          'permission_key': k,
          'allowed': permissions[k] == true
        });
      }
      final oldActive = item?['active'] != false;
      if (creating && !active || !creating && active != oldActive) {
        await api.userActionMap({
          'action': 'set_manager_active',
          'user_id': userId,
          'active': active
        });
      }
      await load();
      if (mounted)
        ScaffoldMessenger.of(context).showSnackBar(const SnackBar(
            content: Text('Usuário e permissões salvos com sucesso ✓')));
    } catch (e) {
      if (mounted)
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(
            content: Text('Erro ao salvar usuário: ${_friendlyError(e)}')));
    } finally {
      if (mounted) setState(() => busy = false);
      name.dispose();
      username.dispose();
      password.dispose();
    }
  }

  Future<void> toggleActive(Map<String, dynamic> u) async {
    setState(() => busy = true);
    try {
      await api.userActionMap({
        'action': 'set_manager_active',
        'user_id': u['user_id'],
        'active': u['active'] != true
      });
      await load();
    } catch (e) {
      if (mounted)
        ScaffoldMessenger.of(context)
            .showSnackBar(SnackBar(content: Text(_friendlyError(e))));
    } finally {
      if (mounted) setState(() => busy = false);
    }
  }

  Future<void> removeUser(Map<String, dynamic> u) async {
    final ok = await showDialog<bool>(
        context: context,
        builder: (ctx) => AlertDialog(
                title: Text('Remover acesso de ${u['name']}?'),
                content: const Text(
                    'O acesso será removido, mas os registros históricos, movimentações e assinaturas serão preservados.'),
                actions: [
                  TextButton(
                      onPressed: () => Navigator.pop(ctx, false),
                      child: const Text('Cancelar')),
                  FilledButton(
                      onPressed: () => Navigator.pop(ctx, true),
                      child: const Text('Remover acesso'))
                ]));
    if (ok != true) return;
    setState(() => busy = true);
    try {
      await api
          .userActionMap({'action': 'delete_manager', 'user_id': u['user_id']});
      await load();
      if (mounted)
        ScaffoldMessenger.of(context).showSnackBar(const SnackBar(
            content: Text('Acesso removido e histórico preservado ✓')));
    } catch (e) {
      if (mounted)
        ScaffoldMessenger.of(context)
            .showSnackBar(SnackBar(content: Text(_friendlyError(e))));
    } finally {
      if (mounted) setState(() => busy = false);
    }
  }

  @override
  Widget build(BuildContext c) {
    final staff = users.where((u) => u['role'] != 'admin').toList();
    return Scaffold(
      appBar: AppBar(title: const Text('Supervisor, gerente e permissões')),
      floatingActionButton: FloatingActionButton.extended(
          onPressed: busy || loading ? null : () => editUser(),
          icon: const Icon(Icons.person_add_alt_1_rounded),
          label: const Text('Cadastrar')),
      body: loading
          ? const Center(child: CircularProgressIndicator())
          : error != null
              ? Center(
                  child: Padding(
                      padding: const EdgeInsets.all(24),
                      child: Column(mainAxisSize: MainAxisSize.min, children: [
                        const Icon(Icons.cloud_off_rounded,
                            size: 52, color: _blue),
                        const SizedBox(height: 14),
                        Text('Não foi possível carregar os usuários.\n$error',
                            textAlign: TextAlign.center),
                        const SizedBox(height: 14),
                        FilledButton.icon(
                            onPressed: load,
                            icon: const Icon(Icons.refresh_rounded),
                            label: const Text('Tentar novamente'))
                      ])))
              : RefreshIndicator(
                  onRefresh: load,
                  child: ListView(
                      padding: const EdgeInsets.fromLTRB(16, 16, 16, 90),
                      children: [
                        const Card(
                            child: ListTile(
                                leading:
                                    Icon(Icons.security_rounded, color: _blue),
                                title: Text('Hall de permissões',
                                    style:
                                        TextStyle(fontWeight: FontWeight.w900)),
                                subtitle: Text(
                                    'Cadastre Supervisor ou Gerente e escolha individualmente o que cada usuário pode visualizar ou alterar.'))),
                        if (staff.isEmpty)
                          const Padding(
                              padding: EdgeInsets.symmetric(
                                  vertical: 70, horizontal: 20),
                              child: Column(children: [
                                Icon(Icons.group_add_outlined,
                                    size: 58, color: _blue),
                                SizedBox(height: 14),
                                Text('Nenhum Supervisor ou Gerente cadastrado.',
                                    style:
                                        TextStyle(fontWeight: FontWeight.w800),
                                    textAlign: TextAlign.center),
                                SizedBox(height: 6),
                                Text(
                                    'Use o botão “Cadastrar” para criar o primeiro acesso.',
                                    textAlign: TextAlign.center)
                              ])),
                        ...staff.map((u) => Card(
                            child: ListTile(
                                contentPadding: const EdgeInsets.all(14),
                                leading: CircleAvatar(
                                    child: Icon(u['role'] == 'manager'
                                        ? Icons.manage_accounts_rounded
                                        : Icons.supervisor_account_rounded)),
                                title: Text('${u['name']}',
                                    style: const TextStyle(
                                        fontWeight: FontWeight.w900)),
                                subtitle: Text(
                                    '${u['role'] == 'manager' ? 'Gerente' : 'Supervisor'} • ${u['username'] ?? ''}\n${u['active'] == true ? 'Ativo' : 'Inativo'}'),
                                isThreeLine: true,
                                onTap: busy ? null : () => editUser(u),
                                trailing: PopupMenuButton<String>(
                                    enabled: !busy,
                                    onSelected: (v) {
                                      if (v == 'edit') editUser(u);
                                      if (v == 'active') toggleActive(u);
                                      if (v == 'delete') removeUser(u);
                                    },
                                    itemBuilder: (_) => [
                                          const PopupMenuItem(
                                              value: 'edit',
                                              child: Text(
                                                  'Editar cadastro e permissões')),
                                          PopupMenuItem(
                                              value: 'active',
                                              child: Text(u['active'] == true
                                                  ? 'Desabilitar acesso'
                                                  : 'Habilitar acesso')),
                                          const PopupMenuItem(
                                              value: 'delete',
                                              child: Text(
                                                  'Excluir / remover acesso'))
                                        ])))),
                      ])),
    );
  }
}

class RefineryEntryScreen extends StatefulWidget {
  final Map<String, dynamic> tank;
  const RefineryEntryScreen({super.key, required this.tank});

  @override
  State<RefineryEntryScreen> createState() => _RefineryEntryScreenState();
}

class _RefineryEntryScreenState extends State<RefineryEntryScreen> {
  final formKey = GlobalKey<FormState>();
  final supplier = TextEditingController();
  final document = TextEditingController();
  final batch = TextEditingController();
  final cost = TextEditingController();
  final liters = TextEditingController();
  final notes = TextEditingController();
  XFile? photo;
  bool busy = false;

  @override
  void dispose() {
    supplier.dispose();
    document.dispose();
    batch.dispose();
    cost.dispose();
    liters.dispose();
    notes.dispose();
    super.dispose();
  }

  Future<void> pickPhoto() async {
    final source = await showModalBottomSheet<ImageSource>(
      context: context,
      builder: (ctx) => SafeArea(
        child: Wrap(children: [
          ListTile(
              leading: const Icon(Icons.camera_alt_outlined),
              title: const Text('Tirar foto da nota fiscal'),
              onTap: () => Navigator.pop(ctx, ImageSource.camera)),
          ListTile(
              leading: const Icon(Icons.photo_library_outlined),
              title: const Text('Escolher foto da galeria'),
              onTap: () => Navigator.pop(ctx, ImageSource.gallery)),
        ]),
      ),
    );
    if (source == null) return;
    final x = await ImagePicker()
        .pickImage(source: source, imageQuality: 75, maxWidth: 1600);
    if (x != null && mounted) setState(() => photo = x);
  }

  Future<void> save() async {
    if (formKey.currentState?.validate() != true) return;
    if (document.text.trim().isEmpty && photo == null) {
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(
          content: Text('Informe o número da nota fiscal ou anexe uma foto.')));
      return;
    }
    setState(() => busy = true);
    try {
      final paths = <String>[];
      if (photo != null) {
        final bytes = await photo!.readAsBytes();
        paths.add(await api.uploadBytes(bytes, 'refinaria',
            mime: photo!.mimeType ?? 'image/jpeg'));
      }
      final tankId = _intOrNull(widget.tank['id']);
      if (tankId == null) throw Exception('Tanque estacionário inválido.');
      final result = await api.refineryEntry(
        tankId: tankId,
        liters: double.parse(liters.text.replaceAll(',', '.')),
        supplier: supplier.text.trim(),
        document: document.text.trim(),
        batch: batch.text.trim(),
        unitCost: cost.text.trim().isEmpty
            ? null
            : double.tryParse(cost.text.replaceAll(',', '.')),
        photos: paths,
        notes: notes.text.trim(),
      );
      if (!mounted) return;
      await showDialog<void>(
          context: context,
          builder: (_) => AlertDialog(
                title: Text(result['queued'] == true
                    ? 'Entrada salva no aparelho'
                    : 'Entrada registrada'),
                content: Text(
                    'Registro ${result['code']}\nNovo saldo: ${_fmtLiters(result['balance_after'])}'),
                actions: [
                  FilledButton(
                      onPressed: () => Navigator.pop(context),
                      child: const Text('OK'))
                ],
              ));
      if (mounted) Navigator.pop(context);
    } catch (e) {
      if (mounted)
        ScaffoldMessenger.of(context)
            .showSnackBar(SnackBar(content: Text(_friendlyError(e))));
    } finally {
      if (mounted) setState(() => busy = false);
    }
  }

  @override
  Widget build(BuildContext context) => Scaffold(
        appBar: AppBar(title: const Text('Entrada da refinaria')),
        body: Form(
          key: formKey,
          child: ListView(
            padding: const EdgeInsets.all(18),
            children: [
              Card(
                  child: ListTile(
                      title: Text(
                          '${widget.tank['code']} • ${widget.tank['name']}',
                          style: const TextStyle(fontWeight: FontWeight.w900)),
                      subtitle: Text(
                          'Saldo atual: ${_fmtLiters(widget.tank['current_balance_liters'])}'))),
              const SizedBox(height: 12),
              TextFormField(
                  controller: supplier,
                  decoration: const InputDecoration(
                      labelText: 'Refinaria / fornecedor *'),
                  validator: (v) => v == null || v.trim().isEmpty
                      ? 'Informe a origem.'
                      : null),
              const SizedBox(height: 12),
              TextFormField(
                  controller: liters,
                  keyboardType:
                      const TextInputType.numberWithOptions(decimal: true),
                  decoration: const InputDecoration(
                      labelText: 'Quantidade recebida (L) *'),
                  validator: _positiveValidator),
              const SizedBox(height: 12),
              TextField(
                  controller: document,
                  decoration:
                      const InputDecoration(labelText: 'NF / documento')),
              const SizedBox(height: 12),
              TextField(
                  controller: batch,
                  decoration: const InputDecoration(labelText: 'Lote / carga')),
              const SizedBox(height: 12),
              TextField(
                  controller: cost,
                  keyboardType:
                      const TextInputType.numberWithOptions(decimal: true),
                  decoration: const InputDecoration(
                      labelText: 'Custo por litro (opcional)')),
              const SizedBox(height: 12),
              OutlinedButton.icon(
                  onPressed: pickPhoto,
                  icon: const Icon(Icons.receipt_long_outlined),
                  label: Text(photo == null
                      ? 'Anexar foto da nota fiscal / documento'
                      : 'Nota fiscal anexada • trocar')),
              const SizedBox(height: 12),
              TextField(
                  controller: notes,
                  maxLines: 3,
                  decoration: const InputDecoration(labelText: 'Observações')),
              const SizedBox(height: 20),
              SizedBox(
                  height: 52,
                  child: FilledButton.icon(
                      onPressed: busy ? null : save,
                      icon: const Icon(Icons.save_rounded),
                      label: Text(busy ? 'Salvando...' : 'Registrar entrada'))),
            ],
          ),
        ),
      );
}

String? _positiveValidator(String? v) {
  final n = double.tryParse((v ?? '').replaceAll(',', '.'));
  return n == null || n <= 0 ? 'Informe um valor válido.' : null;
}

class TransferOnlineScreen extends StatefulWidget {
  final Map<String, dynamic> sourceTank;
  final Map<String, dynamic> referenceData;
  const TransferOnlineScreen(
      {super.key, required this.sourceTank, required this.referenceData});

  @override
  State<TransferOnlineScreen> createState() => _TransferOnlineScreenState();
}

class _TransferOnlineScreenState extends State<TransferOnlineScreen> {
  final formKey = GlobalKey<FormState>();
  int? destination;
  final liters = TextEditingController();
  final notes = TextEditingController();
  bool busy = false;
  Map<String, dynamic>? liveReferenceData;
  Timer? timer;

  @override
  void initState() {
    super.initState();
    liveReferenceData = widget.referenceData;
    refreshReference();
    timer =
        Timer.periodic(const Duration(seconds: 3), (_) => refreshReference());
  }

  Future<void> refreshReference() async {
    try {
      final value = await api.referenceData();
      final ids = _sortedFuelUnits(value['comboio_destinations'])
          .map((x) => _intOrNull(x['id']))
          .whereType<int>()
          .toSet();
      if (mounted) {
        setState(() {
          liveReferenceData = value;
          if (destination != null && !ids.contains(destination))
            destination = null;
        });
      }
    } catch (_) {}
  }

  @override
  void dispose() {
    timer?.cancel();
    liters.dispose();
    notes.dispose();
    super.dispose();
  }

  Future<void> save() async {
    if (formKey.currentState?.validate() != true || destination == null) return;
    setState(() => busy = true);
    try {
      final sourceTankId = _intOrNull(widget.sourceTank['id']);
      if (sourceTankId == null)
        throw Exception('Tanque estacionário inválido.');
      final result = await api.transfer(
        sourceTankId: sourceTankId,
        destinationTankId: destination!,
        liters: double.parse(liters.text.replaceAll(',', '.')),
        notes: notes.text.trim(),
      );
      if (!mounted) return;
      await showDialog<void>(
          context: context,
          builder: (_) => AlertDialog(
                title: Text(result['queued'] == true
                    ? 'Transferência salva no aparelho'
                    : 'Transferência registrada'),
                content: Text(
                    'Registro ${result['code']}\nSaldo do tanque: ${_fmtLiters(result['source_balance'])}\nSaldo do comboio: ${_fmtLiters(result['destination_balance'])}'),
                actions: [
                  FilledButton(
                      onPressed: () => Navigator.pop(context),
                      child: const Text('OK'))
                ],
              ));
      if (mounted) Navigator.pop(context);
    } catch (e) {
      if (mounted)
        ScaffoldMessenger.of(context)
            .showSnackBar(SnackBar(content: Text(_friendlyError(e))));
    } finally {
      if (mounted) setState(() => busy = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final destinations = _sortedFuelUnits(
        (liveReferenceData ?? widget.referenceData)['comboio_destinations']);
    return Scaffold(
      appBar: AppBar(title: const Text('Tanque → comboio')),
      body: Form(
        key: formKey,
        child: ListView(
          padding: const EdgeInsets.all(18),
          children: [
            Card(
                child: ListTile(
                    title: Text('Origem: ${widget.sourceTank['code']}',
                        style: const TextStyle(fontWeight: FontWeight.w900)),
                    subtitle: Text(
                        'Disponível: ${_fmtLiters(widget.sourceTank['current_balance_liters'])}'))),
            const SizedBox(height: 12),
            DropdownButtonFormField<int>(
              initialValue: destination,
              decoration:
                  const InputDecoration(labelText: 'Comboio de destino *'),
              items: destinations
                  .map((t) => DropdownMenuItem<int>(
                      value: _intOrNull(t['id']),
                      child: Text(
                          '${t['code']} • ${t['name']} • ${_fmtLiters(t['current_balance_liters'])}')))
                  .toList(),
              onChanged: (v) => setState(() => destination = v),
              validator: (v) => v == null ? 'Selecione o comboio.' : null,
            ),
            const SizedBox(height: 12),
            TextFormField(
                controller: liters,
                keyboardType:
                    const TextInputType.numberWithOptions(decimal: true),
                decoration: const InputDecoration(
                    labelText: 'Quantidade transferida (L) *'),
                validator: _positiveValidator),
            const SizedBox(height: 12),
            TextField(
                controller: notes,
                maxLines: 3,
                decoration: const InputDecoration(labelText: 'Observações')),
            const SizedBox(height: 20),
            SizedBox(
                height: 52,
                child: FilledButton.icon(
                    onPressed: busy ? null : save,
                    icon: const Icon(Icons.swap_horiz_rounded),
                    label: Text(
                        busy ? 'Salvando...' : 'Registrar transferência'))),
          ],
        ),
      ),
    );
  }
}

class FuelingOnlineScreen extends StatefulWidget {
  final Map<String, dynamic> sourceTank;
  final Map<String, dynamic> referenceData;
  const FuelingOnlineScreen(
      {super.key, required this.sourceTank, required this.referenceData});

  @override
  State<FuelingOnlineScreen> createState() => _FuelingOnlineScreenState();
}

class _FuelingOnlineScreenState extends State<FuelingOnlineScreen> {
  final formKey = GlobalKey<FormState>();
  bool ownAsset = true;
  int? workId;
  int? machineId;
  final assetDisplay = TextEditingController();
  final rentedIdentifier = TextEditingController();
  final company = TextEditingController();
  final description = TextEditingController();
  final liters = TextEditingController();
  final meter = TextEditingController();
  final meterObs = TextEditingController();
  final receiver = TextEditingController();
  final notes = TextEditingController();
  final locationAddress = TextEditingController();
  String fuelType = 'Diesel S10';
  Position? capturedPosition;
  bool locating = false;
  bool meterUnavailable = false;
  bool lubricated = false;
  XFile? photo;
  final List<XFile> extraFuelingPhotos = <XFile>[];
  XFile? damagePhoto;
  XFile? kmBeforePhoto;
  XFile? kmAfterPhoto;
  XFile? totalizerBeforePhoto;
  XFile? totalizerAfterPhoto;
  XFile? plateBeforePhoto;
  XFile? plateAfterPhoto;
  Uint8List? receiverSignature;
  Uint8List? operatorSignature;
  bool busy = false;

  bool get stationary => '${widget.sourceTank['tank_type']}' == 'stationary';
  bool get isGalao {
    if (!ownAsset || machineId == null) return false;
    final n = '${selectedMachine?['numeroAtivo'] ?? ''}'.trim().toLowerCase();
    return n == 'galão' || n == 'galao';
  }

  double get openingTotalizer => _num(widget.sourceTank['accounting_meter']);
  double get litersNumber =>
      double.tryParse(liters.text.trim().replaceAll(',', '.')) ?? 0;
  double get closingTotalizer => openingTotalizer + litersNumber;

  Map<String, dynamic>? get selectedMachine {
    if (machineId == null) return null;
    for (final m in _rows(widget.referenceData['machines'])) {
      if (_intOrNull(m['id']) == machineId) return m;
    }
    return null;
  }

  bool get plateApplicable {
    if (ownAsset) return '${selectedMachine?['placa'] ?? ''}'.trim().isNotEmpty;
    final compact = rentedIdentifier.text
        .toUpperCase()
        .replaceAll(RegExp(r'[^A-Z0-9]'), '');
    return RegExp(r'^[A-Z]{3}[0-9][A-Z0-9][0-9]{2}$').hasMatch(compact);
  }

  @override
  void initState() {
    super.initState();
  }

  @override
  void dispose() {
    assetDisplay.dispose();
    rentedIdentifier.dispose();
    company.dispose();
    description.dispose();
    liters.dispose();
    meter.dispose();
    meterObs.dispose();
    receiver.dispose();
    notes.dispose();
    locationAddress.dispose();
    super.dispose();
  }

  Future<XFile?> camera() => ImagePicker()
      .pickImage(source: ImageSource.camera, imageQuality: 75, maxWidth: 1600);

  Future<void> captureTotalizerBeforeLegacyV70() async {
    if (busy || totalizerBeforePhoto != null) return;
    final x = await camera();
    if (x == null || !mounted) return;
    setState(() => totalizerBeforePhoto = x);
    await loadLocation();
  }

  Future<void> pickAsset() async {
    final machines = _rows(widget.referenceData['machines']);
    final search = TextEditingController();
    String query = '';
    final picked = await showModalBottomSheet<int>(
      context: context,
      isScrollControlled: true,
      useSafeArea: true,
      builder: (ctx) => StatefulBuilder(builder: (ctx, setLocal) {
        final q = query.trim().toLowerCase();
        final filtered = machines.where((m) {
          if (q.isEmpty) return true;
          final blob = [
            m['numeroAtivo'],
            m['placa'],
            m['marca'],
            m['modelo'],
            m['tipo']
          ].where((x) => x != null).join(' ').toLowerCase();
          return blob.contains(q);
        }).toList();
        return SizedBox(
          height: MediaQuery.sizeOf(ctx).height * .82,
          child: Column(children: [
            Padding(
              padding: const EdgeInsets.fromLTRB(16, 14, 16, 10),
              child: TextField(
                controller: search,
                autofocus: true,
                decoration: const InputDecoration(
                    prefixIcon: Icon(Icons.search),
                    labelText: 'Pesquisar ativo',
                    hintText: 'Ativo, placa, marca ou modelo'),
                onChanged: (v) => setLocal(() => query = v),
              ),
            ),
            Expanded(
              child: filtered.isEmpty
                  ? const Center(child: Text('Nenhum ativo encontrado.'))
                  : ListView.separated(
                      itemCount: filtered.length,
                      separatorBuilder: (_, __) => const Divider(height: 1),
                      itemBuilder: (_, i) {
                        final m = filtered[i];
                        final id = _intOrNull(m['id']);
                        final title =
                            '${m['numeroAtivo'] ?? '-'} • ${m['marca'] ?? ''} ${m['modelo'] ?? ''}'
                                .trim();
                        final sub = [m['placa'], m['tipo']]
                            .where((x) => '${x ?? ''}'.trim().isNotEmpty)
                            .join(' • ');
                        return ListTile(
                          leading: const Icon(
                              Icons.precision_manufacturing_outlined),
                          title: Text(title,
                              style:
                                  const TextStyle(fontWeight: FontWeight.w800)),
                          subtitle: sub.isEmpty ? null : Text(sub),
                          onTap:
                              id == null ? null : () => Navigator.pop(ctx, id),
                        );
                      },
                    ),
            ),
          ]),
        );
      }),
    );
    search.dispose();
    if (picked == null || !mounted) return;
    final m = machines.firstWhere((x) => _intOrNull(x['id']) == picked);
    final selectedPlate = '${m['placa'] ?? ''}'.trim();
    setState(() {
      machineId = picked;
      assetDisplay.text =
          '${m['numeroAtivo'] ?? '-'} • ${m['marca'] ?? ''} ${m['modelo'] ?? ''}${selectedPlate.isEmpty ? '' : ' • $selectedPlate'}'
              .trim();
    });
  }

  Future<void> sign(bool receiving) async {
    final bytes = await Navigator.push<Uint8List>(
      context,
      MaterialPageRoute(
          builder: (_) => SignatureCaptureOnlineScreen(
              title: receiving
                  ? 'Assinatura de quem recebe'
                  : 'Assinatura de quem abastece'),
          fullscreenDialog: true),
    );
    if (!mounted || bytes == null) return;
    setState(() {
      if (receiving) {
        receiverSignature = bytes;
      } else {
        operatorSignature = bytes;
      }
    });
  }

  Future<Position?> currentPosition() async {
    try {
      if (!await Geolocator.isLocationServiceEnabled()) return null;
      var permission = await Geolocator.checkPermission();
      if (permission == LocationPermission.denied)
        permission = await Geolocator.requestPermission();
      if (permission == LocationPermission.denied ||
          permission == LocationPermission.deniedForever) return null;
      return await Geolocator.getCurrentPosition(
          locationSettings: const LocationSettings(
              accuracy: LocationAccuracy.high,
              timeLimit: Duration(seconds: 8)));
    } catch (_) {
      return null;
    }
  }

  String formatPlacemark(Placemark p) {
    final street = [p.street, p.subLocality]
        .where((v) => v != null && v.trim().isNotEmpty)
        .map((v) => v!.trim())
        .join(' • ');
    final city = [p.locality, p.administrativeArea]
        .where((v) => v != null && v.trim().isNotEmpty)
        .map((v) => v!.trim())
        .join(' - ');
    final tail = [city, p.postalCode]
        .where((v) => v != null && v.trim().isNotEmpty)
        .map((v) => v!.trim())
        .join(', ');
    return [street, tail].where((v) => v.trim().isNotEmpty).join(' • ');
  }

  Future<void> loadLocation() async {
    if (locating) return;
    if (mounted) setState(() => locating = true);
    try {
      final p = await currentPosition();
      if (p == null) return;
      capturedPosition = p;
      try {
        final places = await placemarkFromCoordinates(p.latitude, p.longitude);
        if (places.isNotEmpty) {
          final address = formatPlacemark(places.first);
          if (address.isNotEmpty) locationAddress.text = address;
        }
      } catch (_) {}
      if (mounted) setState(() {});
    } finally {
      if (mounted) setState(() => locating = false);
    }
  }

  Future<String?> uploadX(XFile? value, String kind) async {
    if (value == null) return null;
    return api.uploadBytes(await value.readAsBytes(), kind,
        mime: value.mimeType ?? 'image/jpeg');
  }

  Future<void> save() async {
    if (locationAddress.text.trim().isEmpty) await loadLocation();
    if (!mounted || formKey.currentState?.validate() != true) return;
    if (receiverSignature == null || operatorSignature == null) {
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(
          content: Text('As duas assinaturas são obrigatórias.')));
      return;
    }
    if (meterUnavailable && damagePhoto == null) {
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(
          content: Text('A foto do KM/horímetro danificado é obrigatória.')));
      return;
    }
    if (isGalao && photo == null) {
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(
          content: Text(
              'Para abastecer o ativo Galão, a foto do abastecimento é obrigatória.')));
      return;
    }
    if (isGalao && photo == null) {
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(
          content: Text(
              'Para abastecer o ativo Galão, a foto do abastecimento é obrigatória.')));
      return;
    }
    if (stationary) {
      if (photo == null) {
        ScaffoldMessenger.of(context).showSnackBar(const SnackBar(
            content: Text(
                'No Tanque Estacionário, a foto do abastecimento é obrigatória.')));
        return;
      }
      if (kmBeforePhoto == null) {
        ScaffoldMessenger.of(context).showSnackBar(const SnackBar(
            content: Text('Fotografe o KM/horímetro antes do abastecimento.')));
        return;
      }
      if (totalizerBeforePhoto == null || totalizerAfterPhoto == null) {
        ScaffoldMessenger.of(context).showSnackBar(const SnackBar(
            content: Text(
                'Fotografe o totalizador antes e depois do abastecimento.')));
        return;
      }
      if (plateBeforePhoto == null) {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(
            content: Text(plateApplicable
                ? 'Fotografe a placa antes do abastecimento.'
                : 'Fotografe o ativo/equipamento antes do abastecimento.')));
        return;
      }
    }

    final confirmed = await showDialog<bool>(
      context: context,
      barrierDismissible: false,
      builder: (ctx) => AlertDialog(
        title: const Text('Confirmar abastecimento'),
        content: Text(
            'Confirma que os dados estão corretos?\n\nQuantidade: ${_fmtLiters(litersNumber)}\nTotalizador: ${_fmtLiters(openingTotalizer)} → ${_fmtLiters(closingTotalizer)}'),
        actions: [
          OutlinedButton(
              onPressed: () => Navigator.pop(ctx, false),
              child: const Text('Não')),
          FilledButton(
              onPressed: () => Navigator.pop(ctx, true),
              child: const Text('Sim')),
        ],
      ),
    );
    if (confirmed != true) return;

    final position = capturedPosition ?? await currentPosition();
    if (!mounted) return;
    setState(() => busy = true);
    try {
      final generalPhotos = <String>[];
      final localFuelingPhotos = <XFile>[
        if (photo != null) photo!,
        ...extraFuelingPhotos
      ];
      for (var i = 0; i < localFuelingPhotos.length; i++) {
        final general =
            await uploadX(localFuelingPhotos[i], 'abastecimento_${i + 1}');
        if (general != null) generalPhotos.add(general);
      }
      final damage = <String>[];
      final damagePath = await uploadX(damagePhoto, 'medidor_danificado');
      if (damagePath != null) damage.add(damagePath);

      final rSig =
          await api.uploadBytes(receiverSignature!, 'assinatura_recebedor');
      final oSig =
          await api.uploadBytes(operatorSignature!, 'assinatura_abastecedor');
      final sourceTankId = _intOrNull(widget.sourceTank['id']);
      if (sourceTankId == null)
        throw Exception('Unidade de abastecimento inválida.');

      final result = await api.fueling(
        sourceTankId: sourceTankId,
        workId: workId,
        machineId: ownAsset ? machineId : null,
        thirdPartyPlate: ownAsset ? null : rentedIdentifier.text.trim(),
        thirdPartyCompany: ownAsset ? null : company.text.trim(),
        thirdPartyDescription: ownAsset ? null : description.text.trim(),
        liters: litersNumber,
        meter: meterUnavailable
            ? null
            : double.tryParse(meter.text.replaceAll(',', '.')),
        meterUnavailable: meterUnavailable,
        meterObservation: meterObs.text.trim(),
        meterDamagePhotos: damage,
        receiverName: receiver.text.trim(),
        receiverCompany: null,
        receiverSignature: rSig,
        operatorSignature: oSig,
        photos: generalPhotos,
        notes: notes.text.trim(),
        lubricated: lubricated,
        latitude: position?.latitude,
        longitude: position?.longitude,
        kmPhotoBefore: await uploadX(kmBeforePhoto, 'km_antes'),
        kmPhotoAfter: null,
        totalizerPhotoBefore:
            await uploadX(totalizerBeforePhoto, 'totalizador_antes'),
        totalizerPhotoAfter:
            await uploadX(totalizerAfterPhoto, 'totalizador_depois'),
        platePhotoBefore: await uploadX(plateBeforePhoto, 'placa_antes'),
        platePhotoAfter: null,
        fuelType: fuelType,
        locationAddress: locationAddress.text.trim(),
      );
      if (!mounted) return;
      final before = result['opening_meter'] ?? openingTotalizer;
      final after = result['closing_meter'] ?? closingTotalizer;
      await showDialog<void>(
        context: context,
        builder: (_) => AlertDialog(
          title: Text(result['queued'] == true
              ? 'Abastecimento salvo no aparelho'
              : 'Abastecimento bem sucedido'),
          content: Text(
              'Número ${result['code']}\nQuantidade: ${_fmtLiters(result['liters'] ?? litersNumber)}\nTotalizador: ${_fmtLiters(before)} → ${_fmtLiters(after)}\nSaldo restante: ${_fmtLiters(result['balance_after'])}'),
          actions: [
            FilledButton(
                onPressed: () => Navigator.pop(context),
                child: const Text('OK'))
          ],
        ),
      );
      if (mounted) Navigator.pop(context);
    } catch (e) {
      if (mounted)
        ScaffoldMessenger.of(context)
            .showSnackBar(SnackBar(content: Text(_friendlyError(e))));
    } finally {
      if (mounted) setState(() => busy = false);
    }
  }

  int get fuelingPhotoCount =>
      (photo == null ? 0 : 1) + extraFuelingPhotos.length;

  List<XFile> get fuelingPhotoFiles => <XFile>[
        if (photo != null) photo!,
        ...extraFuelingPhotos,
      ];

  Future<void> addFuelingPhoto() async {
    if (fuelingPhotoCount >= 4) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
              content: Text(
                  'É possível registrar no máximo 4 fotos do abastecimento.')),
        );
      }
      return;
    }
    final x = await camera();
    if (x == null || !mounted) return;
    setState(() {
      if (photo == null) {
        photo = x;
      } else {
        extraFuelingPhotos.add(x);
      }
    });
  }

  void removeFuelingPhoto(int index) {
    final files = fuelingPhotoFiles;
    if (index < 0 || index >= files.length) return;
    files.removeAt(index);
    setState(() {
      photo = files.isEmpty ? null : files.first;
      extraFuelingPhotos
        ..clear()
        ..addAll(files.skip(1));
    });
  }

  Widget fuelingPhotosBlock({required bool required}) {
    final files = fuelingPhotoFiles;
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        OutlinedButton.icon(
          onPressed: busy || files.length >= 4 ? null : addFuelingPhoto,
          icon: const Icon(Icons.add_a_photo_outlined),
          label: Text(
            files.isEmpty
                ? 'Fotos do abastecimento${required ? ' *' : ''} (0/4)'
                : 'Adicionar foto do abastecimento (${files.length}/4)',
          ),
        ),
        if (files.isNotEmpty) ...[
          const SizedBox(height: 8),
          Wrap(
            spacing: 8,
            runSpacing: 8,
            children: List.generate(
                files.length,
                (i) => Chip(
                      avatar: const Icon(Icons.photo_outlined, size: 18),
                      label: Text('Foto ${i + 1} ✓'),
                      onDeleted: busy ? null : () => removeFuelingPhoto(i),
                    )),
          ),
        ],
        if (required && files.isEmpty) ...[
          const SizedBox(height: 6),
          const Text('Pelo menos 1 foto é obrigatória.',
              style: TextStyle(fontSize: 12, color: Colors.redAccent)),
        ],
      ],
    );
  }

  Widget photoButton(String label, XFile? value, void Function(XFile) setter,
      {bool required = false}) {
    return OutlinedButton.icon(
      onPressed: busy
          ? null
          : () async {
              final x = await camera();
              if (x != null && mounted) setState(() => setter(x));
            },
      icon: const Icon(Icons.camera_alt_outlined),
      label: Text(value == null ? '$label${required ? ' *' : ''}' : '$label ✓'),
    );
  }

  @override
  Widget build(BuildContext context) {
    final works = _rows(widget.referenceData['works']);
    final workRequired = widget.sourceTank['tank_type'] == 'comboio';
    final who =
        '${Supabase.instance.client.auth.currentUser?.userMetadata?['display_name'] ?? 'Motorista'}';
    if (totalizerBeforePhoto == null) {
      return Scaffold(
        appBar: AppBar(title: const Text('Novo abastecimento')),
        body: SafeArea(
          child: ListView(
            padding: const EdgeInsets.fromLTRB(20, 28, 20, 28),
            children: [
              const Icon(Icons.photo_camera_back_rounded,
                  size: 64, color: _blue),
              const SizedBox(height: 18),
              const Text('Foto obrigatória antes de iniciar',
                  textAlign: TextAlign.center,
                  style: TextStyle(fontSize: 22, fontWeight: FontWeight.w900)),
              const SizedBox(height: 20),
              Card(
                  child: ListTile(
                leading: const Icon(Icons.local_gas_station_rounded),
                title: Text(
                    '${widget.sourceTank['code']} • ${widget.sourceTank['name']}',
                    style: const TextStyle(fontWeight: FontWeight.w900)),
                subtitle: Text(
                    'Saldo: ${_fmtLiters(widget.sourceTank['current_balance_liters'])}'),
              )),
              const SizedBox(height: 22),
              SizedBox(
                  height: 54,
                  child: FilledButton.icon(
                      onPressed: busy ? null : captureTotalizerBeforeLegacyV70,
                      icon: const Icon(Icons.camera_alt_rounded),
                      label: const Text(
                          'Tirar foto do totalizador antes do abastecimento'))),
              const SizedBox(height: 10),
              TextButton(
                  onPressed: busy ? null : () => Navigator.maybePop(context),
                  child: const Text('Cancelar')),
            ],
          ),
        ),
      );
    }
    return Scaffold(
      appBar: AppBar(title: const Text('Novo abastecimento')),
      body: Form(
        key: formKey,
        child: ListView(
          padding: const EdgeInsets.fromLTRB(18, 18, 18, 120),
          children: [
            Card(
                child: ListTile(
              title: Text(
                  '${widget.sourceTank['code']} • ${widget.sourceTank['name']}',
                  style: const TextStyle(fontWeight: FontWeight.w900)),
              subtitle: Text(
                  'Saldo: ${_fmtLiters(widget.sourceTank['current_balance_liters'])}'),
            )),
            const SizedBox(height: 10),
            const Card(
                child: ListTile(
              leading: Icon(Icons.verified_rounded, color: Colors.green),
              title: Text('Totalizador antes do abastecimento registrado ✓',
                  style: TextStyle(fontWeight: FontWeight.w900)),
              subtitle: Text(
                  'Foto capturada antes do início. Ela será preservada no registro e no PDF.'),
            )),
            const SizedBox(height: 12),
            DropdownButtonFormField<int>(
              initialValue: workId,
              decoration: InputDecoration(
                  labelText: workRequired ? 'Obra *' : 'Obra (opcional)'),
              items: works
                  .map((w) => DropdownMenuItem<int>(
                      value: _intOrNull(w['id']), child: Text('${w['name']}')))
                  .toList(),
              onChanged: (v) => setState(() => workId = v),
              validator: (v) => workRequired && v == null
                  ? 'Selecione a obra. O administrador pode cadastrá-la.'
                  : null,
            ),
            const SizedBox(height: 12),
            SegmentedButton<bool>(
              segments: const [
                ButtonSegment(value: true, label: Text('Ativo próprio')),
                ButtonSegment(value: false, label: Text('Alugado')),
              ],
              selected: {ownAsset},
              onSelectionChanged: (v) => setState(() {
                ownAsset = v.first;
                machineId = null;
                assetDisplay.clear();
                plateBeforePhoto = null;
                plateAfterPhoto = null;
              }),
            ),
            const SizedBox(height: 12),
            if (ownAsset)
              TextFormField(
                controller: assetDisplay,
                readOnly: true,
                onTap: busy ? null : pickAsset,
                decoration: const InputDecoration(
                    labelText: 'Ativo *',
                    prefixIcon: Icon(Icons.search),
                    suffixIcon: Icon(Icons.arrow_drop_down)),
                validator: (_) =>
                    ownAsset && machineId == null ? 'Selecione o ativo.' : null,
              )
            else ...[
              TextFormField(
                controller: rentedIdentifier,
                textCapitalization: TextCapitalization.sentences,
                decoration: const InputDecoration(
                  labelText: 'Identificação do equipamento alugado *',
                  hintText: 'Ex.: Retroescavadeira New Holland B110B',
                ),
                validator: (v) => !ownAsset && (v == null || v.trim().isEmpty)
                    ? 'Identifique o equipamento alugado.'
                    : null,
                onChanged: (_) => setState(() {
                  plateBeforePhoto = null;
                  plateAfterPhoto = null;
                }),
              ),
              const SizedBox(height: 12),
              TextField(
                  controller: company,
                  decoration:
                      const InputDecoration(labelText: 'Empresa / locadora')),
              const SizedBox(height: 12),
              TextField(
                  controller: description,
                  decoration: const InputDecoration(
                      labelText: 'Descrição complementar (opcional)')),
            ],
            const SizedBox(height: 12),
            TextFormField(
              controller: liters,
              keyboardType:
                  const TextInputType.numberWithOptions(decimal: true),
              decoration:
                  const InputDecoration(labelText: 'Litros abastecidos *'),
              validator: _positiveValidator,
              onChanged: (_) => setState(() {}),
            ),
            const SizedBox(height: 12),
            Container(
              padding: const EdgeInsets.all(14),
              decoration: BoxDecoration(
                  color: const Color(0xFFFFF1F2),
                  borderRadius: BorderRadius.circular(14),
                  border: Border.all(color: const Color(0xFFF4B8BE))),
              child: Row(children: [
                const Expanded(
                    child: Text('Totalizador',
                        style: TextStyle(fontWeight: FontWeight.w900))),
                Text(
                    '${_fmtLiters(openingTotalizer)} → ${_fmtLiters(closingTotalizer)}',
                    style: const TextStyle(
                        color: Color(0xFFD51F2A), fontWeight: FontWeight.w900)),
              ]),
            ),
            const SizedBox(height: 8),
            SwitchListTile.adaptive(
              contentPadding: EdgeInsets.zero,
              title: const Text('Lubrificou?'),
              subtitle: const Text(
                  'Ative quando o equipamento também for lubrificado neste atendimento.'),
              value: lubricated,
              onChanged: busy ? null : (v) => setState(() => lubricated = v),
            ),
            SwitchListTile.adaptive(
              contentPadding: EdgeInsets.zero,
              title: const Text('KM / horímetro danificado ou indisponível'),
              value: meterUnavailable,
              onChanged:
                  busy ? null : (v) => setState(() => meterUnavailable = v),
            ),
            if (!meterUnavailable)
              TextFormField(
                controller: meter,
                keyboardType:
                    const TextInputType.numberWithOptions(decimal: true),
                decoration:
                    const InputDecoration(labelText: 'KM / horímetro *'),
                validator: (v) => !meterUnavailable &&
                        double.tryParse((v ?? '').replaceAll(',', '.')) == null
                    ? 'Informe a leitura.'
                    : null,
              )
            else ...[
              TextFormField(
                  controller: meterObs,
                  decoration: const InputDecoration(
                      labelText: 'Observação sobre o medidor *'),
                  validator: (v) =>
                      meterUnavailable && (v == null || v.trim().isEmpty)
                          ? 'Informe a observação.'
                          : null),
              const SizedBox(height: 10),
              photoButton('Foto do medidor danificado', damagePhoto,
                  (x) => damagePhoto = x,
                  required: true),
            ],
            const SizedBox(height: 12),
            DropdownButtonFormField<String>(
              initialValue: fuelType,
              isExpanded: true,
              decoration:
                  const InputDecoration(labelText: 'Tipo de combustível *'),
              items: _fuelTypes
                  .map(
                      (v) => DropdownMenuItem<String>(value: v, child: Text(v)))
                  .toList(),
              onChanged: busy
                  ? null
                  : (v) {
                      if (v != null) setState(() => fuelType = v);
                    },
            ),
            const SizedBox(height: 12),
            TextFormField(
                controller: receiver,
                decoration: const InputDecoration(
                    labelText:
                        'Responsável pelo recebimento do abastecimento *'),
                validator: (v) => v == null || v.trim().isEmpty
                    ? 'Informe o responsável pelo recebimento do abastecimento.'
                    : null),
            const SizedBox(height: 12),
            InputDecorator(
                decoration: const InputDecoration(labelText: 'Quem abasteceu'),
                child: Text(who,
                    style: const TextStyle(fontWeight: FontWeight.w700))),
            const SizedBox(height: 12),
            TextFormField(
              controller: locationAddress,
              minLines: 1,
              maxLines: 3,
              decoration: InputDecoration(
                labelText: 'Localização *',
                prefixIcon: const Icon(Icons.location_on_outlined),
                suffixIcon: IconButton(
                    onPressed: busy || locating ? null : loadLocation,
                    icon: locating
                        ? const SizedBox(
                            width: 20,
                            height: 20,
                            child: CircularProgressIndicator(strokeWidth: 2))
                        : const Icon(Icons.my_location_rounded)),
                helperText: capturedPosition == null
                    ? 'Informe o endereço completo.'
                    : 'Coordenadas: ${capturedPosition!.latitude.toStringAsFixed(6)}, ${capturedPosition!.longitude.toStringAsFixed(6)}',
              ),
              validator: (v) => v == null || v.trim().isEmpty
                  ? 'Informe o endereço completo da localização.'
                  : null,
            ),
            const SizedBox(height: 12),
            OutlinedButton.icon(
                onPressed: busy ? null : () => sign(true),
                icon: const Icon(Icons.draw_outlined),
                label: Text(receiverSignature == null
                    ? 'Assinatura de quem recebe *'
                    : 'Assinatura de quem recebe ✓')),
            const SizedBox(height: 10),
            OutlinedButton.icon(
                onPressed: busy ? null : () => sign(false),
                icon: const Icon(Icons.draw_outlined),
                label: Text(operatorSignature == null
                    ? 'Assinatura de quem abastece *'
                    : 'Assinatura de quem abastece ✓')),
            const SizedBox(height: 10),
            fuelingPhotosBlock(required: stationary || isGalao),
            if (stationary) ...[
              const SizedBox(height: 18),
              const Text('Registro fotográfico antes e depois',
                  style: TextStyle(fontSize: 17, fontWeight: FontWeight.w900)),
              const SizedBox(height: 4),
              const Text(
                  'Tanque Estacionário: totalizador antes/depois, KM/horímetro antes e placa ou ativo antes.',
                  style: TextStyle(color: Colors.black54)),
              const SizedBox(height: 10),
              photoButton('KM / horímetro antes', kmBeforePhoto,
                  (x) => kmBeforePhoto = x,
                  required: true),
              const SizedBox(height: 8),
              photoButton('Totalizador depois', totalizerAfterPhoto,
                  (x) => totalizerAfterPhoto = x,
                  required: true),
              const SizedBox(height: 8),
              photoButton(
                  plateApplicable
                      ? 'Foto da placa antes'
                      : 'Foto do ativo/equipamento antes',
                  plateBeforePhoto,
                  (x) => plateBeforePhoto = x,
                  required: true),
            ],
            const SizedBox(height: 12),
            TextField(
                controller: notes,
                maxLines: 3,
                decoration: const InputDecoration(labelText: 'Observações')),
            const SizedBox(height: 20),
            SizedBox(
                height: 52,
                child: FilledButton.icon(
                    onPressed: busy ? null : save,
                    icon: const Icon(Icons.save_rounded),
                    label: Text(
                        busy ? 'Salvando...' : 'Registrar abastecimento'))),
          ],
        ),
      ),
    );
  }
}

class SignatureCaptureOnlineScreen extends StatefulWidget {
  final String title;
  const SignatureCaptureOnlineScreen({super.key, required this.title});

  @override
  State<SignatureCaptureOnlineScreen> createState() =>
      _SignatureCaptureOnlineScreenState();
}

class _SignatureCaptureOnlineScreenState
    extends State<SignatureCaptureOnlineScreen> {
  final points = <Offset?>[];
  final boundaryKey = GlobalKey();
  bool get valid => points.whereType<Offset>().length >= 4;

  @override
  void initState() {
    super.initState();
    SystemChrome.setPreferredOrientations(
        [DeviceOrientation.landscapeLeft, DeviceOrientation.landscapeRight]);
  }

  @override
  void dispose() {
    SystemChrome.setPreferredOrientations([DeviceOrientation.portraitUp]);
    super.dispose();
  }

  Future<void> save() async {
    if (!valid) {
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(
          content: Text('Faça a assinatura antes de confirmar.')));
      return;
    }
    final boundary =
        boundaryKey.currentContext!.findRenderObject() as RenderRepaintBoundary;
    final image = await boundary.toImage(pixelRatio: 2.0);
    final data = await image.toByteData(format: ui.ImageByteFormat.png);
    if (mounted && data != null)
      Navigator.pop(context, data.buffer.asUint8List());
  }

  @override
  Widget build(BuildContext context) => Scaffold(
        backgroundColor: Colors.white,
        body: SafeArea(
          child: Stack(
            children: [
              Positioned.fill(
                child: RepaintBoundary(
                  key: boundaryKey,
                  child: Container(
                    color: Colors.white,
                    child: GestureDetector(
                      behavior: HitTestBehavior.opaque,
                      onPanStart: (d) =>
                          setState(() => points.add(d.localPosition)),
                      onPanUpdate: (d) =>
                          setState(() => points.add(d.localPosition)),
                      onPanEnd: (_) => setState(() => points.add(null)),
                      child: CustomPaint(painter: SignaturePainter(points)),
                    ),
                  ),
                ),
              ),
              Positioned(
                  left: 18,
                  top: 14,
                  child: Text(widget.title,
                      style: const TextStyle(fontWeight: FontWeight.w900))),
              Positioned(
                  right: 14,
                  top: 8,
                  child: IconButton(
                      onPressed: () => Navigator.pop(context),
                      icon: const Icon(Icons.close_rounded, size: 30))),
              Positioned(
                  right: 18,
                  bottom: 16,
                  child: Row(children: [
                    OutlinedButton.icon(
                        onPressed: () => setState(points.clear),
                        icon: const Icon(Icons.refresh_rounded),
                        label: const Text('Limpar')),
                    const SizedBox(width: 10),
                    FilledButton.icon(
                        onPressed: save,
                        icon: const Icon(Icons.check_rounded),
                        label: const Text('Confirmar')),
                  ])),
            ],
          ),
        ),
      );
}

class SignaturePainter extends CustomPainter {
  final List<Offset?> points;
  SignaturePainter(this.points);
  @override
  void paint(Canvas canvas, Size size) {
    final paint = Paint()
      ..color = const Color(0xFF17365D)
      ..strokeWidth = 3
      ..strokeCap = StrokeCap.round;
    for (var i = 0; i < points.length - 1; i++) {
      final a = points[i], b = points[i + 1];
      if (a != null && b != null) canvas.drawLine(a, b, paint);
    }
  }

  @override
  bool shouldRepaint(covariant SignaturePainter oldDelegate) => true;
}

const Color _comboioToComboioPale = Color(0xFFFFF3E5);

bool _isComboioToComboio(Map<String, dynamic> item) {
  if (item['comboio_to_comboio'] == true) return true;
  final sourceType = '${item['source_tank_type'] ?? ''}'.toLowerCase();
  if (sourceType != 'comboio') return false;
  final type = '${item['type'] ?? ''}';
  if (type == 'tank_transfer') {
    return '${item['destination_tank_type'] ?? ''}'.toLowerCase() == 'comboio';
  }
  if (type == 'fueling') {
    return '${item['asset_number'] ?? ''}'.trim().startsWith('008');
  }
  return false;
}

class MyOnlineMovementsScreen extends StatefulWidget {
  const MyOnlineMovementsScreen({super.key});
  @override
  State<MyOnlineMovementsScreen> createState() =>
      _MyOnlineMovementsScreenState();
}

class _MyOnlineMovementsScreenState extends State<MyOnlineMovementsScreen> {
  List<Map<String, dynamic>>? items;
  Timer? timer;
  Timer? holdTimer;
  final Set<String> selectedCodes = <String>{};
  bool busy = false;
  bool loading = false;
  bool loadRunning = false;
  bool suppressNextTap = false;
  String? loadError;

  String itemKey(Map<String, dynamic> x) => '${x['code'] ?? x['id'] ?? ''}';
  bool get selectionMode => selectedCodes.isNotEmpty;
  List<Map<String, dynamic>> get selectedItems =>
      (items ?? const <Map<String, dynamic>>[])
          .where((x) => selectedCodes.contains(itemKey(x)))
          .toList();

  @override
  void initState() {
    super.initState();
    load();
    timer = Timer.periodic(const Duration(seconds: 15), (_) {
      if (!selectionMode && !busy && !loadRunning) load(silent: true);
    });
  }

  @override
  void dispose() {
    timer?.cancel();
    holdTimer?.cancel();
    super.dispose();
  }

  Future<void> load({bool silent = false}) async {
    if (loadRunning) return;
    loadRunning = true;
    if (mounted && !silent)
      setState(() {
        loading = true;
        loadError = null;
      });
    try {
      final x =
          await api.recent(limit: 100).timeout(const Duration(seconds: 12));
      if (mounted)
        setState(() {
          items = x;
          loadError = null;
        });
    } catch (e) {
      if (mounted)
        setState(() => loadError =
            'Não foi possível carregar os registros. ${_friendlyError(e)}');
    } finally {
      loadRunning = false;
      if (mounted && !silent) setState(() => loading = false);
    }
  }

  void toggleSelected(Map<String, dynamic> x) {
    final key = itemKey(x);
    if (key.isEmpty) return;
    setState(() {
      if (!selectedCodes.add(key)) selectedCodes.remove(key);
    });
  }

  void beginHold(Map<String, dynamic> x) {
    holdTimer?.cancel();
    suppressNextTap = false;
    holdTimer = Timer(const Duration(seconds: 1), () {
      if (!mounted) return;
      suppressNextTap = true;
      toggleSelected(x);
    });
  }

  void cancelHold() {
    holdTimer?.cancel();
    holdTimer = null;
  }

  void clearSelection() => setState(() {
        selectedCodes.clear();
        suppressNextTap = false;
      });
  void openOrSelect(Map<String, dynamic> x) {
    if (suppressNextTap) {
      suppressNextTap = false;
      return;
    }
    if (selectionMode) {
      toggleSelected(x);
      return;
    }
    Navigator.push(context,
        MaterialPageRoute(builder: (_) => MovementDetailScreen(item: x)));
  }

  Future<void> exportPdf() async {
    final targets = selectedItems;
    if (targets.isEmpty) return;
    setState(() => busy = true);
    try {
      if (mounted)
        await Navigator.push(
            context,
            MaterialPageRoute(
                builder: (_) => OfficialPdfPreviewV28Screen(
                    items: targets,
                    title: 'Prévia • ${targets.length} registro(s)')));
      if (mounted) clearSelection();
    } catch (e) {
      if (mounted)
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(
            content: Text('Falha ao gerar PDF: ${_friendlyError(e)}')));
    } finally {
      if (mounted) setState(() => busy = false);
    }
  }

  Widget recordList() {
    final list = items ?? const <Map<String, dynamic>>[];
    return RefreshIndicator(
        onRefresh: () => load(),
        child: ListView(
            padding: const EdgeInsets.fromLTRB(16, 8, 16, 60),
            children: [
              if (loadError != null)
                Card(
                    child: ListTile(
                        leading: const Icon(Icons.warning_amber_rounded,
                            color: _blue),
                        title: const Text('Não foi possível atualizar agora.'),
                        subtitle: Text(loadError!),
                        trailing: IconButton(
                            onPressed: () => load(),
                            icon: const Icon(Icons.refresh_rounded)))),
              if (loading) const LinearProgressIndicator(minHeight: 2),
              if (list.isEmpty)
                const Padding(
                    padding: EdgeInsets.only(top: 160),
                    child: Center(child: Text('Nenhum registro ainda.'))),
              ...list.map((x) {
                final asset = x['asset_number'] ??
                    x['third_party_plate'] ??
                    x['destination_tank'] ??
                    x['source_tank'] ??
                    '-';
                final selected = selectedCodes.contains(itemKey(x));
                final comboioToComboio = _isComboioToComboio(x);
                return GestureDetector(
                    behavior: HitTestBehavior.opaque,
                    onTapDown: (_) => beginHold(x),
                    onTapUp: (_) => cancelHold(),
                    onTapCancel: cancelHold,
                    onTap: () => openOrSelect(x),
                    child: Card(
                        color: comboioToComboio ? _comboioToComboioPale : null,
                        shape: RoundedRectangleBorder(
                            borderRadius: BorderRadius.circular(18),
                            side: BorderSide(
                                color:
                                    selected ? _blue : const Color(0xFFE2E8F0),
                                width: selected ? 1.5 : 1)),
                        child: Padding(
                            padding: const EdgeInsets.all(16),
                            child: Row(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  Expanded(
                                      child: Column(
                                          crossAxisAlignment:
                                              CrossAxisAlignment.start,
                                          children: [
                                        Text(
                                            '${_movementLabelForItem(x)} • $asset',
                                            style: const TextStyle(
                                                fontSize: 17,
                                                fontWeight: FontWeight.w900)),
                                        const SizedBox(height: 10),
                                        Row(children: [
                                          const Icon(
                                              Icons.calendar_today_outlined,
                                              size: 18,
                                              color: _blue),
                                          const SizedBox(width: 10),
                                          Text(_fmtDate(x['created_at']))
                                        ]),
                                        const SizedBox(height: 7),
                                        Row(children: [
                                          const Icon(
                                              Icons.location_city_outlined,
                                              size: 18,
                                              color: _blue),
                                          const SizedBox(width: 10),
                                          Expanded(
                                              child: Text(
                                                  '${x['work'] ?? 'Sem obra'}'))
                                        ]),
                                        const SizedBox(height: 7),
                                        Row(children: [
                                          const Icon(Icons.water_drop_outlined,
                                              size: 18, color: _blue),
                                          const SizedBox(width: 10),
                                          Text(_fmtLiters(x['liters'])),
                                          if (_hasValue(x['fuel_type']))
                                            Text(' • ${x['fuel_type']}',
                                                style: const TextStyle(
                                                    color: _ink))
                                        ]),
                                        const SizedBox(height: 7),
                                        Row(children: [
                                          const Icon(
                                              Icons.person_outline_rounded,
                                              size: 18,
                                              color: _blue),
                                          const SizedBox(width: 10),
                                          Expanded(
                                              child: Text(
                                                  '${x['operator'] ?? '-'}'))
                                        ])
                                      ])),
                                  const SizedBox(width: 8),
                                  if (selectionMode)
                                    Checkbox(
                                        value: selected,
                                        onChanged: (_) => toggleSelected(x))
                                  else
                                    const Icon(Icons.chevron_right_rounded)
                                ]))));
              }),
            ]));
  }

  Widget bodyContent() {
    if (items == null && loading)
      return const Center(child: CircularProgressIndicator());
    if (items == null && loadError != null) {
      return Center(
          child: Padding(
              padding: const EdgeInsets.all(24),
              child: Column(mainAxisSize: MainAxisSize.min, children: [
                const Icon(Icons.cloud_off_rounded, size: 56, color: _blue),
                const SizedBox(height: 16),
                Text(loadError!, textAlign: TextAlign.center),
                const SizedBox(height: 16),
                FilledButton.icon(
                    onPressed: () => load(),
                    icon: const Icon(Icons.refresh_rounded),
                    label: const Text('Tentar novamente')),
              ])));
    }
    return recordList();
  }

  @override
  Widget build(BuildContext context) => Scaffold(
        appBar: AppBar(
            title: Text(selectionMode
                ? '${selectedCodes.length} selecionado(s)'
                : 'Meus registros'),
            actions: [
              if (selectionMode)
                IconButton(
                    onPressed: busy ? null : exportPdf,
                    tooltip: 'Exportar selecionados em PDF',
                    icon: const Icon(Icons.picture_as_pdf_outlined)),
              if (selectionMode)
                IconButton(
                    onPressed: busy ? null : clearSelection,
                    tooltip: 'Cancelar seleção',
                    icon: const Icon(Icons.close_rounded))
            ]),
        body: bodyContent(),
      );
}

class GeneratedReportsV23Screen extends StatefulWidget {
  const GeneratedReportsV23Screen({super.key});
  @override
  State<GeneratedReportsV23Screen> createState() =>
      _GeneratedReportsV23ScreenState();
}

class _GeneratedReportsV23ScreenState extends State<GeneratedReportsV23Screen> {
  final work = TextEditingController(),
      responsible = TextEditingController(),
      asset = TextEditingController();
  DateTime? start, end;
  List<Map<String, dynamic>>? items;
  bool busy = false;
  String? error;
  @override
  void initState() {
    super.initState();
    search();
  }

  @override
  void dispose() {
    work.dispose();
    responsible.dispose();
    asset.dispose();
    super.dispose();
  }

  Future<void> choose(bool first) async {
    final v = await showDatePicker(
        context: context,
        firstDate: DateTime(2024),
        lastDate: DateTime.now().add(const Duration(days: 365)),
        initialDate: (first ? start : end) ?? DateTime.now());
    if (v != null) {
      setState(() {
        if (first) {
          start = v;
        } else {
          end = v;
        }
      });
    }
  }

  Future<void> search() async {
    if (busy) return;
    setState(() {
      busy = true;
      error = null;
    });
    try {
      final x = await api.generatedReportsSearchV23(
          workName: work.text.trim(),
          responsible: responsible.text.trim(),
          start: start,
          end: end,
          asset: asset.text.trim());
      if (mounted) setState(() => items = x);
    } catch (e) {
      if (mounted) setState(() => error = _friendlyError(e));
    } finally {
      if (mounted) setState(() => busy = false);
    }
  }

  Future<void> openReport(Map<String, dynamic> r) async {
    final path = '${r['pdf_path'] ?? ''}'.trim();
    if (path.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(
          content: Text('PDF armazenado não encontrado para este relatório.')));
      return;
    }
    setState(() => busy = true);
    try {
      final bytes = await api.downloadMedia(path);
      if (bytes == null)
        throw Exception('Não foi possível baixar o PDF armazenado.');
      await Printing.sharePdf(
          bytes: bytes,
          filename: 'RC-Relatorio-Final-${r['work_name'] ?? r['id']}.pdf');
    } catch (e) {
      if (mounted)
        ScaffoldMessenger.of(context)
            .showSnackBar(SnackBar(content: Text(_friendlyError(e))));
    } finally {
      if (mounted) setState(() => busy = false);
    }
  }

  @override
  Widget build(BuildContext c) => Scaffold(
      appBar: AppBar(title: const Text('Relatórios')),
      body: ListView(padding: const EdgeInsets.all(16), children: [
        const Card(
            child: ListTile(
                leading: Icon(Icons.folder_copy_outlined, color: _blue),
                title: Text('Relatórios gerados'),
                subtitle: Text(
                    'Os Relatórios Finais permanecem armazenados mesmo depois da conclusão da obra.'))),
        TextField(
            controller: work,
            decoration: const InputDecoration(
                labelText: 'Nome da obra',
                prefixIcon: Icon(Icons.location_city_outlined))),
        const SizedBox(height: 8),
        TextField(
            controller: responsible,
            decoration: const InputDecoration(
                labelText: 'Responsável da obra',
                prefixIcon: Icon(Icons.person_search_outlined))),
        const SizedBox(height: 8),
        TextField(
            controller: asset,
            decoration: const InputDecoration(
                labelText: 'Ativo / placa / identificação',
                prefixIcon: Icon(Icons.precision_manufacturing_outlined))),
        const SizedBox(height: 8),
        Row(children: [
          Expanded(
              child: OutlinedButton.icon(
                  onPressed: busy ? null : () => choose(true),
                  icon: const Icon(Icons.calendar_today_outlined),
                  label: Text(start == null
                      ? 'Data inicial'
                      : _fmtDate(start!.toIso8601String()).split(' ').first))),
          const SizedBox(width: 8),
          Expanded(
              child: OutlinedButton.icon(
                  onPressed: busy ? null : () => choose(false),
                  icon: const Icon(Icons.event_outlined),
                  label: Text(end == null
                      ? 'Data final'
                      : _fmtDate(end!.toIso8601String()).split(' ').first)))
        ]),
        const SizedBox(height: 10),
        SizedBox(
            width: double.infinity,
            child: FilledButton.icon(
                onPressed: busy ? null : search,
                icon: const Icon(Icons.search_rounded),
                label: const Text('Pesquisar relatórios'))),
        if (busy)
          const Padding(
              padding: EdgeInsets.only(top: 8),
              child: LinearProgressIndicator()),
        if (error != null)
          Card(
              child: ListTile(
                  leading: const Icon(Icons.error_outline_rounded),
                  title: const Text('Não foi possível carregar os relatórios'),
                  subtitle: Text(error!),
                  trailing: IconButton(
                      onPressed: busy ? null : search,
                      icon: const Icon(Icons.refresh_rounded)))),
        if (items != null && items!.isEmpty && !busy && error == null)
          const Padding(
              padding: EdgeInsets.all(30),
              child: Center(child: Text('Nenhum relatório encontrado.'))),
        ...?items?.map((r) => Card(
            child: ListTile(
                leading: const CircleAvatar(
                    child: Icon(Icons.picture_as_pdf_outlined)),
                title: Text('${r['title']}',
                    style: const TextStyle(fontWeight: FontWeight.w900)),
                subtitle: Text(
                    'Obra: ${r['work_name'] ?? '-'}\nResponsável: ${r['responsible'] ?? '-'}\nGerado em: ${_fmtDate(r['report_date'])}'),
                isThreeLine: true,
                trailing: const Icon(Icons.share_outlined),
                onTap: busy ? null : () => openReport(r)))),
      ]));
}

class MovementTraceV23Screen extends StatefulWidget {
  final int movementId;
  const MovementTraceV23Screen({super.key, required this.movementId});

  @override
  State<MovementTraceV23Screen> createState() => _MovementTraceV23ScreenState();
}

class _MovementTraceV23ScreenState extends State<MovementTraceV23Screen> {
  Map<String, dynamic>? data;
  String? error;

  @override
  void initState() {
    super.initState();
    load();
  }

  Future<void> load() async {
    setState(() => error = null);
    try {
      final x = await api.movementTraceV23(widget.movementId);
      if (mounted) setState(() => data = x);
    } catch (e) {
      if (mounted) setState(() => error = _friendlyError(e));
    }
  }

  Widget errorBody() {
    return Padding(
      padding: const EdgeInsets.all(24),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          Text(error ?? 'Não foi possível carregar a rastreabilidade.',
              textAlign: TextAlign.center),
          const SizedBox(height: 10),
          FilledButton.icon(
            onPressed: load,
            icon: const Icon(Icons.refresh),
            label: const Text('Tentar novamente'),
          ),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final d = data;
    Widget body;
    if (d == null) {
      body = Center(
        child: error == null ? const CircularProgressIndicator() : errorBody(),
      );
    } else {
      final allocations = _rows(d['allocations']);
      final lineage = _rows(d['lineage']);
      body = ListView(
        padding: const EdgeInsets.all(16),
        children: [
          const Card(
            child: ListTile(
              leading: Icon(Icons.route_rounded, color: _blue),
              title: Text('Origem do combustível deste registro'),
              subtitle: Text(
                  'Quando há mistura de NFs, o app mostra exatamente quantos litros vieram de cada lote.'),
            ),
          ),
          const Text(
            'NF(s) utilizadas',
            style: TextStyle(fontSize: 17, fontWeight: FontWeight.w900),
          ),
          if (allocations.isEmpty)
            const Card(
                child: ListTile(
                    title: Text(
                        'Nenhuma alocação de NF encontrada para este registro.'))),
          ...allocations.map((a) {
            final unitCost = a['unit_cost'];
            final extra =
                unitCost != null ? '\nCusto/L: ${_fmtMoney(unitCost)}' : '';
            return Card(
              child: ListTile(
                title: Text(
                  'NF ${a['invoice_number'] ?? '-'} • ${_fmtLiters(a['liters'])}',
                  style: const TextStyle(fontWeight: FontWeight.w900),
                ),
                subtitle: Text(
                    '${a['supplier_name'] ?? '-'} • ${a['fuel_type'] ?? '-'}$extra'),
              ),
            );
          }),
          const SizedBox(height: 10),
          const Text(
            'Caminho anterior dos lotes',
            style: TextStyle(fontSize: 17, fontWeight: FontWeight.w900),
          ),
          if (lineage.isEmpty)
            const Card(
                child: ListTile(
                    title: Text(
                        'Nenhum movimento anterior encontrado para estes lotes.'))),
          ...lineage.map((m) {
            final source = '${m['source'] ?? 'Entrada'}';
            final destination = m['destination'];
            final route =
                destination != null ? '$source → $destination' : source;
            return Card(
              child: ListTile(
                title: Text(
                  'NF ${m['invoice_number'] ?? '-'} • ${_movementLabel('${m['type'] ?? ''}')}',
                  style: const TextStyle(fontWeight: FontWeight.w900),
                ),
                subtitle: Text(
                    '${_fmtDate(m['created_at'])}\n$route • ${_fmtLiters(m['liters'])}'),
              ),
            );
          }),
        ],
      );
    }

    return Scaffold(
      appBar: AppBar(title: const Text('Rastreabilidade do combustível')),
      body: body,
    );
  }
}

class WorkFinalPdf {
  static Future<Uint8List> build(Map<String, dynamic> snapshot) async {
    final doc = pw.Document();
    final regular = pw.Font.helvetica();
    final bold = pw.Font.helveticaBold();
    final navy = PdfColor.fromHex('#062A69');
    final royal = PdfColor.fromHex('#0E58C7');
    final line = PdfColor.fromHex('#D9E2EE');
    final text = PdfColor.fromHex('#20242B');
    final work = _map(snapshot['work']);
    final inst = _map(work['institutional_company']);
    final summary = _map(snapshot['summary']);
    final company = _hasValue(inst['company_name'])
        ? '${inst['company_name']}'
        : 'Empresa não cadastrada';
    final subtitle = '${inst['company_subtitle'] ?? ''}';

    pw.Widget header(String title) {
      return pw.Column(
          crossAxisAlignment: pw.CrossAxisAlignment.start,
          children: [
            pw.Text(company,
                style: pw.TextStyle(font: bold, fontSize: 28, color: navy)),
            if (subtitle.isNotEmpty)
              pw.Text(subtitle,
                  style:
                      pw.TextStyle(font: regular, fontSize: 18, color: navy)),
            pw.SizedBox(height: 8),
            pw.Container(height: 1.5, color: royal),
            pw.SizedBox(height: 8),
            pw.Text('CNPJ: ${inst['document'] ?? '-'}',
                style: pw.TextStyle(font: regular, fontSize: 9.5, color: text)),
            pw.Text('Endereço: ${inst['address'] ?? '-'}',
                style: pw.TextStyle(font: regular, fontSize: 9.5, color: text)),
            pw.SizedBox(height: 14),
            pw.Text(title,
                style: pw.TextStyle(font: bold, fontSize: 19, color: navy)),
            pw.SizedBox(height: 8),
          ]);
    }

    pw.Widget infoRow(String label, String value) {
      return pw.Container(
        padding: const pw.EdgeInsets.symmetric(vertical: 7),
        decoration: pw.BoxDecoration(
            border: pw.Border(bottom: pw.BorderSide(color: line, width: .6))),
        child:
            pw.Row(crossAxisAlignment: pw.CrossAxisAlignment.start, children: [
          pw.SizedBox(
              width: 175,
              child: pw.Text(label,
                  style:
                      pw.TextStyle(font: bold, fontSize: 9.5, color: royal))),
          pw.Expanded(
              child: pw.Text(value,
                  style:
                      pw.TextStyle(font: regular, fontSize: 10, color: text))),
        ]),
      );
    }

    doc.addPage(pw.Page(
      pageFormat: PdfPageFormat.a4,
      margin: const pw.EdgeInsets.all(30),
      theme: pw.ThemeData.withFont(base: regular, bold: bold),
      build: (_) {
        return pw
            .Column(crossAxisAlignment: pw.CrossAxisAlignment.start, children: [
          header('Relatório Final da Obra'),
          pw.Container(
            padding: const pw.EdgeInsets.all(14),
            decoration: pw.BoxDecoration(
                border: pw.Border.all(color: line),
                borderRadius:
                    const pw.BorderRadius.all(pw.Radius.circular(10))),
            child: pw.Column(children: [
              infoRow('Obra', '${work['name'] ?? '-'}'),
              infoRow('Empresa da obra', '${work['company_name'] ?? '-'}'),
              infoRow('Responsável da obra', '${work['responsible'] ?? '-'}'),
              infoRow('Local', '${work['location'] ?? '-'}'),
              infoRow('Início', _fmtDate(work['created_at'])),
              infoRow('Finalização',
                  _fmtDate(work['finalized_at'] ?? snapshot['generated_at'])),
            ]),
          ),
          pw.SizedBox(height: 14),
          pw.Text('Resumo geral',
              style: pw.TextStyle(font: bold, fontSize: 15, color: navy)),
          infoRow('Registros vinculados', '${summary['movement_count'] ?? 0}'),
          infoRow('Abastecimentos', '${summary['fueling_count'] ?? 0}'),
          infoRow('Volume abastecido', _fmtLiters(summary['fueling_liters'])),
          infoRow('Custo do combustível utilizado',
              _fmtMoney(summary['purchase_cost_total'])),
          infoRow('Valor de venda', _fmtMoney(summary['sale_total'])),
          infoRow('Lucro total', _fmtMoney(summary['profit_total'])),
          pw.Spacer(),
          pw.Container(height: 1.5, color: royal),
          pw.SizedBox(height: 6),
          pw.Text(
              'Documento gerado automaticamente pelo R&C Abastecimento. Os registros e a rastreabilidade permanecem armazenados no sistema.',
              style: pw.TextStyle(font: regular, fontSize: 8.5, color: text)),
        ]);
      },
    ));

    final details = <pw.Widget>[
      pw.Text('Consumo por combustível',
          style: pw.TextStyle(font: bold, fontSize: 14, color: navy)),
    ];
    for (final f in _rows(snapshot['fuel_summary'])) {
      details.add(infoRow('${f['fuel_type'] ?? '-'}',
          '${_fmtLiters(f['liters'])} • ${f['fueling_count'] ?? 0} abastecimento(s)'));
    }
    details.add(pw.SizedBox(height: 14));
    details.add(pw.Text('Ativos e equipamentos atendidos',
        style: pw.TextStyle(font: bold, fontSize: 14, color: navy)));
    for (final a in _rows(snapshot['assets'])) {
      final kind = a['kind'] == 'third_party'
          ? 'Equipamento de terceiros'
          : 'Ativo próprio';
      details.add(infoRow('$kind • ${a['label'] ?? '-'}',
          'Proprietário: ${a['owner_company'] ?? '-'} • ${_fmtLiters(a['liters'])} • ${a['fueling_count'] ?? 0} registro(s)'));
    }
    details.add(pw.SizedBox(height: 14));
    details.add(pw.Text('Notas Fiscais utilizadas',
        style: pw.TextStyle(font: bold, fontSize: 14, color: navy)));
    for (final n in _rows(snapshot['nfs'])) {
      details.add(infoRow('NF ${n['invoice_number'] ?? '-'}',
          'Fornecedor: ${n['supplier_name'] ?? '-'} • Usado na obra: ${_fmtLiters(n['liters_used_by_work'])} • Custo: ${_fmtMoney(n['cost_used_by_work'])}'));
    }
    details.add(pw.SizedBox(height: 14));
    details.add(pw.Text('Registros da obra',
        style: pw.TextStyle(font: bold, fontSize: 14, color: navy)));
    for (final m in _rows(snapshot['movements'])) {
      details.add(pw.Container(
        margin: const pw.EdgeInsets.only(bottom: 7),
        padding: const pw.EdgeInsets.all(9),
        decoration: pw.BoxDecoration(
            border: pw.Border.all(color: line),
            borderRadius: const pw.BorderRadius.all(pw.Radius.circular(6))),
        child: pw
            .Column(crossAxisAlignment: pw.CrossAxisAlignment.start, children: [
          pw.Text(
              '${m['code'] ?? '-'} • ${_movementLabel('${m['type'] ?? ''}')} • ${_fmtLiters(m['liters'])}',
              style: pw.TextStyle(font: bold, fontSize: 10.5, color: navy)),
          pw.SizedBox(height: 3),
          pw.Text(
              '${_fmtDate(m['created_at'])} • ${m['asset_number'] ?? m['third_party_plate'] ?? m['third_party_description'] ?? '-'} • ${m['operator'] ?? '-'}',
              style: pw.TextStyle(font: regular, fontSize: 9.5, color: text)),
          if (_hasValue(m['location_address']))
            pw.Text('${m['location_address']}',
                style: pw.TextStyle(font: regular, fontSize: 9, color: text)),
        ]),
      ));
    }
    details.add(pw.SizedBox(height: 14));
    details.add(pw.Text('Rastreabilidade dos lotes usados',
        style: pw.TextStyle(font: bold, fontSize: 14, color: navy)));
    for (final m in _rows(snapshot['lineage'])) {
      final route =
          '${m['source'] ?? 'Entrada'}${m['destination'] != null ? ' → ${m['destination']}' : ''}';
      details.add(infoRow(
          'NF ${m['invoice_number'] ?? '-'} • ${m['code'] ?? '-'}',
          '${_movementLabel('${m['type'] ?? ''}')} • $route • ${_fmtLiters(m['liters'])} • ${_fmtDate(m['created_at'])}'));
    }
    if (_rows(snapshot['audit']).isNotEmpty) {
      details.add(pw.SizedBox(height: 14));
      details.add(pw.Text('Auditoria e correções',
          style: pw.TextStyle(font: bold, fontSize: 14, color: navy)));
      for (final a in _rows(snapshot['audit'])) {
        details.add(infoRow('${a['action'] ?? '-'} • ${a['user_name'] ?? '-'}',
            '${_fmtDate(a['created_at'])} • Registro ${a['record_id'] ?? '-'}'));
      }
    }

    doc.addPage(pw.MultiPage(
      pageFormat: PdfPageFormat.a4,
      margin: const pw.EdgeInsets.all(30),
      theme: pw.ThemeData.withFont(base: regular, bold: bold),
      header: (_) => header('Detalhamento do Relatório Final'),
      build: (_) => details,
    ));
    return doc.save();
  }
}

class AdminSecurityV35Screen extends StatefulWidget {
  const AdminSecurityV35Screen({super.key});
  @override
  State<AdminSecurityV35Screen> createState() => _AdminSecurityV35ScreenState();
}

class _AdminSecurityV35ScreenState extends State<AdminSecurityV35Screen> {
  final pin = TextEditingController(),
      password = TextEditingController(),
      confirm = TextEditingController();
  bool sending = false, saving = false, pinSent = false, hidePassword = true;
  static const ownerEmail = 'marinhrodrigo@gmail.com';
  @override
  void dispose() {
    pin.dispose();
    password.dispose();
    confirm.dispose();
    super.dispose();
  }

  Future<void> sendPin() async {
    if (!offlineStore.online.value) {
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(
          content:
              Text('Conecte-se à internet para enviar o PIN de segurança.')));
      return;
    }
    setState(() => sending = true);
    try {
      final client = Supabase.instance.client;
      final res = await client.functions.invoke('admin-security',
          body: {'action': 'prepare_password_change'});
      final data = _map(res.data);
      if (res.status < 200 || res.status >= 300 || data['ok'] != true)
        throw Exception(
            '${data['error'] ?? 'Não foi possível preparar a verificação.'}');
      try {
        await client.auth.refreshSession();
      } catch (_) {}
      await client.auth.reauthenticate();
      if (mounted) {
        setState(() => pinSent = true);
        ScaffoldMessenger.of(context).showSnackBar(const SnackBar(
            content: Text('PIN enviado para marinhrodrigo@gmail.com.')));
      }
    } catch (e) {
      if (mounted)
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(
            content:
                Text('Não foi possível enviar o PIN: ${_friendlyError(e)}')));
    } finally {
      if (mounted) setState(() => sending = false);
    }
  }

  Future<void> changePassword() async {
    if (!pinSent) {
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(
          content: Text('Envie o PIN para o seu e-mail primeiro.')));
      return;
    }
    final code = pin.text.trim(), next = password.text, again = confirm.text;
    if (code.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Informe o PIN recebido por e-mail.')));
      return;
    }
    if (next.length < 4) {
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(
          content: Text('A nova senha/PIN deve ter pelo menos 4 caracteres.')));
      return;
    }
    if (next != again) {
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(
          content: Text('A confirmação da nova senha não confere.')));
      return;
    }
    if (!offlineStore.online.value) {
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(
          content:
              Text('Conecte-se à internet para alterar a senha do Admin.')));
      return;
    }
    setState(() => saving = true);
    try {
      final client = Supabase.instance.client;
      await client.auth.updateUser(
          UserAttributes(password: _authPasswordForLogin(next), nonce: code));
      try {
        await client.auth.signOut(scope: SignOutScope.others);
      } catch (_) {}
      final sessionId = offlineStore.appSessionIdV30;
      final res = await client.functions.invoke('admin-security', body: {
        'action': 'complete_password_change',
        'session_id': sessionId
      });
      final data = _map(res.data);
      if (res.status < 200 || res.status >= 300 || data['ok'] != true)
        throw Exception(
            '${data['error'] ?? 'Senha alterada, mas houve falha ao registrar a segurança.'}');
      pin.clear();
      password.clear();
      confirm.clear();
      if (mounted) {
        setState(() => pinSent = false);
        await showDialog<void>(
            context: context,
            builder: (ctx) => AlertDialog(
                    title: const Text('Senha alterada ✓'),
                    content: const Text(
                        'A senha do Admin foi alterada. Outras sessões foram encerradas e a alteração foi registrada na Auditoria.'),
                    actions: [
                      FilledButton(
                          onPressed: () => Navigator.pop(ctx),
                          child: const Text('OK'))
                    ]));
      }
    } catch (e) {
      if (mounted)
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(
            content: Text(
                'Não foi possível alterar a senha: ${_friendlyError(e)}')));
    } finally {
      if (mounted) setState(() => saving = false);
    }
  }

  @override
  Widget build(BuildContext context) => Scaffold(
        appBar: AppBar(title: const Text('Segurança do Admin')),
        body: ListView(padding: const EdgeInsets.all(16), children: [
          Card(
              child: Padding(
                  padding: const EdgeInsets.all(16),
                  child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        const Row(children: [
                          Icon(Icons.verified_user_outlined, color: _blue),
                          SizedBox(width: 8),
                          Expanded(
                              child: Text('Proteção da senha do Admin',
                                  style: TextStyle(
                                      fontSize: 17,
                                      fontWeight: FontWeight.w900)))
                        ]),
                        const SizedBox(height: 10),
                        const Text(
                            'Para alterar a senha do Admin, será obrigatório confirmar um PIN enviado para o e-mail do proprietário.'),
                        const SizedBox(height: 8),
                        const Text(ownerEmail,
                            style: TextStyle(fontWeight: FontWeight.w900)),
                        const SizedBox(height: 12),
                        FilledButton.icon(
                            onPressed: sending || saving ? null : sendPin,
                            icon: sending
                                ? const SizedBox(
                                    width: 18,
                                    height: 18,
                                    child: CircularProgressIndicator(
                                        strokeWidth: 2))
                                : const Icon(Icons.email_outlined),
                            label: Text(pinSent
                                ? 'Reenviar PIN'
                                : 'Enviar PIN para o e-mail')),
                      ]))),
          if (pinSent) ...[
            const SizedBox(height: 12),
            Card(
                child: Padding(
                    padding: const EdgeInsets.all(16),
                    child: Column(children: [
                      TextField(
                          controller: pin,
                          keyboardType: TextInputType.number,
                          inputFormatters: [
                            FilteringTextInputFormatter.digitsOnly
                          ],
                          decoration: const InputDecoration(
                              labelText: 'PIN recebido por e-mail *',
                              prefixIcon: Icon(Icons.pin_outlined))),
                      const SizedBox(height: 10),
                      TextField(
                          controller: password,
                          obscureText: hidePassword,
                          decoration: InputDecoration(
                              labelText: 'Nova senha / PIN do Admin *',
                              prefixIcon: const Icon(Icons.lock_outline),
                              suffixIcon: IconButton(
                                  onPressed: () => setState(
                                      () => hidePassword = !hidePassword),
                                  icon: Icon(hidePassword
                                      ? Icons.visibility_outlined
                                      : Icons.visibility_off_outlined)))),
                      const SizedBox(height: 10),
                      TextField(
                          controller: confirm,
                          obscureText: hidePassword,
                          decoration: const InputDecoration(
                              labelText: 'Confirmar nova senha / PIN *',
                              prefixIcon: Icon(Icons.lock_reset_outlined))),
                      const SizedBox(height: 14),
                      SizedBox(
                          width: double.infinity,
                          child: FilledButton.icon(
                              onPressed: saving ? null : changePassword,
                              icon: saving
                                  ? const SizedBox(
                                      width: 18,
                                      height: 18,
                                      child: CircularProgressIndicator(
                                          strokeWidth: 2))
                                  : const Icon(Icons.security_rounded),
                              label:
                                  const Text('Confirmar PIN e alterar senha'))),
                    ]))),
          ],
          const SizedBox(height: 12),
          const Card(
              child: ListTile(
                  leading: Icon(Icons.info_outline, color: _blue),
                  title: Text('Regra de segurança'),
                  subtitle: Text(
                      'A troca de senha funciona somente online. O código enviado por e-mail é temporário e a alteração fica registrada na Auditoria.'))),
        ]),
      );
}

class AdminHomeScreen extends StatefulWidget {
  final Map<String, dynamic> profile;
  final Future<void> Function() onLogout;
  const AdminHomeScreen(
      {super.key, required this.profile, required this.onLogout});
  @override
  State<AdminHomeScreen> createState() => _AdminHomeScreenState();
}

class _AdminHomeScreenState extends State<AdminHomeScreen> {
  Map<String, dynamic>? ref;
  Map<String, dynamic> kpis = {};
  Map<String, dynamic> currentUnit = {};
  List<Map<String, dynamic>> statuses = [];
  Timer? timer;
  bool running = false;
  final globalSearch = TextEditingController();
  @override
  void initState() {
    super.initState();
    refresh();
    timer = Timer.periodic(const Duration(seconds: 20), (_) => refresh());
  }

  @override
  void dispose() {
    timer?.cancel();
    globalSearch.dispose();
    super.dispose();
  }

  Future<void> refresh() async {
    if (running) return;
    running = true;
    try {
      if (!offlineStore.online.value) {
        final d = offlineStore.cachedReferenceData;
        final tid = offlineStore.lastTankId;
        Map<String, dynamic> mine = {};
        for (final x in _sortedFuelUnits(d?['tanks'])) {
          if (_intOrNull(x['id']) == tid) {
            mine = {
              'tank_id': tid,
              'unit_code': x['code'],
              'unit_name': x['name'],
              'tank_type': x['tank_type'],
              'user_name': widget.profile['display_name']
            };
            break;
          }
        }
        if (mounted)
          setState(() {
            ref = d;
            kpis = {};
            currentUnit = mine;
            statuses = [];
          });
        return;
      }
      final d = await api.referenceData();
      Map<String, dynamic> k = {};
      Map<String, dynamic> mine = {};
      List<Map<String, dynamic>> st = [];
      try {
        k = await api.dashboardKpisV28();
      } catch (_) {}
      try {
        mine = await api.myUnitV30();
      } catch (_) {}
      try {
        st = await api.unitStatusV30();
      } catch (_) {}
      final tid = _intOrNull(mine['tank_id']);
      await offlineStore.setLastTankId(tid);
      if (mounted)
        setState(() {
          ref = d;
          kpis = k;
          currentUnit = mine;
          statuses = st;
        });
    } catch (_) {
    } finally {
      running = false;
    }
  }

  List<Map<String, dynamic>> _sources(Set<String> types) =>
      _sortedFuelUnits(ref?['tanks'])
          .where((t) =>
              t['authorized'] != false && types.contains('${t['tank_type']}'))
          .toList();
  Map<String, dynamic>? _statusFor(int id) {
    for (final x in statuses) {
      if (_intOrNull(x['tank_id']) == id) return x;
    }
    return null;
  }

  Map<String, dynamic>? _tankFor(int? id) {
    if (id == null) return null;
    for (final t in _sortedFuelUnits(ref?['tanks'])) {
      if (_intOrNull(t['id']) == id) return t;
    }
    return null;
  }

  Future<bool> _claim(Map<String, dynamic> t) async {
    final id = _intOrNull(t['id']);
    if (id == null) return false;
    if (!offlineStore.online.value) {
      await offlineStore.setLastTankId(id);
      if (mounted)
        setState(() => currentUnit = {
              'tank_id': id,
              'unit_code': t['code'],
              'unit_name': t['name'],
              'tank_type': t['tank_type'],
              'user_name': widget.profile['display_name']
            });
      if (mounted)
        ScaffoldMessenger.of(context).showSnackBar(const SnackBar(
            content: Text(
                'Unidade selecionada offline. A validação será feita quando a internet voltar.')));
      return true;
    }
    try {
      final x = await api.claimUnitV31(id);
      if (x['ok'] != true) {
        if (mounted)
          ScaffoldMessenger.of(context).showSnackBar(SnackBar(
              content:
                  Text('${x['message'] ?? 'Esta unidade já está em uso.'}')));
        await refresh();
        return false;
      }
      await offlineStore.setLastTankId(id);
      if (mounted)
        setState(() => currentUnit = {
              'tank_id': id,
              'unit_code': t['code'],
              'unit_name': t['name'],
              'tank_type': t['tank_type'],
              'user_name': widget.profile['display_name']
            });
      return true;
    } catch (e) {
      if (mounted)
        ScaffoldMessenger.of(context)
            .showSnackBar(SnackBar(content: Text(_friendlyError(e))));
      return false;
    }
  }

  Future<Map<String, dynamic>?> _choose(
      String title, String subtitle, Set<String> types,
      {bool excludeCurrent = false}) async {
    if (offlineStore.online.value) {
      try {
        statuses = await api.unitStatusV30();
      } catch (_) {}
    } else {
      statuses = [];
    }
    final currentId = _intOrNull(currentUnit['tank_id']);
    final list = _sources(types)
        .where((t) => !excludeCurrent || _intOrNull(t['id']) != currentId)
        .toList();
    if (list.isEmpty) {
      if (mounted)
        ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(content: Text('Nenhuma unidade disponível para $title.')));
      return null;
    }
    if (list.length == 1) {
      final t = list.first,
          id = _intOrNull(t['id']),
          st = id == null ? null : _statusFor(id);
      final blocked = st?['in_use'] == true && st?['is_mine'] != true;
      if (blocked) {
        final owner = '${st?['user_name'] ?? ''}'.trim();
        if (mounted)
          ScaffoldMessenger.of(context).showSnackBar(SnackBar(
              content: Text(
                  'Esta unidade já está sendo usada por ${owner.isEmpty ? 'outro usuário' : owner}.')));
        return null;
      }
      return await _claim(t) ? t : null;
    }
    if (!mounted) return null;
    final selected = await showModalBottomSheet<Map<String, dynamic>>(
        context: context,
        showDragHandle: true,
        isScrollControlled: true,
        builder: (ctx) => SafeArea(
            child: ConstrainedBox(
                constraints: BoxConstraints(
                    maxHeight: MediaQuery.of(ctx).size.height * .75),
                child: ListView(
                    shrinkWrap: true,
                    padding: const EdgeInsets.fromLTRB(16, 0, 16, 20),
                    children: [
                      Text(title,
                          style: Theme.of(ctx)
                              .textTheme
                              .titleLarge
                              ?.copyWith(fontWeight: FontWeight.w900)),
                      const SizedBox(height: 4),
                      Text(subtitle,
                          style: const TextStyle(color: Colors.black54)),
                      const SizedBox(height: 10),
                      ...list.map((t) {
                        final id = _intOrNull(t['id']),
                            st = id == null ? null : _statusFor(id);
                        final mine = st?['is_mine'] == true,
                            inUse = st?['in_use'] == true,
                            blocked = inUse && !mine,
                            owner = '${st?['user_name'] ?? ''}'.trim();
                        return Card(
                            child: ListTile(
                                leading: Icon(
                                    '${t['tank_type']}' == 'stationary'
                                        ? Icons.oil_barrel_outlined
                                        : Icons.local_shipping_rounded,
                                    color: blocked ? Colors.black38 : _blue),
                                title: Text('${t['code']} • ${t['name']}',
                                    style: const TextStyle(
                                        fontWeight: FontWeight.w800)),
                                subtitle: Text(blocked
                                    ? 'Em uso por ${owner.isEmpty ? 'outro usuário' : owner}'
                                    : 'Saldo: ${_fmtLiters(t['current_balance_liters'])}'),
                                trailing: mine
                                    ? const Icon(Icons.check_circle_rounded,
                                        color: Colors.green)
                                    : blocked
                                        ? const Icon(Icons.lock_outline_rounded)
                                        : const Icon(Icons.chevron_right),
                                onTap: blocked
                                    ? () {
                                        ScaffoldMessenger.of(ctx).showSnackBar(
                                            SnackBar(
                                                content: Text(
                                                    'Esta unidade já está sendo usada por ${owner.isEmpty ? 'outro usuário' : owner}.')));
                                      }
                                    : () => Navigator.pop(ctx, t)));
                      })
                    ]))));
    if (selected == null || !mounted) return null;
    return await _claim(selected) ? selected : null;
  }

  Future<void> _switchUnit() async {
    final selected = await _choose(
        'Trocar unidade',
        'Selecione uma unidade disponível. A unidade atual será liberada automaticamente.',
        const {'stationary', 'comboio', 'truck'},
        excludeCurrent: true);
    if (selected != null && mounted) {
      await refresh();
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(
          content: Text('Unidade alterada para ${selected['code']} ✓')));
    }
  }

  Future<void> _releaseUnit() async {
    final id = _intOrNull(currentUnit['tank_id']);
    if (id == null) return;
    final code = '${currentUnit['unit_code'] ?? ''}';
    final ok = await showDialog<bool>(
        context: context,
        builder: (ctx) => AlertDialog(
                title: const Text('Liberar unidade?'),
                content: Text(code.isEmpty
                    ? 'A unidade ficará disponível para outro usuário.'
                    : 'A unidade $code ficará disponível para outro usuário.'),
                actions: [
                  TextButton(
                      onPressed: () => Navigator.pop(ctx, false),
                      child: const Text('Cancelar')),
                  FilledButton(
                      onPressed: () => Navigator.pop(ctx, true),
                      child: const Text('Liberar'))
                ]));
    if (ok != true) return;
    if (!offlineStore.online.value) {
      await offlineStore.queueOfflineReleaseV62(
          tankId: id, occurredAt: DateTime.now());
      await offlineStore.setLastTankId(null);
      if (mounted) setState(() => currentUnit = {});
      if (mounted)
        ScaffoldMessenger.of(context).showSnackBar(const SnackBar(
            content: Text(
                'Unidade liberada offline. A liberação será sincronizada quando a internet voltar.')));
      return;
    }
    try {
      await api.releaseMyUnitV31();
      await offlineStore.setLastTankId(null);
      if (mounted) setState(() => currentUnit = {});
      await refresh();
      if (mounted)
        ScaffoldMessenger.of(context)
            .showSnackBar(const SnackBar(content: Text('Unidade liberada ✓')));
    } catch (e) {
      if (mounted)
        ScaffoldMessenger.of(context)
            .showSnackBar(SnackBar(content: Text(_friendlyError(e))));
    }
  }

  Future<Map<String, dynamic>?> _operationUnit(
      Set<String> types, String title, String subtitle) async {
    final currentId = _intOrNull(currentUnit['tank_id']);
    final current = _tankFor(currentId);
    if (current != null && types.contains('${current['tank_type']}'))
      return current;
    return _choose(title, subtitle, types, excludeCurrent: currentId != null);
  }

  Future<void> _fueling() async {
    if (ref == null) return;
    final t = await _operationUnit(const {'stationary', 'comboio', 'truck'},
        'Novo abastecimento', 'Selecione a unidade de origem.');
    if (!mounted || t == null || ref == null) return;
    await Navigator.push(
        context,
        MaterialPageRoute(
            builder: (_) => FuelingV23Screen(
                source: t, ref: ref!, profile: widget.profile)));
    if (mounted) refresh();
  }

  bool _requireOnlineV69() {
    if (offlineStore.online.value) return true;
    ScaffoldMessenger.of(context).showSnackBar(const SnackBar(
        content: Text(
            'Este recurso administrativo precisa de internet. Os abastecimentos de campo continuam disponíveis offline.')));
    return false;
  }

  Future<void> _transfer() async {
    if (!_requireOnlineV69() || ref == null) return;
    final t = await _operationUnit(const {'comboio', 'truck'}, 'Transferir',
        'Selecione a unidade doadora.');
    if (!mounted || t == null || ref == null) return;
    await Navigator.push(
        context,
        MaterialPageRoute(
            builder: (_) => TransferV23Screen(
                source: t, ref: ref!, profile: widget.profile)));
    if (mounted) refresh();
  }

  Future<void> _receipt() async {
    if (!_requireOnlineV69() || ref == null) return;
    final t = await _operationUnit(
        const {'truck'},
        'Recebimento de combustível / NF',
        'Selecione o caminhão-tanque que receberá a carga.');
    if (!mounted || t == null) return;
    await Navigator.push(context,
        MaterialPageRoute(builder: (_) => RefineryLoadV23Screen(truck: t)));
    if (mounted) refresh();
  }

  void open(Widget page) {
    if (!_requireOnlineV69()) return;
    Navigator.push(context, MaterialPageRoute(builder: (_) => page));
  }

  void openRecordsV71(Widget page) {
    Navigator.push(context, MaterialPageRoute(builder: (_) => page));
  }

  Widget quick(
          IconData icon, String title, String subtitle, VoidCallback onTap) =>
      Card(
          margin: EdgeInsets.zero,
          child: InkWell(
              onTap: onTap,
              borderRadius: BorderRadius.circular(12),
              child: Padding(
                  padding:
                      const EdgeInsets.symmetric(horizontal: 7, vertical: 11),
                  child: Column(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        Icon(icon, color: _blue, size: 29),
                        const SizedBox(height: 7),
                        Text(title,
                            textAlign: TextAlign.center,
                            maxLines: 2,
                            overflow: TextOverflow.ellipsis,
                            style: const TextStyle(
                                fontWeight: FontWeight.w900, fontSize: 12.2))
                      ]))));
  @override
  Widget build(BuildContext context) {
    final tanks = _sortedFuelUnits(ref?['tanks']);
    final isAdmin = widget.profile['is_admin'] == true;
    final isManager = widget.profile['is_manager'] == true;
    final canCorrect = isAdmin || widget.profile['can_correct'] == true;
    final currentCode = '${currentUnit['unit_code'] ?? ''}'.trim(),
        currentName = '${currentUnit['unit_name'] ?? ''}'.trim();
    final actions = <Widget>[
      quick(Icons.local_gas_station_rounded, 'Novo abastecimento',
          'Registrar abastecimento', _fueling),
      quick(Icons.swap_horiz_rounded, 'Transferir', 'Registrar transferência',
          _transfer),
      quick(Icons.receipt_long_rounded, 'Recebimento (NF)', 'Registrar entrada',
          _receipt),
      quick(
          Icons.today_rounded,
          'Registro Diário',
          'Movimentações do dia',
          () => openRecordsV71(DailyRecordsV28Screen(
              canEdit: canCorrect, canCancel: isAdmin || isManager))),
      quick(
          Icons.manage_search_rounded,
          'Registro Geral',
          'Histórico e pesquisa',
          () => openRecordsV71(const GeneralRecordsV28Screen())),
      if (canCorrect)
        quick(
            Icons.rule_folder_outlined,
            'Pendências / conflitos',
            'Abastecimentos aguardando análise',
            () => open(const OfflineConflictsV58Screen())),
      if (isAdmin || isManager)
        quick(Icons.folder_copy_outlined, 'Relatórios', 'PDFs e obras',
            () => open(const GeneratedReportsV23Screen())),
      quick(Icons.location_city_outlined, 'Obras', 'Gestão completa',
          () => open(WorksAdminScreen(profile: widget.profile))),
      if (isAdmin)
        quick(
            Icons.business_outlined,
            'Empresas',
            'Clientes, locadoras e fornecedores',
            () => open(const CompaniesAdminScreen())),
      quick(
          Icons.precision_manufacturing_outlined,
          'Ativos',
          'Equipamentos próprios',
          () => open(MachinesAdminScreen(canEdit: isAdmin))),
      quick(
          Icons.handyman_outlined,
          'Equip. terceiros',
          'Proprietária / locadora',
          () => open(ThirdPartyAdminScreen(canEdit: isAdmin))),
      if (isAdmin)
        quick(Icons.oil_barrel_outlined, 'Tanques estacionários',
            'Capacidade e saldo', () => open(const TanksAdminScreen())),
      if (isAdmin)
        quick(Icons.local_shipping_rounded, 'Caminhão-tanque',
            'Função do ativo', () => open(const TruckFunctionAdminScreen())),
      if (isAdmin)
        quick(
            Icons.manage_accounts_rounded,
            'Usuários',
            'Supervisor, Gerente e Operacional',
            () => open(UnifiedUsersV29Screen(referenceData: ref!))),
      if (isAdmin)
        quick(Icons.badge_outlined, 'Dados da empresa', 'Empresa operadora',
            () => open(const ReportCompanyAdminScreen())),
      if (isAdmin)
        quick(Icons.shield_outlined, 'Segurança', 'Senha e proteção do Admin',
            () => open(const AdminSecurityV35Screen())),
    ];
    Widget kpi(IconData icon, String label, String value) => Expanded(
        child: Container(
            padding: const EdgeInsets.all(10),
            decoration: BoxDecoration(
                color: Colors.white,
                borderRadius: BorderRadius.circular(12),
                border: Border.all(color: Colors.black12)),
            child: Column(children: [
              Icon(icon, color: _blue, size: 22),
              const SizedBox(height: 5),
              Text(value,
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                  style: const TextStyle(
                      fontWeight: FontWeight.w900, fontSize: 15)),
              Text(label,
                  textAlign: TextAlign.center,
                  style: const TextStyle(fontSize: 9.5, color: Colors.black54))
            ])));
    return Scaffold(
        appBar: AppBar(
            title: const Text('R&C ABASTECIMENTO',
                style: TextStyle(fontWeight: FontWeight.w900)),
            actions: [
              IconButton(
                  onPressed: () =>
                      open(GlobalSearchV28Screen(profile: widget.profile)),
                  tooltip: 'Pesquisa global',
                  icon: const Icon(Icons.search_rounded)),
              IconButton(
                  onPressed: () =>
                      open(AdminCatalogScreen(profile: widget.profile)),
                  tooltip: 'Cadastros',
                  icon: const Icon(Icons.menu_rounded)),
              IconButton(
                  onPressed: () async {
                    await _logoutToLogin(context, widget.onLogout);
                  },
                  tooltip: 'Sair',
                  icon: const Icon(Icons.logout_rounded))
            ]),
        body: ref == null
            ? const Center(child: CircularProgressIndicator())
            : RefreshIndicator(
                onRefresh: refresh,
                child: ListView(padding: const EdgeInsets.all(16), children: [
                  GreetingLine(name: '${widget.profile['display_name']}'),
                  if (currentCode.isNotEmpty) ...[
                    const SizedBox(height: 10),
                    Card(
                        child: Padding(
                            padding: const EdgeInsets.all(14),
                            child: Column(
                                crossAxisAlignment: CrossAxisAlignment.stretch,
                                children: [
                                  Row(children: [
                                    const Icon(Icons.lock_clock_outlined,
                                        size: 19, color: _blue),
                                    const SizedBox(width: 7),
                                    Expanded(
                                        child: Text(
                                            'Unidade em uso: $currentCode${currentName.isNotEmpty ? ' • $currentName' : ''}',
                                            style: const TextStyle(
                                                fontWeight: FontWeight.w900)))
                                  ]),
                                  const SizedBox(height: 10),
                                  Row(children: [
                                    Expanded(
                                        child: OutlinedButton.icon(
                                            onPressed: _switchUnit,
                                            icon: const Icon(
                                                Icons.swap_horiz_rounded),
                                            label:
                                                const Text('Trocar unidade'))),
                                    const SizedBox(width: 8),
                                    Expanded(
                                        child: OutlinedButton.icon(
                                            onPressed: _releaseUnit,
                                            icon: const Icon(
                                                Icons.lock_open_rounded),
                                            label:
                                                const Text('Liberar unidade')))
                                  ])
                                ]))),
                  ],
                  const SizedBox(height: 8),
                  TextField(
                      controller: globalSearch,
                      textInputAction: TextInputAction.search,
                      onSubmitted: (q) {
                        if (q.trim().isNotEmpty)
                          open(GlobalSearchV28Screen(
                              profile: widget.profile, initialQuery: q.trim()));
                      },
                      decoration: InputDecoration(
                          labelText: 'Pesquisar em todo o sistema',
                          hintText:
                              'Obra, empresa, ativo, placa, NF, CB01, Nº sequencial...',
                          prefixIcon: const Icon(Icons.search_rounded),
                          suffixIcon: IconButton(
                              onPressed: () {
                                final q = globalSearch.text.trim();
                                if (q.isNotEmpty)
                                  open(GlobalSearchV28Screen(
                                      profile: widget.profile,
                                      initialQuery: q));
                              },
                              icon: const Icon(Icons.arrow_forward_rounded)))),
                  const SizedBox(height: 12),
                  Row(children: [
                    kpi(Icons.inventory_2_outlined, 'Estoque atual',
                        _fmtLiters(kpis['stock_liters'])),
                    const SizedBox(width: 7),
                    kpi(Icons.water_drop_outlined, 'Consumo hoje',
                        _fmtLiters(kpis['fueling_liters_today']))
                  ]),
                  const SizedBox(height: 7),
                  Row(children: [
                    kpi(Icons.local_gas_station_outlined, 'Abastecimentos hoje',
                        '${kpis['fueling_count_today'] ?? 0}'),
                    const SizedBox(width: 7),
                    kpi(Icons.location_city_outlined, 'Obras ativas',
                        '${kpis['active_works'] ?? 0}')
                  ]),
                  const SizedBox(height: 12),
                  const Card(
                      child: ListTile(
                          leading: Icon(Icons.location_on_outlined,
                              color: Colors.orange),
                          title: Text('Localização deve estar ativada',
                              style: TextStyle(fontWeight: FontWeight.w900)),
                          subtitle: Text(
                              'O ponto exato do abastecimento será capturado automaticamente ao concluir.'))),
                  const SizedBox(height: 10),
                  GridView.count(
                      shrinkWrap: true,
                      physics: const NeverScrollableScrollPhysics(),
                      crossAxisCount: 3,
                      crossAxisSpacing: 8,
                      mainAxisSpacing: 8,
                      childAspectRatio: .92,
                      children: actions),
                  const SizedBox(height: 18),
                  Row(children: [
                    const Icon(Icons.water_drop_outlined, color: _blue),
                    const SizedBox(width: 7),
                    Text('Saldos em tempo real',
                        style: Theme.of(context)
                            .textTheme
                            .titleMedium
                            ?.copyWith(fontWeight: FontWeight.w900))
                  ]),
                  const SizedBox(height: 8),
                  ...tanks.map((t) => Padding(
                      padding: const EdgeInsets.only(bottom: 8),
                      child: BalanceCard(tank: t))),
                  const SizedBox(height: 12),
                  HomeActionCard(
                      icon: Icons.dashboard_outlined,
                      title: 'Painel de combustível',
                      subtitle:
                          'Estoque, NFs, consumo, autonomia, custos e lucros em tempo real',
                      onTap: () => open(FuelDashboardV23Screen(
                          profile: widget.profile, ref: ref!)))
                ])));
  }
}

class AdminRecordsScreen extends StatelessWidget {
  final Map<String, dynamic> referenceData;
  const AdminRecordsScreen({super.key, required this.referenceData});
  @override
  Widget build(BuildContext context) => const GeneralRecordsV28Screen();
}

class OfficialPdfPreviewV28Screen extends StatelessWidget {
  final List<Map<String, dynamic>> items;
  final String title;
  const OfficialPdfPreviewV28Screen(
      {super.key, required this.items, this.title = 'Prévia do PDF'});
  @override
  Widget build(BuildContext context) => Scaffold(
      appBar: AppBar(title: Text(title)),
      body: PdfPreview(
          build: (_) => FuelPdfReport.build(items),
          canChangePageFormat: false,
          canChangeOrientation: false,
          canDebug: false,
          pdfFileName:
              'RC-Abastecimento-${DateTime.now().millisecondsSinceEpoch}.pdf'));
}

String _recordSequenceV28(Map<String, dynamic> x) {
  if (x['offline_pending'] == true) {
    final local = _intOrNull(x['offline_sequence_v74']);
    if (local != null) return local.toString().padLeft(4, '0');
  }
  final raw = '${x['code'] ?? ''}';
  final m = RegExp(r'(\d+)$').firstMatch(raw);
  final n = int.tryParse(m?.group(1) ?? '');
  return n == null ? '----' : n.toString().padLeft(4, '0');
}

String _recordOriginV28(Map<String, dynamic> x) {
  final s = '${x['source_tank'] ?? ''}'.trim();
  if (s.isNotEmpty && s != 'null') return s;
  final d = '${x['destination_tank'] ?? ''}'.trim();
  if (d.isNotEmpty && d != 'null') return d;
  final code = '${x['code'] ?? ''}';
  final m = RegExp(r'^(.+?)-\d+$').firstMatch(code);
  return m?.group(1) ?? '-';
}

List<Map<String, dynamic>> _sortRecordsV70(
    Iterable<Map<String, dynamic>> values) {
  final out = values.toList();
  out.sort((a, b) => '${b['occurred_at'] ?? b['created_at'] ?? ''}'
      .compareTo('${a['occurred_at'] ?? a['created_at'] ?? ''}'));
  return out;
}

bool _recordInRangeV70(Map<String, dynamic> x, DateTime? start, DateTime? end) {
  final d = DateTime.tryParse('${x['occurred_at'] ?? x['created_at'] ?? ''}')
      ?.toLocal();
  if (d == null) return start == null && end == null;
  if (start != null && d.isBefore(start)) return false;
  if (end != null && !d.isBefore(end)) return false;
  return true;
}

Map<String, dynamic> _summaryWithLocalV70(
    Map<String, dynamic> server, List<Map<String, dynamic>> local) {
  final s = Map<String, dynamic>.from(server);
  if (local.isEmpty) return s;
  final liters = local.fold<double>(0, (v, x) => v + _num(x['liters']));
  final sales = local.fold<double>(0, (v, x) => v + _num(x['total_value']));
  s['record_count'] = _num(s['record_count']).toInt() + local.length;
  s['fueling_count'] = _num(s['fueling_count']).toInt() + local.length;
  s['fueling_liters'] = _num(s['fueling_liters']) + liters;
  s['sale_total'] = _num(s['sale_total']) + sales;
  return s;
}

class _RecordCardV28 extends StatelessWidget {
  final Map<String, dynamic> item;
  final VoidCallback onOpen;
  final VoidCallback onPdf;
  final VoidCallback? onSelect;
  final bool selected;
  final bool selectionMode;
  const _RecordCardV28(
      {required this.item,
      required this.onOpen,
      required this.onPdf,
      this.onSelect,
      this.selected = false,
      this.selectionMode = false});
  @override
  Widget build(BuildContext context) {
    final asset = item['asset_number'] ??
        item['third_party_plate'] ??
        item['destination_tank'] ??
        item['source_tank'] ??
        '-';
    final fueling = '${item['type']}' == 'fueling';
    final id = _intOrNull(item['id']);
    return Card(
        child: InkWell(
            onTap: selectionMode ? (onSelect ?? onOpen) : onOpen,
            borderRadius: BorderRadius.circular(12),
            child: Padding(
                padding: const EdgeInsets.all(13),
                child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(children: [
                        Expanded(
                            child: Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                              Text('${_movementLabelForItem(item)} • $asset',
                                  style: const TextStyle(
                                      fontWeight: FontWeight.w900,
                                      fontSize: 15)),
                              if (item['offline_pending'] == true)
                                Padding(
                                    padding: const EdgeInsets.only(top: 3),
                                    child: Text(
                                        item['sync_conflict'] == true
                                            ? 'CONFLITO • AGUARDANDO ANÁLISE'
                                            : item['sync_rejected'] == true
                                                ? 'REJEITADO'
                                                : _hasValue(item['sync_error'])
                                                    ? 'PENDENTE • ${item['sync_error']}'
                                                    : 'SALVO OFFLINE • aguardando sincronização',
                                        maxLines: 2,
                                        overflow: TextOverflow.ellipsis,
                                        style: TextStyle(
                                            fontSize: 11,
                                            fontWeight: FontWeight.w900,
                                            color: item['sync_rejected'] == true
                                                ? Colors.red
                                                : Colors.orange)))
                            ])),
                        if (selectionMode)
                          Checkbox(
                              value: selected,
                              onChanged: (_) => onSelect?.call())
                        else
                          IconButton(
                              onPressed: onPdf,
                              tooltip: 'Prévia / Exportar PDF',
                              icon: const Icon(Icons.picture_as_pdf_outlined,
                                  color: _blue))
                      ]),
                      Wrap(spacing: 7, runSpacing: 6, children: [
                        ActionChip(
                            avatar: const Icon(
                                Icons.confirmation_number_outlined,
                                size: 16),
                            label: Text.rich(TextSpan(children: [
                              TextSpan(
                                  text: '${_recordOriginV28(item)} • Nº: ',
                                  style: const TextStyle(
                                      fontWeight: FontWeight.w800)),
                              TextSpan(
                                  text: _recordSequenceV28(item),
                                  style: const TextStyle(
                                      color: Color(0xFFD51F2A),
                                      fontWeight: FontWeight.w900))
                            ])),
                            onPressed: fueling && id != null
                                ? () => Navigator.push(
                                    context,
                                    MaterialPageRoute(
                                        builder: (_) => MovementTraceV23Screen(
                                            movementId: id)))
                                : onOpen),
                        if (_hasValue(item['work']))
                          Chip(label: Text('${item['work']}')),
                        if (_hasValue(item['fuel_type']))
                          Chip(label: Text('${item['fuel_type']}'))
                      ]),
                      const SizedBox(height: 8),
                      Text(
                          '${_fmtDate(item['created_at'])} • ${_fmtLiters(item['liters'])}',
                          style: const TextStyle(fontWeight: FontWeight.w700)),
                      const SizedBox(height: 3),
                      Text(
                          'Responsável/operador: ${item['operator'] ?? item['work_responsible'] ?? '-'}',
                          style: const TextStyle(color: Colors.black54)),
                    ]))));
  }
}

class _RecordsSummaryV28 extends StatelessWidget {
  final Map<String, dynamic> summary;
  final DateTime? start;
  final DateTime? end;
  const _RecordsSummaryV28({required this.summary, this.start, this.end});
  @override
  Widget build(BuildContext context) {
    final oneDay =
        start != null && end != null && end!.difference(start!).inDays == 1;
    final date =
        oneDay ? _fmtDate(start!.toIso8601String()).split(' ').first : '';
    Widget m(String l, String v, {bool hi = false}) => Container(
        padding: const EdgeInsets.all(11),
        decoration: BoxDecoration(
            color: hi ? const Color(0xFFEAF2FF) : Colors.white,
            borderRadius: BorderRadius.circular(12),
            border: Border.all(color: hi ? _blue : Colors.black12)),
        child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Text(l,
              style: TextStyle(
                  fontSize: 11,
                  color: hi ? _blue : Colors.black54,
                  fontWeight: FontWeight.w700)),
          const SizedBox(height: 3),
          Text(v,
              style: TextStyle(
                  fontSize: hi ? 20 : 15,
                  fontWeight: FontWeight.w900,
                  color: hi ? _blue : Colors.black87))
        ]));
    return Card(
        child: Padding(
            padding: const EdgeInsets.all(15),
            child: Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  Text(
                      oneDay
                          ? 'Resumo do dia • $date'
                          : 'Resumo dos resultados',
                      style: const TextStyle(
                          fontSize: 17, fontWeight: FontWeight.w900)),
                  const SizedBox(height: 10),
                  m(oneDay ? 'Total abastecido no dia' : 'Total abastecido',
                      _fmtLiters(summary['fueling_liters']),
                      hi: true),
                  const SizedBox(height: 8),
                  Row(children: [
                    Expanded(
                        child: m('Abastecimentos',
                            '${summary['fueling_count'] ?? 0}')),
                    const SizedBox(width: 7),
                    Expanded(
                        child: m('Total de registros',
                            '${summary['record_count'] ?? 0}'))
                  ]),
                  const SizedBox(height: 7),
                  Row(children: [
                    Expanded(
                        child: m('Transferido',
                            _fmtLiters(summary['transfer_liters']))),
                    const SizedBox(width: 7),
                    Expanded(
                        child: m('Recebido por NF',
                            _fmtLiters(summary['refinery_liters'])))
                  ]),
                  if (summary['sale_total'] != null) ...[
                    const SizedBox(height: 7),
                    Row(children: [
                      Expanded(
                          child: m('Valor abastecido',
                              _fmtMoney(summary['sale_total']))),
                      const SizedBox(width: 7),
                      Expanded(
                          child: m('Lucro', _fmtMoney(summary['profit_total'])))
                    ])
                  ],
                  if (_rows(summary['fuel_breakdown']).isNotEmpty) ...[
                    const SizedBox(height: 12),
                    const Text('Por combustível',
                        style: TextStyle(fontWeight: FontWeight.w900)),
                    const SizedBox(height: 5),
                    ..._rows(summary['fuel_breakdown']).map((x) => Padding(
                        padding: const EdgeInsets.only(bottom: 3),
                        child: Row(children: [
                          Expanded(child: Text('${x['fuel_type']}')),
                          Text(_fmtLiters(x['liters']),
                              style:
                                  const TextStyle(fontWeight: FontWeight.w800))
                        ])))
                  ],
                  if (_rows(summary['asset_breakdown']).isNotEmpty) ...[
                    const SizedBox(height: 12),
                    const Text('Por ativo / equipamento',
                        style: TextStyle(fontWeight: FontWeight.w900)),
                    const SizedBox(height: 5),
                    ..._rows(summary['asset_breakdown']).map((x) => Padding(
                        padding: const EdgeInsets.only(bottom: 3),
                        child: Row(children: [
                          Expanded(child: Text('${x['asset']}')),
                          Text(
                              '${_fmtLiters(x['liters'])} • ${x['count'] ?? 0} reg.',
                              style:
                                  const TextStyle(fontWeight: FontWeight.w800))
                        ])))
                  ],
                  const SizedBox(height: 9),
                  const Text(
                      'Transferências e recebimentos de NF ficam separados do Total abastecido para não contar o mesmo combustível mais de uma vez.',
                      style: TextStyle(fontSize: 11, color: Colors.black54))
                ])));
  }
}

class DailyRecordsV28Screen extends StatefulWidget {
  final bool canEdit;
  final bool canCancel;
  const DailyRecordsV28Screen(
      {super.key, this.canEdit = false, this.canCancel = false});
  @override
  State<DailyRecordsV28Screen> createState() => _DailyRecordsV28ScreenState();
}

class _DailyRecordsV28ScreenState extends State<DailyRecordsV28Screen> {
  DateTime day = DateTime.now();
  List<Map<String, dynamic>> items = [];
  Map<String, dynamic> summary = {};
  bool busy = false;
  String? error;
  @override
  void initState() {
    super.initState();
    offlineStore.syncRevision.addListener(_offlineChangedV70);
    offlineStore.pendingCount.addListener(_offlineChangedV70);
    load();
  }

  void _offlineChangedV70() {
    if (mounted) unawaited(load());
  }

  @override
  void dispose() {
    offlineStore.syncRevision.removeListener(_offlineChangedV70);
    offlineStore.pendingCount.removeListener(_offlineChangedV70);
    super.dispose();
  }

  DateTime get start => DateTime(day.year, day.month, day.day);
  DateTime get end => start.add(const Duration(days: 1));
  Future<void> load() async {
    if (busy) return;
    setState(() => busy = true);
    final local = offlineStore
        .pendingFuelingsForCurrentUser()
        .where((x) => _recordInRangeV70(x, start, end))
        .toList();
    try {
      if (offlineStore.online.value) {
        final r =
            await api.generalRecordsV28(start: start, end: end, limit: 1000);
        if (mounted)
          setState(() {
            items = _sortRecordsV70([...local, ..._rows(r['items'])]);
            summary = _summaryWithLocalV70(_map(r['summary']), local);
            error = null;
          });
      } else if (mounted) {
        setState(() {
          items = _sortRecordsV70(local);
          summary = _summaryWithLocalV70({}, local);
          error = null;
        });
      }
    } catch (e) {
      if (mounted)
        setState(() {
          items = _sortRecordsV70(local);
          summary = _summaryWithLocalV70({}, local);
          error = local.isEmpty ? _friendlyError(e) : null;
        });
    } finally {
      if (mounted) setState(() => busy = false);
    }
  }

  Future<void> choose() async {
    final d = await showDatePicker(
        context: context,
        firstDate: DateTime(2024),
        lastDate: DateTime.now().add(const Duration(days: 730)),
        initialDate: day);
    if (d != null) {
      setState(() => day = d);
      load();
    }
  }

  void preview(Map<String, dynamic> x) => Navigator.push(
      context,
      MaterialPageRoute(
          builder: (_) => OfficialPdfPreviewV28Screen(
              items: [x], title: 'Prévia • ${x['code'] ?? 'Registro'}')));
  @override
  Widget build(BuildContext context) => Scaffold(
      appBar: AppBar(title: const Text('Registro Diário')),
      body: RefreshIndicator(
          onRefresh: load,
          child: ListView(padding: const EdgeInsets.all(12), children: [
            Card(
                child: Padding(
                    padding: const EdgeInsets.all(12),
                    child: Column(children: [
                      Row(children: [
                        Expanded(
                            child: FilledButton.tonal(
                                onPressed: () {
                                  setState(() => day = DateTime.now());
                                  load();
                                },
                                child: const Text('Hoje'))),
                        const SizedBox(width: 7),
                        Expanded(
                            child: OutlinedButton(
                                onPressed: () {
                                  setState(() => day = DateTime.now()
                                      .subtract(const Duration(days: 1)));
                                  load();
                                },
                                child: const Text('Ontem'))),
                        const SizedBox(width: 7),
                        Expanded(
                            child: OutlinedButton.icon(
                                onPressed: choose,
                                icon: const Icon(Icons.calendar_month_outlined),
                                label: const Text('Data')))
                      ]),
                      const SizedBox(height: 8),
                      Text(
                          'Dia selecionado: ${_fmtDate(start.toIso8601String()).split(' ').first}',
                          style: const TextStyle(fontWeight: FontWeight.w800))
                    ]))),
            if (busy) const LinearProgressIndicator(minHeight: 2),
            if (error != null)
              Card(
                  child: ListTile(
                      leading: const Icon(Icons.error_outline),
                      title: Text(error!),
                      trailing: IconButton(
                          onPressed: load, icon: const Icon(Icons.refresh)))),
            if (summary.isNotEmpty)
              _RecordsSummaryV28(summary: summary, start: start, end: end),
            const SizedBox(height: 8),
            Text('${items.length} registro(s) carregado(s)',
                style: const TextStyle(fontWeight: FontWeight.w800)),
            const SizedBox(height: 5),
            if (items.isEmpty && !busy && error == null)
              const Card(
                  child: ListTile(title: Text('Nenhum registro neste dia.'))),
            ...items.map((x) => _RecordCardV28(
                item: x,
                onOpen: () => Navigator.push(
                    context,
                    MaterialPageRoute(
                        builder: (_) => MovementDetailScreen(
                            item: x,
                            canEdit: widget.canEdit,
                            canCancel: widget.canCancel))),
                onPdf: () => preview(x)))
          ])));
}

class GeneralRecordsV28Screen extends StatefulWidget {
  final int? initialWorkId;
  final String? initialQuery;
  final String? initialInvoice;
  const GeneralRecordsV28Screen(
      {super.key, this.initialWorkId, this.initialQuery, this.initialInvoice});
  @override
  State<GeneralRecordsV28Screen> createState() =>
      _GeneralRecordsV28ScreenState();
}

class _GeneralRecordsV28ScreenState extends State<GeneralRecordsV28Screen> {
  DateTime? start;
  DateTime? end;
  int? workId;
  int? companyId;
  String? type;
  String? fuelType;
  final query = TextEditingController(),
      asset = TextEditingController(),
      plate = TextEditingController(),
      operatorName = TextEditingController(),
      responsible = TextEditingController(),
      source = TextEditingController(),
      invoice = TextEditingController();
  List<Map<String, dynamic>> works = [];
  List<Map<String, dynamic>> items = [];
  Map<String, dynamic> summary = {};
  bool busy = false;
  bool filters = true;
  bool canCorrect = false;
  bool canCancel = false;
  String? error;
  final Set<String> selected = <String>{};
  @override
  void initState() {
    super.initState();
    workId = widget.initialWorkId;
    query.text = widget.initialQuery ?? '';
    invoice.text = widget.initialInvoice ?? '';
    offlineStore.syncRevision.addListener(_offlineChangedV70);
    offlineStore.pendingCount.addListener(_offlineChangedV70);
    bootstrap();
  }

  void _offlineChangedV70() {
    if (mounted) unawaited(search(collapse: false));
  }

  @override
  void dispose() {
    offlineStore.syncRevision.removeListener(_offlineChangedV70);
    offlineStore.pendingCount.removeListener(_offlineChangedV70);
    for (final c in [
      query,
      asset,
      plate,
      operatorName,
      responsible,
      source,
      invoice
    ]) {
      c.dispose();
    }
    super.dispose();
  }

  Future<void> bootstrap() async {
    try {
      final values =
          await Future.wait<dynamic>([api.worksCatalogV28(), api.profile()]);
      works = (values[0] as List).cast<Map<String, dynamic>>();
      final profile = _map(values[1]);
      canCorrect =
          profile['is_admin'] == true || profile['can_correct'] == true;
      canCancel = profile['is_admin'] == true ||
          profile['is_manager'] == true ||
          '${profile['role'] ?? ''}'.toLowerCase() == 'manager' ||
          '${profile['role'] ?? ''}'.toLowerCase() == 'gerente';
    } catch (_) {
      try {
        works = await api.worksCatalogV28();
      } catch (_) {}
    }
    if (mounted) setState(() {});
    await search(collapse: false);
  }

  String key(Map<String, dynamic> x) => '${x['code'] ?? x['id']}';
  Future<void> pick(bool first) async {
    final base = first
        ? (start ?? DateTime.now().subtract(const Duration(days: 30)))
        : ((end ?? DateTime.now().add(const Duration(days: 1)))
            .subtract(const Duration(days: 1)));
    final d = await showDatePicker(
        context: context,
        firstDate: DateTime(2024),
        lastDate: DateTime.now().add(const Duration(days: 730)),
        initialDate: base);
    if (d == null) return;
    setState(() {
      if (first) {
        start = DateTime(d.year, d.month, d.day);
      } else {
        end = DateTime(d.year, d.month, d.day).add(const Duration(days: 1));
      }
    });
  }

  Future<void> chooseWork() async {
    final result = await showModalBottomSheet<int>(
        context: context,
        isScrollControlled: true,
        showDragHandle: true,
        builder: (ctx) => _WorkPickerV28(works: works, current: workId));
    if (!mounted || result == null) return;
    setState(() => workId = result == 0 ? null : result);
  }

  bool _localMatchV70(Map<String, dynamic> x) {
    if (!_recordInRangeV70(x, start, end)) return false;
    if (type != null && type != 'fueling') return false;
    if (workId != null && _intOrNull(x['work_id']) != workId) return false;
    bool has(String value, String needle) =>
        needle.trim().isEmpty ||
        value.toLowerCase().contains(needle.trim().toLowerCase());
    if (!has(
        '${x['asset_number'] ?? ''} ${x['asset_model'] ?? ''} ${x['third_party_description'] ?? ''}',
        asset.text)) return false;
    if (!has('${x['asset_plate'] ?? ''} ${x['third_party_plate'] ?? ''}',
        plate.text)) return false;
    if (!has(
        '${x['operator'] ?? ''} ${x['receiver'] ?? ''}', operatorName.text))
      return false;
    if (!has('${x['source_tank'] ?? ''} ${x['source_tank_name'] ?? ''}',
        source.text)) return false;
    if (fuelType != null && !has('${x['fuel_type'] ?? ''}', fuelType!))
      return false;
    final q = query.text.trim();
    if (q.isNotEmpty &&
        !has(
            '${x['code'] ?? ''} ${x['work'] ?? ''} ${x['asset_number'] ?? ''} ${x['asset_plate'] ?? ''} ${x['third_party_plate'] ?? ''} ${x['third_party_description'] ?? ''} ${x['source_tank'] ?? ''}',
            q)) return false;
    if (invoice.text.trim().isNotEmpty ||
        responsible.text.trim().isNotEmpty ||
        companyId != null) return false;
    return true;
  }

  Future<void> search({bool collapse = true}) async {
    if (busy) return;
    setState(() {
      busy = true;
      error = null;
    });
    final local = offlineStore
        .pendingFuelingsForCurrentUser()
        .where(_localMatchV70)
        .toList();
    try {
      if (offlineStore.online.value) {
        final r = await api
            .generalRecordsV28(
                start: start,
                end: end,
                workId: workId,
                asset: asset.text.trim(),
                plate: plate.text.trim(),
                operatorName: operatorName.text.trim(),
                type: type,
                query: query.text.trim(),
                sourceCode: source.text.trim(),
                invoice: invoice.text.trim(),
                responsible: responsible.text.trim(),
                companyId: companyId,
                fuelType: fuelType,
                limit: 1000)
            .timeout(const Duration(seconds: 20));
        if (mounted)
          setState(() {
            items = _sortRecordsV70([...local, ..._rows(r['items'])]);
            summary = _summaryWithLocalV70(_map(r['summary']), local);
            selected.clear();
            if (collapse) filters = false;
          });
      } else if (mounted) {
        setState(() {
          items = _sortRecordsV70(local);
          summary = _summaryWithLocalV70({}, local);
          selected.clear();
          if (collapse) filters = false;
        });
      }
    } catch (e) {
      if (mounted)
        setState(() {
          items = _sortRecordsV70(local);
          summary = _summaryWithLocalV70({}, local);
          error = local.isEmpty ? _friendlyError(e) : null;
          selected.clear();
        });
    } finally {
      if (mounted) setState(() => busy = false);
    }
  }

  void clearFilters() {
    setState(() {
      start = null;
      end = null;
      workId = null;
      companyId = null;
      type = null;
      fuelType = null;
      for (final c in [
        query,
        asset,
        plate,
        operatorName,
        responsible,
        source,
        invoice
      ]) {
        c.clear();
      }
      filters = true;
    });
  }

  void preview(List<Map<String, dynamic>> x) {
    if (x.isEmpty) return;
    Navigator.push(
        context,
        MaterialPageRoute(
            builder: (_) => OfficialPdfPreviewV28Screen(
                items: x,
                title: x.length == 1
                    ? 'Prévia • ${x.first['code'] ?? 'Registro'}'
                    : 'Prévia • ${x.length} registros')));
  }

  String workLabel() {
    if (workId == null) return 'Todas as obras';
    for (final w in works) {
      if (_intOrNull(w['id']) == workId) return '${w['name']}';
    }
    return 'Obra selecionada';
  }

  List<Map<String, dynamic>> clientCompanies() {
    final seen = <int>{};
    final out = <Map<String, dynamic>>[];
    for (final w in works) {
      final id = _intOrNull(w['contracting_company_id']);
      if (id != null && seen.add(id))
        out.add({'id': id, 'name': w['company_name'] ?? 'Empresa $id'});
    }
    out.sort((a, b) => '${a['name']}'.compareTo('${b['name']}'));
    return out;
  }

  @override
  Widget build(BuildContext context) => Scaffold(
      appBar: AppBar(
          title: Text(selected.isEmpty
              ? 'Registro Geral'
              : '${selected.length} selecionado(s)'),
          actions: [
            if (selected.isNotEmpty)
              IconButton(
                  onPressed: () => preview(
                      items.where((x) => selected.contains(key(x))).toList()),
                  tooltip: 'Prévia / Exportar selecionados',
                  icon: const Icon(Icons.picture_as_pdf_outlined)),
            if (selected.isNotEmpty)
              IconButton(
                  onPressed: () => setState(() => selected.clear()),
                  icon: const Icon(Icons.close))
          ]),
      body: ListView(
          padding: const EdgeInsets.fromLTRB(12, 12, 12, 30),
          children: [
            Card(
                child: Column(children: [
              ListTile(
                  title: const Text('Pesquisa e filtros',
                      style: TextStyle(fontWeight: FontWeight.w900)),
                  subtitle: Text(workLabel()),
                  trailing:
                      Icon(filters ? Icons.expand_less : Icons.expand_more),
                  onTap: () => setState(() => filters = !filters)),
              if (filters)
                Padding(
                    padding: const EdgeInsets.fromLTRB(12, 0, 12, 12),
                    child: Column(children: [
                      TextField(
                          controller: query,
                          decoration: const InputDecoration(
                              labelText: 'Pesquisa geral',
                              hintText:
                                  'Sequencial, obra, ativo, placa, NF, empresa...',
                              prefixIcon: Icon(Icons.search_rounded))),
                      const SizedBox(height: 8),
                      Row(children: [
                        Expanded(
                            child: OutlinedButton.icon(
                                onPressed: () => pick(true),
                                icon: const Icon(Icons.calendar_today),
                                label: Text(start == null
                                    ? 'Data inicial'
                                    : 'De ${_fmtDate(start!.toIso8601String()).split(' ').first}'))),
                        const SizedBox(width: 7),
                        Expanded(
                            child: OutlinedButton.icon(
                                onPressed: () => pick(false),
                                icon: const Icon(Icons.event),
                                label: Text(end == null
                                    ? 'Data final'
                                    : 'Até ${_fmtDate(end!.subtract(const Duration(days: 1)).toIso8601String()).split(' ').first}')))
                      ]),
                      const SizedBox(height: 8),
                      SizedBox(
                          width: double.infinity,
                          child: OutlinedButton.icon(
                              onPressed: chooseWork,
                              icon: const Icon(Icons.location_city_outlined),
                              label: Text('Obra: ${workLabel()}'))),
                      const SizedBox(height: 8),
                      DropdownButtonFormField<int?>(
                          initialValue: companyId,
                          isExpanded: true,
                          decoration: const InputDecoration(
                              labelText: 'Empresa cliente / contratante',
                              prefixIcon: Icon(Icons.business_outlined)),
                          items: [
                            const DropdownMenuItem<int?>(
                                value: null, child: Text('Todas as empresas')),
                            ...clientCompanies().map((c) =>
                                DropdownMenuItem<int?>(
                                    value: _intOrNull(c['id']),
                                    child: Text('${c['name']}')))
                          ],
                          onChanged: (v) => setState(() => companyId = v)),
                      const SizedBox(height: 8),
                      TextField(
                          controller: asset,
                          decoration: const InputDecoration(
                              labelText: 'Ativo / equipamento',
                              prefixIcon: Icon(
                                  Icons.precision_manufacturing_outlined))),
                      const SizedBox(height: 8),
                      Row(children: [
                        Expanded(
                            child: TextField(
                                controller: plate,
                                decoration:
                                    const InputDecoration(labelText: 'Placa'))),
                        const SizedBox(width: 7),
                        Expanded(
                            child: TextField(
                                controller: source,
                                decoration: const InputDecoration(
                                    labelText: 'Origem / unidade',
                                    hintText: 'CB01, TE01...')))
                      ]),
                      const SizedBox(height: 8),
                      TextField(
                          controller: invoice,
                          decoration: const InputDecoration(
                              labelText: 'Nota Fiscal / lote',
                              prefixIcon: Icon(Icons.receipt_long_outlined))),
                      const SizedBox(height: 8),
                      Row(children: [
                        Expanded(
                            child: TextField(
                                controller: operatorName,
                                decoration: const InputDecoration(
                                    labelText: 'Operador / recebedor'))),
                        const SizedBox(width: 7),
                        Expanded(
                            child: TextField(
                                controller: responsible,
                                decoration: const InputDecoration(
                                    labelText: 'Responsável')))
                      ]),
                      const SizedBox(height: 8),
                      Row(children: [
                        Expanded(
                            child: DropdownButtonFormField<String?>(
                                initialValue: type,
                                decoration:
                                    const InputDecoration(labelText: 'Tipo'),
                                items: const [
                                  DropdownMenuItem<String?>(
                                      value: null, child: Text('Todos')),
                                  DropdownMenuItem(
                                      value: 'fueling',
                                      child: Text('Abastecimento')),
                                  DropdownMenuItem(
                                      value: 'tank_transfer',
                                      child: Text('Transferência')),
                                  DropdownMenuItem(
                                      value: 'refinery_entry',
                                      child: Text('Recebimento/NF'))
                                ],
                                onChanged: (v) => setState(() => type = v))),
                        const SizedBox(width: 7),
                        Expanded(
                            child: DropdownButtonFormField<String?>(
                                initialValue: fuelType,
                                decoration: const InputDecoration(
                                    labelText: 'Combustível'),
                                items: [
                                  const DropdownMenuItem<String?>(
                                      value: null, child: Text('Todos')),
                                  ..._fuelTypes.map((f) =>
                                      DropdownMenuItem<String?>(
                                          value: f, child: Text(f)))
                                ],
                                onChanged: (v) => setState(() => fuelType = v)))
                      ]),
                      const SizedBox(height: 10),
                      Row(children: [
                        Expanded(
                            child: OutlinedButton.icon(
                                onPressed: busy ? null : clearFilters,
                                icon: const Icon(Icons.filter_alt_off_outlined),
                                label: const Text('Limpar'))),
                        const SizedBox(width: 8),
                        Expanded(
                            flex: 2,
                            child: FilledButton.icon(
                                onPressed: busy ? null : () => search(),
                                icon: const Icon(Icons.search),
                                label: const Text('Pesquisar')))
                      ])
                    ]))
            ])),
            if (busy) const LinearProgressIndicator(minHeight: 2),
            if (error != null)
              Card(
                  child: ListTile(
                      leading: const Icon(Icons.error_outline),
                      title: Text(error!),
                      trailing: IconButton(
                          onPressed: () => search(collapse: false),
                          icon: const Icon(Icons.refresh)))),
            if (summary.isNotEmpty)
              _RecordsSummaryV28(summary: summary, start: start, end: end),
            const SizedBox(height: 8),
            Row(children: [
              Expanded(
                  child: Text(
                      '${summary['record_count'] ?? items.length} resultado(s) no filtro • ${items.length} carregado(s)',
                      style: const TextStyle(fontWeight: FontWeight.w800))),
              if (items.isNotEmpty)
                TextButton.icon(
                    onPressed: () =>
                        setState(() => selected.addAll(items.map(key))),
                    icon: const Icon(Icons.select_all),
                    label: const Text('Selecionar carregados'))
            ]),
            if (items.isEmpty && !busy && error == null)
              const Card(
                  child: ListTile(title: Text('Nenhum registro encontrado.'))),
            ...items.map((x) => GestureDetector(
                onLongPress: () => setState(() => selected.add(key(x))),
                child: _RecordCardV28(
                    item: x,
                    selectionMode: selected.isNotEmpty,
                    selected: selected.contains(key(x)),
                    onSelect: () => setState(() {
                          final k = key(x);
                          if (!selected.add(k)) selected.remove(k);
                        }),
                    onOpen: () async {
                      final changed = await Navigator.push<bool>(
                          context,
                          MaterialPageRoute(
                              builder: (_) => MovementDetailScreen(
                                  item: x,
                                  canEdit: canCorrect,
                                  canCancel: canCancel)));
                      if (changed == true && mounted)
                        await search(collapse: false);
                    },
                    onPdf: () => preview([x]))))
          ]));
}

class _WorkPickerV28 extends StatefulWidget {
  final List<Map<String, dynamic>> works;
  final int? current;
  const _WorkPickerV28({required this.works, this.current});
  @override
  State<_WorkPickerV28> createState() => _WorkPickerV28State();
}

class _WorkPickerV28State extends State<_WorkPickerV28> {
  final q = TextEditingController();
  @override
  void dispose() {
    q.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final f = q.text.trim().toLowerCase();
    final list = widget.works
        .where((w) =>
            f.isEmpty ||
            '${w['name']} ${w['company_name']} ${w['responsible']}'
                .toLowerCase()
                .contains(f))
        .toList();
    return SafeArea(
        child: Padding(
      padding: EdgeInsets.only(
          left: 16,
          right: 16,
          bottom: MediaQuery.of(context).viewInsets.bottom + 16),
      child: Column(mainAxisSize: MainAxisSize.min, children: [
        const Align(
            alignment: Alignment.centerLeft,
            child: Text('Pesquisar por obra',
                style: TextStyle(fontSize: 19, fontWeight: FontWeight.w900))),
        const SizedBox(height: 8),
        TextField(
            controller: q,
            onChanged: (_) => setState(() {}),
            autofocus: true,
            decoration: const InputDecoration(
                labelText: 'Nome da obra, cliente ou responsável',
                prefixIcon: Icon(Icons.search))),
        const SizedBox(height: 8),
        Flexible(
            child: ListView(shrinkWrap: true, children: [
          ListTile(
              leading: const Icon(Icons.all_inclusive),
              title: const Text('Todas as obras'),
              selected: widget.current == null,
              onTap: () => Navigator.pop(context, 0)),
          ...list.map((w) => ListTile(
                leading: Icon('${w['status']}' == 'finalized'
                    ? Icons.task_alt
                    : '${w['status']}' == 'deleted'
                        ? Icons.delete_outline
                        : Icons.location_city_outlined),
                title: Text('${w['name']}',
                    style: const TextStyle(fontWeight: FontWeight.w800)),
                subtitle: Text(
                    '${w['company_name'] ?? '-'} • ${w['responsible'] ?? '-'}'),
                selected: _intOrNull(w['id']) == widget.current,
                onTap: () => Navigator.pop(context, _intOrNull(w['id'])),
              )),
        ])),
      ]),
    ));
  }
}

class AuditHistoryV28Screen extends StatefulWidget {
  const AuditHistoryV28Screen({super.key});
  @override
  State<AuditHistoryV28Screen> createState() => _AuditHistoryV28ScreenState();
}

class _AuditHistoryV28ScreenState extends State<AuditHistoryV28Screen> {
  final q = TextEditingController();
  List<Map<String, dynamic>> items = [];
  bool busy = false;
  @override
  void initState() {
    super.initState();
    load();
  }

  @override
  void dispose() {
    q.dispose();
    super.dispose();
  }

  Future<void> load() async {
    setState(() => busy = true);
    try {
      final x = await api.auditHistoryV28(query: q.text.trim(), limit: 1500);
      if (mounted) setState(() => items = x);
    } catch (e) {
      if (mounted)
        ScaffoldMessenger.of(context)
            .showSnackBar(SnackBar(content: Text(_friendlyError(e))));
    } finally {
      if (mounted) setState(() => busy = false);
    }
  }

  String safe(dynamic v) {
    final x = '${v ?? ''}'.trim();
    return x.isEmpty || x == 'undefined' ? '—' : x;
  }

  String area(dynamic v) {
    final x = safe(v).toLowerCase();
    if (x == 'registro') return 'Registro';
    const m = {
      'managers': 'Usuários de gestão',
      'drivers': 'Usuários operacionais',
      'user_permissions': 'Permissões',
      'role_default_permissions': 'Permissões padrão',
      'works': 'Obras',
      'companies': 'Empresas',
      'receipt_lots': 'Notas fiscais / lotes',
      'refinery_receipts': 'Recebimentos',
      'machines': 'Ativos',
      'third_party_vehicles': 'Equipamentos de terceiros'
    };
    return m[x] ?? safe(v);
  }

  @override
  Widget build(BuildContext context) => Scaffold(
        appBar: AppBar(title: const Text('Auditoria • Registros')),
        body: Column(children: [
          Padding(
              padding: const EdgeInsets.all(12),
              child: TextField(
                controller: q,
                onSubmitted: (_) => load(),
                decoration: InputDecoration(
                    labelText: 'Pesquisar nos registros',
                    hintText:
                        'Usuário, comboio, abastecimento, login, saída...',
                    prefixIcon: const Icon(Icons.search),
                    suffixIcon: IconButton(
                        onPressed: load, icon: const Icon(Icons.search))),
              )),
          const Padding(
              padding: EdgeInsets.fromLTRB(12, 0, 12, 8),
              child: Card(
                  child: ListTile(
                leading: Icon(Icons.history_rounded, color: _blue),
                title: Text('Histórico geral em ordem cronológica',
                    style: TextStyle(fontWeight: FontWeight.w900)),
                subtitle: Text(
                    'Login, seleção/troca/liberação de comboio, abastecimentos, conflitos e decisões, logout e demais alterações ficam concentrados aqui.'),
              ))),
          if (busy) const LinearProgressIndicator(minHeight: 2),
          Expanded(
              child: RefreshIndicator(
            onRefresh: load,
            child: ListView(
                padding: const EdgeInsets.fromLTRB(12, 4, 12, 30),
                children: [
                  if (items.isEmpty && !busy)
                    const Card(
                        child: ListTile(
                            title: Text('Nenhum registro encontrado.'))),
                  ...items.map((x) {
                    final detail = safe(x['detail_text']);
                    final user = safe(x['user_name']);
                    final ref = safe(x['record_id']);
                    final table = area(x['table_name']);
                    return Card(
                        child: ListTile(
                      leading: const CircleAvatar(
                          child: Icon(Icons.receipt_long_outlined)),
                      title: Text(detail,
                          style: const TextStyle(fontWeight: FontWeight.w900)),
                      subtitle: Text(
                          '${_fmtDate(x['created_at'])}\nUsuário: $user\nÁrea: $table${ref == '—' ? '' : ' • Referência: $ref'}'),
                      isThreeLine: false,
                      onTap: () => showDialog(
                        context: context,
                        builder: (ctx) => AlertDialog(
                          title: const Text('Detalhes do registro'),
                          content: SingleChildScrollView(
                              child: SelectableText(
                            'Data/hora: ${_fmtDate(x['created_at'])}\nUsuário: $user\nRegistro: $detail\nÁrea: $table\nReferência: $ref\n\nDados anteriores:\n${const JsonEncoder.withIndent('  ').convert(x['old_data'])}\n\nDados do evento:\n${const JsonEncoder.withIndent('  ').convert(x['new_data'])}',
                          )),
                          actions: [
                            TextButton(
                                onPressed: () => Navigator.pop(ctx),
                                child: const Text('Fechar'))
                          ],
                        ),
                      ),
                    ));
                  }),
                ]),
          )),
        ]),
      );
}

class GlobalSearchV28Screen extends StatefulWidget {
  final Map<String, dynamic> profile;
  final String? initialQuery;
  const GlobalSearchV28Screen(
      {super.key, required this.profile, this.initialQuery});
  @override
  State<GlobalSearchV28Screen> createState() => _GlobalSearchV28ScreenState();
}

class _GlobalSearchV28ScreenState extends State<GlobalSearchV28Screen> {
  final q = TextEditingController();
  Map<String, dynamic> data = {};
  bool busy = false;
  @override
  void initState() {
    super.initState();
    q.text = widget.initialQuery ?? '';
    if (q.text.trim().isNotEmpty) search();
  }

  @override
  void dispose() {
    q.dispose();
    super.dispose();
  }

  Future<void> search() async {
    if (q.text.trim().isEmpty) return;
    setState(() => busy = true);
    try {
      final r = await api.globalSearchV28(q.text.trim(), limit: 30);
      if (mounted) setState(() => data = r);
    } catch (e) {
      if (mounted)
        ScaffoldMessenger.of(context)
            .showSnackBar(SnackBar(content: Text(_friendlyError(e))));
    } finally {
      if (mounted) setState(() => busy = false);
    }
  }

  Widget section(String title, List<Map<String, dynamic>> list,
      Widget Function(Map<String, dynamic>) tile) {
    if (list.isEmpty) return const SizedBox.shrink();
    return Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
      Padding(
          padding: const EdgeInsets.fromLTRB(4, 14, 4, 5),
          child: Text('$title (${list.length})',
              style:
                  const TextStyle(fontWeight: FontWeight.w900, fontSize: 16))),
      ...list.map(tile)
    ]);
  }

  void open(Widget w) =>
      Navigator.push(context, MaterialPageRoute(builder: (_) => w));
  @override
  Widget build(BuildContext context) => Scaffold(
      appBar: AppBar(title: const Text('Pesquisa global')),
      body: ListView(padding: const EdgeInsets.all(12), children: [
        TextField(
            controller: q,
            autofocus: widget.initialQuery == null,
            textInputAction: TextInputAction.search,
            onSubmitted: (_) => search(),
            decoration: InputDecoration(
                labelText: 'Pesquisar em todo o R&C',
                hintText: 'Obra, empresa, ativo, placa, NF, CB01, Nº...',
                prefixIcon: const Icon(Icons.search),
                suffixIcon: IconButton(
                    onPressed: search, icon: const Icon(Icons.arrow_forward)))),
        if (busy)
          const Padding(
              padding: EdgeInsets.only(top: 8),
              child: LinearProgressIndicator(minHeight: 2)),
        section(
            'Registros',
            _rows(data['movements']),
            (x) => Card(
                child: ListTile(
                    leading:
                        const Icon(Icons.receipt_long_outlined, color: _blue),
                    title: Text('${x['code']} • ${_movementLabelForItem(x)}',
                        style: const TextStyle(fontWeight: FontWeight.w900)),
                    subtitle: Text(
                        '${x['work'] ?? 'Sem obra'} • ${x['asset'] ?? '-'} • ${_fmtLiters(x['liters'])}'),
                    onTap: () => open(GeneralRecordsV28Screen(
                        initialQuery: '${x['code']}'))))),
        section(
            'Obras',
            _rows(data['works']),
            (x) => Card(
                child: ListTile(
                    leading:
                        const Icon(Icons.location_city_outlined, color: _blue),
                    title: Text('${x['name']}',
                        style: const TextStyle(fontWeight: FontWeight.w900)),
                    subtitle: Text(
                        '${x['company_name'] ?? '-'} • ${x['responsible'] ?? '-'}'),
                    onTap: () => open(WorkDetailsV28Screen(
                        profile: widget.profile,
                        workId: _intOrNull(x['id'])!))))),
        section(
            'Empresas',
            _rows(data['companies']),
            (x) => Card(
                child: ListTile(
                    leading: const Icon(Icons.business_outlined, color: _blue),
                    title: Text('${x['name']}'),
                    subtitle: Text('${x['document'] ?? ''}'),
                    onTap: widget.profile['is_admin'] == true
                        ? () => open(const CompaniesAdminScreen())
                        : null))),
        section(
            'Ativos',
            _rows(data['assets']),
            (x) => Card(
                child: ListTile(
                    leading: const Icon(Icons.precision_manufacturing_outlined,
                        color: _blue),
                    title: Text(
                        '${x['asset_number']} • ${x['marca'] ?? ''} ${x['modelo'] ?? ''}'),
                    subtitle: _hasValue(x['placa'])
                        ? Text('Placa: ${x['placa']}')
                        : null,
                    onTap: () => open(MachinesAdminScreen(
                        canEdit: widget.profile['is_admin'] == true))))),
        section(
            'Equipamentos de terceiros',
            _rows(data['third_party']),
            (x) => Card(
                child: ListTile(
                    leading: const Icon(Icons.handyman_outlined, color: _blue),
                    title: Text(
                        _plateDescriptionLabel(x['plate'], x['description'])),
                    subtitle: Text('${x['company_name'] ?? '-'}'),
                    onTap: () => open(ThirdPartyAdminScreen(
                        canEdit: widget.profile['is_admin'] == true))))),
        section(
            'Notas Fiscais',
            _rows(data['invoices']),
            (x) => Card(
                child: ListTile(
                    leading: const Icon(Icons.receipt_outlined, color: _blue),
                    title: Text('NF ${x['invoice_number']}',
                        style: const TextStyle(fontWeight: FontWeight.w900)),
                    subtitle: Text(
                        '${x['supplier_name'] ?? '-'} • ${_fmtLiters(x['total_liters'])}'),
                    onTap: () => open(GeneralRecordsV28Screen(
                        initialInvoice: '${x['invoice_number']}'))))),
        if (!busy &&
            data.isNotEmpty &&
            [
              'movements',
              'works',
              'companies',
              'assets',
              'third_party',
              'invoices'
            ].every((k) => _rows(data[k]).isEmpty))
          const Padding(
              padding: EdgeInsets.all(30),
              child: Center(child: Text('Nenhum resultado encontrado.')))
      ]));
}

class MovementDetailScreen extends StatelessWidget {
  final Map<String, dynamic> item;
  final bool canEdit;
  final bool canCancel;
  const MovementDetailScreen(
      {super.key,
      required this.item,
      this.canEdit = false,
      this.canCancel = false});

  Future<void> _cancelFuelingV87(BuildContext context) async {
    final id = _intOrNull(item['id']);
    if (id == null) return;
    final reason = TextEditingController();
    try {
      final confirmed = await showDialog<bool>(
              context: context,
              builder: (ctx) => AlertDialog(
                    title: const Text('Cancelar abastecimento?'),
                    content: Column(
                        mainAxisSize: MainAxisSize.min,
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                              'Registro ${item['code'] ?? ''} • Nº ${_recordSequenceV28(item)}',
                              style:
                                  const TextStyle(fontWeight: FontWeight.w900)),
                          const SizedBox(height: 8),
                          const Text(
                              'O número sequencial será preservado e nunca será reutilizado. O cancelamento e o estorno ficarão registrados na auditoria.'),
                          const SizedBox(height: 12),
                          TextField(
                              controller: reason,
                              autofocus: true,
                              maxLines: 3,
                              textCapitalization: TextCapitalization.sentences,
                              decoration: const InputDecoration(
                                  labelText:
                                      'Justificativa do cancelamento *')),
                        ]),
                    actions: [
                      TextButton(
                          onPressed: () => Navigator.pop(ctx, false),
                          child: const Text('Voltar')),
                      FilledButton.icon(
                          style: FilledButton.styleFrom(
                              backgroundColor: Colors.red.shade700),
                          onPressed: () {
                            if (reason.text.trim().isEmpty) {
                              ScaffoldMessenger.of(ctx).showSnackBar(const SnackBar(
                                  content: Text(
                                      'Informe a justificativa do cancelamento.')));
                              return;
                            }
                            Navigator.pop(ctx, true);
                          },
                          icon: const Icon(Icons.cancel_outlined),
                          label: const Text('Confirmar cancelamento')),
                    ],
                  )) ??
          false;
      if (!confirmed || !context.mounted) return;
      final result = await api.cancelFuelingV87(id, reason.text.trim());
      if (!context.mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(
          content: Text(result['ok'] == true
              ? 'Abastecimento cancelado. Sequencial preservado e auditoria registrada ✓'
              : '${result['message'] ?? 'Não foi possível cancelar o abastecimento.'}')));
      if (result['ok'] == true && context.mounted) {
        Navigator.pop(context, true);
      }
    } catch (e) {
      if (context.mounted) {
        ScaffoldMessenger.of(context)
            .showSnackBar(SnackBar(content: Text(_friendlyError(e))));
      }
    } finally {
      reason.dispose();
    }
  }

  Future<void> exportOne(BuildContext context) async {
    await Navigator.push(
        context,
        MaterialPageRoute(
            builder: (_) => OfficialPdfPreviewV28Screen(
                items: [item],
                title: 'Prévia • ${item['code'] ?? 'Registro'}')));
  }

  @override
  Widget build(BuildContext context) {
    final asset = item['asset_number'] ??
        item['third_party_plate'] ??
        item['destination_tank'] ??
        item['source_tank'] ??
        '-';
    final source = '${item['source_tank'] ?? ''}'.trim();
    final location = _hasValue(item['location_address'])
        ? '${item['location_address']}'
        : (item['latitude'] != null && item['longitude'] != null
            ? '${item['latitude']}, ${item['longitude']}'
            : '-');
    final fuel =
        _hasValue(item['fuel_type']) ? '${item['fuel_type']}' : 'Não informado';
    final fueling = '${item['type']}' == 'fueling';
    final comboioToComboio = _isComboioToComboio(item);
    final measurementType =
        '${item['measurement_type'] ?? ''}'.trim().toLowerCase();
    final kmValue = item['km_value'];
    final hourmeterValue = item['hourmeter_value'];
    final legacyMeterValue = item['km_hourmeter'];
    final meterUnavailable = item['km_unavailable'] == true;
    final showKm = fueling &&
        (measurementType == 'km' ||
            measurementType == 'both' ||
            (measurementType.isEmpty && kmValue != null));
    final showHourmeter = fueling &&
        (measurementType == 'hourmeter' ||
            measurementType == 'both' ||
            (measurementType.isEmpty && hourmeterValue != null));
    final showLegacyMeter = fueling &&
        measurementType.isEmpty &&
        kmValue == null &&
        hourmeterValue == null &&
        legacyMeterValue != null;
    final syncError = '${item['sync_error'] ?? ''}'.trim();
    final normalizedSyncError = syncError.toUpperCase();
    final conflictErrorDetail = syncError.isNotEmpty &&
            normalizedSyncError != 'CONFLITO • AGUARDANDO ANÁLISE'
        ? '\n$syncError'
        : '';

    final rows = <_RecordDetailData>[
      _RecordDetailData(Icons.calendar_today_outlined, 'Data e hora',
          _fmtDate(item['created_at'])),
      if (_hasValue(item['work']))
        _RecordDetailData(
            Icons.location_city_outlined, 'Obra', '${item['work']}'),
      if (fueling)
        _RecordDetailData(Icons.location_on_outlined, 'Localização', location),
      if (fueling)
        _RecordDetailData(Icons.water_drop_outlined, 'Combustível', fuel),
      if (item['liters'] != null)
        _RecordDetailData(Icons.water_drop_outlined,
            'Abastecimento/Lubrificação', _fmtLiters(item['liters'])),
      if (showKm)
        _RecordDetailData(Icons.speed_outlined, 'KM',
            meterUnavailable ? 'Indisponível' : '${kmValue ?? '-'}'),
      if (showHourmeter)
        _RecordDetailData(Icons.speed_outlined, 'Horímetro',
            meterUnavailable ? 'Indisponível' : '${hourmeterValue ?? '-'}'),
      if (showLegacyMeter)
        _RecordDetailData(Icons.speed_outlined, 'Medição (registro legado)',
            meterUnavailable ? 'Indisponível' : '$legacyMeterValue'),
      if (fueling && _hasValue(item['totalizer_photo_before_captured_at']))
        _RecordDetailData(
            Icons.photo_camera_outlined,
            'Foto do totalizador antes',
            _fmtDate(item['totalizer_photo_before_captured_at'])),
      if (_hasValue(item['receiver']))
        _RecordDetailData(
            Icons.person_outline_rounded, 'Recebedor', '${item['receiver']}'),
      if (_hasValue(item['operator']))
        _RecordDetailData(Icons.person_outline_rounded, 'Quem abasteceu',
            '${item['operator']}'),
      if (_hasValue(source) && item['source_balance_before'] != null)
        _RecordDetailData(Icons.storage_outlined, 'Estoque do $source antes',
            _fmtLiters(item['source_balance_before'])),
      if (_hasValue(source) && item['source_balance_after'] != null)
        _RecordDetailData(Icons.storage_outlined, 'Estoque do $source depois',
            _fmtLiters(item['source_balance_after'])),
      if (item['lubricated'] == true)
        const _RecordDetailData(
            Icons.build_outlined, 'Lubrificação', 'Realizada'),
      if (_hasValue(item['notes']))
        _RecordDetailData(
            Icons.description_outlined, 'Observações', '${item['notes']}'),
    ];

    final media = <MapEntry<String, String>>[];
    final knownMedia = <String>{};
    void mediaOne(String label, dynamic value) {
      if (_hasValue(value)) {
        final p = '$value';
        if (knownMedia.add(p)) media.add(MapEntry(label, p));
      }
    }

    mediaOne('Foto do KM/Horímetro', item['meter_photo_path']);
    mediaOne(
        'Totalizador antes do abastecimento',
        item['totalizer_photo_before_path'] ??
            item['totalizer_evidence_photo_path']);
    mediaOne('Totalizador depois', item['totalizer_photo_after_path']);
    mediaOne(
        'Foto da placa ou identificação', item['identity_evidence_photo_path']);
    mediaOne('Foto adicional', item['extra_evidence_photo_path']);
    for (final p in _rowsFromPaths(item['photo_paths'])) {
      if (knownMedia.add(p)) media.add(MapEntry('Foto do abastecimento', p));
    }
    for (final p in _rowsFromPaths(item['damage_photo_paths'])) {
      if (knownMedia.add(p)) media.add(MapEntry('Medidor danificado', p));
    }
    mediaOne('KM/Horímetro antes', item['km_photo_before_path']);
    mediaOne('Placa ou ativo antes', item['plate_photo_before_path']);
    mediaOne('Assinatura de quem recebe', item['receiver_signature_path']);
    mediaOne('Assinatura de quem abastece', item['operator_signature_path']);

    return Scaffold(
      appBar: AppBar(
        title: const Text('Detalhe do registro'),
        actions: [
          if (fueling)
            Padding(
                padding: const EdgeInsets.symmetric(horizontal: 6),
                child: Center(
                    child: Text('Nº ${_recordSequenceV28(item)}',
                        style: const TextStyle(
                            color: Color(0xFFD51F2A),
                            fontWeight: FontWeight.w900)))),
          if (fueling && canEdit && _intOrNull(item['id']) != null)
            IconButton(
              onPressed: () async {
                final changed = await Navigator.push<bool>(
                    context,
                    MaterialPageRoute(
                        builder: (_) => AdminEditFuelingV48Screen(item: item)));
                if (changed == true && context.mounted)
                  Navigator.pop(context, true);
              },
              tooltip: 'Editar / corrigir abastecimento',
              icon: const Icon(Icons.edit_outlined),
            ),
          if (fueling &&
              canCancel &&
              item['offline_pending'] != true &&
              _intOrNull(item['id']) != null &&
              '${item['status'] ?? 'finalized'}'.toLowerCase() == 'finalized')
            IconButton(
              onPressed: () => _cancelFuelingV87(context),
              tooltip: 'Cancelar abastecimento • somente Admin/Gerente',
              icon: const Icon(Icons.cancel_outlined, color: Colors.red),
            ),
          IconButton(
              onPressed: () => exportOne(context),
              tooltip: 'Exportar PDF',
              icon: const Icon(Icons.picture_as_pdf_outlined)),
        ],
      ),
      body: ListView(
        padding: const EdgeInsets.fromLTRB(16, 16, 16, 60),
        children: [
          if (item['offline_pending'] == true)
            Card(
                color: const Color(0xFFFFF4E5),
                child: Padding(
                    padding: const EdgeInsets.only(bottom: 10),
                    child: Column(children: [
                      ListTile(
                          leading: const Icon(Icons.cloud_off_rounded,
                              color: Colors.orange),
                          title: const Text(
                              'Registro salvo offline neste aparelho',
                              style: TextStyle(fontWeight: FontWeight.w900)),
                          subtitle: Text(item['sync_conflict'] == true
                              ? 'CONFLITO • AGUARDANDO ANÁLISE$conflictErrorDetail'
                              : item['sync_rejected'] == true
                                  ? 'REJEITADO${_hasValue(item['sync_error']) ? '\n${item['sync_error']}' : ''}'
                                  : _hasValue(item['sync_error'])
                                      ? 'PENDENTE • ${item['sync_error']}'
                                      : 'Sequencial local: ${_recordSequenceV28(item)} • aguardando envio ao servidor.')),
                      if (item['sync_conflict'] == true && canEdit)
                        Padding(
                            padding: const EdgeInsets.symmetric(horizontal: 12),
                            child: SizedBox(
                                width: double.infinity,
                                child: OutlinedButton.icon(
                                    onPressed: () => Navigator.push(
                                        context,
                                        MaterialPageRoute(
                                            builder: (_) =>
                                                const OfflineConflictsV58Screen())),
                                    icon:
                                        const Icon(Icons.rule_folder_outlined),
                                    label: const Text('Analisar conflito')))),
                      if (item['sync_conflict'] != true &&
                          item['sync_rejected'] != true)
                        Padding(
                            padding: const EdgeInsets.symmetric(horizontal: 12),
                            child: ValueListenableBuilder<bool>(
                                valueListenable: offlineStore.online,
                                builder: (_, isOnline, __) => ValueListenableBuilder<
                                        bool>(
                                    valueListenable: offlineStore.syncing,
                                    builder: (_, isSyncing, __) => SizedBox(
                                        width: double.infinity,
                                        child: OutlinedButton.icon(
                                            onPressed: !isOnline || isSyncing
                                                ? null
                                                : () =>
                                                    _syncPendingWithFeedbackV74(
                                                        context),
                                            icon: const Icon(
                                                Icons.cloud_upload_outlined),
                                            label: Text(isSyncing
                                                ? 'Sincronizando...'
                                                : isOnline
                                                    ? 'Sincronizar pendentes'
                                                    : 'Sem internet para sincronizar'))))))
                    ]))),
          Card(
              color: comboioToComboio ? _comboioToComboioPale : null,
              child: Padding(
                padding: const EdgeInsets.all(18),
                child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text('${_movementLabelForItem(item)} • $asset',
                          style: const TextStyle(
                              fontSize: 20, fontWeight: FontWeight.w900)),
                      const SizedBox(height: 4),
                      Text('${item['code'] ?? ''}',
                          style: const TextStyle(
                              fontSize: 17,
                              color: Color(0xFFD51F2A),
                              fontWeight: FontWeight.w900)),
                      const SizedBox(height: 14),
                      ...rows.map((r) => _RecordDetailRow(data: r)),
                    ]),
              )),
          if (fueling && _intOrNull(item['id']) != null) ...[
            const SizedBox(height: 14),
            SizedBox(
                width: double.infinity,
                child: FilledButton.icon(
                    onPressed: () => Navigator.push(
                        context,
                        MaterialPageRoute(
                            builder: (_) => MovementTraceV23Screen(
                                movementId: _intOrNull(item['id'])!))),
                    icon: const Icon(Icons.route_rounded),
                    label: const Text('Rastrear origem do combustível'))),
          ],
          if (media.isNotEmpty) ...[
            const SizedBox(height: 16),
            const Text('',
                style: TextStyle(fontSize: 18, fontWeight: FontWeight.w900)),
            const SizedBox(height: 8),
            Wrap(
                spacing: 10,
                runSpacing: 10,
                children: media
                    .map((m) => _MovementMediaTile(label: m.key, path: m.value))
                    .toList()),
          ],
        ],
      ),
    );
  }
}

class AdminEditFuelingV48Screen extends StatefulWidget {
  final Map<String, dynamic> item;
  const AdminEditFuelingV48Screen({super.key, required this.item});
  @override
  State<AdminEditFuelingV48Screen> createState() =>
      _AdminEditFuelingV48ScreenState();
}

class _AdminEditFuelingV48ScreenState extends State<AdminEditFuelingV48Screen> {
  final code = TextEditingController(),
      liters = TextEditingController(),
      km = TextEditingController(),
      hour = TextEditingController(),
      receiver = TextEditingController(),
      receiverCompany = TextEditingController(),
      responsible = TextEditingController(),
      operatorName = TextEditingController(),
      notes = TextEditingController(),
      location = TextEditingController(),
      lat = TextEditingController(),
      lon = TextEditingController(),
      accuracy = TextEditingController(),
      sale = TextEditingController(),
      reason = TextEditingController();
  List<Map<String, dynamic>> works = [], machines = [], thirds = [], tanks = [];
  int? workId, machineId, thirdId, sourceTankId;
  String fuel = 'Diesel';
  bool lubricated = false, loading = true, saving = false;
  String? error;
  String? meterPath,
      totalizerPath,
      identityPath,
      extraPath,
      receiverSigPath,
      operatorSigPath,
      identityKind;
  DateTime? occurredAt, locationCapturedAt;
  XFile? newMeter, newTotalizer, newIdentity, newExtra;
  Uint8List? newReceiverSig, newOperatorSig;
  @override
  void initState() {
    super.initState();
    final x = widget.item;
    code.text = '${x['code'] ?? ''}';
    liters.text = x['liters'] == null ? '' : '${x['liters']}';
    km.text = x['km_value'] == null ? '' : '${x['km_value']}';
    hour.text = x['hourmeter_value'] == null ? '' : '${x['hourmeter_value']}';
    receiver.text = '${x['receiver'] ?? ''}';
    receiverCompany.text = '${x['receiver_company'] ?? ''}';
    responsible.text = '${x['work_responsible'] ?? ''}';
    operatorName.text = '${x['operator'] ?? ''}';
    notes.text = '${x['notes'] ?? ''}';
    location.text = '${x['location_address'] ?? ''}';
    lat.text = x['latitude'] == null ? '' : '${x['latitude']}';
    lon.text = x['longitude'] == null ? '' : '${x['longitude']}';
    accuracy.text =
        x['location_accuracy_m'] == null ? '' : '${x['location_accuracy_m']}';
    sale.text =
        x['sale_price_per_liter'] == null ? '' : '${x['sale_price_per_liter']}';
    workId = _intOrNull(x['work_id']);
    machineId = _intOrNull(x['asset_id']);
    thirdId = _intOrNull(x['third_party_vehicle_id']);
    sourceTankId = _intOrNull(x['source_tank_id']);
    fuel = '${x['fuel_type'] ?? 'Diesel'}';
    lubricated = x['lubricated'] == true;
    meterPath = x['meter_photo_path']?.toString();
    totalizerPath = x['totalizer_evidence_photo_path']?.toString();
    identityPath = x['identity_evidence_photo_path']?.toString();
    extraPath = x['extra_evidence_photo_path']?.toString();
    receiverSigPath = x['receiver_signature_path']?.toString();
    operatorSigPath = x['operator_signature_path']?.toString();
    identityKind = x['identity_evidence_kind']?.toString();
    occurredAt =
        DateTime.tryParse('${x['occurred_at'] ?? x['created_at'] ?? ''}');
    locationCapturedAt =
        DateTime.tryParse('${x['location_captured_at'] ?? ''}');
    load();
  }

  Future<XFile?> cam() => ImagePicker()
      .pickImage(source: ImageSource.camera, imageQuality: 75, maxWidth: 1600);
  Future<Uint8List?> sign(String t) => Navigator.push<Uint8List>(
      context,
      MaterialPageRoute(
          builder: (_) => SignatureCaptureOnlineScreen(title: t),
          fullscreenDialog: true));
  double? number(TextEditingController c) {
    final t = c.text.trim().replaceAll(',', '.');
    return t.isEmpty ? null : double.tryParse(t);
  }

  Future<void> load() async {
    try {
      final p = await api.profile();
      if (p['is_admin'] != true && p['can_correct'] != true)
        throw Exception(
            'Seu perfil não possui permissão para corrigir abastecimentos');
      final ref = await api.referenceData();
      final ws = _rows(ref['works']),
          ms = _rows(ref['machines']),
          ts = _rows(ref['third_party_vehicles']),
          us = _rows(ref['tanks'])
              .where((x) =>
                  x['active'] != false &&
                  ['comboio', 'stationary', 'truck']
                      .contains('${x['tank_type']}'))
              .toList();
      if (sourceTankId == null) {
        for (final t in us) {
          if ('${t['code']}' == '${widget.item['source_tank']}') {
            sourceTankId = _intOrNull(t['id']);
            break;
          }
        }
      }
      if (mounted)
        setState(() {
          works = ws;
          machines = ms;
          thirds = ts;
          tanks = us;
          loading = false;
        });
    } catch (e) {
      if (mounted)
        setState(() {
          error = _friendlyError(e);
          loading = false;
        });
    }
  }

  Future<String?> up(XFile? x, String kind, String? existing) async => x == null
      ? existing
      : api.uploadBytes(await x.readAsBytes(), kind,
          mime: x.mimeType ?? 'image/jpeg');
  Future<void> pickDate() async {
    final base = (occurredAt ?? DateTime.now()).toLocal();
    final d = await showDatePicker(
        context: context,
        firstDate: DateTime(2020),
        lastDate: DateTime.now().add(const Duration(days: 1)),
        initialDate: base);
    if (d == null || !mounted) return;
    final t = await showTimePicker(
        context: context, initialTime: TimeOfDay.fromDateTime(base));
    if (t == null) return;
    setState(
        () => occurredAt = DateTime(d.year, d.month, d.day, t.hour, t.minute));
  }

  Future<void> save() async {
    if (saving) return;
    final l = number(liters), k = number(km), h = number(hour);
    if (sourceTankId == null || l == null || l <= 0) {
      setState(() => error = 'Informe origem e quantidade válida.');
      return;
    }
    if ((machineId == null) == (thirdId == null)) {
      setState(() => error =
          'Selecione somente um destino: Ativo próprio ou Equipamento de terceiros.');
      return;
    }
    if (reason.text.trim().isEmpty) {
      setState(() => error = 'Informe o motivo da correção.');
      return;
    }
    setState(() {
      saving = true;
      error = null;
    });
    try {
      final paths = await Future.wait<String?>([
        up(newMeter, 'km_horimetro_correcao', meterPath),
        up(newTotalizer, 'totalizador_correcao', totalizerPath),
        up(newIdentity, 'identificacao_correcao', identityPath),
        up(newExtra, 'abastecimento_extra_correcao', extraPath)
      ]);
      final rs = newReceiverSig == null
          ? receiverSigPath
          : await api.uploadBytes(
              newReceiverSig!, 'assinatura_recebedor_correcao');
      final os = newOperatorSig == null
          ? operatorSigPath
          : await api.uploadBytes(
              newOperatorSig!, 'assinatura_abastecedor_correcao');
      await api.adminEditFuelingV48(
          movementId: _intOrNull(widget.item['id'])!,
          code: code.text.trim(),
          sourceTankId: sourceTankId!,
          workId: workId,
          machineId: machineId,
          thirdPartyVehicleId: thirdId,
          liters: l,
          fuelType: fuel,
          kmValue: k,
          hourmeterValue: h,
          receiverName: receiver.text.trim(),
          receiverCompany: receiverCompany.text.trim(),
          responsibleName: responsible.text.trim(),
          operatorName: operatorName.text.trim(),
          notes: notes.text.trim(),
          locationAddress: location.text.trim(),
          latitude: number(lat),
          longitude: number(lon),
          locationCapturedAt: locationCapturedAt,
          locationAccuracyM: number(accuracy),
          salePrice: number(sale),
          lubricated: lubricated,
          meterPhotoPath: paths[0],
          totalizerPhotoPath: paths[1],
          identityPhotoPath: paths[2],
          identityKind: identityKind,
          extraPhotoPath: paths[3],
          receiverSignaturePath: rs,
          operatorSignaturePath: os,
          occurredAt: occurredAt,
          reason: reason.text.trim());
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(
          content: Text('Abastecimento corrigido e estoque recalculado ✓')));
      Navigator.pop(context, true);
    } catch (e) {
      if (mounted) setState(() => error = _friendlyError(e));
    } finally {
      if (mounted) setState(() => saving = false);
    }
  }

  @override
  void dispose() {
    for (final c in [
      code,
      liters,
      km,
      hour,
      receiver,
      receiverCompany,
      responsible,
      operatorName,
      notes,
      location,
      lat,
      lon,
      accuracy,
      sale,
      reason
    ]) {
      c.dispose();
    }
    super.dispose();
  }

  @override
  Widget build(BuildContext context) => Scaffold(
      appBar: AppBar(
          title: const Text('Editar / corrigir abastecimento'),
          actions: [
            Padding(
                padding: const EdgeInsets.symmetric(horizontal: 12),
                child: Center(
                    child: Text('Nº ${_recordSequenceV28(widget.item)}',
                        style: const TextStyle(
                            color: Color(0xFFD51F2A),
                            fontSize: 17,
                            fontWeight: FontWeight.w900))))
          ]),
      body: loading
          ? const Center(child: CircularProgressIndicator())
          : ListView(
              padding: const EdgeInsets.fromLTRB(16, 16, 16, 40),
              children: [
                  const Card(
                      child: ListTile(
                          leading:
                              Icon(Icons.verified_user_outlined, color: _blue),
                          title: Text('Correção autorizada e auditada',
                              style: TextStyle(fontWeight: FontWeight.w900)),
                          subtitle: Text(
                              'Admin, gerente ou supervisor com permissão podem corrigir horímetro e outros dados. Alterações em litros/origem recalculam estoque e FIFO. Dados anteriores, novos e motivo ficam preservados na auditoria.'))),
                  if (error != null)
                    Card(
                        child: ListTile(
                            leading: const Icon(Icons.error_outline,
                                color: Colors.red),
                            title: Text(error!))),
                  TextField(
                      controller: reason,
                      enabled: !saving,
                      maxLines: 2,
                      decoration: const InputDecoration(
                          labelText: 'Motivo da correção *',
                          prefixIcon: Icon(Icons.history_edu_outlined))),
                  const SizedBox(height: 10),
                  TextField(
                      controller: code,
                      enabled: !saving,
                      decoration:
                          const InputDecoration(labelText: 'Nº do registro *')),
                  const SizedBox(height: 10),
                  DropdownButtonFormField<int>(
                      initialValue: sourceTankId,
                      isExpanded: true,
                      decoration: const InputDecoration(
                          labelText: 'Origem do combustível *'),
                      items: tanks
                          .map((x) => DropdownMenuItem(
                              value: _intOrNull(x['id']),
                              child: Text('${x['code']} • ${x['name']}')))
                          .toList(),
                      onChanged: saving
                          ? null
                          : (v) => setState(() => sourceTankId = v)),
                  const SizedBox(height: 10),
                  DropdownButtonFormField<int?>(
                      initialValue: workId,
                      isExpanded: true,
                      decoration: const InputDecoration(labelText: 'Obra'),
                      items: [
                        const DropdownMenuItem<int?>(
                            value: null, child: Text('Sem obra')),
                        ...works.map((x) => DropdownMenuItem<int?>(
                            value: _intOrNull(x['id']),
                            child: Text('${x['name']}')))
                      ],
                      onChanged:
                          saving ? null : (v) => setState(() => workId = v)),
                  const SizedBox(height: 10),
                  Text('Destino do abastecimento',
                      style: Theme.of(context)
                          .textTheme
                          .titleSmall
                          ?.copyWith(fontWeight: FontWeight.w900)),
                  const SizedBox(height: 6),
                  DropdownButtonFormField<int?>(
                      initialValue: machineId,
                      isExpanded: true,
                      decoration:
                          const InputDecoration(labelText: 'Ativo próprio'),
                      items: [
                        const DropdownMenuItem<int?>(
                            value: null, child: Text('Nenhum')),
                        ...machines.map((x) => DropdownMenuItem<int?>(
                            value: _intOrNull(x['id']),
                            child: Text(
                                '${x['numeroAtivo'] ?? '-'} • ${x['modelo'] ?? ''}')))
                      ],
                      onChanged: (saving || thirdId != null)
                          ? null
                          : (v) => setState(() {
                                machineId = v;
                                if (v != null) thirdId = null;
                              })),
                  const SizedBox(height: 8),
                  DropdownButtonFormField<int?>(
                      initialValue: thirdId,
                      isExpanded: true,
                      decoration: const InputDecoration(
                          labelText: 'Equipamento de terceiros'),
                      items: [
                        const DropdownMenuItem<int?>(
                            value: null, child: Text('Nenhum')),
                        ...thirds.map((x) => DropdownMenuItem<int?>(
                            value: _intOrNull(x['id']),
                            child: Text(_plateDescriptionLabel(
                                x['plate'], x['description']))))
                      ],
                      onChanged: (saving || machineId != null)
                          ? null
                          : (v) => setState(() {
                                thirdId = v;
                                if (v != null) machineId = null;
                              })),
                  const SizedBox(height: 10),
                  DropdownButtonFormField<String>(
                      initialValue:
                          _fuelTypes.contains(fuel) ? fuel : _fuelTypes.first,
                      decoration:
                          const InputDecoration(labelText: 'Combustível'),
                      items: _fuelTypes
                          .map(
                              (x) => DropdownMenuItem(value: x, child: Text(x)))
                          .toList(),
                      onChanged: saving
                          ? null
                          : (v) => setState(() => fuel = v ?? fuel)),
                  const SizedBox(height: 8),
                  Row(children: [
                    Expanded(
                        child: TextField(
                            controller: liters,
                            enabled: !saving,
                            keyboardType: const TextInputType.numberWithOptions(
                                decimal: true),
                            decoration: const InputDecoration(
                                labelText: 'Quantidade (L) *'))),
                    const SizedBox(width: 8),
                    Expanded(
                        child: TextField(
                            controller: sale,
                            enabled: !saving,
                            keyboardType: const TextInputType.numberWithOptions(
                                decimal: true),
                            decoration: const InputDecoration(
                                labelText: 'Preço venda/L')))
                  ]),
                  const SizedBox(height: 8),
                  Row(children: [
                    Expanded(
                        child: TextField(
                            controller: km,
                            enabled: !saving,
                            keyboardType: const TextInputType.numberWithOptions(
                                decimal: true),
                            decoration:
                                const InputDecoration(labelText: 'KM'))),
                    const SizedBox(width: 8),
                    Expanded(
                        child: TextField(
                            controller: hour,
                            enabled: !saving,
                            keyboardType: const TextInputType.numberWithOptions(
                                decimal: true),
                            decoration:
                                const InputDecoration(labelText: 'Horímetro')))
                  ]),
                  const SizedBox(height: 8),
                  SwitchListTile(
                      value: lubricated,
                      onChanged:
                          saving ? null : (v) => setState(() => lubricated = v),
                      title: const Text('Lubrificou?')),
                  TextField(
                      controller: receiver,
                      enabled: !saving,
                      decoration: const InputDecoration(
                          labelText: 'Responsável pelo recebimento')),
                  const SizedBox(height: 8),
                  TextField(
                      controller: receiverCompany,
                      enabled: !saving,
                      decoration: const InputDecoration(
                          labelText: 'Empresa de quem recebeu')),
                  const SizedBox(height: 8),
                  TextField(
                      controller: responsible,
                      enabled: !saving,
                      decoration: const InputDecoration(
                          labelText: 'Responsável da obra')),
                  const SizedBox(height: 8),
                  TextField(
                      controller: operatorName,
                      enabled: !saving,
                      decoration: const InputDecoration(
                          labelText: 'Operador / quem abasteceu')),
                  const SizedBox(height: 8),
                  TextField(
                      controller: location,
                      enabled: !saving,
                      maxLines: 2,
                      decoration: const InputDecoration(
                          labelText: 'Localização / endereço')),
                  const SizedBox(height: 8),
                  Row(children: [
                    Expanded(
                        child: TextField(
                            controller: lat,
                            enabled: !saving,
                            keyboardType: const TextInputType.numberWithOptions(
                                decimal: true, signed: true),
                            decoration:
                                const InputDecoration(labelText: 'Latitude'))),
                    const SizedBox(width: 8),
                    Expanded(
                        child: TextField(
                            controller: lon,
                            enabled: !saving,
                            keyboardType: const TextInputType.numberWithOptions(
                                decimal: true, signed: true),
                            decoration:
                                const InputDecoration(labelText: 'Longitude')))
                  ]),
                  const SizedBox(height: 8),
                  TextField(
                      controller: accuracy,
                      enabled: !saving,
                      keyboardType:
                          const TextInputType.numberWithOptions(decimal: true),
                      decoration:
                          const InputDecoration(labelText: 'Precisão GPS (m)')),
                  const SizedBox(height: 8),
                  ListTile(
                      contentPadding: EdgeInsets.zero,
                      title: const Text('Data/hora do abastecimento'),
                      subtitle: Text(occurredAt == null
                          ? '-'
                          : _fmtDate(occurredAt!.toIso8601String())),
                      trailing: IconButton(
                          onPressed: saving ? null : pickDate,
                          icon: const Icon(Icons.edit_calendar_outlined))),
                  TextField(
                      controller: notes,
                      enabled: !saving,
                      minLines: 3,
                      maxLines: 5,
                      decoration:
                          const InputDecoration(labelText: 'Observações')),
                  const SizedBox(height: 12),
                  OutlinedButton.icon(
                      onPressed: saving
                          ? null
                          : () async {
                              final x = await cam();
                              if (x != null) setState(() => newMeter = x);
                            },
                      icon: const Icon(Icons.camera_alt_outlined),
                      label: Text(newMeter != null
                          ? 'Nova foto KM/Horímetro ✓'
                          : meterPath == null
                              ? 'Adicionar foto KM/Horímetro'
                              : 'Substituir foto KM/Horímetro')),
                  OutlinedButton.icon(
                      onPressed: saving
                          ? null
                          : () async {
                              final x = await cam();
                              if (x != null) setState(() => newTotalizer = x);
                            },
                      icon: const Icon(Icons.camera_alt_outlined),
                      label: Text(newTotalizer != null
                          ? 'Nova foto totalizador ✓'
                          : totalizerPath == null
                              ? 'Adicionar foto totalizador'
                              : 'Substituir foto totalizador')),
                  OutlinedButton.icon(
                      onPressed: saving
                          ? null
                          : () async {
                              final x = await cam();
                              if (x != null) setState(() => newIdentity = x);
                            },
                      icon: const Icon(Icons.camera_alt_outlined),
                      label: Text(newIdentity != null
                          ? 'Nova foto identificação ✓'
                          : identityPath == null
                              ? 'Adicionar foto identificação'
                              : 'Substituir foto identificação')),
                  OutlinedButton.icon(
                      onPressed: saving
                          ? null
                          : () async {
                              final x = await cam();
                              if (x != null) setState(() => newExtra = x);
                            },
                      icon: const Icon(Icons.camera_alt_outlined),
                      label: Text(newExtra != null
                          ? 'Nova foto extra ✓'
                          : extraPath == null
                              ? 'Adicionar foto extra'
                              : 'Substituir foto extra')),
                  OutlinedButton.icon(
                      onPressed: saving
                          ? null
                          : () async {
                              final x = await sign(
                                  'Nova assinatura do responsável pelo recebimento');
                              if (x != null) setState(() => newReceiverSig = x);
                            },
                      icon: const Icon(Icons.draw_outlined),
                      label: Text(newReceiverSig != null
                          ? 'Nova assinatura do recebedor ✓'
                          : 'Substituir assinatura do recebedor')),
                  OutlinedButton.icon(
                      onPressed: saving
                          ? null
                          : () async {
                              final x = await sign(
                                  'Nova assinatura de quem abasteceu');
                              if (x != null) setState(() => newOperatorSig = x);
                            },
                      icon: const Icon(Icons.draw_outlined),
                      label: Text(newOperatorSig != null
                          ? 'Nova assinatura do operador ✓'
                          : 'Substituir assinatura do operador')),
                  const SizedBox(height: 14),
                  FilledButton.icon(
                      onPressed: saving ? null : save,
                      icon: saving
                          ? const SizedBox(
                              width: 18,
                              height: 18,
                              child: CircularProgressIndicator(strokeWidth: 2))
                          : const Icon(Icons.save_outlined),
                      label: Text(saving
                          ? 'Recalculando e salvando...'
                          : 'Salvar correção completa')),
                ]));
}

class _RecordDetailData {
  final IconData icon;
  final String label;
  final String value;
  const _RecordDetailData(this.icon, this.label, this.value);
}

class _RecordDetailRow extends StatelessWidget {
  final _RecordDetailData data;
  const _RecordDetailRow({required this.data});
  @override
  Widget build(BuildContext context) => Container(
        padding: const EdgeInsets.symmetric(vertical: 12),
        decoration: const BoxDecoration(
            border: Border(bottom: BorderSide(color: Color(0xFFE5EAF1)))),
        child: Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Container(
              width: 44,
              height: 44,
              decoration: const BoxDecoration(
                  color: Color(0xFFEAF1FF), shape: BoxShape.circle),
              child: Icon(data.icon, color: _blue)),
          const SizedBox(width: 14),
          Expanded(
              child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                Text(data.label,
                    style: const TextStyle(
                        color: _ink, fontWeight: FontWeight.w700)),
                const SizedBox(height: 3),
                Text(data.value,
                    style:
                        const TextStyle(fontSize: 16, color: Colors.black87)),
              ])),
        ]),
      );
}

class _MovementMediaTile extends StatelessWidget {
  final String label;
  final String path;
  const _MovementMediaTile({required this.label, required this.path});

  @override
  Widget build(BuildContext context) {
    final width = (MediaQuery.sizeOf(context).width - 44) / 2;
    return SizedBox(
      width: width,
      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        Container(
          height: 115,
          width: double.infinity,
          decoration: BoxDecoration(
              color: Colors.white,
              borderRadius: BorderRadius.circular(12),
              border: Border.all(color: const Color(0xFFE2E8F0))),
          child: FutureBuilder<Uint8List?>(
            future: api.downloadMedia(path),
            builder: (_, s) {
              if (s.connectionState != ConnectionState.done)
                return const Center(child: CircularProgressIndicator());
              if (s.data == null)
                return const Center(child: Icon(Icons.broken_image_outlined));
              return ClipRRect(
                  borderRadius: BorderRadius.circular(11),
                  child: Image.memory(s.data!, fit: BoxFit.contain));
            },
          ),
        ),
        const SizedBox(height: 4),
        Text(label,
            style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w700)),
      ]),
    );
  }
}

List<String> _rowsFromPaths(dynamic value) {
  if (value is List)
    return value.map((e) => '$e').where((e) => e.isNotEmpty).toList();
  return const [];
}

class FuelPdfReport {
  static const Color _iconBlue = Color(0xFF08367C);

  static Future<Uint8List> _materialIconPng(IconData icon, Color color) async {
    const canvasSize = 72.0;
    const glyphSize = 52.0;
    final recorder = ui.PictureRecorder();
    final canvas = ui.Canvas(recorder);
    final painter = TextPainter(
      text: TextSpan(
          text: String.fromCharCode(icon.codePoint),
          style: TextStyle(
              fontFamily: icon.fontFamily,
              package: icon.fontPackage,
              fontSize: glyphSize,
              color: color)),
      textDirection: ui.TextDirection.ltr,
      textAlign: TextAlign.center,
    );
    painter.layout();
    painter.paint(
        canvas,
        ui.Offset((canvasSize - painter.width) / 2,
            (canvasSize - painter.height) / 2));
    final picture = recorder.endRecording();
    final image = await picture.toImage(canvasSize.toInt(), canvasSize.toInt());
    final data = await image.toByteData(format: ui.ImageByteFormat.png);
    image.dispose();
    picture.dispose();
    if (data == null) throw StateError('Falha ao preparar ícone para o PDF.');
    return data.buffer.asUint8List();
  }

  static String _nfs(Map<String, dynamic> ctx) {
    final values = _rows(ctx['nfs'])
        .map((x) =>
            'NF ${x['invoice_number']}${_hasValue(x['batch_number']) ? ' / Lote ${x['batch_number']}' : ''}')
        .toSet()
        .toList();
    return values.isEmpty ? '-' : values.join(' • ');
  }

  static String _fuelOrigin(Map<String, dynamic> ctx, Map<String, dynamic> x) {
    final fromContext = '${ctx['origem'] ?? ''}'.trim();
    if (fromContext.isNotEmpty && fromContext != 'null') return fromContext;
    final source = '${x['source_tank'] ?? ''}'.trim();
    if (source.isNotEmpty && source != 'null') return source;
    final code = '${x['code'] ?? ''}'.trim();
    final match = RegExp(r'^(.+?)-\d+$').firstMatch(code);
    return (match?.group(1) ?? code).trim();
  }

  static String _fuelSequence(Map<String, dynamic> x) {
    if (x['offline_pending'] == true) {
      final local = _intOrNull(x['offline_sequence_v74']);
      if (local != null) return local.toString().padLeft(4, '0');
    }
    final code = '${x['code'] ?? ''}'.trim();
    final match = RegExp(r'(\d+)$').firstMatch(code);
    final raw = match?.group(1) ?? '';
    final number = int.tryParse(raw);
    if (number == null) return raw.isEmpty ? '0000' : raw;
    return number.toString().padLeft(4, '0');
  }

  static String _fuelLabel(dynamic value) {
    final raw = '${value ?? ''}'.trim();
    final low = raw.toLowerCase();
    if (low == 'diesel' ||
        low == 'diesel s10' ||
        low == 'óleo diesel s10' ||
        low == 'oleo diesel s10') return 'Diesel S10';
    if (low == 'arla' || low == 'arla32' || low == 'arla 32') return 'Arla 32';
    return raw.isEmpty ? '-' : raw;
  }

  static String _measurementTypeForPdf(Map<String, dynamic> x) {
    final configured = '${x['measurement_type'] ?? ''}'.trim().toLowerCase();
    if (configured == 'km' ||
        configured == 'hourmeter' ||
        configured == 'both' ||
        configured == 'none') {
      return configured;
    }
    final hasKm = x['km_value'] != null;
    final hasHour = x['hourmeter_value'] != null;
    if (hasKm && hasHour) return 'both';
    if (hasKm) return 'km';
    if (hasHour) return 'hourmeter';
    return 'none';
  }

  static Future<Uint8List> build(List<Map<String, dynamic>> items) async {
    final doc = pw.Document();
    final regular = pw.Font.helvetica();
    final bold = pw.Font.helveticaBold();
    final navy = PdfColor.fromHex('#062A69');
    final royal = PdfColor.fromHex('#0E58C7');
    final line = PdfColor.fromHex('#D9E2EE');
    final text = PdfColor.fromHex('#20242B');

    final iconSet = <IconData>[
      Icons.local_gas_station_rounded,
      Icons.local_shipping_outlined,
      Icons.location_city_outlined,
      Icons.location_on_outlined,
      Icons.water_drop_outlined,
      Icons.person_outline_rounded,
      Icons.speed_outlined,
      Icons.storage_outlined,
      Icons.assignment_outlined,
      Icons.draw_outlined,
      Icons.business_outlined,
      Icons.receipt_long_outlined,
      Icons.swap_horiz_rounded,
      Icons.precision_manufacturing_outlined,
    ];
    final blue = <int, pw.MemoryImage>{};
    final white = <int, pw.MemoryImage>{};
    for (final i in iconSet) {
      blue[i.codePoint] = pw.MemoryImage(await _materialIconPng(i, _iconBlue));
    }
    white[Icons.local_gas_station_rounded.codePoint] = pw.MemoryImage(
        await _materialIconPng(Icons.local_gas_station_rounded, Colors.white));
    white[Icons.assignment_outlined.codePoint] = pw.MemoryImage(
        await _materialIconPng(Icons.assignment_outlined, Colors.white));

    pw.Widget icon(IconData d, {double size = 22, bool isWhite = false}) {
      final m = (isWhite ? white : blue)[d.codePoint];
      if (m == null) return pw.SizedBox(width: size, height: size);
      return pw.Image(m, width: size, height: size, fit: pw.BoxFit.contain);
    }

    pw.Widget row(IconData d, String label, String value, PdfColor accent) {
      return pw.Container(
        constraints: const pw.BoxConstraints(minHeight: 30),
        padding: const pw.EdgeInsets.symmetric(vertical: 4),
        decoration: pw.BoxDecoration(
            border: pw.Border(bottom: pw.BorderSide(color: line, width: .6))),
        child:
            pw.Row(crossAxisAlignment: pw.CrossAxisAlignment.center, children: [
          pw.SizedBox(width: 28, child: pw.Center(child: icon(d, size: 17))),
          pw.SizedBox(width: 5),
          pw.Expanded(
              child: pw.Column(
                  crossAxisAlignment: pw.CrossAxisAlignment.start,
                  mainAxisAlignment: pw.MainAxisAlignment.center,
                  children: [
                pw.Text(label,
                    style:
                        pw.TextStyle(font: bold, fontSize: 8.1, color: accent)),
                pw.SizedBox(height: 1),
                pw.Text(value,
                    style: pw.TextStyle(
                        font: regular, fontSize: 9.2, color: text)),
              ])),
        ]),
      );
    }

    pw.Widget pairRows(pw.Widget left, pw.Widget right) {
      return pw.Row(crossAxisAlignment: pw.CrossAxisAlignment.start, children: [
        pw.Expanded(child: left),
        pw.SizedBox(width: 8),
        pw.Expanded(child: right),
      ]);
    }

    pw.Widget signature(
        String title, String name, Uint8List? bytes, PdfColor accent) {
      return pw.Expanded(
          child: pw.Container(
        height: 72,
        padding: const pw.EdgeInsets.all(8),
        decoration: pw.BoxDecoration(
            border: pw.Border.all(color: line),
            borderRadius: const pw.BorderRadius.all(pw.Radius.circular(6))),
        child: pw.Column(
            crossAxisAlignment: pw.CrossAxisAlignment.start,
            children: [
              pw.Row(children: [
                icon(Icons.draw_outlined, size: 15),
                pw.SizedBox(width: 4),
                pw.Text(title,
                    style:
                        pw.TextStyle(font: bold, fontSize: 8.5, color: accent))
              ]),
              pw.SizedBox(height: 4),
              pw.Expanded(
                  child: pw.Center(
                      child: bytes == null
                          ? pw.Text('Assinatura não disponível',
                              style: pw.TextStyle(
                                  font: regular,
                                  fontSize: 7.5,
                                  color: PdfColors.grey600))
                          : pw.Image(pw.MemoryImage(bytes),
                              fit: pw.BoxFit.contain))),
              pw.Container(height: .5, color: line),
              pw.Text(name,
                  style: pw.TextStyle(font: regular, fontSize: 8, color: text),
                  maxLines: 1),
            ]),
      ));
    }

    for (final x in items) {
      final id = _intOrNull(x['id']);
      Map<String, dynamic> ctx = x['report_context'] is Map
          ? _map(x['report_context'])
          : <String, dynamic>{};
      if (id != null) {
        try {
          ctx = await api.reportContextV23(id);
        } catch (_) {}
      }
      final inst = _map(ctx['institutional_company']);
      final itemInst = _map(x['institutional_company']);
      final companyName = _hasValue(inst['company_name'])
          ? '${inst['company_name']}'
          : _hasValue(itemInst['company_name'])
              ? '${itemInst['company_name']}'
              : _hasValue(ctx['empresa'])
                  ? '${ctx['empresa']}'
                  : 'Empresa não cadastrada';
      final type = '${x['type'] ?? ''}';
      final transfer = type == 'tank_transfer';
      final fueling = type == 'fueling';
      final refinery = type == 'refinery_entry';
      Map<String, dynamic> pdfSale = {};
      if (fueling && id != null) {
        try {
          pdfSale = await api.pdfSaleV41(id);
        } catch (_) {}
      }
      final accentN = transfer ? PdfColor.fromHex('#9A4D00') : navy;
      final accent = transfer ? PdfColor.fromHex('#E67E22') : royal;
      final own = [
        if (_hasValue(x['asset_number'])) '${x['asset_number']}',
        if (_hasValue(x['asset_model'])) '${x['asset_model']}'
      ].join(' • ');
      final third = [
        if (_hasValue(x['third_party_plate'])) '${x['third_party_plate']}',
        if (_hasValue(x['third_party_description']))
          '${x['third_party_description']}'
      ].join(' • ');
      final equipment =
          [if (own.isNotEmpty) own, if (third.isNotEmpty) third].join(' + ');
      final title =
          '${_movementLabelForItem(x)}${equipment.isNotEmpty ? ' • $equipment' : ''}';
      final fuelOrigin = _fuelOrigin(ctx, x);
      final fuelSequence = _fuelSequence(x);
      final operator = '${x['operator'] ?? '-'}';
      final receiver = '${x['receiver'] ?? '-'}';
      final nfs = _nfs(ctx);
      final rows = <pw.Widget>[];

      if (refinery) {
        rows.add(row(Icons.business_outlined, 'Empresa compradora',
            '${ctx['empresa_compradora'] ?? companyName}', accent));
        rows.add(row(Icons.business_outlined, 'Fornecedor do combustível',
            '${ctx['fornecedor_combustivel'] ?? '-'}', accent));
        rows.add(row(
            Icons.receipt_long_outlined, 'Nota Fiscal / lote', nfs, accent));
        rows.add(row(Icons.water_drop_outlined, 'Combustível',
            '${x['fuel_type'] ?? '-'}', accent));
        rows.add(row(Icons.local_gas_station_rounded, 'Volume recebido',
            _fmtLiters(x['liters']), accent));
        rows.add(row(Icons.local_shipping_outlined, 'Caminhão-tanque',
            '${x['destination_tank'] ?? '-'}', accent));
        rows.add(row(
            Icons.person_outline_rounded, 'Quem registrou', operator, accent));
      } else if (transfer) {
        rows.add(row(Icons.business_outlined, 'Empresa',
            '${ctx['empresa'] ?? companyName}', accent));
        rows.add(row(Icons.swap_horiz_rounded, 'Tipo de movimento',
            'Transferência interna — sem venda', accent));
        rows.add(row(Icons.storage_outlined, 'Origem',
            '${ctx['origem'] ?? x['source_tank'] ?? '-'}', accent));
        rows.add(row(Icons.storage_outlined, 'Destino',
            '${ctx['destino'] ?? x['destination_tank'] ?? '-'}', accent));
        rows.add(row(Icons.water_drop_outlined, 'Volume',
            _fmtLiters(x['liters']), accent));
        rows.add(row(Icons.person_outline_rounded, 'Responsável doador',
            '${x['donor_responsible'] ?? operator}', accent));
        rows.add(row(Icons.person_outline_rounded, 'Responsável recebedor',
            '${x['receiver_responsible'] ?? receiver}', accent));
        rows.add(row(Icons.receipt_long_outlined, 'NF(s)/Lote(s) envolvidos',
            nfs, accent));
      } else {
        final litersValue = _num(x['liters']);
        final salePriceRaw =
            pdfSale['sale_price_per_liter'] ?? x['sale_price_per_liter'];
        final salePriceValue = _num(salePriceRaw);
        final totalSaleValue = pdfSale['total_value'] ??
            x['sale_total'] ??
            x['total_value'] ??
            (litersValue * salePriceValue);

        rows.add(pairRows(
          row(
              Icons.business_outlined,
              'Empresa fornecedora/vendedora do combustível',
              '${ctx['empresa_fornecedora_vendedora'] ?? companyName}',
              navy),
          row(Icons.business_outlined, 'Empresa recebedora/compradora',
              '${ctx['empresa_recebedora_compradora'] ?? '-'}', navy),
        ));
        rows.add(pairRows(
          row(Icons.location_city_outlined, 'Obra',
              '${ctx['obra'] ?? x['work'] ?? '-'}', navy),
          row(Icons.person_outline_rounded, 'Responsável',
              '${ctx['responsavel_obra'] ?? '-'}', navy),
        ));
        rows.add(pairRows(
          row(
              Icons.precision_manufacturing_outlined,
              'Equipamento abastecido',
              equipment.isEmpty
                  ? '-'
                  : equipment
                      .replaceAll('\u2022', '-')
                      .replaceAll('\u00B7', '-')
                      .replaceAll('\u2013', '-')
                      .replaceAll('\u2014', '-')
                      .replaceAll('\uFFFD', '-'),
              navy),
          row(Icons.business_outlined, 'Proprietário do equipamento',
              '${ctx['proprietario_equipamento'] ?? '-'}', navy),
        ));
        rows.add(pairRows(
          row(Icons.location_on_outlined, 'Localização',
              '${x['location_address'] ?? '-'}', navy),
          row(Icons.water_drop_outlined, 'Combustível',
              _fuelLabel(x['fuel_type']), navy),
        ));
        final measurementType = _measurementTypeForPdf(x);
        if (measurementType == 'both') {
          rows.add(pairRows(
            row(Icons.speed_outlined, 'KM', '${x['km_value'] ?? '-'}', navy),
            row(Icons.speed_outlined, 'Horímetro',
                '${x['hourmeter_value'] ?? '-'}', navy),
          ));
        } else if (measurementType == 'km') {
          rows.add(
              row(Icons.speed_outlined, 'KM', '${x['km_value'] ?? '-'}', navy));
        } else if (measurementType == 'hourmeter') {
          rows.add(row(Icons.speed_outlined, 'Horímetro',
              '${x['hourmeter_value'] ?? '-'}', navy));
        }
        rows.add(pairRows(
          row(Icons.person_outline_rounded, 'Quem abasteceu', operator, navy),
          row(Icons.person_outline_rounded,
              'Responsável pelo recebimento do abastecimento', receiver, navy),
        ));
        rows.add(pairRows(
          row(Icons.assignment_outlined, 'Preço de venda/L',
              salePriceRaw == null ? '-' : _fmtMoney(salePriceRaw), navy),
          row(Icons.assignment_outlined, 'Valor total',
              salePriceRaw == null ? '-' : _fmtMoney(totalSaleValue), navy),
        ));
        final totalizerValue = x['totalizer'] ?? x['closing_meter'];
        rows.add(pairRows(
          row(Icons.local_gas_station_rounded, 'Volume',
              _fmtLiters(x['liters']), navy),
          row(Icons.storage_outlined, 'Totalizador',
              totalizerValue == null ? '-' : _fmtLiters(totalizerValue), navy),
        ));
        if (_hasValue(x['notes'])) {
          rows.add(row(
              Icons.assignment_outlined, 'Observação', '${x['notes']}', navy));
        }
      }

      Uint8List? sig1;
      Uint8List? sig2;
      String sig1Name = '';
      String sig2Name = '';
      String sig1Title = '';
      String sig2Title = '';
      if (transfer) {
        sig1 = await api.downloadMedia('${x['donor_signature_path'] ?? ''}');
        sig2 = await api.downloadMedia(
            '${x['receiver_transfer_signature_path'] ?? x['receiver_signature_path'] ?? ''}');
        sig1Name = '${x['donor_responsible'] ?? operator}';
        sig2Name = '${x['receiver_responsible'] ?? receiver}';
        sig1Title = 'Assinatura responsável doador';
        sig2Title = 'Assinatura responsável recebedor';
      } else if (fueling) {
        sig1 = await api.downloadMedia('${x['receiver_signature_path'] ?? ''}');
        sig2 = await api.downloadMedia('${x['operator_signature_path'] ?? ''}');
        sig1Name = receiver;
        sig2Name = operator;
        sig1Title = 'Assinatura de quem recebeu';
        sig2Title = 'Assinatura de quem abasteceu';
      }

      final body = <pw.Widget>[
        pw.Text(companyName,
            style: pw.TextStyle(font: bold, fontSize: 27, color: navy)),
        pw.SizedBox(height: 7),
        pw.Container(height: 1.5, color: royal),
        pw.SizedBox(height: 12),
      ];
      body.add(pw.Container(
        padding: const pw.EdgeInsets.all(10),
        decoration: pw.BoxDecoration(
            border: pw.Border.all(color: line),
            borderRadius: const pw.BorderRadius.all(pw.Radius.circular(10))),
        child: pw.Column(
            crossAxisAlignment: pw.CrossAxisAlignment.start,
            children: [
              pw.Row(children: [
                pw.Container(
                    width: 42,
                    height: 42,
                    decoration: pw.BoxDecoration(
                        color: accentN, shape: pw.BoxShape.circle),
                    child: pw.Center(
                        child: icon(Icons.local_gas_station_rounded,
                            size: 21, isWhite: true))),
                pw.SizedBox(width: 12),
                pw.Expanded(
                    child: pw.Column(
                        crossAxisAlignment: pw.CrossAxisAlignment.start,
                        children: [
                      if (fueling)
                        pw.Row(mainAxisSize: pw.MainAxisSize.min, children: [
                          pw.Text('Abastecimento',
                              style: pw.TextStyle(
                                  font: bold, fontSize: 14, color: navy)),
                          pw.SizedBox(width: 7),
                          pw.Container(
                              width: 3,
                              height: 3,
                              decoration: pw.BoxDecoration(
                                  color: navy, shape: pw.BoxShape.circle)),
                          pw.SizedBox(width: 7),
                          pw.Text(fuelOrigin.isEmpty ? '-' : fuelOrigin,
                              style: pw.TextStyle(
                                  font: bold, fontSize: 14, color: navy)),
                          pw.SizedBox(width: 7),
                          pw.Container(
                              width: 3,
                              height: 3,
                              decoration: pw.BoxDecoration(
                                  color: navy, shape: pw.BoxShape.circle)),
                          pw.SizedBox(width: 7),
                          pw.Text('Nº: $fuelSequence',
                              style: pw.TextStyle(
                                  font: bold,
                                  fontSize: 14,
                                  color: PdfColor.fromHex('#D51F2A'))),
                        ])
                      else
                        pw.Text(title,
                            style: pw.TextStyle(
                                font: bold, fontSize: 15, color: accentN)),
                      pw.SizedBox(height: 3),
                      pw.Text('${_fmtDate(x['created_at'])} | $operator',
                          style: pw.TextStyle(
                              font: regular, fontSize: 9.5, color: text)),
                    ])),
              ]),
              pw.SizedBox(height: 8),
              ...rows,
              if (_hasValue(x['notes']) && !fueling)
                row(Icons.assignment_outlined, 'Observações', '${x['notes']}',
                    accent),
              if (sig1Title.isNotEmpty) ...[
                pw.SizedBox(height: 10),
                pw.Row(children: [
                  signature(sig1Title, sig1Name, sig1, accent),
                  pw.SizedBox(width: 8),
                  signature(sig2Title, sig2Name, sig2, accent)
                ]),
              ],
            ]),
      ));
      body.add(pw.SizedBox(height: 10));
      body.add(pw.Container(height: 1.5, color: accent));

      doc.addPage(pw.Page(
        pageFormat: PdfPageFormat.a4,
        margin: const pw.EdgeInsets.fromLTRB(26, 22, 26, 20),
        theme: pw.ThemeData.withFont(base: regular, bold: bold),
        build: (_) => pw.Column(
            crossAxisAlignment: pw.CrossAxisAlignment.start, children: body),
      ));

      final evidence = <MapEntry<String, String>>[];
      void addEvidence(String label, dynamic value) {
        if (_hasValue(value)) evidence.add(MapEntry(label, '$value'));
      }

      if (refinery) {
        addEvidence(
            'Foto da placa do caminhão-tanque', ctx['truck_plate_photo_path']);
        addEvidence('Foto legível da Nota Fiscal', ctx['invoice_photo_path']);
        if (evidence.isEmpty) {
          for (final p in _rowsFromPaths(x['photo_paths'])) {
            evidence.add(MapEntry('Evidência do recebimento', p));
          }
        }
      }
      if (fueling) {
        final measurementType = _measurementTypeForPdf(x);
        final meterEvidenceLabel = measurementType == 'km'
            ? 'Foto do KM'
            : measurementType == 'hourmeter'
                ? 'Foto do Horímetro'
                : 'Foto do KM ou Horímetro';
        addEvidence(meterEvidenceLabel, x['meter_photo_path']);
        addEvidence(
            'Totalizador antes do abastecimento',
            x['totalizer_photo_before_path'] ??
                x['totalizer_evidence_photo_path']);
        addEvidence('Totalizador depois', x['totalizer_photo_after_path']);
        addEvidence('Foto da placa ou identificação',
            x['identity_evidence_photo_path']);
        addEvidence('4ª foto (opcional)', x['extra_evidence_photo_path']);
      }
      final loadedEvidence = <MapEntry<String, Uint8List>>[];
      for (final e in evidence) {
        final bytes = await api.downloadMedia(e.value);
        if (bytes != null) loadedEvidence.add(MapEntry(e.key, bytes));
      }

      for (var offset = 0; offset < loadedEvidence.length; offset += 4) {
        final pageItems = loadedEvidence.skip(offset).take(4).toList();

        pw.Widget evidenceSlot(int index) {
          if (index >= pageItems.length) {
            return pw.Expanded(
                child: pw.Container(
              decoration: pw.BoxDecoration(
                  border: pw.Border.all(color: line),
                  borderRadius:
                      const pw.BorderRadius.all(pw.Radius.circular(7))),
            ));
          }
          final item = pageItems[index];
          return pw.Expanded(
              child: pw.Container(
            padding: const pw.EdgeInsets.all(7),
            decoration: pw.BoxDecoration(
                border: pw.Border.all(color: line),
                borderRadius: const pw.BorderRadius.all(pw.Radius.circular(7))),
            child: pw.Column(children: [
              pw.Expanded(
                  child: pw.Center(
                      child: pw.Image(pw.MemoryImage(item.value),
                          fit: pw.BoxFit.contain))),
              pw.SizedBox(height: 5),
              pw.Text(item.key,
                  textAlign: pw.TextAlign.center,
                  style: pw.TextStyle(font: bold, fontSize: 9, color: navy)),
            ]),
          ));
        }

        doc.addPage(pw.Page(
          pageFormat: PdfPageFormat.a4,
          margin: const pw.EdgeInsets.fromLTRB(28, 24, 28, 22),
          theme: pw.ThemeData.withFont(base: regular, bold: bold),
          build: (_) => pw.Column(
              crossAxisAlignment: pw.CrossAxisAlignment.start,
              children: [
                pw.Text(companyName,
                    style: pw.TextStyle(font: bold, fontSize: 27, color: navy)),
                pw.SizedBox(height: 7),
                pw.Container(height: 1.5, color: royal),
                pw.SizedBox(height: 12),
                pw.Container(
                  padding: const pw.EdgeInsets.all(10),
                  decoration: pw.BoxDecoration(
                      border: pw.Border.all(color: line),
                      borderRadius:
                          const pw.BorderRadius.all(pw.Radius.circular(8))),
                  child: pw.Row(children: [
                    pw.Container(
                        width: 40,
                        height: 40,
                        decoration: pw.BoxDecoration(
                            color: navy, shape: pw.BoxShape.circle),
                        child: pw.Center(
                            child: icon(Icons.assignment_outlined,
                                size: 20, isWhite: true))),
                    pw.SizedBox(width: 10),
                    pw.Expanded(
                        child: pw.Column(
                            crossAxisAlignment: pw.CrossAxisAlignment.start,
                            children: [
                          if (fueling)
                            pw.Row(
                                mainAxisSize: pw.MainAxisSize.min,
                                children: [
                                  pw.Text('Evidências do registro',
                                      style: pw.TextStyle(
                                          font: bold,
                                          fontSize: 13.5,
                                          color: navy)),
                                  pw.SizedBox(width: 7),
                                  pw.Container(
                                      width: 3,
                                      height: 3,
                                      decoration: pw.BoxDecoration(
                                          color: navy,
                                          shape: pw.BoxShape.circle)),
                                  pw.SizedBox(width: 7),
                                  pw.Text(fuelOrigin.isEmpty ? '-' : fuelOrigin,
                                      style: pw.TextStyle(
                                          font: bold,
                                          fontSize: 13.5,
                                          color: navy)),
                                  pw.SizedBox(width: 7),
                                  pw.Container(
                                      width: 3,
                                      height: 3,
                                      decoration: pw.BoxDecoration(
                                          color: navy,
                                          shape: pw.BoxShape.circle)),
                                  pw.SizedBox(width: 7),
                                  pw.Text('Nº: $fuelSequence',
                                      style: pw.TextStyle(
                                          font: bold,
                                          fontSize: 13.5,
                                          color: PdfColor.fromHex('#D51F2A'))),
                                ])
                          else
                            pw.Text('Evidências do registro',
                                style: pw.TextStyle(
                                    font: bold, fontSize: 13.5, color: navy)),
                          pw.SizedBox(height: 3),
                          pw.Text('${_fmtDate(x['created_at'])} | $operator',
                              style: pw.TextStyle(
                                  font: regular, fontSize: 9.2, color: text)),
                        ])),
                  ]),
                ),
                pw.SizedBox(height: 12),
                pw.Expanded(
                    child: pw.Column(children: [
                  pw.Expanded(
                      child: pw.Row(children: [
                    evidenceSlot(0),
                    pw.SizedBox(width: 10),
                    evidenceSlot(1)
                  ])),
                  pw.SizedBox(height: 10),
                  pw.Expanded(
                      child: pw.Row(children: [
                    evidenceSlot(2),
                    pw.SizedBox(width: 10),
                    evidenceSlot(3)
                  ])),
                ])),
                pw.SizedBox(height: 10),
                pw.Container(height: 1.5, color: royal),
              ]),
        ));
      }
    }
    return doc.save();
  }
}

class AdminUsersOnlineScreen extends StatefulWidget {
  final Map<String, dynamic> referenceData;
  const AdminUsersOnlineScreen({super.key, required this.referenceData});
  @override
  State<AdminUsersOnlineScreen> createState() => _AdminUsersOnlineScreenState();
}

class _AdminUsersOnlineScreenState extends State<AdminUsersOnlineScreen> {
  List<Map<String, dynamic>>? users;
  bool busy = false;

  @override
  void initState() {
    super.initState();
    load();
  }

  Future<void> load() async {
    try {
      final x = await api.listDrivers();
      if (mounted) setState(() => users = x);
    } catch (e) {
      if (mounted)
        ScaffoldMessenger.of(context)
            .showSnackBar(SnackBar(content: Text(_friendlyError(e))));
    }
  }

  List<Map<String, dynamic>> get operationalUnits {
    final out = <Map<String, dynamic>>[];
    for (final m in _rows(widget.referenceData['machines'])) {
      final mid = _intOrNull(m['id']);
      if (mid == null) continue;
      final asset = '${m['numeroAtivo'] ?? ''}'.trim();
      final model = '${m['modelo'] ?? ''}'.trim();
      final plate = '${m['placa'] ?? ''}'.trim();
      final label =
          '${asset.isNotEmpty ? asset : 'Ativo $mid'}${model.isNotEmpty ? ' • $model' : ''}${plate.isNotEmpty ? ' • $plate' : ''}';
      out.add({
        'key': 'M:$mid',
        'kind': 'machine',
        'machine_id': mid,
        'tank_id': _intOrNull(m['comboio_tank_id']),
        'label': label
      });
    }
    for (final t in _rows(widget.referenceData['tanks'])) {
      if ('${t['tank_type']}' != 'stationary') continue;
      final tid = _intOrNull(t['id']);
      if (tid == null) continue;
      out.add({
        'key': 'T:$tid',
        'kind': 'stationary',
        'machine_id': null,
        'tank_id': tid,
        'label': 'T.E. • ${t['code']} • ${t['name']}'
      });
    }
    out.sort((a, b) =>
        '${a['label']}'.toLowerCase().compareTo('${b['label']}'.toLowerCase()));
    return out;
  }

  String? assignmentKey(Map<String, dynamic> u) {
    final mid = _intOrNull(u['machine_id']);
    if (mid != null) return 'M:$mid';
    final ids = ((u['tank_ids'] as List?) ?? const [])
        .map(_intOrNull)
        .whereType<int>()
        .toSet();
    for (final unit in operationalUnits) {
      if (unit['kind'] == 'stationary' &&
          ids.contains(_intOrNull(unit['tank_id']))) return '${unit['key']}';
    }
    return null;
  }

  String assignmentLabel(Map<String, dynamic> u) {
    final key = assignmentKey(u);
    if (key == null) return '-';
    for (final unit in operationalUnits) {
      if ('${unit['key']}' == key) return '${unit['label']}';
    }
    return '-';
  }

  Map<String, dynamic> assignmentPayload(String key) {
    final unit = operationalUnits.firstWhere((x) => '${x['key']}' == key);
    return unit['kind'] == 'stationary'
        ? {'tank_id': unit['tank_id']}
        : {'machine_id': unit['machine_id']};
  }

  Future<void> createUser() async {
    final name = TextEditingController();
    final username = TextEditingController();
    final password = TextEditingController();
    String? selected;
    final units = operationalUnits;
    final ok = await showDialog<bool>(
        context: context,
        builder: (ctx) => StatefulBuilder(
            builder: (ctx, setLocal) => AlertDialog(
                  title: const Text('Cadastrar usuário'),
                  content: SingleChildScrollView(
                      child: Column(mainAxisSize: MainAxisSize.min, children: [
                    TextField(
                        controller: name,
                        decoration: const InputDecoration(labelText: 'Nome')),
                    const SizedBox(height: 10),
                    TextField(
                        controller: username,
                        decoration:
                            const InputDecoration(labelText: 'Usuário')),
                    const SizedBox(height: 10),
                    TextField(
                        controller: password,
                        decoration: const InputDecoration(
                            labelText: 'Senha / PIN (mínimo 4 caracteres)')),
                    const SizedBox(height: 12),
                    DropdownButtonFormField<String>(
                      initialValue: selected,
                      isExpanded: true,
                      decoration: const InputDecoration(
                          labelText: 'Ativo que vai operar *'),
                      items: units
                          .map((u) => DropdownMenuItem<String>(
                              value: '${u['key']}',
                              child: Text('${u['label']}',
                                  overflow: TextOverflow.ellipsis)))
                          .toList(),
                      onChanged: (v) => setLocal(() => selected = v),
                    ),
                  ])),
                  actions: [
                    TextButton(
                        onPressed: () => Navigator.pop(ctx, false),
                        child: const Text('Cancelar')),
                    FilledButton(
                        onPressed: units.isEmpty
                            ? null
                            : () => Navigator.pop(ctx, true),
                        child: const Text('Cadastrar'))
                  ],
                )));
    if (ok == true && selected != null) {
      setState(() => busy = true);
      try {
        await api.invokeUserAction({
          'action': 'create_driver',
          'name': name.text.trim(),
          'username': username.text.trim(),
          'password': password.text,
          ...assignmentPayload(selected!)
        });
        await load();
      } catch (e) {
        if (mounted)
          ScaffoldMessenger.of(context)
              .showSnackBar(SnackBar(content: Text(_friendlyError(e))));
      }
      if (mounted) setState(() => busy = false);
    }
    name.dispose();
    username.dispose();
    password.dispose();
  }

  Future<void> editUser(Map<String, dynamic> u) async {
    final name = TextEditingController(text: '${u['name'] ?? ''}');
    final username = TextEditingController(text: '${u['username'] ?? ''}');
    final password = TextEditingController();
    String? selected = assignmentKey(u);
    final units = operationalUnits;
    final ok = await showDialog<bool>(
        context: context,
        builder: (ctx) => StatefulBuilder(
            builder: (ctx, setLocal) => AlertDialog(
                  title: Text('Editar ${u['username']}'),
                  content: SingleChildScrollView(
                      child: Column(mainAxisSize: MainAxisSize.min, children: [
                    TextField(
                        controller: name,
                        decoration: const InputDecoration(labelText: 'Nome')),
                    const SizedBox(height: 10),
                    TextField(
                        controller: username,
                        decoration:
                            const InputDecoration(labelText: 'Usuário')),
                    const SizedBox(height: 10),
                    TextField(
                        controller: password,
                        decoration: const InputDecoration(
                            labelText:
                                'Nova senha / PIN (opcional, mínimo 4 caracteres)')),
                    const SizedBox(height: 12),
                    DropdownButtonFormField<String>(
                      initialValue: units.any((x) => '${x['key']}' == selected)
                          ? selected
                          : null,
                      isExpanded: true,
                      decoration: const InputDecoration(
                          labelText: 'Ativo que vai operar *'),
                      items: units
                          .map((x) => DropdownMenuItem<String>(
                              value: '${x['key']}',
                              child: Text('${x['label']}',
                                  overflow: TextOverflow.ellipsis)))
                          .toList(),
                      onChanged: (v) => setLocal(() => selected = v),
                    ),
                  ])),
                  actions: [
                    TextButton(
                        onPressed: () => Navigator.pop(ctx, false),
                        child: const Text('Cancelar')),
                    FilledButton(
                        onPressed: units.isEmpty
                            ? null
                            : () => Navigator.pop(ctx, true),
                        child: const Text('Salvar'))
                  ],
                )));
    if (ok == true && selected != null) {
      setState(() => busy = true);
      try {
        await api.invokeUserAction({
          'action': 'update_driver',
          'user_id': u['user_id'],
          'name': name.text.trim(),
          'username': username.text.trim(),
          'password': password.text,
          ...assignmentPayload(selected!)
        });
        await load();
      } catch (e) {
        if (mounted)
          ScaffoldMessenger.of(context)
              .showSnackBar(SnackBar(content: Text(_friendlyError(e))));
      }
      if (mounted) setState(() => busy = false);
    }
    name.dispose();
    username.dispose();
    password.dispose();
  }

  Future<void> toggle(Map<String, dynamic> u) async {
    final key = assignmentKey(u);
    if (key == null) {
      if (mounted)
        ScaffoldMessenger.of(context).showSnackBar(const SnackBar(
            content: Text(
                'Edite o usuário e selecione o ativo ou tanque que ele irá operar.')));
      return;
    }
    setState(() => busy = true);
    try {
      await api.invokeUserAction({
        'action': 'set_active',
        'user_id': u['user_id'],
        'name': u['name'],
        'active': u['active'] != true,
        ...assignmentPayload(key)
      });
      await load();
    } catch (e) {
      if (mounted)
        ScaffoldMessenger.of(context)
            .showSnackBar(SnackBar(content: Text(_friendlyError(e))));
    }
    if (mounted) setState(() => busy = false);
  }

  Future<void> deleteUser(Map<String, dynamic> u) async {
    final name = '${u['name'] ?? u['username'] ?? 'usuário'}';
    final ok = await showDialog<bool>(
        context: context,
        builder: (ctx) => AlertDialog(
              title: const Text('Excluir usuário?'),
              content: Text(
                  'O usuário $name será excluído, mas os registros permanecerão salvos.'),
              actions: [
                TextButton(
                    onPressed: () => Navigator.pop(ctx, false),
                    child: const Text('Cancelar')),
                FilledButton.icon(
                    onPressed: () => Navigator.pop(ctx, true),
                    icon: const Icon(Icons.delete_outline_rounded),
                    label: const Text('Excluir'))
              ],
            ));
    if (ok != true) return;
    final userId = '${u['user_id'] ?? ''}';
    if (userId.isEmpty) return;
    setState(() => busy = true);
    try {
      await api.deleteDriverUser(userId);
      await load();
      if (mounted)
        ScaffoldMessenger.of(context).showSnackBar(const SnackBar(
            content:
                Text('Usuário excluído. Os registros foram preservados.')));
    } catch (e) {
      if (mounted)
        ScaffoldMessenger.of(context)
            .showSnackBar(SnackBar(content: Text(_friendlyError(e))));
    } finally {
      if (mounted) setState(() => busy = false);
    }
  }

  @override
  Widget build(BuildContext context) => Scaffold(
        appBar: AppBar(title: const Text('Gerenciar usuários')),
        floatingActionButton: FloatingActionButton.extended(
            onPressed: busy ? null : createUser,
            icon: const Icon(Icons.person_add_alt_1_rounded),
            label: const Text('Cadastrar')),
        body: users == null
            ? const Center(child: CircularProgressIndicator())
            : RefreshIndicator(
                onRefresh: load,
                child: ListView.separated(
                  padding: const EdgeInsets.fromLTRB(16, 12, 16, 90),
                  itemCount: users!.length,
                  separatorBuilder: (_, __) => const SizedBox(height: 8),
                  itemBuilder: (_, i) {
                    final u = users![i];
                    final removed = u['access_removed_at'] != null;
                    return Card(
                        child: Padding(
                            padding: const EdgeInsets.all(14),
                            child: Column(
                                crossAxisAlignment: CrossAxisAlignment.stretch,
                                children: [
                                  Row(children: [
                                    const CircleAvatar(
                                        child: Icon(Icons.person_rounded)),
                                    const SizedBox(width: 12),
                                    Expanded(
                                        child: Column(
                                            crossAxisAlignment:
                                                CrossAxisAlignment.start,
                                            children: [
                                          Text('${u['name']}',
                                              style: const TextStyle(
                                                  fontWeight: FontWeight.w900)),
                                          Text('${u['username']}')
                                        ])),
                                    Chip(
                                        label: Text(removed
                                            ? 'ACESSO REMOVIDO'
                                            : u['active'] == true
                                                ? 'ATIVO'
                                                : 'DESATIVADO')),
                                  ]),
                                  const SizedBox(height: 8),
                                  Text(
                                      'Ativo que vai operar: ${assignmentLabel(u)}'),
                                  const SizedBox(height: 10),
                                  Wrap(spacing: 8, runSpacing: 8, children: [
                                    if (!removed)
                                      OutlinedButton.icon(
                                          onPressed:
                                              busy ? null : () => editUser(u),
                                          icon: const Icon(Icons.edit_outlined),
                                          label: const Text('Editar')),
                                    if (!removed)
                                      OutlinedButton.icon(
                                          onPressed:
                                              busy ? null : () => toggle(u),
                                          icon: Icon(u['active'] == true
                                              ? Icons.block_rounded
                                              : Icons
                                                  .check_circle_outline_rounded),
                                          label: Text(u['active'] == true
                                              ? 'Desativar'
                                              : 'Ativar')),
                                    TextButton.icon(
                                        onPressed:
                                            busy ? null : () => deleteUser(u),
                                        icon: const Icon(
                                            Icons.delete_outline_rounded),
                                        label: const Text('Excluir usuário')),
                                  ]),
                                  if (removed)
                                    const Padding(
                                        padding: EdgeInsets.only(top: 8),
                                        child: Text(
                                            'O acesso já está removido. A exclusão mantém os registros anteriores.')),
                                ])));
                  },
                ),
              ),
      );
}

class AdminMoreScreen extends StatelessWidget {
  const AdminMoreScreen({super.key});

  @override
  Widget build(BuildContext context) => Scaffold(
        appBar: AppBar(title: const Text('Mais')),
        body: ListView(
          padding: const EdgeInsets.all(16),
          children: [
            HomeActionCard(
              icon: Icons.business_outlined,
              title: 'Empresas',
              subtitle:
                  'Clientes/contratantes, proprietárias/locadoras e fornecedores de combustível',
              onTap: () => Navigator.push(
                  context,
                  MaterialPageRoute(
                      builder: (_) => const CompaniesAdminScreen())),
            ),
            const SizedBox(height: 12),
            HomeActionCard(
              icon: Icons.badge_outlined,
              title: 'Dados da empresa',
              subtitle:
                  'Consultar e editar a identificação institucional usada nos PDFs',
              onTap: () => Navigator.push(
                  context,
                  MaterialPageRoute(
                      builder: (_) => const ReportCompanyAdminScreen())),
            ),
            const SizedBox(height: 12),
            HomeActionCard(
              icon: Icons.av_timer_outlined,
              title: 'Substituição de horímetro',
              subtitle:
                  'Registrar horímetro danificado e iniciar um novo ciclo sem perder o total acumulado',
              onTap: () => Navigator.push(
                  context,
                  MaterialPageRoute(
                      builder: (_) => const HourmeterReplacementV48Screen())),
            ),
          ],
        ),
      );
}

class HourmeterReplacementV48Screen extends StatefulWidget {
  const HourmeterReplacementV48Screen({super.key});
  @override
  State<HourmeterReplacementV48Screen> createState() =>
      _HourmeterReplacementV48ScreenState();
}

class _HourmeterReplacementV48ScreenState
    extends State<HourmeterReplacementV48Screen> {
  List<Map<String, dynamic>> machines = [];
  int? machineId;
  Map<String, dynamic>? status;
  final broken = TextEditingController(),
      initial = TextEditingController(text: '0'),
      reason = TextEditingController(text: 'Horímetro danificado');
  XFile? oldPhoto, newPhoto;
  bool loading = true, saving = false;
  String? error;
  @override
  void initState() {
    super.initState();
    load();
  }

  Future<XFile?> cam() => ImagePicker()
      .pickImage(source: ImageSource.camera, imageQuality: 75, maxWidth: 1600);
  Future<void> load() async {
    try {
      final p = await api.profile();
      if (p['is_admin'] != true)
        throw Exception('Somente o Admin pode registrar troca de horímetro');
      final r = await api.referenceData();
      final ms = _rows(r['machines'])
          .where((x) => ['hourmeter', 'both']
              .contains('${x['measurement_type'] ?? ''}'.toLowerCase()))
          .toList();
      if (mounted)
        setState(() {
          machines = ms;
          loading = false;
        });
    } catch (e) {
      if (mounted)
        setState(() {
          error = _friendlyError(e);
          loading = false;
        });
    }
  }

  Future<void> select(int? id) async {
    setState(() {
      machineId = id;
      status = null;
      error = null;
    });
    if (id == null) return;
    try {
      final x = await api.meterStatusV48(id);
      if (mounted)
        setState(() {
          status = x;
          if (x['last_hourmeter'] != null)
            broken.text = '${x['last_hourmeter']}';
        });
    } catch (e) {
      if (mounted) setState(() => error = _friendlyError(e));
    }
  }

  double? numc(TextEditingController c) =>
      double.tryParse(c.text.trim().replaceAll(',', '.'));
  Future<void> save() async {
    final b = numc(broken), n = numc(initial);
    if (machineId == null ||
        b == null ||
        b < 0 ||
        n == null ||
        n < 0 ||
        reason.text.trim().isEmpty) {
      setState(() =>
          error = 'Selecione o equipamento e informe as leituras e o motivo.');
      return;
    }
    setState(() {
      saving = true;
      error = null;
    });
    try {
      Future<String?> up(XFile? x, String k) async => x == null
          ? null
          : api.uploadBytes(await x.readAsBytes(), k,
              mime: x.mimeType ?? 'image/jpeg');
      final paths = await Future.wait(
          [up(oldPhoto, 'horimetro_antigo'), up(newPhoto, 'horimetro_novo')]);
      final r = await api.replaceHourmeterV48(
          machineId: machineId!,
          brokenReading: b,
          newInitialReading: n,
          reason: reason.text.trim(),
          oldPhotoPath: paths[0],
          newPhotoPath: paths[1]);
      if (!mounted) return;
      await showDialog<void>(
          context: context,
          builder: (ctx) => AlertDialog(
                  title: const Text('Substituição registrada ✓'),
                  content: Text(
                      'Leitura antiga: $b h\nNovo horímetro: $n h\nHorímetro acumulado: ${r['hourmeter_accumulated']} h\n\nOs próximos abastecimentos usarão o novo ciclo e o total acumulado continuará preservado.'),
                  actions: [
                    FilledButton(
                        onPressed: () => Navigator.pop(ctx),
                        child: const Text('OK'))
                  ]));
      if (mounted) {
        broken.clear();
        initial.text = '0';
        oldPhoto = null;
        newPhoto = null;
        await select(machineId);
      }
    } catch (e) {
      if (mounted) setState(() => error = _friendlyError(e));
    } finally {
      if (mounted) setState(() => saving = false);
    }
  }

  @override
  void dispose() {
    broken.dispose();
    initial.dispose();
    reason.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) => Scaffold(
      appBar: AppBar(title: const Text('Substituição de horímetro')),
      body: loading
          ? const Center(child: CircularProgressIndicator())
          : ListView(padding: const EdgeInsets.all(16), children: [
              const Card(
                  child: ListTile(
                      leading: Icon(Icons.info_outline, color: _blue),
                      title: Text(
                          'Use somente quando o horímetro físico for substituído',
                          style: TextStyle(fontWeight: FontWeight.w900)),
                      subtitle: Text(
                          'Uma simples leitura menor continuará sendo bloqueada. A troca cria um novo ciclo e preserva as horas acumuladas para manutenção.'))),
              if (error != null)
                Card(
                    child: ListTile(
                        leading:
                            const Icon(Icons.error_outline, color: Colors.red),
                        title: Text(error!))),
              DropdownButtonFormField<int?>(
                  initialValue: machineId,
                  isExpanded: true,
                  decoration: const InputDecoration(
                      labelText: 'Equipamento com horímetro danificado *'),
                  items: [
                    const DropdownMenuItem<int?>(
                        value: null, child: Text('Selecione')),
                    ...machines.map((x) => DropdownMenuItem<int?>(
                        value: _intOrNull(x['id']),
                        child: Text(
                            '${x['numeroAtivo'] ?? '-'} • ${x['modelo'] ?? ''}')))
                  ],
                  onChanged: saving ? null : select),
              if (status != null)
                Card(
                    child: ListTile(
                        title: Text(
                            'Última leitura: ${status!['last_hourmeter'] ?? '-'} h'),
                        subtitle: Text(
                            'Acumulado atual: ${status!['hourmeter_accumulated'] ?? status!['last_hourmeter'] ?? '-'} h • Offset: ${status!['hourmeter_offset'] ?? 0}'))),
              const SizedBox(height: 8),
              TextField(
                  controller: broken,
                  enabled: !saving,
                  keyboardType:
                      const TextInputType.numberWithOptions(decimal: true),
                  decoration: const InputDecoration(
                      labelText: 'Quanto marcava quando quebrou *')),
              const SizedBox(height: 8),
              TextField(
                  controller: initial,
                  enabled: !saving,
                  keyboardType:
                      const TextInputType.numberWithOptions(decimal: true),
                  decoration: const InputDecoration(
                      labelText: 'Leitura inicial do novo horímetro *',
                      helperText: 'Normalmente 0')),
              const SizedBox(height: 8),
              TextField(
                  controller: reason,
                  enabled: !saving,
                  maxLines: 2,
                  decoration: const InputDecoration(labelText: 'Motivo *')),
              const SizedBox(height: 10),
              OutlinedButton.icon(
                  onPressed: saving
                      ? null
                      : () async {
                          final x = await cam();
                          if (x != null) setState(() => oldPhoto = x);
                        },
                  icon: const Icon(Icons.camera_alt_outlined),
                  label: Text(oldPhoto == null
                      ? 'Foto do horímetro antigo (opcional)'
                      : 'Foto do antigo ✓')),
              OutlinedButton.icon(
                  onPressed: saving
                      ? null
                      : () async {
                          final x = await cam();
                          if (x != null) setState(() => newPhoto = x);
                        },
                  icon: const Icon(Icons.camera_alt_outlined),
                  label: Text(newPhoto == null
                      ? 'Foto do novo horímetro (opcional)'
                      : 'Foto do novo ✓')),
              const SizedBox(height: 12),
              FilledButton.icon(
                  onPressed: saving ? null : save,
                  icon: saving
                      ? const SizedBox(
                          width: 18,
                          height: 18,
                          child: CircularProgressIndicator(strokeWidth: 2))
                      : const Icon(Icons.save_outlined),
                  label: Text(saving
                      ? 'Registrando troca...'
                      : 'Registrar substituição'))
            ]));
}

// v48 build trigger
class CompaniesAdminScreen extends StatefulWidget {
  const CompaniesAdminScreen({super.key});

  @override
  State<CompaniesAdminScreen> createState() => _CompaniesAdminScreenState();
}

class _CompaniesAdminScreenState extends State<CompaniesAdminScreen> {
  List<Map<String, dynamic>>? items;
  bool busy = false;

  @override
  void initState() {
    super.initState();
    load();
  }

  Future<void> load() async {
    try {
      final x = await api.managedCompanies();
      if (mounted)
        setState(() => items = x.where((e) => e['active'] != false).toList());
    } catch (e) {
      if (mounted)
        ScaffoldMessenger.of(context)
            .showSnackBar(SnackBar(content: Text(_friendlyError(e))));
    }
  }

  String addressOf(Map<String, dynamic> x) {
    final first = [x['street'], x['street_number'], x['complement']]
        .where((v) => _hasValue(v))
        .join(', ');
    final second =
        [x['neighborhood'], x['city']].where((v) => _hasValue(v)).join(' • ');
    final state = _hasValue(x['state']) ? ' - ${x['state']}' : '';
    final zip = _hasValue(x['zip_code']) ? ', ${x['zip_code']}' : '';
    final cityPart = second.isEmpty ? '' : '$second$state';
    return [first, cityPart].where((v) => v.isNotEmpty).join(' • ') + zip;
  }

  List<String> rolesOf(Map<String, dynamic> x) => [
        if (x['is_client'] == true) 'CLIENTE',
        if (x['is_equipment_owner'] == true) 'LOCADORA',
        if (x['is_fuel_supplier'] == true) 'FORNECEDOR',
      ];

  Future<void> edit([Map<String, dynamic>? item]) async {
    final name = TextEditingController(text: '${item?['name'] ?? ''}');
    final subtitle = TextEditingController(text: '${item?['subtitle'] ?? ''}');
    final document = TextEditingController(text: '${item?['document'] ?? ''}');
    final zip = TextEditingController(text: '${item?['zip_code'] ?? ''}');
    final street = TextEditingController(text: '${item?['street'] ?? ''}');
    final number =
        TextEditingController(text: '${item?['street_number'] ?? ''}');
    final complement =
        TextEditingController(text: '${item?['complement'] ?? ''}');
    final neighborhood =
        TextEditingController(text: '${item?['neighborhood'] ?? ''}');
    final city = TextEditingController(text: '${item?['city'] ?? ''}');
    final state = TextEditingController(text: '${item?['state'] ?? ''}');
    var active = item?['active'] != false;
    var isClient = item?['is_client'] == true;
    var isEquipmentOwner = item?['is_equipment_owner'] == true;
    var isFuelSupplier = item?['is_fuel_supplier'] == true;

    final ok = await showDialog<bool>(
      context: context,
      builder: (ctx) => StatefulBuilder(
        builder: (ctx, setDialogState) => AlertDialog(
          title: Text(item == null ? 'Cadastrar empresa' : 'Editar empresa'),
          content: SizedBox(
            width: 540,
            child: SingleChildScrollView(
              child: Column(
                  mainAxisSize: MainAxisSize.min,
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: [
                    const Text('Tipo de relação',
                        style: TextStyle(
                            fontWeight: FontWeight.w900, color: _blue)),
                    const SizedBox(height: 4),
                    const Text(
                        'A mesma empresa pode exercer mais de uma função no sistema.',
                        style: TextStyle(fontSize: 12, color: Colors.black54)),
                    CheckboxListTile(
                        contentPadding: EdgeInsets.zero,
                        dense: true,
                        value: isClient,
                        onChanged: (v) =>
                            setDialogState(() => isClient = v == true),
                        title: const Text('Cliente / Contratante'),
                        subtitle: const Text(
                            'Empresa para quem a obra é executada e que recebe/compra o serviço ou combustível.')),
                    CheckboxListTile(
                        contentPadding: EdgeInsets.zero,
                        dense: true,
                        value: isEquipmentOwner,
                        onChanged: (v) =>
                            setDialogState(() => isEquipmentOwner = v == true),
                        title: const Text(
                            'Proprietária / Locadora de equipamento'),
                        subtitle: const Text(
                            'Empresa externa proprietária do equipamento contratado.')),
                    CheckboxListTile(
                        contentPadding: EdgeInsets.zero,
                        dense: true,
                        value: isFuelSupplier,
                        onChanged: (v) =>
                            setDialogState(() => isFuelSupplier = v == true),
                        title: const Text('Fornecedor de combustível'),
                        subtitle: const Text(
                            'Empresa/distribuidora que fornece combustível e emite a NF.')),
                    const Divider(height: 20),
                    TextField(
                        controller: name,
                        onChanged: (_) => setDialogState(() {}),
                        decoration: const InputDecoration(
                            labelText: 'Nome da empresa *')),
                    const SizedBox(height: 9),
                    TextField(
                        controller: subtitle,
                        decoration: const InputDecoration(
                            labelText: 'Subtítulo / segmento',
                            hintText:
                                'Ex.: Engenharia, Locação, Distribuidora')),
                    const SizedBox(height: 9),
                    TextField(
                        controller: document,
                        keyboardType: TextInputType.number,
                        decoration: const InputDecoration(labelText: 'CNPJ')),
                    const SizedBox(height: 9),
                    TextField(
                        controller: zip,
                        keyboardType: TextInputType.number,
                        decoration: const InputDecoration(labelText: 'CEP')),
                    const SizedBox(height: 9),
                    TextField(
                        controller: street,
                        decoration:
                            const InputDecoration(labelText: 'Logradouro')),
                    const SizedBox(height: 9),
                    Row(children: [
                      Expanded(
                          flex: 2,
                          child: TextField(
                              controller: number,
                              decoration:
                                  const InputDecoration(labelText: 'Número'))),
                      const SizedBox(width: 9),
                      Expanded(
                          flex: 3,
                          child: TextField(
                              controller: complement,
                              decoration: const InputDecoration(
                                  labelText: 'Complemento'))),
                    ]),
                    const SizedBox(height: 9),
                    TextField(
                        controller: neighborhood,
                        decoration: const InputDecoration(labelText: 'Bairro')),
                    const SizedBox(height: 9),
                    Row(children: [
                      Expanded(
                          flex: 4,
                          child: TextField(
                              controller: city,
                              decoration:
                                  const InputDecoration(labelText: 'Cidade'))),
                      const SizedBox(width: 9),
                      Expanded(
                          child: TextField(
                              controller: state,
                              textCapitalization: TextCapitalization.characters,
                              maxLength: 2,
                              decoration: const InputDecoration(
                                  labelText: 'UF', counterText: ''))),
                    ]),
                    SwitchListTile.adaptive(
                        contentPadding: EdgeInsets.zero,
                        title: const Text('Empresa ativa'),
                        value: active,
                        onChanged: (v) => setDialogState(() => active = v)),
                  ]),
            ),
          ),
          actions: [
            TextButton(
                onPressed: () => Navigator.pop(ctx, false),
                child: const Text('Cancelar')),
            FilledButton(
                onPressed: name.text.trim().isEmpty ||
                        !(isClient || isEquipmentOwner || isFuelSupplier)
                    ? null
                    : () => Navigator.pop(ctx, true),
                child: const Text('Salvar')),
          ],
        ),
      ),
    );

    if (ok == true && name.text.trim().isNotEmpty) {
      setState(() => busy = true);
      try {
        await api.saveManagedCompany(
          id: _intOrNull(item?['id']),
          name: name.text.trim(),
          subtitle: subtitle.text.trim(),
          document: document.text.trim(),
          zipCode: zip.text.trim(),
          street: street.text.trim(),
          streetNumber: number.text.trim(),
          complement: complement.text.trim(),
          neighborhood: neighborhood.text.trim(),
          city: city.text.trim(),
          state: state.text.trim(),
          active: active,
          isClient: isClient,
          isEquipmentOwner: isEquipmentOwner,
          isFuelSupplier: isFuelSupplier,
        );
        await load();
        if (mounted)
          ScaffoldMessenger.of(context).showSnackBar(const SnackBar(
              content: Text('Empresa salva com seus tipos de relação ✓')));
      } catch (e) {
        if (mounted)
          ScaffoldMessenger.of(context)
              .showSnackBar(SnackBar(content: Text(_friendlyError(e))));
      } finally {
        if (mounted) setState(() => busy = false);
      }
    }
    for (final c in [
      name,
      subtitle,
      document,
      zip,
      street,
      number,
      complement,
      neighborhood,
      city,
      state
    ]) {
      c.dispose();
    }
  }

  Future<void> removeCompany(Map<String, dynamic> x) async {
    final ok = await showDialog<bool>(
        context: context,
        builder: (ctx) => AlertDialog(
              title: const Text('Excluir empresa?'),
              content: Text(
                  '“${x['name']}” será retirada dos cadastros ativos e das novas seleções. Todos os abastecimentos, obras, equipamentos, notas, relatórios e auditorias já vinculados continuarão preservados.'),
              actions: [
                TextButton(
                    onPressed: () => Navigator.pop(ctx, false),
                    child: const Text('Cancelar')),
                FilledButton(
                    style: FilledButton.styleFrom(
                        backgroundColor: Colors.red.shade700),
                    onPressed: () => Navigator.pop(ctx, true),
                    child: const Text('Excluir'))
              ],
            ));
    if (ok != true) return;
    setState(() => busy = true);
    try {
      await api.archiveManagedCompany(x);
      await load();
      if (mounted)
        ScaffoldMessenger.of(context).showSnackBar(const SnackBar(
            content: Text(
                'Empresa retirada dos cadastros ativos. Histórico preservado ✓')));
    } catch (e) {
      if (mounted)
        ScaffoldMessenger.of(context)
            .showSnackBar(SnackBar(content: Text(_friendlyError(e))));
    } finally {
      if (mounted) setState(() => busy = false);
    }
  }

  @override
  Widget build(BuildContext context) => Scaffold(
        appBar: AppBar(title: const Text('Empresas')),
        floatingActionButton: FloatingActionButton.extended(
            onPressed: busy ? null : () => edit(),
            icon: const Icon(Icons.add_business_outlined),
            label: const Text('Nova empresa')),
        body: items == null
            ? const Center(child: CircularProgressIndicator())
            : RefreshIndicator(
                onRefresh: load,
                child: ListView(
                  padding: const EdgeInsets.fromLTRB(12, 12, 12, 90),
                  children: [
                    const Card(
                        child: ListTile(
                            leading:
                                Icon(Icons.info_outline_rounded, color: _blue),
                            title: Text('Um cadastro, vários papéis'),
                            subtitle: Text(
                                'Cadastre cada empresa apenas uma vez e marque se ela é Cliente/Contratante, Proprietária/Locadora e/ou Fornecedor de combustível.'))),
                    if (items!.isEmpty)
                      const Padding(
                          padding: EdgeInsets.only(top: 120),
                          child: Center(
                              child: Text('Nenhuma empresa cadastrada.'))),
                    ...items!.map((x) {
                      final roles = rolesOf(x);
                      final address = addressOf(x);
                      return Card(
                          child: InkWell(
                              onTap: busy ? null : () => edit(x),
                              borderRadius: BorderRadius.circular(12),
                              child: Padding(
                                  padding: const EdgeInsets.all(14),
                                  child: Column(
                                      crossAxisAlignment:
                                          CrossAxisAlignment.start,
                                      children: [
                                        Row(children: [
                                          CircleAvatar(
                                              child: Icon(x[
                                                          'is_fuel_supplier'] ==
                                                      true
                                                  ? Icons
                                                      .local_gas_station_rounded
                                                  : x['is_equipment_owner'] ==
                                                          true
                                                      ? Icons
                                                          .precision_manufacturing_outlined
                                                      : Icons
                                                          .business_rounded)),
                                          const SizedBox(width: 10),
                                          Expanded(
                                              child: Text('${x['name']}',
                                                  style: const TextStyle(
                                                      fontWeight:
                                                          FontWeight.w900,
                                                      fontSize: 16))),
                                          IconButton(
                                              tooltip:
                                                  'Excluir sem apagar histórico',
                                              onPressed: busy
                                                  ? null
                                                  : () => removeCompany(x),
                                              icon: const Icon(
                                                  Icons.delete_outline_rounded,
                                                  color: Colors.red)),
                                          const Icon(
                                              Icons.chevron_right_rounded)
                                        ]),
                                        const SizedBox(height: 8),
                                        Wrap(
                                            spacing: 6,
                                            runSpacing: 6,
                                            children: roles.isEmpty
                                                ? [
                                                    const Chip(
                                                        label: Text(
                                                            'Sem função definida'))
                                                  ]
                                                : roles
                                                    .map((r) => Chip(
                                                        label: Text(r,
                                                            style: const TextStyle(
                                                                fontWeight:
                                                                    FontWeight
                                                                        .w900))))
                                                    .toList()),
                                        if (_hasValue(x['document']))
                                          Padding(
                                              padding:
                                                  const EdgeInsets.only(top: 6),
                                              child: Text(
                                                  'CNPJ: ${x['document']}')),
                                        if (address.isNotEmpty)
                                          Padding(
                                              padding:
                                                  const EdgeInsets.only(top: 3),
                                              child: Text(address,
                                                  style: const TextStyle(
                                                      color: Colors.black54))),
                                      ]))));
                    }),
                  ],
                ),
              ),
      );
}

class AdminCatalogScreen extends StatelessWidget {
  final Map<String, dynamic> profile;
  const AdminCatalogScreen({super.key, required this.profile});

  @override
  Widget build(BuildContext context) {
    final isAdmin = profile['is_admin'] == true;
    return Scaffold(
      appBar: AppBar(title: const Text('Cadastros')),
      body: ListView(padding: const EdgeInsets.all(16), children: [
        if (isAdmin) ...[
          HomeActionCard(
              icon: Icons.badge_outlined,
              title: 'Dados da empresa',
              subtitle:
                  'Sua empresa operadora: identificação institucional usada nos PDFs e relatórios',
              onTap: () => Navigator.push(
                  context,
                  MaterialPageRoute(
                      builder: (_) => const ReportCompanyAdminScreen()))),
          const SizedBox(height: 10),
          HomeActionCard(
              icon: Icons.business_outlined,
              title: 'Empresas',
              subtitle:
                  'Clientes/contratantes, proprietárias/locadoras e fornecedores de combustível',
              onTap: () => Navigator.push(
                  context,
                  MaterialPageRoute(
                      builder: (_) => const CompaniesAdminScreen()))),
          const SizedBox(height: 10),
        ],
        HomeActionCard(
            icon: Icons.location_city_outlined,
            title: 'Obras',
            subtitle: isAdmin
                ? 'Cadastrar, editar e consultar obras'
                : 'Consultar obras cadastradas',
            onTap: () => Navigator.push(
                context,
                MaterialPageRoute(
                    builder: (_) => WorksAdminScreen(profile: profile)))),
        const SizedBox(height: 10),
        HomeActionCard(
            icon: Icons.precision_manufacturing_outlined,
            title: 'Ativos próprios',
            subtitle: isAdmin
                ? 'Cadastrar, editar e consultar equipamentos próprios'
                : 'Consultar equipamentos próprios',
            onTap: () => Navigator.push(
                context,
                MaterialPageRoute(
                    builder: (_) => MachinesAdminScreen(canEdit: isAdmin)))),
        const SizedBox(height: 10),
        HomeActionCard(
            icon: Icons.handyman_outlined,
            title: 'Equipamentos de terceiros',
            subtitle: isAdmin
                ? 'Cadastrar, editar e consultar equipamentos contratados'
                : 'Consultar equipamentos contratados',
            onTap: () => Navigator.push(
                context,
                MaterialPageRoute(
                    builder: (_) => ThirdPartyAdminScreen(canEdit: isAdmin)))),
        if (isAdmin) ...[
          const SizedBox(height: 10),
          HomeActionCard(
              icon: Icons.oil_barrel_outlined,
              title: 'Tanques estacionários',
              subtitle: 'Cadastrar tanques estacionários e alterar capacidades',
              onTap: () => Navigator.push(context,
                  MaterialPageRoute(builder: (_) => const TanksAdminScreen()))),
          const SizedBox(height: 10),
          HomeActionCard(
              icon: Icons.local_shipping_rounded,
              title: 'Função Caminhão-tanque',
              subtitle:
                  'Atribuir, editar ou remover a função de caminhão-tanque de um ativo',
              onTap: () => Navigator.push(
                  context,
                  MaterialPageRoute(
                      builder: (_) => const TruckFunctionAdminScreen()))),
        ],
      ]),
    );
  }
}

class TruckFunctionAdminScreen extends StatefulWidget {
  const TruckFunctionAdminScreen({super.key});
  @override
  State<TruckFunctionAdminScreen> createState() =>
      _TruckFunctionAdminScreenState();
}

class _TruckFunctionAdminScreenState extends State<TruckFunctionAdminScreen> {
  List<Map<String, dynamic>> trucks = [];
  List<Map<String, dynamic>> machines = [];
  bool loading = true, busy = false;
  @override
  void initState() {
    super.initState();
    load();
  }

  Future<void> load() async {
    try {
      final t = await api.truckRoles();
      final r = await api.referenceData();
      if (mounted)
        setState(() {
          trucks = t;
          machines = _rows(r['machines']);
          loading = false;
        });
    } catch (e) {
      if (mounted) {
        setState(() => loading = false);
        ScaffoldMessenger.of(context)
            .showSnackBar(SnackBar(content: Text(_friendlyError(e))));
      }
    }
  }

  Future<void> edit([Map<String, dynamic>? item]) async {
    int? machineId = _intOrNull(item?['machine_id']);
    final capacity = TextEditingController(
        text: item == null
            ? '40000'
            : _num(item['capacity_liters']).toStringAsFixed(0));
    bool active = item?['active'] != false;
    final ok = await showDialog<bool>(
        context: context,
        builder: (ctx) => StatefulBuilder(
            builder: (ctx, setD) => AlertDialog(
                    title: Text(item == null
                        ? 'Adicionar caminhão-tanque'
                        : 'Editar função caminhão-tanque'),
                    content: SingleChildScrollView(
                        child:
                            Column(mainAxisSize: MainAxisSize.min, children: [
                      DropdownButtonFormField<int>(
                          initialValue: machineId,
                          isExpanded: true,
                          decoration:
                              const InputDecoration(labelText: 'Ativo *'),
                          items: machines
                              .map((m) => DropdownMenuItem(
                                  value: _intOrNull(m['id']),
                                  child: Text(
                                      '${m['numeroAtivo']} • ${m['modelo'] ?? ''}')))
                              .toList(),
                          onChanged: (v) => setD(() => machineId = v)),
                      const SizedBox(height: 10),
                      TextField(
                          controller: capacity,
                          keyboardType: const TextInputType.numberWithOptions(
                              decimal: true),
                          decoration: const InputDecoration(
                              labelText: 'Capacidade (litros) *')),
                      SwitchListTile(
                          contentPadding: EdgeInsets.zero,
                          title: const Text('Função ativa'),
                          value: active,
                          onChanged: (v) => setD(() => active = v)),
                    ])),
                    actions: [
                      TextButton(
                          onPressed: () => Navigator.pop(ctx, false),
                          child: const Text('Cancelar')),
                      FilledButton(
                          onPressed: () => Navigator.pop(ctx, true),
                          child: const Text('Salvar'))
                    ])));
    if (ok == true) {
      final cap = double.tryParse(capacity.text.trim().replaceAll(',', '.'));
      if (machineId == null || cap == null || cap <= 0) {
        if (mounted)
          ScaffoldMessenger.of(context).showSnackBar(const SnackBar(
              content:
                  Text('Selecione o ativo e informe uma capacidade válida.')));
      } else {
        setState(() => busy = true);
        try {
          await api.saveTruckRole(
              tankId: _intOrNull(item?['id']),
              machineId: machineId!,
              capacityLiters: cap,
              active: active);
          await load();
          if (mounted)
            ScaffoldMessenger.of(context).showSnackBar(const SnackBar(
                content: Text('Função caminhão-tanque atualizada.')));
        } catch (e) {
          if (mounted)
            ScaffoldMessenger.of(context)
                .showSnackBar(SnackBar(content: Text(_friendlyError(e))));
        } finally {
          if (mounted) setState(() => busy = false);
        }
      }
    }
    capacity.dispose();
  }

  Future<void> remove(Map<String, dynamic> item) async {
    final id = _intOrNull(item['id']);
    if (id == null) return;
    final ok = await showDialog<bool>(
        context: context,
        builder: (ctx) => AlertDialog(
                title: Text(
                    'Remover função de ${item['machine_asset_number'] ?? item['code']}?'),
                content: const Text(
                    'O ativo será preservado. Se houver histórico, a estrutura será apenas desativada para manter a rastreabilidade.'),
                actions: [
                  TextButton(
                      onPressed: () => Navigator.pop(ctx, false),
                      child: const Text('Cancelar')),
                  FilledButton(
                      onPressed: () => Navigator.pop(ctx, true),
                      child: const Text('Remover função'))
                ]));
    if (ok != true) return;
    setState(() => busy = true);
    try {
      final r = await api.removeTruckRole(id);
      await load();
      if (mounted)
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(
            content: Text(r['action'] == 'deleted'
                ? 'Função removida.'
                : 'Função desativada e histórico preservado.')));
    } catch (e) {
      if (mounted)
        ScaffoldMessenger.of(context)
            .showSnackBar(SnackBar(content: Text(_friendlyError(e))));
    } finally {
      if (mounted) setState(() => busy = false);
    }
  }

  @override
  Widget build(BuildContext context) => Scaffold(
      appBar: AppBar(title: const Text('Função Caminhão-tanque')),
      floatingActionButton: FloatingActionButton.extended(
          onPressed: busy ? null : () => edit(),
          icon: const Icon(Icons.add),
          label: const Text('Adicionar')),
      body: loading
          ? const Center(child: CircularProgressIndicator())
          : RefreshIndicator(
              onRefresh: load,
              child: ListView(
                  padding: const EdgeInsets.fromLTRB(12, 12, 12, 90),
                  children: [
                    if (trucks.isEmpty)
                      const Padding(
                          padding: EdgeInsets.all(32),
                          child: Text('Nenhum caminhão-tanque configurado.',
                              textAlign: TextAlign.center)),
                    ...trucks.map((x) => Card(
                        child: ListTile(
                            leading: const Icon(Icons.local_shipping_rounded,
                                color: _blue),
                            title: Text(
                                '${x['machine_asset_number'] ?? 'Sem ativo'} • ${x['code']}',
                                style: const TextStyle(
                                    fontWeight: FontWeight.w900)),
                            subtitle: Text(
                                '${x['machine_model'] ?? ''}\nCapacidade: ${_fmtLiters(x['capacity_liters'])} • Saldo: ${_fmtLiters(x['current_balance_liters'])} • ${x['active'] == true ? 'Ativo' : 'Inativo'}'),
                            isThreeLine: true,
                            onTap: busy ? null : () => edit(x),
                            trailing: PopupMenuButton<String>(
                                enabled: !busy,
                                onSelected: (v) {
                                  if (v == 'edit') edit(x);
                                  if (v == 'remove') remove(x);
                                },
                                itemBuilder: (_) => const [
                                      PopupMenuItem(
                                          value: 'edit', child: Text('Editar')),
                                      PopupMenuItem(
                                          value: 'remove',
                                          child: Text('Remover função'))
                                    ])))),
                  ])));
}

class TanksAdminScreen extends StatefulWidget {
  const TanksAdminScreen({super.key});

  @override
  State<TanksAdminScreen> createState() => _TanksAdminScreenState();
}

class _TanksAdminScreenState extends State<TanksAdminScreen> {
  List<Map<String, dynamic>>? items;
  bool busy = false;

  @override
  void initState() {
    super.initState();
    load();
  }

  Future<void> load() async {
    try {
      final d = await api.referenceData();
      if (mounted)
        setState(() => items = _sortedFuelUnits(d['tanks'])
            .where((t) => t['tank_type'] == 'stationary')
            .toList());
    } catch (e) {
      if (mounted)
        ScaffoldMessenger.of(context)
            .showSnackBar(SnackBar(content: Text(_friendlyError(e))));
    }
  }

  Future<void> removeUnit(Map<String, dynamic> item) async {
    final tankId = _intOrNull(item['id']);
    if (tankId == null) return;
    final ok = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: Text('Remover ${item['code']}?'),
        content: const Text(
            'Se a unidade ainda não tiver lançamentos e estiver sem saldo, ela será excluída. Se já possuir histórico, será desativada para preservar os registros.'),
        actions: [
          TextButton(
              onPressed: () => Navigator.pop(ctx, false),
              child: const Text('Cancelar')),
          FilledButton(
              onPressed: () => Navigator.pop(ctx, true),
              child: const Text('Confirmar')),
        ],
      ),
    );
    if (ok != true) return;
    setState(() => busy = true);
    try {
      final result = await api.removeTank(tankId);
      await load();
      if (!mounted) return;
      final deleted = result['action'] == 'deleted';
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(
          content: Text(deleted
              ? 'Unidade excluída.'
              : 'Unidade desativada. O histórico foi preservado.')));
    } catch (e) {
      if (mounted)
        ScaffoldMessenger.of(context)
            .showSnackBar(SnackBar(content: Text(_friendlyError(e))));
    } finally {
      if (mounted) setState(() => busy = false);
    }
  }

  Future<void> edit([Map<String, dynamic>? item]) async {
    final creating = item == null;
    final code = TextEditingController(text: '${item?['code'] ?? ''}');
    final name = TextEditingController(text: '${item?['name'] ?? ''}');
    final currentCapacity =
        item == null ? '' : _num(item['capacity_liters']).toStringAsFixed(0);
    final capacity = TextEditingController(text: currentCapacity);
    var tankType = 'stationary';

    final ok = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: Text(creating
            ? 'Cadastrar tanque estacionário'
            : 'Editar tanque estacionário'),
        content: SingleChildScrollView(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              TextField(
                controller: code,
                textCapitalization: TextCapitalization.characters,
                decoration: const InputDecoration(
                    labelText: 'Código *', hintText: 'Ex.: TE02'),
              ),
              const SizedBox(height: 10),
              TextField(
                  controller: name,
                  decoration: const InputDecoration(labelText: 'Nome *')),
              const SizedBox(height: 10),
              TextField(
                controller: capacity,
                keyboardType:
                    const TextInputType.numberWithOptions(decimal: true),
                decoration:
                    const InputDecoration(labelText: 'Capacidade (litros) *'),
              ),
              const SizedBox(height: 10),
              const InputDecorator(
                  decoration: InputDecoration(labelText: 'Tipo'),
                  child: Text('Tanque estacionário')),
              if (!creating) ...[
                const SizedBox(height: 10),
                Align(
                  alignment: Alignment.centerLeft,
                  child: Text(
                      'Saldo atual: ${_fmtLiters(item['current_balance_liters'])}',
                      style: const TextStyle(fontWeight: FontWeight.w700)),
                ),
              ],
            ],
          ),
        ),
        actions: [
          TextButton(
              onPressed: () => Navigator.pop(ctx, false),
              child: const Text('Cancelar')),
          FilledButton(
              onPressed: () => Navigator.pop(ctx, true),
              child: const Text('Salvar')),
        ],
      ),
    );

    if (ok == true) {
      final parsed = double.tryParse(capacity.text.trim().replaceAll(',', '.'));
      if (code.text.trim().isEmpty ||
          name.text.trim().isEmpty ||
          parsed == null ||
          parsed <= 0) {
        if (mounted)
          ScaffoldMessenger.of(context).showSnackBar(const SnackBar(
              content: Text('Informe código, nome e capacidade válida.')));
      } else {
        setState(() => busy = true);
        try {
          final normalizedCode = code.text
              .trim()
              .toUpperCase()
              .replaceAll(RegExp(r'[^A-Z0-9]'), '');
          if (!normalizedCode.startsWith('TE'))
            throw Exception(
                'O código do tanque estacionário deve começar com TE.');
          tankType = 'stationary';
          await api.saveTank(
            id: _intOrNull(item?['id']),
            code: code.text.trim(),
            name: name.text.trim(),
            tankType: tankType,
            capacityLiters: parsed,
          );
          await load();
          if (mounted)
            ScaffoldMessenger.of(context).showSnackBar(SnackBar(
                content: Text(creating
                    ? 'Tanque estacionário cadastrado.'
                    : 'Tanque estacionário atualizado.')));
        } catch (e) {
          if (mounted)
            ScaffoldMessenger.of(context)
                .showSnackBar(SnackBar(content: Text(_friendlyError(e))));
        } finally {
          if (mounted) setState(() => busy = false);
        }
      }
    }

    code.dispose();
    name.dispose();
    capacity.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final tanks = items ?? const <Map<String, dynamic>>[];
    return Scaffold(
      appBar: AppBar(title: const Text('Tanques estacionários')),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: busy ? null : () => edit(),
        icon: const Icon(Icons.add_rounded),
        label: const Text('Novo tanque'),
      ),
      body: items == null
          ? const Center(child: CircularProgressIndicator())
          : RefreshIndicator(
              onRefresh: load,
              child: ListView.builder(
                padding: const EdgeInsets.fromLTRB(12, 12, 12, 90),
                itemCount: tanks.length,
                itemBuilder: (_, i) {
                  final t = tanks[i];
                  final stationary = t['tank_type'] == 'stationary';
                  return Card(
                    child: ListTile(
                      contentPadding: const EdgeInsets.all(14),
                      leading: Icon(
                          stationary
                              ? Icons.oil_barrel_outlined
                              : Icons.local_shipping_outlined,
                          color: _blue),
                      title: Text('${t['code']} • ${t['name']}',
                          style: const TextStyle(fontWeight: FontWeight.w900)),
                      subtitle: Text(
                          '${stationary ? 'Tanque estacionário' : 'Comboio'}\nCapacidade: ${_fmtLiters(t['capacity_liters'])} • Saldo: ${_fmtLiters(t['current_balance_liters'])}'),
                      isThreeLine: true,
                      trailing: IconButton(
                          tooltip: 'Excluir ou desativar',
                          onPressed: busy ? null : () => removeUnit(t),
                          icon: const Icon(Icons.delete_outline_rounded)),
                      onTap: busy ? null : () => edit(t),
                    ),
                  );
                },
              ),
            ),
    );
  }
}

class ReportCompanyAdminScreen extends StatefulWidget {
  const ReportCompanyAdminScreen({super.key});
  @override
  State<ReportCompanyAdminScreen> createState() =>
      _ReportCompanyAdminScreenState();
}

class _ReportCompanyAdminScreenState extends State<ReportCompanyAdminScreen> {
  final name = TextEditingController(text: 'Hydra');
  final subtitle = TextEditingController(text: 'Equipamentos');
  final document = TextEditingController();
  final address = TextEditingController();
  bool busy = true;
  String? errorMessage;

  @override
  void initState() {
    super.initState();
    load();
  }

  @override
  void dispose() {
    name.dispose();
    subtitle.dispose();
    document.dispose();
    address.dispose();
    super.dispose();
  }

  Future<void> load() async {
    if (mounted)
      setState(() {
        busy = true;
        errorMessage = null;
      });
    try {
      final d = await api.reportCompany().timeout(const Duration(seconds: 12));
      name.text = '${d['company_name'] ?? ''}';
      subtitle.text = '${d['company_subtitle'] ?? ''}';
      document.text = '${d['document'] ?? ''}';
      address.text = '${d['address'] ?? ''}';
    } catch (e) {
      errorMessage = _friendlyError(e);
    }
    if (mounted) setState(() => busy = false);
  }

  Future<void> save() async {
    if (name.text.trim().isEmpty) return;
    setState(() => busy = true);
    try {
      await api
          .saveReportCompany(
              companyName: name.text.trim(),
              companySubtitle: subtitle.text.trim(),
              document: document.text.trim(),
              address: address.text.trim())
          .timeout(const Duration(seconds: 12));
      await load();
      if (mounted)
        ScaffoldMessenger.of(context).showSnackBar(const SnackBar(
            content: Text('Dados da empresa atualizados com sucesso ✓')));
    } catch (e) {
      if (mounted)
        ScaffoldMessenger.of(context)
            .showSnackBar(SnackBar(content: Text(_friendlyError(e))));
    } finally {
      if (mounted) setState(() => busy = false);
    }
  }

  @override
  Widget build(BuildContext context) => Scaffold(
        appBar: AppBar(title: const Text('Dados da empresa')),
        body: ListView(padding: const EdgeInsets.all(16), children: [
          const Card(
              child: ListTile(
                  leading: Icon(Icons.info_outline_rounded),
                  title: Text('Sua empresa (Operadora)'),
                  subtitle: Text(
                      'É a empresa que opera o R&C, presta a mão de obra, utiliza equipamentos próprios e vende/fornece combustível ao cliente da obra. Estes dados identificam os PDFs e relatórios.'))),
          if (errorMessage != null)
            Card(
                child: Padding(
                    padding: const EdgeInsets.all(14),
                    child: Column(children: [
                      Text('Não foi possível carregar os dados: $errorMessage'),
                      const SizedBox(height: 8),
                      OutlinedButton.icon(
                          onPressed: busy ? null : load,
                          icon: const Icon(Icons.refresh),
                          label: const Text('Tentar novamente'))
                    ]))),
          const SizedBox(height: 10),
          TextField(
              controller: name,
              decoration:
                  const InputDecoration(labelText: 'Nome empresarial *')),
          const SizedBox(height: 10),
          TextField(
              controller: subtitle,
              decoration: const InputDecoration(
                  labelText: 'Texto abaixo do nome (exibido nos documentos)',
                  hintText: 'Engenharia')),
          const SizedBox(height: 10),
          TextField(
              controller: document,
              decoration: const InputDecoration(labelText: 'CNPJ')),
          const SizedBox(height: 10),
          TextField(
              controller: address,
              maxLines: 3,
              decoration:
                  const InputDecoration(labelText: 'Endereço completo')),
          const SizedBox(height: 18),
          SizedBox(
              height: 52,
              child: FilledButton.icon(
                  onPressed: busy ? null : save,
                  icon: const Icon(Icons.save_outlined),
                  label: Text(busy ? 'Salvando...' : 'Salvar alterações'))),
        ]),
      );
}

class WorksAdminScreen extends StatefulWidget {
  final Map<String, dynamic> profile;
  const WorksAdminScreen({super.key, required this.profile});
  @override
  State<WorksAdminScreen> createState() => _WorksAdminScreenState();
}

class _WorksAdminScreenState extends State<WorksAdminScreen> {
  List<Map<String, dynamic>>? items;
  List<Map<String, dynamic>> companies = [];
  bool busy = false;
  bool get canEdit => widget.profile['is_admin'] == true;
  bool get canFinalize =>
      widget.profile['is_admin'] == true ||
      widget.profile['is_manager'] == true;
  @override
  void initState() {
    super.initState();
    load();
  }

  Future<void> load() async {
    try {
      final w =
          await api.worksCatalogV28().timeout(const Duration(seconds: 15));
      var c = <Map<String, dynamic>>[];
      if (canEdit) {
        try {
          c = await api.managedCompanies();
        } catch (_) {}
      }
      if (mounted)
        setState(() {
          items = w;
          companies = c;
        });
    } catch (e) {
      if (mounted)
        ScaffoldMessenger.of(context)
            .showSnackBar(SnackBar(content: Text(_friendlyError(e))));
    }
  }

  Future<void> openCompanies() async {
    await Navigator.push(context,
        MaterialPageRoute(builder: (_) => const CompaniesAdminScreen()));
    if (mounted) load();
  }

  Future<void> edit([Map<String, dynamic>? item]) async {
    if (!canEdit) return;
    final name = TextEditingController(text: '${item?['name'] ?? ''}'),
        responsible =
            TextEditingController(text: '${item?['responsible'] ?? ''}'),
        location = TextEditingController(text: '${item?['location'] ?? ''}');
    int? companyId = _intOrNull(item?['contracting_company_id']);
    final clients = companies
        .where((x) => x['active'] != false && x['is_client'] == true)
        .toList();
    final ok = await showDialog<bool>(
        context: context,
        builder: (ctx) => StatefulBuilder(
            builder: (ctx, setD) => AlertDialog(
                    title:
                        Text(item == null ? 'Cadastrar obra' : 'Editar obra'),
                    content: SingleChildScrollView(
                        child:
                            Column(mainAxisSize: MainAxisSize.min, children: [
                      TextField(
                          controller: name,
                          decoration: const InputDecoration(
                              labelText: 'Nome da obra *')),
                      const SizedBox(height: 8),
                      DropdownButtonFormField<int>(
                          initialValue: companyId,
                          isExpanded: true,
                          decoration: const InputDecoration(
                              labelText: 'Empresa cliente / contratante *'),
                          items: clients
                              .map((c) => DropdownMenuItem(
                                  value: _intOrNull(c['id']),
                                  child: Text('${c['name']}')))
                              .toList(),
                          onChanged: (v) => setD(() => companyId = v)),
                      const SizedBox(height: 8),
                      TextField(
                          controller: responsible,
                          decoration: const InputDecoration(
                              labelText: 'Responsável da obra *')),
                      const SizedBox(height: 8),
                      TextField(
                          controller: location,
                          decoration: const InputDecoration(labelText: 'Local'))
                    ])),
                    actions: [
                      TextButton(
                          onPressed: () => Navigator.pop(ctx, false),
                          child: const Text('Cancelar')),
                      FilledButton(
                          onPressed: () => Navigator.pop(ctx, true),
                          child: const Text('Salvar'))
                    ])));
    if (ok == true) {
      if (name.text.trim().isEmpty ||
          responsible.text.trim().isEmpty ||
          companyId == null) {
        ScaffoldMessenger.of(context).showSnackBar(const SnackBar(
            content: Text(
                'Preencha Nome da obra, Empresa cliente/contratante e Responsável da obra.')));
      } else {
        setState(() => busy = true);
        try {
          await api.saveWork(
              id: _intOrNull(item?['id']),
              name: name.text.trim(),
              location: location.text.trim(),
              responsible: responsible.text.trim(),
              companyId: companyId);
          await load();
          if (mounted)
            ScaffoldMessenger.of(context).showSnackBar(
                const SnackBar(content: Text('Obra salva com sucesso ✓')));
        } catch (e) {
          if (mounted)
            ScaffoldMessenger.of(context)
                .showSnackBar(SnackBar(content: Text(_friendlyError(e))));
        } finally {
          if (mounted) setState(() => busy = false);
        }
      }
    }
    name.dispose();
    responsible.dispose();
    location.dispose();
  }

  Future<void> finalize(Map<String, dynamic> item) async {
    if (!canFinalize) return;
    if (!offlineStore.online.value) {
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(
          content: Text(
              'Internet obrigatória para finalizar e armazenar o Relatório Final.')));
      return;
    }
    final id = _intOrNull(item['id']);
    if (id == null) return;
    final count = _intOrNull(item['movement_count']) ?? 0;
    final liters = _fmtLiters(item['fueling_liters']);
    final ok = await showDialog<bool>(
        context: context,
        builder: (ctx) => AlertDialog(
                title: const Text('Finalizar obra?'),
                content: Text(
                    'Obra: ${item['name']}\nCliente: ${item['company_name'] ?? '-'}\nResponsável: ${item['responsible'] ?? '-'}\n\n$count registro(s) existentes • $liters abastecidos.\n\nA obra ficará somente para consulta e novos abastecimentos serão bloqueados. O Relatório Final será gerado e armazenado.'),
                actions: [
                  TextButton(
                      onPressed: () => Navigator.pop(ctx, false),
                      child: const Text('Cancelar')),
                  FilledButton(
                      onPressed: () => Navigator.pop(ctx, true),
                      child: const Text('Finalizar e gerar PDF'))
                ]));
    if (ok != true || !mounted) return;
    setState(() => busy = true);
    try {
      final snapshot = await api.workFinalReportDataV23(id);
      final now = DateTime.now().toUtc().toIso8601String();
      _map(snapshot['work'])['finalized_at'] = now;
      _map(snapshot['work'])['status'] = 'finalized';
      snapshot['generated_at'] = now;
      final bytes = await WorkFinalPdf.build(snapshot);
      final path = await api.uploadBytes(bytes, 'relatorio_final_obra_$id',
          mime: 'application/pdf');
      if (path.startsWith('local://'))
        throw Exception('O PDF não foi enviado ao servidor.');
      await api.finalizeWorkV23(id, path);
      await load();
      if (mounted)
        await Navigator.push(
            context,
            MaterialPageRoute(
                builder: (_) => Scaffold(
                    appBar: AppBar(title: const Text('Relatório Final')),
                    body: PdfPreview(
                        build: (_) async => bytes,
                        canChangePageFormat: false,
                        canChangeOrientation: false,
                        canDebug: false))));
    } catch (e) {
      if (mounted)
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(
            content: Text('Não foi possível finalizar: ${_friendlyError(e)}')));
    } finally {
      if (mounted) setState(() => busy = false);
    }
  }

  Future<void> deleteWork(Map<String, dynamic> x) async {
    if (!canEdit) return;
    final id = _intOrNull(x['id']);
    if (id == null) return;
    final mov = _intOrNull(x['movement_count']) ?? 0,
        rep = _intOrNull(x['report_count']) ?? 0;
    final ok = await showDialog<bool>(
        context: context,
        builder: (ctx) => AlertDialog(
                title: const Text('Enviar obra para Excluídas?'),
                content: Text(
                    'Obra: ${x['name']}\n\nEla sairá das operações ativas, mas $mov registro(s) e $rep relatório(s) permanecerão preservados e consultáveis. Você poderá restaurá-la depois.'),
                actions: [
                  TextButton(
                      onPressed: () => Navigator.pop(ctx, false),
                      child: const Text('Cancelar')),
                  FilledButton.icon(
                      style: FilledButton.styleFrom(
                          backgroundColor: Colors.red.shade700),
                      onPressed: () => Navigator.pop(ctx, true),
                      icon: const Icon(Icons.delete_outline),
                      label: const Text('Mover para Excluídas'))
                ]));
    if (ok != true) return;
    setState(() => busy = true);
    try {
      await api.deleteWorkV25(id);
      await load();
    } catch (e) {
      if (mounted)
        ScaffoldMessenger.of(context)
            .showSnackBar(SnackBar(content: Text(_friendlyError(e))));
    } finally {
      if (mounted) setState(() => busy = false);
    }
  }

  Future<void> restore(Map<String, dynamic> x) async {
    final id = _intOrNull(x['id']);
    if (id == null) return;
    final ok = await showDialog<bool>(
        context: context,
        builder: (ctx) => AlertDialog(
                title: const Text('Restaurar obra?'),
                content: Text(
                    'A obra “${x['name']}” voltará para ${x['finalized_at'] != null ? 'Finalizadas' : 'Ativas'}.'),
                actions: [
                  TextButton(
                      onPressed: () => Navigator.pop(ctx, false),
                      child: const Text('Cancelar')),
                  FilledButton(
                      onPressed: () => Navigator.pop(ctx, true),
                      child: const Text('Restaurar'))
                ]));
    if (ok == true) {
      setState(() => busy = true);
      try {
        await api.restoreWorkV28(id);
        await load();
      } catch (e) {
        if (mounted)
          ScaffoldMessenger.of(context)
              .showSnackBar(SnackBar(content: Text(_friendlyError(e))));
      } finally {
        if (mounted) setState(() => busy = false);
      }
    }
  }

  Future<void> purge(Map<String, dynamic> x) async {
    final id = _intOrNull(x['id']);
    if (id == null) return;
    final mov = _intOrNull(x['movement_count']) ?? 0,
        rep = _intOrNull(x['report_count']) ?? 0;
    if (mov > 0 || rep > 0) {
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(
          content: Text(
              'Exclusão definitiva bloqueada: $mov registro(s) e $rep relatório(s) precisam ser preservados.')));
      return;
    }
    final ok = await showDialog<bool>(
        context: context,
        builder: (ctx) => AlertDialog(
                title: const Text('Excluir definitivamente?'),
                content: Text(
                    'A obra “${x['name']}” não possui registros nem relatórios. Esta ação não poderá ser desfeita.'),
                actions: [
                  TextButton(
                      onPressed: () => Navigator.pop(ctx, false),
                      child: const Text('Cancelar')),
                  FilledButton(
                      style: FilledButton.styleFrom(
                          backgroundColor: Colors.red.shade800),
                      onPressed: () => Navigator.pop(ctx, true),
                      child: const Text('Excluir definitivamente'))
                ]));
    if (ok == true) {
      setState(() => busy = true);
      try {
        await api.purgeWorkV28(id);
        await load();
      } catch (e) {
        if (mounted)
          ScaffoldMessenger.of(context)
              .showSnackBar(SnackBar(content: Text(_friendlyError(e))));
      } finally {
        if (mounted) setState(() => busy = false);
      }
    }
  }

  Widget workCard(Map<String, dynamic> x) {
    final status = '${x['status']}';
    final deleted = status == 'deleted' || x['deleted_at'] != null;
    final finalized = status == 'finalized';
    return Card(
        child: InkWell(
            onTap: () => Navigator.push(
                context,
                MaterialPageRoute(
                    builder: (_) => WorkDetailsV28Screen(
                        profile: widget.profile,
                        workId: _intOrNull(x['id'])!,
                        onFinalize: finalize))),
            borderRadius: BorderRadius.circular(12),
            child: Padding(
                padding: const EdgeInsets.all(13),
                child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(children: [
                        CircleAvatar(
                            child: Icon(deleted
                                ? Icons.delete_outline
                                : finalized
                                    ? Icons.task_alt_rounded
                                    : Icons.location_city_outlined)),
                        const SizedBox(width: 9),
                        Expanded(
                            child: Text('${x['name']}',
                                style: const TextStyle(
                                    fontWeight: FontWeight.w900,
                                    fontSize: 16))),
                        PopupMenuButton<String>(
                            enabled: !busy,
                            onSelected: (v) {
                              if (v == 'edit') edit(x);
                              if (v == 'finalize') finalize(x);
                              if (v == 'delete') deleteWork(x);
                              if (v == 'restore') restore(x);
                              if (v == 'purge') purge(x);
                            },
                            itemBuilder: (_) => [
                                  if (!deleted && !finalized && canEdit)
                                    const PopupMenuItem(
                                        value: 'edit',
                                        child: Text('Editar obra')),
                                  if (!deleted && !finalized && canFinalize)
                                    const PopupMenuItem(
                                        value: 'finalize',
                                        child:
                                            Text('Finalizar obra e gerar PDF')),
                                  if (!deleted && canEdit)
                                    const PopupMenuItem(
                                        value: 'delete',
                                        child: Text('Excluir obra',
                                            style:
                                                TextStyle(color: Colors.red))),
                                  if (deleted && canEdit)
                                    const PopupMenuItem(
                                        value: 'restore',
                                        child: Text('Restaurar obra')),
                                  if (deleted && canEdit)
                                    const PopupMenuItem(
                                        value: 'purge',
                                        child: Text('Excluir definitivamente',
                                            style:
                                                TextStyle(color: Colors.red)))
                                ])
                      ]),
                      const SizedBox(height: 7),
                      Text(
                          'Cliente: ${x['company_name'] ?? '-'}\nResponsável: ${x['responsible'] ?? '-'}\nLocal: ${x['location'] ?? '-'}'),
                      const SizedBox(height: 8),
                      Wrap(spacing: 7, runSpacing: 6, children: [
                        Chip(
                            label: Text(deleted
                                ? 'EXCLUÍDA'
                                : finalized
                                    ? 'FINALIZADA'
                                    : 'ATIVA')),
                        Chip(
                            label: Text(
                                'Abastecido: ${_fmtLiters(x['fueling_liters'])}')),
                        Chip(
                            label: Text(
                                '${x['fueling_count'] ?? 0} abastecimento(s)')),
                        Chip(
                            label: Text(
                                '${x['own_assets_count'] ?? 0} próprios • ${x['third_assets_count'] ?? 0} terceiros'))
                      ])
                    ]))));
  }

  @override
  Widget build(BuildContext context) {
    final all = items ?? const <Map<String, dynamic>>[],
        active = all
            .where(
                (x) => '${x['status']}' == 'active' && x['deleted_at'] == null)
            .toList(),
        fin = all
            .where((x) =>
                '${x['status']}' == 'finalized' && x['deleted_at'] == null)
            .toList(),
        del = all
            .where(
                (x) => '${x['status']}' == 'deleted' || x['deleted_at'] != null)
            .toList();
    Widget tab(List<Map<String, dynamic>> l, String empty) => RefreshIndicator(
        onRefresh: load,
        child: ListView(
            padding: const EdgeInsets.fromLTRB(12, 12, 12, 90),
            children: [
              if (l.isEmpty) Card(child: ListTile(title: Text(empty))),
              ...l.map(workCard)
            ]));
    return DefaultTabController(
        length: 3,
        child: Scaffold(
            appBar: AppBar(
                title: const Text('Obras'),
                bottom: TabBar(tabs: [
                  Tab(text: 'Ativas (${active.length})'),
                  Tab(text: 'Finalizadas (${fin.length})'),
                  Tab(text: 'Excluídas (${del.length})')
                ])),
            floatingActionButton: canEdit
                ? FloatingActionButton.extended(
                    onPressed: busy
                        ? null
                        : () => companies
                                .where((x) =>
                                    x['is_client'] == true &&
                                    x['active'] != false)
                                .isEmpty
                            ? openCompanies()
                            : edit(),
                    icon: const Icon(Icons.add),
                    label: const Text('Nova obra'))
                : null,
            body: items == null
                ? const Center(child: CircularProgressIndicator())
                : TabBarView(children: [
                    tab(active, 'Nenhuma obra ativa.'),
                    tab(fin, 'Nenhuma obra finalizada.'),
                    tab(del, 'Nenhuma obra excluída.')
                  ])));
  }
}

class WorkDetailsV28Screen extends StatefulWidget {
  final Map<String, dynamic> profile;
  final int workId;
  final Future<void> Function(Map<String, dynamic>)? onFinalize;
  const WorkDetailsV28Screen(
      {super.key,
      required this.profile,
      required this.workId,
      this.onFinalize});
  @override
  State<WorkDetailsV28Screen> createState() => _WorkDetailsV28ScreenState();
}

class _WorkDetailsV28ScreenState extends State<WorkDetailsV28Screen> {
  Map<String, dynamic>? data;
  bool busy = false;
  @override
  void initState() {
    super.initState();
    load();
  }

  Future<void> load() async {
    setState(() => busy = true);
    try {
      final d = await api.workDetailV28(widget.workId);
      if (mounted) setState(() => data = d);
    } catch (e) {
      if (mounted)
        ScaffoldMessenger.of(context)
            .showSnackBar(SnackBar(content: Text(_friendlyError(e))));
    } finally {
      if (mounted) setState(() => busy = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final w = _map(data?['work']);
    final sm = _map(data?['summary']);
    Widget metric(String l, String v) => Expanded(
            child: Card(
                child: Padding(
          padding: const EdgeInsets.all(12),
          child:
              Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            Text(l,
                style: const TextStyle(fontSize: 11, color: Colors.black54)),
            const SizedBox(height: 3),
            Text(v,
                style:
                    const TextStyle(fontWeight: FontWeight.w900, fontSize: 17)),
          ]),
        )));
    return Scaffold(
      appBar:
          AppBar(title: Text(w.isEmpty ? 'Detalhes da obra' : '${w['name']}')),
      body: data == null
          ? const Center(child: CircularProgressIndicator())
          : RefreshIndicator(
              onRefresh: load,
              child: ListView(padding: const EdgeInsets.all(12), children: [
                Card(
                    child: Padding(
                        padding: const EdgeInsets.all(15),
                        child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text('${w['name']}',
                                  style: const TextStyle(
                                      fontWeight: FontWeight.w900,
                                      fontSize: 20)),
                              const SizedBox(height: 7),
                              Text(
                                  'Empresa cliente/contratante: ${w['company_name'] ?? '-'}\nResponsável da obra: ${w['responsible'] ?? '-'}\nLocal: ${w['location'] ?? '-'}\nStatus: ${w['status'] ?? '-'}'),
                            ]))),
                Row(children: [
                  metric('Total abastecido', _fmtLiters(sm['fueling_liters'])),
                  metric('Abastecimentos', '${sm['fueling_count'] ?? 0}')
                ]),
                Row(children: [
                  metric('Registros', '${sm['movement_count'] ?? 0}'),
                  if (sm['sale_total'] != null)
                    metric('Valor', _fmtMoney(sm['sale_total']))
                  else
                    metric('Combustíveis',
                        '${_rows(data?['fuel_breakdown']).length}')
                ]),
                if (_rows(data?['fuel_breakdown']).isNotEmpty)
                  Card(
                      child: Padding(
                          padding: const EdgeInsets.all(14),
                          child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                const Text('Consumo por combustível',
                                    style:
                                        TextStyle(fontWeight: FontWeight.w900)),
                                const SizedBox(height: 7),
                                ..._rows(data?['fuel_breakdown']).map((x) =>
                                    ListTile(
                                        dense: true,
                                        contentPadding: EdgeInsets.zero,
                                        title: Text('${x['fuel_type']}'),
                                        trailing: Text(_fmtLiters(x['liters']),
                                            style: const TextStyle(
                                                fontWeight: FontWeight.w900)))),
                              ]))),
                if (_rows(data?['own_assets']).isNotEmpty)
                  Card(
                      child: ExpansionTile(
                    title: const Text('Equipamentos próprios',
                        style: TextStyle(fontWeight: FontWeight.w900)),
                    children: _rows(data?['own_assets'])
                        .map((x) => ListTile(
                            title: Text(
                                '${x['asset_number']} • ${x['model'] ?? ''}'),
                            subtitle: _hasValue(x['plate'])
                                ? Text('Placa: ${x['plate']}')
                                : null,
                            trailing: Text(_fmtLiters(x['liters']))))
                        .toList(),
                  )),
                if (_rows(data?['third_assets']).isNotEmpty)
                  Card(
                      child: ExpansionTile(
                    title: const Text('Equipamentos de terceiros',
                        style: TextStyle(fontWeight: FontWeight.w900)),
                    children: _rows(data?['third_assets'])
                        .map((x) => ListTile(
                            title: Text(_plateDescriptionLabel(
                                x['plate'], x['description'])),
                            subtitle: Text('${x['company_name'] ?? '-'}'),
                            trailing: Text(_fmtLiters(x['liters']))))
                        .toList(),
                  )),
                if (_rows(data?['reports']).isNotEmpty)
                  Card(
                      child: ExpansionTile(
                    title: const Text('Relatórios',
                        style: TextStyle(fontWeight: FontWeight.w900)),
                    children: _rows(data?['reports'])
                        .map((r) => ListTile(
                              leading: const Icon(Icons.picture_as_pdf_outlined,
                                  color: _blue),
                              title: Text('${r['title']}'),
                              subtitle: Text(_fmtDate(r['report_date'])),
                              onTap: () async {
                                final b =
                                    await api.downloadMedia('${r['pdf_path']}');
                                if (b != null && mounted) {
                                  await Navigator.push(
                                      context,
                                      MaterialPageRoute(
                                          builder: (_) => Scaffold(
                                                appBar: AppBar(
                                                    title:
                                                        Text('${r['title']}')),
                                                body: PdfPreview(
                                                    build: (_) async => b,
                                                    canChangePageFormat: false,
                                                    canChangeOrientation: false,
                                                    canDebug: false),
                                              )));
                                }
                              },
                            ))
                        .toList(),
                  )),
                const SizedBox(height: 5),
                FilledButton.icon(
                  onPressed: () => Navigator.push(
                      context,
                      MaterialPageRoute(
                          builder: (_) => GeneralRecordsV28Screen(
                              initialWorkId: widget.workId))),
                  icon: const Icon(Icons.manage_search),
                  label: const Text('Ver Registro Geral desta obra'),
                ),
                if ('${w['status']}' == 'active' &&
                    widget.onFinalize != null &&
                    (widget.profile['is_admin'] == true ||
                        widget.profile['is_manager'] == true)) ...[
                  const SizedBox(height: 8),
                  OutlinedButton.icon(
                    onPressed: busy
                        ? null
                        : () async {
                            final target = Map<String, dynamic>.from(w)
                              ..addAll(sm);
                            await widget.onFinalize!(target);
                            if (mounted) load();
                          },
                    icon: const Icon(Icons.task_alt_outlined),
                    label: const Text('Finalizar obra e gerar Relatório Final'),
                  ),
                ],
                const SizedBox(height: 40),
              ]),
            ),
    );
  }
}

String _measurementTypeLabel(dynamic value) {
  switch ('${value ?? ''}'.trim().toLowerCase()) {
    case 'km':
      return 'KM';
    case 'hourmeter':
      return 'Horímetro';
    case 'both':
      return 'KM + Horímetro';
    case 'none':
      return 'Não se aplica';
    default:
      return 'Não definido';
  }
}

class MachinesAdminScreen extends StatefulWidget {
  final bool canEdit;
  const MachinesAdminScreen({super.key, this.canEdit = false});
  @override
  State<MachinesAdminScreen> createState() => _MachinesAdminScreenState();
}

class _MachinesAdminScreenState extends State<MachinesAdminScreen> {
  List<Map<String, dynamic>>? items;
  final filter = TextEditingController();
  @override
  void initState() {
    super.initState();
    load();
  }

  @override
  void dispose() {
    filter.dispose();
    super.dispose();
  }

  Future<void> load() async {
    final d = await api.referenceData();
    if (mounted) setState(() => items = _rows(d['machines']));
  }

  Future<void> edit([Map<String, dynamic>? item]) async {
    if (!widget.canEdit) return;
    final number = TextEditingController(text: '${item?['numeroAtivo'] ?? ''}');
    final model = TextEditingController(text: '${item?['modelo'] ?? ''}');
    final plate = TextEditingController(text: '${item?['placa'] ?? ''}');
    final type = TextEditingController(text: '${item?['tipo'] ?? ''}');
    final location =
        TextEditingController(text: '${item?['localizacao'] ?? ''}');
    final capacity = TextEditingController(
        text: item?['comboio_capacity_liters'] == null
            ? ''
            : _num(item?['comboio_capacity_liters']).toStringAsFixed(0));
    final fuelCapacity = TextEditingController(
        text: item?['fuel_tank_capacity_liters'] == null
            ? ''
            : _num(item?['fuel_tank_capacity_liters']).toStringAsFixed(0));
    final measurementRaw = '${item?['measurement_type'] ?? ''}'.trim();
    String? measurement = measurementRaw.isEmpty ? null : measurementRaw;
    final ok = await showDialog<bool>(
        context: context,
        builder: (ctx) => StatefulBuilder(builder: (ctx, setLocal) {
              final isComboio = number.text.trim().startsWith('008');
              return AlertDialog(
                  title:
                      Text(item == null ? 'Cadastrar ativo' : 'Editar ativo'),
                  content: SingleChildScrollView(
                      child: Column(mainAxisSize: MainAxisSize.min, children: [
                    TextField(
                        controller: number,
                        onChanged: (_) => setLocal(() {}),
                        decoration: const InputDecoration(
                            labelText: 'Número do ativo *')),
                    const SizedBox(height: 8),
                    TextField(
                        controller: model,
                        decoration: const InputDecoration(labelText: 'Modelo')),
                    const SizedBox(height: 8),
                    TextField(
                        controller: plate,
                        decoration: const InputDecoration(labelText: 'Placa')),
                    const SizedBox(height: 8),
                    TextField(
                        controller: type,
                        decoration: const InputDecoration(labelText: 'Tipo')),
                    const SizedBox(height: 8),
                    DropdownButtonFormField<String>(
                        initialValue: measurement,
                        decoration: const InputDecoration(
                            labelText: 'Tipo de medição *'),
                        items: const [
                          DropdownMenuItem(value: 'km', child: Text('KM')),
                          DropdownMenuItem(
                              value: 'hourmeter', child: Text('Horímetro')),
                          DropdownMenuItem(
                              value: 'both', child: Text('KM + Horímetro')),
                          DropdownMenuItem(
                              value: 'none', child: Text('Não se aplica')),
                        ],
                        onChanged: (v) => setLocal(() => measurement = v)),
                    const Padding(
                        padding: EdgeInsets.only(top: 5),
                        child: Align(
                            alignment: Alignment.centerLeft,
                            child: Text(
                                'Define qual medição será exigida ao abastecer este ativo.',
                                style: TextStyle(
                                    fontSize: 12, color: Colors.black54)))),
                    if (isComboio) ...[
                      const SizedBox(height: 8),
                      TextField(
                          controller: capacity,
                          keyboardType: const TextInputType.numberWithOptions(
                              decimal: true),
                          decoration: const InputDecoration(
                              labelText: 'Capacidade do comboio (litros) *')),
                      if (_hasValue(item?['comboio_code']))
                        Padding(
                            padding: const EdgeInsets.only(top: 8),
                            child: Align(
                                alignment: Alignment.centerLeft,
                                child: Text(
                                    'Unidade: ${item?['comboio_code']} • Saldo: ${_fmtLiters(item?['comboio_balance_liters'])}',
                                    style: const TextStyle(
                                        fontWeight: FontWeight.w700)))),
                    ],
                    const SizedBox(height: 8),
                    TextField(
                        controller: fuelCapacity,
                        keyboardType: const TextInputType.numberWithOptions(
                            decimal: true),
                        decoration: const InputDecoration(
                            labelText:
                                'Capacidade do tanque de combustível do ativo (litros)')),
                    const SizedBox(height: 8),
                    TextField(
                        controller: location,
                        decoration:
                            const InputDecoration(labelText: 'Localização')),
                  ])),
                  actions: [
                    TextButton(
                        onPressed: () => Navigator.pop(ctx, false),
                        child: const Text('Cancelar')),
                    FilledButton(
                        onPressed: () => Navigator.pop(ctx, true),
                        child: const Text('Salvar'))
                  ]);
            }));
    if (ok == true && number.text.trim().isNotEmpty) {
      if (measurement == null) {
        if (mounted)
          ScaffoldMessenger.of(context).showSnackBar(const SnackBar(
              content: Text('Selecione o tipo de medição do ativo.')));
      } else {
        final isComboio = number.text.trim().startsWith('008');
        final parsed =
            double.tryParse(capacity.text.trim().replaceAll(',', '.'));
        if (isComboio && (parsed == null || parsed <= 0)) {
          if (mounted)
            ScaffoldMessenger.of(context).showSnackBar(const SnackBar(
                content: Text('Informe a capacidade do comboio.')));
        } else {
          try {
            final parsedFuel = fuelCapacity.text.trim().isEmpty
                ? null
                : double.tryParse(
                    fuelCapacity.text.trim().replaceAll(',', '.'));
            if (fuelCapacity.text.trim().isNotEmpty &&
                (parsedFuel == null || parsedFuel <= 0))
              throw Exception(
                  'Informe uma capacidade válida para o tanque de combustível do ativo.');
            await api.saveMachine(
                id: _intOrNull(item?['id']),
                assetNumber: number.text.trim(),
                model: model.text.trim(),
                plate: plate.text.trim(),
                type: type.text.trim(),
                location: location.text.trim(),
                comboioCapacityLiters: isComboio ? parsed : null,
                fuelTankCapacityLiters: parsedFuel,
                measurementType: measurement!);
            await load();
            if (mounted)
              ScaffoldMessenger.of(context).showSnackBar(SnackBar(
                  content: Text(isComboio
                      ? 'Ativo e comboio sincronizados.'
                      : 'Ativo salvo com sucesso ✓')));
          } catch (e) {
            if (mounted)
              ScaffoldMessenger.of(context)
                  .showSnackBar(SnackBar(content: Text(_friendlyError(e))));
          }
        }
      }
    }
    number.dispose();
    model.dispose();
    plate.dispose();
    type.dispose();
    location.dispose();
    capacity.dispose();
    fuelCapacity.dispose();
  }

  Future<void> removeMachine(Map<String, dynamic> x) async {
    if (!widget.canEdit) return;
    final label = '${x['numeroAtivo'] ?? x['asset_number'] ?? 'este ativo'}';
    final ok = await showDialog<bool>(
        context: context,
        builder: (ctx) => AlertDialog(
              title: const Text('Excluir ativo?'),
              content: Text(
                  '$label será retirado dos cadastros ativos e não poderá ser selecionado em novos abastecimentos. Todo o histórico, KM/horímetro, relatórios, fotos e auditoria permanecerão preservados.'),
              actions: [
                TextButton(
                    onPressed: () => Navigator.pop(ctx, false),
                    child: const Text('Cancelar')),
                FilledButton(
                    style: FilledButton.styleFrom(
                        backgroundColor: Colors.red.shade700),
                    onPressed: () => Navigator.pop(ctx, true),
                    child: const Text('Excluir'))
              ],
            ));
    if (ok != true) return;
    try {
      await api.archiveMachine(x);
      await load();
      if (mounted)
        ScaffoldMessenger.of(context).showSnackBar(const SnackBar(
            content: Text(
                'Ativo retirado dos cadastros ativos. Histórico preservado ✓')));
    } catch (e) {
      if (mounted)
        ScaffoldMessenger.of(context)
            .showSnackBar(SnackBar(content: Text(_friendlyError(e))));
    }
  }

  @override
  Widget build(BuildContext context) {
    final q = filter.text.trim().toLowerCase();
    final shown = (items ?? [])
        .where((x) =>
            q.isEmpty ||
            '${x['numeroAtivo']} ${x['modelo']} ${x['placa']}'
                .toLowerCase()
                .contains(q))
        .toList();
    return Scaffold(
        appBar: AppBar(title: const Text('Ativos próprios')),
        floatingActionButton: widget.canEdit
            ? FloatingActionButton(
                onPressed: () => edit(), child: const Icon(Icons.add))
            : null,
        body: items == null
            ? const Center(child: CircularProgressIndicator())
            : Column(children: [
                Padding(
                    padding: const EdgeInsets.all(12),
                    child: TextField(
                        controller: filter,
                        onChanged: (_) => setState(() {}),
                        decoration: const InputDecoration(
                            labelText: 'Pesquisar ativo ou placa',
                            prefixIcon: Icon(Icons.search)))),
                Expanded(
                    child: ListView.builder(
                        padding: const EdgeInsets.fromLTRB(12, 0, 12, 80),
                        itemCount: shown.length,
                        itemBuilder: (_, i) {
                          final x = shown[i];
                          return Card(
                              child: ListTile(
                                  title: Text(
                                      '${x['numeroAtivo']} • ${x['modelo'] ?? ''}',
                                      style: const TextStyle(
                                          fontWeight: FontWeight.w900)),
                                  subtitle: Text([
                                    if (_hasValue(x['placa']))
                                      'Placa: ${x['placa']}',
                                    'Medição: ${_measurementTypeLabel(x['measurement_type'])}',
                                    'Tanque: ${x['fuel_tank_capacity_liters'] == null ? '-' : _fmtLiters(x['fuel_tank_capacity_liters'])}',
                                    if (_hasValue(x['localizacao']))
                                      '${x['localizacao']}'
                                  ].join(' • ')),
                                  onTap: widget.canEdit ? () => edit(x) : null,
                                  trailing: widget.canEdit
                                      ? PopupMenuButton<String>(
                                          onSelected: (v) {
                                            if (v == 'edit') edit(x);
                                            if (v == 'delete') removeMachine(x);
                                          },
                                          itemBuilder: (_) => const [
                                                PopupMenuItem(
                                                    value: 'edit',
                                                    child: Text('Editar')),
                                                PopupMenuItem(
                                                    value: 'delete',
                                                    child: Text('Excluir',
                                                        style: TextStyle(
                                                            color: Colors.red)))
                                              ])
                                      : null));
                        }))
              ]));
  }
}

class ThirdPartyAdminScreen extends StatefulWidget {
  final bool canEdit;
  const ThirdPartyAdminScreen({super.key, this.canEdit = false});
  @override
  State<ThirdPartyAdminScreen> createState() => _ThirdPartyAdminScreenState();
}

class _ThirdPartyAdminScreenState extends State<ThirdPartyAdminScreen> {
  List<Map<String, dynamic>>? items;
  List<Map<String, dynamic>> companies = [];
  bool loading = false;
  @override
  void initState() {
    super.initState();
    load();
  }

  Future<void> load() async {
    if (mounted) setState(() => loading = true);
    try {
      final reference = await api.referenceData();
      final c = <Map<String, dynamic>>[];
      if (widget.canEdit) {
        c.addAll(await api.managedCompanies());
        c.removeWhere(
            (x) => x['active'] == false || x['is_equipment_owner'] != true);
        c.sort((a, b) => '${a['name']}'
            .toLowerCase()
            .compareTo('${b['name']}'.toLowerCase()));
      }
      if (mounted)
        setState(() {
          items = _rows(reference['third_party_vehicles']);
          companies = c;
        });
    } catch (e) {
      if (mounted)
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(
            content: Text(
                'Erro ao carregar equipamentos/empresas: ${_friendlyError(e)}')));
    } finally {
      if (mounted) setState(() => loading = false);
    }
  }

  int? companyIdFor(String name) {
    for (final c in companies) {
      if ('${c['name']}'.trim().toLowerCase() == name.trim().toLowerCase())
        return _intOrNull(c['id']);
    }
    return null;
  }

  String? companyNameFor(int? id) {
    if (id == null) return null;
    for (final c in companies) {
      if (_intOrNull(c['id']) == id) return '${c['name']}';
    }
    return null;
  }

  Future<void> edit([Map<String, dynamic>? item]) async {
    if (!widget.canEdit) return;
    final plate = TextEditingController(text: '${item?['plate'] ?? ''}'),
        desc = TextEditingController(text: '${item?['description'] ?? ''}');
    int? companyId = companyIdFor('${item?['company_name'] ?? ''}');
    if (companies.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(
          content: Text(
              'Nenhuma empresa Proprietária / Locadora cadastrada. Cadastre a empresa e marque esse tipo de relação antes do equipamento.')));
      plate.dispose();
      desc.dispose();
      return;
    }
    final ok = await showDialog<bool>(
        context: context,
        builder: (ctx) => StatefulBuilder(
            builder: (ctx, setD) => AlertDialog(
                    title: Text(item == null
                        ? 'Cadastrar equipamento de terceiros'
                        : 'Editar equipamento de terceiros'),
                    content: SingleChildScrollView(
                        child:
                            Column(mainAxisSize: MainAxisSize.min, children: [
                      DropdownButtonFormField<int>(
                          initialValue: companyId,
                          isExpanded: true,
                          decoration: const InputDecoration(
                              labelText: 'Empresa proprietária / locadora *'),
                          items: companies
                              .map((c) => DropdownMenuItem(
                                  value: _intOrNull(c['id']),
                                  child: Text('${c['name']}')))
                              .toList(),
                          onChanged: (v) => setD(() => companyId = v)),
                      const SizedBox(height: 8),
                      TextField(
                          controller: plate,
                          textCapitalization: TextCapitalization.characters,
                          decoration: const InputDecoration(
                              labelText: 'Placa (quando houver)')),
                      const SizedBox(height: 8),
                      TextField(
                          controller: desc,
                          decoration: const InputDecoration(
                              labelText: 'Descrição / identificação *')),
                      const SizedBox(height: 8),
                      const Align(
                          alignment: Alignment.centerLeft,
                          child: Text(
                              'A mão de obra é da própria empresa. O cadastro identifica apenas o equipamento contratado e sua empresa proprietária.',
                              style: TextStyle(
                                  fontSize: 12, color: Colors.black54))),
                    ])),
                    actions: [
                      TextButton(
                          onPressed: () => Navigator.pop(ctx, false),
                          child: const Text('Cancelar')),
                      FilledButton(
                          onPressed: () => Navigator.pop(ctx, true),
                          child: const Text('Salvar'))
                    ])));
    if (ok == true) {
      if (companyId == null) {
        ScaffoldMessenger.of(context).showSnackBar(const SnackBar(
            content: Text(
                'Preenchimento obrigatório: Empresa proprietária / locadora')));
      } else if (plate.text.trim().isEmpty && desc.text.trim().isEmpty) {
        ScaffoldMessenger.of(context).showSnackBar(const SnackBar(
            content: Text(
                'Preenchimento obrigatório: Placa ou identificação do equipamento')));
      } else {
        try {
          await api.saveThirdParty(
              id: _intOrNull(item?['id']),
              plate: plate.text.trim(),
              company: companyNameFor(companyId),
              description: desc.text.trim(),
              driverName: null);
          await load();
          if (mounted)
            ScaffoldMessenger.of(context).showSnackBar(const SnackBar(
                content: Text('Equipamento de terceiros salvo com sucesso ✓')));
        } catch (e) {
          if (mounted)
            ScaffoldMessenger.of(context).showSnackBar(SnackBar(
                content:
                    Text('Erro ao salvar equipamento: ${_friendlyError(e)}')));
        }
      }
    }
    plate.dispose();
    desc.dispose();
  }

  Future<void> removeThirdParty(Map<String, dynamic> x) async {
    if (!widget.canEdit) return;
    final label = _hasValue(x['plate'])
        ? '${x['plate']}'
        : '${x['description'] ?? 'este equipamento'}';
    final ok = await showDialog<bool>(
        context: context,
        builder: (ctx) => AlertDialog(
              title: const Text('Excluir equipamento de terceiros?'),
              content: Text(
                  '$label será retirado dos cadastros ativos. Todos os abastecimentos, relatórios, fotos, assinaturas e auditorias anteriores permanecerão preservados.'),
              actions: [
                TextButton(
                    onPressed: () => Navigator.pop(ctx, false),
                    child: const Text('Cancelar')),
                FilledButton(
                    style: FilledButton.styleFrom(
                        backgroundColor: Colors.red.shade700),
                    onPressed: () => Navigator.pop(ctx, true),
                    child: const Text('Excluir'))
              ],
            ));
    if (ok != true) return;
    setState(() => loading = true);
    try {
      await api.archiveThirdParty(x);
      await load();
      if (mounted)
        ScaffoldMessenger.of(context).showSnackBar(const SnackBar(
            content: Text(
                'Equipamento retirado dos cadastros ativos. Histórico preservado ✓')));
    } catch (e) {
      if (mounted)
        ScaffoldMessenger.of(context)
            .showSnackBar(SnackBar(content: Text(_friendlyError(e))));
    } finally {
      if (mounted) setState(() => loading = false);
    }
  }

  @override
  Widget build(BuildContext context) => Scaffold(
      appBar: AppBar(title: const Text('Equipamentos de terceiros')),
      floatingActionButton: widget.canEdit
          ? FloatingActionButton(
              onPressed: loading ? null : () => edit(),
              child: const Icon(Icons.add))
          : null,
      body: items == null
          ? const Center(child: CircularProgressIndicator())
          : RefreshIndicator(
              onRefresh: load,
              child: ListView(padding: const EdgeInsets.all(12), children: [
                if (widget.canEdit && companies.isEmpty)
                  const Card(
                      child: ListTile(
                          leading: Icon(Icons.business_outlined, color: _blue),
                          title: Text(
                              'Nenhuma proprietária / locadora cadastrada'),
                          subtitle: Text(
                              'Cadastre em “Empresas” e marque o tipo de relação “Proprietária / Locadora de equipamento”.'))),
                ...items!.map((x) => Card(
                    child: ListTile(
                        title: Text(
                            _plateDescriptionLabel(
                                x['plate'], x['description']),
                            style:
                                const TextStyle(fontWeight: FontWeight.w900)),
                        subtitle: Text(
                            'Empresa / locadora: ${x['company_name'] ?? 'Não informada'}'),
                        onTap:
                            widget.canEdit && !loading ? () => edit(x) : null,
                        trailing: widget.canEdit
                            ? PopupMenuButton<String>(
                                enabled: !loading,
                                onSelected: (v) {
                                  if (v == 'edit') edit(x);
                                  if (v == 'delete') removeThirdParty(x);
                                },
                                itemBuilder: (_) => const [
                                      PopupMenuItem(
                                          value: 'edit', child: Text('Editar')),
                                      PopupMenuItem(
                                          value: 'delete',
                                          child: Text('Excluir',
                                              style:
                                                  TextStyle(color: Colors.red)))
                                    ])
                            : null))),
              ])));
}
