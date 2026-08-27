import 'dart:async';

import 'package:flutter/material.dart';
import 'package:supabase_flutter/supabase_flutter.dart';

import 'backend_service.dart';
import 'phase4_pages.dart';
import 'phase4_theme.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();

  if (IntelligenceApi.publishableKey.trim().isEmpty) {
    runApp(const _ConfigurationErrorApp());
    return;
  }

  await Supabase.initialize(
    url: IntelligenceApi.projectUrl,
    publishableKey: IntelligenceApi.publishableKey,
  );

  runApp(const RCIntelligenceApp());
}

class RCIntelligenceApp extends StatelessWidget {
  const RCIntelligenceApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      debugShowCheckedModeBanner: false,
      title: 'R&C Intelligence',
      theme: RCTheme.build(),
      home: AuthGate(api: IntelligenceApi(Supabase.instance.client)),
    );
  }
}

class AuthGate extends StatefulWidget {
  const AuthGate({super.key, required this.api});
  final IntelligenceApi api;

  @override
  State<AuthGate> createState() => _AuthGateState();
}

class _AuthGateState extends State<AuthGate> {
  StreamSubscription<AuthState>? subscription;

  @override
  void initState() {
    super.initState();
    subscription = widget.api.client.auth.onAuthStateChange.listen((_) {
      if (mounted) setState(() {});
    });
  }

  @override
  void dispose() {
    subscription?.cancel();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    if (!widget.api.hasSession) return LoginPage(api: widget.api);
    return IntelligenceShell(api: widget.api);
  }
}

class LoginPage extends StatefulWidget {
  const LoginPage({super.key, required this.api});
  final IntelligenceApi api;

  @override
  State<LoginPage> createState() => _LoginPageState();
}

class _LoginPageState extends State<LoginPage> {
  final username = TextEditingController();
  final password = TextEditingController();
  bool loading = false;
  bool obscure = true;
  String? error;

