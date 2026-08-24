from pathlib import Path

path = Path('lib/main_online.dart')
text = path.read_text()

def once(old: str, new: str, label: str) -> None:
    global text
    if old not in text:
        raise SystemExit(f'Patch v9 não aplicado: {label}')
    text = text.replace(old, new, 1)

once("  Future<List<Map<String, dynamic>>> listDrivers() async => _rows(await client.rpc('rca_list_drivers'));\n", """  Future<List<Map<String, dynamic>>> listDrivers() async => _rows(await client.rpc('rca_list_drivers'));

  Future<void> deleteDriverUser(String userId) async {
    await client.rpc('rca_delete_driver_user', params: {'p_user_id': userId});
  }
""", 'API excluir usuário')

once("  bool busy = false;\n  bool filtersExpanded = true;\n", """  bool busy = false;
  bool filtersExpanded = true;
  final Set<String> selectedCodes = <String>{};
  Timer? holdTimer;
  bool suppressNextTap = false;

  String itemKey(Map<String, dynamic> x) => '${x['code'] ?? x['id'] ?? ''}';
  bool get selectionMode => selectedCodes.isNotEmpty;

  List<Map<String, dynamic>> get selectedItems {
    final list = items ?? const <Map<String, dynamic>>[];
    return list.where((x) => selectedCodes.contains(itemKey(x))).toList();
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
    holdTimer = Timer(const Duration(seconds: 2), () {
      if (!mounted) return;
      suppressNextTap = true;
      toggleSelected(x);
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Modo de seleção ativado. Toque em outros registros para marcar ou desmarcar.')));
    });
  }

  void cancelHold() { holdTimer?.cancel(); holdTimer = null; }

  void clearSelection() {
    cancelHold();
    setState(() { selectedCodes.clear(); suppressNextTap = false; });
  }

  void openOrSelect(Map<String, dynamic> x) {
    if (suppressNextTap) { suppressNextTap = false; return; }
    if (selectionMode) { toggleSelected(x); return; }
    Navigator.push(context, MaterialPageRoute(builder: (_) => MovementDetailScreen(item: x)));
  }
""", 'estado de seleção dos registros')

once("  void dispose() { asset.dispose(); plate.dispose(); operatorName.dispose(); super.dispose(); }\n", "  void dispose() { holdTimer?.cancel(); asset.dispose(); plate.dispose(); operatorName.dispose(); super.dispose(); }\n", 'cancelar timer no dispose')
once("      if (mounted) setState(() { items = x; if (collapse) filtersExpanded = false; });\n", "      if (mounted) setState(() { items = x; selectedCodes.clear(); suppressNextTap = false; if (collapse) filtersExpanded = false; });\n", 'limpar seleção após pesquisa')

once("""  Future<void> exportPdf() async {
    if (items == null || items!.isEmpty) return;
    setState(() => busy = true);
    try {
      final bytes = await FuelPdfReport.build(items!);
      await Printing.sharePdf(bytes: bytes, filename: 'RC-Abastecimento-${DateTime.now().millisecondsSinceEpoch}.pdf');
    } catch (e) {
      if (mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Falha ao gerar PDF: ${_friendlyError(e)}')));
    } finally { if (mounted) setState(() => busy = false); }
  }
""", """  Future<void> exportPdf() async {
    final targets = selectedItems;
    if (targets.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Selecione um ou mais registros para exportar.')));
      return;
    }
    setState(() => busy = true);
    try {
      final bytes = await FuelPdfReport.build(targets);
      await Printing.sharePdf(bytes: bytes, filename: 'RC-Abastecimento-${DateTime.now().millisecondsSinceEpoch}.pdf');
    } catch (e) {
      if (mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Falha ao gerar PDF: ${_friendlyError(e)}')));
    } finally { if (mounted) setState(() => busy = false); }
  }
""", 'exportar somente selecionados')

once("""      appBar: AppBar(
        title: const Text('Registros de abastecimento'),
        actions: [IconButton(onPressed: items?.isNotEmpty == true && !busy ? exportPdf : null, tooltip: 'Exportar PDF', icon: const Icon(Icons.picture_as_pdf_outlined))],
      ),
""", """      appBar: AppBar(
        title: Text(selectionMode ? '${selectedCodes.length} selecionado(s)' : 'Registros de abastecimento'),
        actions: [
          if (selectionMode) IconButton(onPressed: !busy ? exportPdf : null, tooltip: 'Exportar selecionados em PDF', icon: const Icon(Icons.picture_as_pdf_outlined)),
          if (selectionMode) IconButton(onPressed: !busy ? clearSelection : null, tooltip: 'Cancelar seleção', icon: const Icon(Icons.close_rounded)),
        ],
      ),
""", 'barra de seleção')

once("""          const SizedBox(height: 8),
          if (items == null && !busy) const Padding(padding: EdgeInsets.all(30), child: Center(child: CircularProgressIndicator())),
""", """          const SizedBox(height: 8),
          if (items != null && list.isNotEmpty && !selectionMode)
            const Padding(
              padding: EdgeInsets.fromLTRB(6, 0, 6, 8),
              child: Text('Pressione um registro por 2 segundos para selecionar. Depois, toque nos demais registros que deseja exportar em PDF.', style: TextStyle(color: Colors.black54)),
            ),
          if (items == null && !busy) const Padding(padding: EdgeInsets.all(30), child: Center(child: CircularProgressIndicator())),
""", 'instrução de seleção')

