from pathlib import Path

main_path = Path('lib/main_online.dart')
v29_path = Path('lib/v29_features.dart')
main = main_path.read_text()
v29 = v29_path.read_text()

def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f'{label}: expected 1 anchor, found {count}')
    return text.replace(old, new, 1)

main = replace_once(main,
"""  Future<void> deleteDriverUser(String userId) async {
    await client.rpc('rca_delete_driver_user', params: {'p_user_id': userId});
  }
""",
"""  Future<void> deleteFuelUser(String userId) async {
    await client.rpc('rca_delete_fuel_user_v1', params: {'p_user_id': userId});
  }
""", 'unified delete API')

main = replace_once(main, "await api.deleteDriverUser(userId);", "await api.deleteFuelUser(userId);", 'operational delete call')

main = replace_once(main,
"""  Future<void> removeUser(Map<String, dynamic> u) async {
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
""",
"""  Future<void> removeUser(Map<String, dynamic> u) async {
    final ok = await showDialog<bool>(
        context: context,
        builder: (ctx) => AlertDialog(
                title: Text('Excluir ${u['name']}?'),
                content: const Text(
                    'O login será excluído definitivamente. Registros históricos, movimentações, correções e assinaturas serão preservados, e o mesmo usuário poderá ser cadastrado novamente.'),
                actions: [
                  TextButton(
                      onPressed: () => Navigator.pop(ctx, false),
                      child: const Text('Cancelar')),
                  FilledButton(
                      onPressed: () => Navigator.pop(ctx, true),
                      child: const Text('Excluir usuário'))
                ]));
    if (ok != true) return;
    setState(() => busy = true);
    try {
      await api.deleteFuelUser('${u['user_id']}');
      await load();
      if (mounted)
        ScaffoldMessenger.of(context).showSnackBar(const SnackBar(
            content: Text('Usuário excluído. Histórico preservado e login liberado para novo cadastro ✓')));
    } catch (e) {
      if (mounted)
        ScaffoldMessenger.of(context)
            .showSnackBar(SnackBar(content: Text(_friendlyError(e))));
    } finally {
      if (mounted) setState(() => busy = false);
    }
  }
""", 'supervisor/manager delete flow')

v29 = replace_once(v29,
"""    try {
      if ('${u['role']}' == 'operator') {
        await api.userActionMap({
          'action': 'remove_access',
          'user_id': u['user_id'],
          'reason': 'Exclusão pelo Admin'
        });
      } else {
        await api.userActionMap(
            {'action': 'delete_manager', 'user_id': u['user_id']});
      }
      await load();
      if (mounted)
        ScaffoldMessenger.of(context).showSnackBar(const SnackBar(
            content: Text('Acesso removido. Histórico preservado ✓')));
""",
"""    try {
      await api.deleteFuelUser('${u['user_id']}');
      await load();
      if (mounted)
        ScaffoldMessenger.of(context).showSnackBar(const SnackBar(
            content: Text('Usuário excluído. Histórico preservado e login liberado para novo cadastro ✓')));
""", 'unified users-screen delete flow')

v29 = replace_once(v29,
"""                content: Text(
                    '${u['name']} perderá o acesso, mas todos os registros, movimentações, correções e assinaturas permanecerão preservados.'),
""",
"""                content: Text(
                    '${u['name']} terá o login excluído definitivamente. Todos os registros, movimentações, correções e assinaturas permanecerão preservados, e o mesmo usuário poderá ser cadastrado novamente.'),
""", 'delete confirmation text')

main_path.write_text(main)
v29_path.write_text(v29)
print('V94_USER_RECREATE_FIX_PASS')