  @override
  void dispose() {
    username.dispose();
    password.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    if (loading) return;
    setState(() {
      loading = true;
      error = null;
    });
    try {
      await widget.api.signIn(
        usernameOrEmail: username.text,
        password: password.text,
      );
      await widget.api.profile();
    } catch (e) {
      await widget.api.signOut();
      if (mounted) {
        setState(() => error = _loginError(e));
      }
    } finally {
      if (mounted) setState(() => loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: SafeArea(
        child: Center(
          child: SingleChildScrollView(
            padding: const EdgeInsets.all(24),
            child: ConstrainedBox(
              constraints: const BoxConstraints(maxWidth: 430),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  Container(
                    width: 76,
                    height: 76,
                    decoration: BoxDecoration(
                      color: RCTheme.blue,
                      borderRadius: BorderRadius.circular(22),
                    ),
                    child: const Icon(Icons.psychology_alt_rounded, color: Colors.white, size: 42),
                  ),
                  const SizedBox(height: 20),
                  const Text(
                    'R&C Intelligence',
                    style: TextStyle(fontSize: 32, fontWeight: FontWeight.w900, color: RCTheme.navy),
                  ),
                  const SizedBox(height: 6),
                  const Text('Inteligência operacional do ecossistema R&C'),
                  const SizedBox(height: 28),
                  TextField(
                    controller: username,
                    autofillHints: const [AutofillHints.username],
                    textInputAction: TextInputAction.next,
                    decoration: const InputDecoration(
                      labelText: 'Usuário ou e-mail',
                      prefixIcon: Icon(Icons.person_outline),
                    ),
                  ),
                  const SizedBox(height: 12),
                  TextField(
                    controller: password,
                    obscureText: obscure,
                    autofillHints: const [AutofillHints.password],
                    onSubmitted: (_) => _submit(),
                    decoration: InputDecoration(
                      labelText: 'Senha',
                      prefixIcon: const Icon(Icons.lock_outline),
                      suffixIcon: IconButton(
                        onPressed: () => setState(() => obscure = !obscure),
                        icon: Icon(obscure ? Icons.visibility_outlined : Icons.visibility_off_outlined),
                      ),
                    ),
                  ),
                  if (error != null) ...[
                    const SizedBox(height: 12),
                    Container(
                      padding: const EdgeInsets.all(12),
                      decoration: BoxDecoration(
                        color: const Color(0xFFFFECEA),
                        borderRadius: BorderRadius.circular(12),
                      ),
                      child: Text(error!, style: const TextStyle(color: Color(0xFF8A1C13))),
                    ),
                  ],
                  const SizedBox(height: 18),
                  FilledButton.icon(
                    onPressed: loading ? null : _submit,
                    icon: loading
                        ? const SizedBox(width: 18, height: 18, child: CircularProgressIndicator(strokeWidth: 2))
                        : const Icon(Icons.login),
                    label: Text(loading ? 'Entrando...' : 'Entrar'),
                  ),
                  const SizedBox(height: 16),
                  const Text(
                    'A tela respeita a Central de Permissões. Quem não tiver acesso ao Intelligence não entra no painel.',
                    textAlign: TextAlign.center,
                    style: TextStyle(fontSize: 12),
                  ),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }
}

class IntelligenceShell extends StatefulWidget {
  const IntelligenceShell({super.key, required this.api});
  final IntelligenceApi api;

  @override
  State<IntelligenceShell> createState() => _IntelligenceShellState();
}

class _IntelligenceShellState extends State<IntelligenceShell> {
  int index = 0;
  Map<String, dynamic>? profile;
  Map<String, dynamic>? dashboard;
  Object? loadError;
  bool loading = true;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    if (mounted) {
      setState(() {
        loading = true;
        loadError = null;
      });
    }
    try {
      final values = await Future.wait([
        widget.api.profile(),
        widget.api.dashboard(),
      ]);
      if (!mounted) return;
      setState(() {
        profile = values[0];
        dashboard = values[1];
        loading = false;
      });
    } catch (e) {
      if (!mounted) return;
      setState(() {
        loadError = e;
        loading = false;
      });
    }
  }

  Future<void> _openInsight(String id) async {
    await Navigator.of(context).push(
      MaterialPageRoute(builder: (_) => InsightDetailPage(api: widget.api, insightId: id)),
    );
    await _load();
  }

  @override
  Widget build(BuildContext context) {
    if (loading && dashboard == null) {
      return const Scaffold(body: Center(child: CircularProgressIndicator()));
    }
    if (loadError != null && dashboard == null) {
      return _AccessErrorPage(
        error: loadError,
        retry: _load,
        signOut: widget.api.signOut,
      );
    }

    final d = dashboard ?? const <String, dynamic>{};
    final p = profile ?? const <String, dynamic>{};
    final pages = <Widget>[
      DashboardPage(dashboard: d, onRefresh: _load, onOpenInsight: _openInsight),
      AlertsPage(api: widget.api, onChanged: _load),
      AssetsPage(api: widget.api, onChanged: _load),
      DataHealthPage(dashboard: d, profile: p, onRefresh: _load),
      OemPage(api: widget.api),
    ];

    return Scaffold(
      appBar: AppBar(
        titleSpacing: 16,
        title: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text('R&C Intelligence', style: TextStyle(fontWeight: FontWeight.w900)),
            Text(
              '${p['display_name'] ?? p['username'] ?? ''} • ${RCTheme.roleLabel('${p['role'] ?? ''}')}',
              style: const TextStyle(fontSize: 11, fontWeight: FontWeight.w500),
            ),
          ],
        ),
        actions: [
          IconButton(
            tooltip: 'Atualizar',
            onPressed: loading ? null : _load,
            icon: const Icon(Icons.refresh),
          ),
          PopupMenuButton<String>(
            onSelected: (v) {
              if (v == 'logout') widget.api.signOut();
            },
            itemBuilder: (_) => const [
              PopupMenuItem(value: 'logout', child: ListTile(leading: Icon(Icons.logout), title: Text('Sair'))),
            ],
          ),
        ],
      ),
      body: IndexedStack(index: index, children: pages),
      bottomNavigationBar: NavigationBar(
        selectedIndex: index,
        onDestinationSelected: (value) => setState(() => index = value),
        destinations: const [
          NavigationDestination(icon: Icon(Icons.dashboard_outlined), selectedIcon: Icon(Icons.dashboard), label: 'Visão'),
          NavigationDestination(icon: Icon(Icons.notifications_none), selectedIcon: Icon(Icons.notifications_active), label: 'Alertas'),
          NavigationDestination(icon: Icon(Icons.precision_manufacturing_outlined), selectedIcon: Icon(Icons.precision_manufacturing), label: 'Ativos'),
          NavigationDestination(icon: Icon(Icons.storage_outlined), selectedIcon: Icon(Icons.storage), label: 'Dados'),
          NavigationDestination(icon: Icon(Icons.menu_book_outlined), selectedIcon: Icon(Icons.menu_book), label: 'OEM'),
        ],
      ),
    );
  }
}

class _AccessErrorPage extends StatelessWidget {
  const _AccessErrorPage({required this.error, required this.retry, required this.signOut});
  final Object? error;
  final Future<void> Function() retry;
  final Future<void> Function() signOut;

  @override
  Widget build(BuildContext context) {
    final text = '$error';
    final denied = text.contains('Sem permissão') || text.contains('sem acesso');
    return Scaffold(
      appBar: AppBar(title: const Text('R&C Intelligence')),
      body: Center(
        child: Padding(
          padding: const EdgeInsets.all(28),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              Icon(denied ? Icons.lock_outline : Icons.cloud_off_outlined, size: 56, color: RCTheme.blue),
              const SizedBox(height: 14),
              Text(
                denied ? 'Acesso não liberado' : 'Não foi possível carregar o Intelligence',
                textAlign: TextAlign.center,
                style: const TextStyle(fontSize: 21, fontWeight: FontWeight.w800),
              ),
              const SizedBox(height: 8),
              Text(
                denied
                    ? 'Seu usuário está autenticado, mas a permissão intelligence.view não está liberada para este perfil.'
                    : text,
                textAlign: TextAlign.center,
              ),
              const SizedBox(height: 18),
              Wrap(
                spacing: 8,
                children: [
                  if (!denied) OutlinedButton.icon(onPressed: retry, icon: const Icon(Icons.refresh), label: const Text('Tentar novamente')),
                  FilledButton.icon(onPressed: signOut, icon: const Icon(Icons.logout), label: const Text('Sair')),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _ConfigurationErrorApp extends StatelessWidget {
  const _ConfigurationErrorApp();
  @override
  Widget build(BuildContext context) => MaterialApp(
        debugShowCheckedModeBanner: false,
        theme: RCTheme.build(),
        home: const Scaffold(
          body: Center(
            child: Padding(
              padding: EdgeInsets.all(28),
              child: Text(
                'R&C Intelligence não foi configurado para acessar o Supabase. O build deve fornecer SUPABASE_KEY via --dart-define.',
                textAlign: TextAlign.center,
              ),
            ),
          ),
        ),
      );
}

String _loginError(Object e) {
  final text = '$e';
  final lower = text.toLowerCase();
  if (lower.contains('invalid login credentials')) return 'Usuário ou senha inválidos.';
  if (text.contains('Sem permissão') || lower.contains('sem acesso')) {
    return 'Login válido, mas este usuário não possui acesso ao R&C Intelligence.';
  }
  if (lower.contains('network') || lower.contains('socket')) {
    return 'Sem conexão com o servidor. Confira a internet e tente novamente.';
  }
  return text.replaceFirst('AuthException(message: ', '').replaceFirst('Exception: ', '');
}