once("""          ...list.map((x) {
            final assetText = x['asset_number'] ?? x['third_party_plate'] ?? x['destination_tank'] ?? x['source_tank'] ?? '';
            return Card(child: ListTile(
              contentPadding: const EdgeInsets.all(14),
              title: Text('${_movementLabelForItem(x)}${_hasValue(assetText) ? ' • $assetText' : ''}', style: const TextStyle(fontWeight: FontWeight.w900)),
              subtitle: Text('${_fmtDate(x['created_at'])}\\n${x['work'] ?? 'Sem obra'} • ${_fmtLiters(x['liters'])}\\n${x['operator'] ?? '-'}'),
              isThreeLine: true,
              trailing: const Icon(Icons.chevron_right_rounded),
              onTap: () => Navigator.push(context, MaterialPageRoute(builder: (_) => MovementDetailScreen(item: x))),
            ));
          }),
""", """          ...list.map((x) {
            final assetText = x['asset_number'] ?? x['third_party_plate'] ?? x['destination_tank'] ?? x['source_tank'] ?? '';
            final selected = selectedCodes.contains(itemKey(x));
            return GestureDetector(
              behavior: HitTestBehavior.opaque,
              onTapDown: (_) => beginHold(x),
              onTapUp: (_) => cancelHold(),
              onTapCancel: cancelHold,
              onTap: () => openOrSelect(x),
              child: Card(child: ListTile(
                contentPadding: const EdgeInsets.all(14),
                title: Text('${_movementLabelForItem(x)}${_hasValue(assetText) ? ' • $assetText' : ''}', style: const TextStyle(fontWeight: FontWeight.w900)),
                subtitle: Text('${_fmtDate(x['created_at'])}\\n${x['work'] ?? 'Sem obra'} • ${_fmtLiters(x['liters'])}\\n${x['operator'] ?? '-'}'),
                isThreeLine: true,
                trailing: selectionMode ? Checkbox(value: selected, onChanged: (_) => toggleSelected(x)) : const Icon(Icons.chevron_right_rounded),
              )),
            );
          }),
""", 'cartões selecionáveis por 2 segundos')

start = text.find("  Future<void> removeAccess(Map<String, dynamic> u) async {")
end = text.find("\n  @override\n  Widget build(BuildContext context) => Scaffold(", start)
if start < 0 or end < 0:
    raise SystemExit('Patch v9 não aplicado: função remover acesso')
text = text[:start] + """  Future<void> deleteUser(Map<String, dynamic> u) async {
    final name = '${u['name'] ?? u['username'] ?? 'usuário'}';
    final ok = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('Excluir usuário?'),
        content: Text('Deseja realmente excluir o usuário $name? O login será excluído, mas todos os registros de abastecimento e o histórico desse usuário serão preservados.'),
        actions: [
          TextButton(onPressed: () => Navigator.pop(ctx, false), child: const Text('Cancelar')),
          FilledButton.icon(onPressed: () => Navigator.pop(ctx, true), icon: const Icon(Icons.delete_outline_rounded), label: const Text('Excluir usuário')),
        ],
      ),
    );
    if (ok != true) return;
    final userId = '${u['user_id'] ?? ''}';
    if (userId.isEmpty) return;
    setState(() => busy = true);
    try {
      await api.deleteDriverUser(userId);
      await load();
      if (mounted) ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Usuário excluído. Os registros de abastecimento foram preservados.')));
    } catch (e) {
      if (mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(_friendlyError(e))));
    } finally {
      if (mounted) setState(() => busy = false);
    }
  }
""" + text[end:]

once("""                  if (!removed) ...[
                    const SizedBox(height: 10),
                    Wrap(spacing: 8, runSpacing: 8, children: [
                      OutlinedButton.icon(onPressed: busy ? null : () => editUser(u), icon: const Icon(Icons.edit_outlined), label: const Text('Editar')),
                      OutlinedButton.icon(onPressed: busy ? null : () => toggle(u), icon: Icon(u['active'] == true ? Icons.block_rounded : Icons.check_circle_outline_rounded), label: Text(u['active'] == true ? 'Desativar' : 'Ativar')),
                      TextButton.icon(onPressed: busy ? null : () => removeAccess(u), icon: const Icon(Icons.person_remove_alt_1_outlined), label: const Text('Remover acesso')),
                    ]),
                  ] else const Padding(padding: EdgeInsets.only(top: 8), child: Text('Cadastro e histórico preservados.')),
""", """                  const SizedBox(height: 10),
                  Wrap(spacing: 8, runSpacing: 8, children: [
                    if (!removed) OutlinedButton.icon(onPressed: busy ? null : () => editUser(u), icon: const Icon(Icons.edit_outlined), label: const Text('Editar')),
                    if (!removed) OutlinedButton.icon(onPressed: busy ? null : () => toggle(u), icon: Icon(u['active'] == true ? Icons.block_rounded : Icons.check_circle_outline_rounded), label: Text(u['active'] == true ? 'Desativar' : 'Ativar')),
                    TextButton.icon(onPressed: busy ? null : () => deleteUser(u), icon: const Icon(Icons.delete_outline_rounded), label: const Text('Excluir usuário')),
                  ]),
                  if (removed) const Padding(padding: EdgeInsets.only(top: 8), child: Text('O acesso já está removido. A exclusão do usuário mantém todos os registros anteriores.')),
""", 'botão excluir usuário')

path.write_text(text)
print('Patch v9 aplicado: exclusão real de usuário com histórico preservado e seleção de registros para PDF.')
