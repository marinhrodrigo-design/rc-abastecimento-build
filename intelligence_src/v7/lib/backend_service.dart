import 'package:supabase_flutter/supabase_flutter.dart';

class IntelligenceApi {
  IntelligenceApi(this.client);

  final SupabaseClient client;

  static const projectUrl = String.fromEnvironment(
    'SUPABASE_URL',
    defaultValue: 'https://zitwhbfplafvarivgzdr.supabase.co',
  );

  static const publishableKey = String.fromEnvironment('SUPABASE_KEY');

  bool get hasSession => client.auth.currentSession != null;

  static List<String> loginCandidates(String usernameOrEmail) {
    final raw = usernameOrEmail.trim().toLowerCase();
    if (raw.isEmpty) return const [];
    if (raw.contains('@')) return [raw];

    final candidates = <String>[];

    // O alias "admin" deve funcionar nos dois módulos administrativos
    // históricos do ecossistema. No Combustível, o usuário técnico real é
    // "adminfuel", portanto não pode ser derivado apenas como admin@... .
    if (raw == 'admin') {
      candidates.add('admin@rcmanutencao.app');
      candidates.add('adminfuel@rccombustivel.app');
    }

    candidates.add('$raw@rcmanutencao.app');
    candidates.add('$raw@rccombustivel.app');

    return candidates.toSet().toList(growable: false);
  }

  Future<void> signIn({
    required String usernameOrEmail,
    required String password,
  }) async {
    final raw = usernameOrEmail.trim();
    if (raw.isEmpty || password.isEmpty) {
      throw const AuthException('Informe usuário e senha.');
    }

    final candidates = loginCandidates(raw);

    AuthException? lastAuthError;
    for (final email in candidates) {
      try {
        await client.auth.signInWithPassword(email: email, password: password);
        return;
      } on AuthException catch (e) {
        lastAuthError = e;
      }
    }

    throw lastAuthError ?? const AuthException('Usuário ou senha inválidos.');
  }

  Future<void> signOut() => client.auth.signOut();

  Future<Map<String, dynamic>> profile() async {
    return _map(await client.rpc('rca_profile'));
  }

  Future<Map<String, dynamic>> dashboard() async {
    return _map(await client.rpc('rc_intelligence_dashboard'));
  }

  Future<List<Map<String, dynamic>>> feed({
    int limit = 100,
    String? status,
    int? machineId,
    String? severity,
    String? ruleCode,
    String? query,
  }) async {
    final result = await client.rpc(
      'rc_intelligence_feed_v2',
      params: {
        'p_limit': limit,
        'p_status': status,
        'p_machine_id': machineId,
        'p_severity': severity,
        'p_rule_code': ruleCode,
        'p_query': query,
      },
    );
    return _list(result);
  }

  Future<Map<String, dynamic>> detail(String insightId) async {
    return _map(
      await client.rpc(
        'rc_intelligence_detail',
        params: {'p_insight_id': insightId},
      ),
    );
  }

  Future<List<Map<String, dynamic>>> assets({
    String? query,
    int limit = 250,
  }) async {
    final result = await client.rpc(
      'rc_intelligence_assets',
      params: {'p_query': query, 'p_limit': limit},
    );
    return _list(result);
  }

  Future<void> startReview(String insightId, {String? notes}) async {
    await client.rpc(
      'rc_intelligence_start_review',
      params: {'p_insight_id': insightId, 'p_notes': notes},
    );
  }

  Future<void> addNote(String insightId, String notes) async {
    await client.rpc(
      'rc_intelligence_add_note',
      params: {'p_insight_id': insightId, 'p_notes': notes},
    );
  }

  Future<void> setStatus(
    String insightId,
    String status, {
    String? notes,
  }) async {
    await client.rpc(
      'rc_intelligence_set_status',
      params: {
        'p_insight_id': insightId,
        'p_status': status,
        'p_notes': notes,
      },
    );
  }

  static Map<String, dynamic> _map(dynamic value) {
    if (value is Map<String, dynamic>) return value;
    if (value is Map) return Map<String, dynamic>.from(value);
    throw StateError('Resposta inválida do R&C Intelligence.');
  }

  static List<Map<String, dynamic>> _list(dynamic value) {
    if (value is! List) return const [];
    return value
        .whereType<Map>()
        .map((e) => Map<String, dynamic>.from(e))
        .toList(growable: false);
  }
}
