from pathlib import Path
p=Path('lib/main_online.dart')
s=p.read_text()

def rep(old,new,label):
    global s
    if old not in s:
        raise SystemExit(f'anchor missing: {label}')
    s=s.replace(old,new,1)

# API: resumo completo dos filtros, calculado no banco sem depender do limite visual da lista.
anchor="""    return _rows(data);\n  }\n\n  Future<Map<String, dynamic>> refineryEntry({"""
insert="""    return _rows(data);\n  }\n\n  Future<Map<String, dynamic>> adminSearchSummary({\n    DateTime? start,\n    DateTime? end,\n    int? workId,\n    String? asset,\n    String? plate,\n    String? operatorName,\n    String? type,\n  }) async {\n    final data = await client.rpc('rca_admin_search_summary_v27', params: {\n      'p_start': start?.toUtc().toIso8601String(),\n      'p_end': end?.toUtc().toIso8601String(),\n      'p_work_id': workId,\n      'p_asset_query': asset,\n      'p_plate': plate,\n      'p_operator': operatorName,\n      'p_type': type,\n    });\n    return _map(data);\n  }\n\n  Future<Map<String, dynamic>> refineryEntry({"""
rep(anchor,insert,'admin summary api')

# Estado do resumo.
rep("""  List<Map<String, dynamic>>? items;\n  bool busy = false;""","""  List<Map<String, dynamic>>? items;\n  Map<String, dynamic>? summary;\n  bool busy = false;""",'summary state')

# Pesquisa traz lista + totais coerentes com os mesmos filtros.
old_search="""      final x = await api.adminSearch(start: start, end: end, workId: workId, asset: asset.text.trim(), plate: plate.text.trim(), operatorName: operatorName.text.trim(), type: type).timeout(const Duration(seconds: 12));\n      if (mounted) setState(() { items = x; selectedCodes.clear(); suppressNextTap = false; errorMessage = null; if (collapse) filtersExpanded = false; });"""
new_search="""      final x = await api.adminSearch(start: start, end: end, workId: workId, asset: asset.text.trim(), plate: plate.text.trim(), operatorName: operatorName.text.trim(), type: type).timeout(const Duration(seconds: 12));\n      final sm = await api.adminSearchSummary(start: start, end: end, workId: workId, asset: asset.text.trim(), plate: plate.text.trim(), operatorName: operatorName.text.trim(), type: type).timeout(const Duration(seconds: 12));\n      if (mounted) setState(() { items = x; summary = sm; selectedCodes.clear(); suppressNextTap = false; errorMessage = null; if (collapse) filtersExpanded = false; });"""
rep(old_search,new_search,'search with summary')

# PDF individual diretamente na lista.
anchor2="""  Future<void> exportPdf() async {\n    final targets = selectedItems;"""
insert2="""  Future<void> exportOne(Map<String, dynamic> item) async {\n    setState(() => busy = true);\n    try {\n      final bytes = await FuelPdfReport.build([item]);\n      await Printing.sharePdf(bytes: bytes, filename: 'RC-Abastecimento-${item['code'] ?? DateTime.now().millisecondsSinceEpoch}.pdf');\n    } catch (e) {\n      if (mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Falha ao gerar PDF: ${_friendlyError(e)}')));\n    } finally { if (mounted) setState(() => busy = false); }\n  }\n\n  Future<void> exportPdf() async {\n    final targets = selectedItems;"""
rep(anchor2,insert2,'direct single pdf')

# Nome inequívoco da tela.
s=s.replace("'Registros de abastecimento'","'Registro Geral'",1)

# Botão PDF em cada registro quando não estiver em seleção múltipla.
old_trailing="""                trailing: selectionMode ? Checkbox(value: selected, onChanged: (_) => toggleSelected(x)) : const Icon(Icons.chevron_right_rounded),"""
new_trailing="""                trailing: selectionMode\n                    ? Checkbox(value: selected, onChanged: (_) => toggleSelected(x))\n                    : Row(mainAxisSize: MainAxisSize.min, children: [\n                        IconButton(onPressed: busy ? null : () => exportOne(x), tooltip: 'Exportar este registro em PDF', icon: const Icon(Icons.picture_as_pdf_outlined, color: _blue)),\n                        const Icon(Icons.chevron_right_rounded),\n                      ]),"""
rep(old_trailing,new_trailing,'pdf on every record')

# Resumo no final da página, respeitando exatamente o período/filtros pesquisados.
marker="""          ...list.map((x) {\n            final assetText = x['asset_number'] ?? x['third_party_plate'] ?? x['destination_tank'] ?? x['source_tank'] ?? '';"""
if marker not in s:
    raise SystemExit('anchor missing: list marker')

# Insere resumo imediatamente após o fechamento do map da lista.
old_end="""          }),\n        ],\n      ),\n    );\n  }\n}\n\nclass MovementDetailScreen"""
new_end="""          }),\n          if (items != null && summary != null) ...[\n            const SizedBox(height: 14),\n            Builder(builder: (context) {\n              final sm = summary!;\n              final oneDay = end.difference(start).inDays == 1;\n              final dateText = _fmtDate(start.toIso8601String()).split(' ').first;\n              final fuelingLiters = _num(sm['fueling_liters']);\n              final transferLiters = _num(sm['transfer_liters']);\n              final refineryLiters = _num(sm['refinery_liters']);\n              final saleTotal = sm['sale_total'];\n              final profitTotal = sm['profit_total'];\n              Widget metric(String label, String value, {bool highlight=false}) => Container(\n                padding: const EdgeInsets.all(12),\n                decoration: BoxDecoration(color: highlight ? const Color(0xFFEAF2FF) : Colors.white, borderRadius: BorderRadius.circular(12), border: Border.all(color: highlight ? _blue : Colors.black12)),\n                child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [\n                  Text(label, style: TextStyle(fontSize: 12, color: highlight ? _blue : Colors.black54, fontWeight: FontWeight.w700)),\n                  const SizedBox(height: 4),\n                  Text(value, style: TextStyle(fontSize: highlight ? 22 : 17, fontWeight: FontWeight.w900, color: highlight ? _blue : Colors.black87)),\n                ]),\n              );\n              return Card(child: Padding(\n                padding: const EdgeInsets.all(16),\n                child: Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [\n                  Text(oneDay ? 'Resumo do dia • $dateText' : 'Resumo do período pesquisado', style: const TextStyle(fontSize: 17, fontWeight: FontWeight.w900)),\n                  const SizedBox(height: 4),\n                  Text(oneDay ? 'Totais referentes somente aos filtros aplicados em $dateText.' : 'Totais referentes somente aos filtros atualmente aplicados.', style: const TextStyle(fontSize: 12, color: Colors.black54)),\n                  const SizedBox(height: 12),\n                  metric(oneDay ? 'Total abastecido no dia' : 'Total abastecido no período', _fmtLiters(fuelingLiters), highlight: true),\n                  const SizedBox(height: 10),\n                  Row(children: [\n                    Expanded(child: metric('Abastecimentos', '${sm['fueling_count'] ?? 0} registro(s)')),\n                    const SizedBox(width: 8),\n                    Expanded(child: metric('Total de registros', '${sm['record_count'] ?? 0}')),\n                  ]),\n                  const SizedBox(height: 8),\n                  Row(children: [\n                    Expanded(child: metric('Transferido internamente', _fmtLiters(transferLiters))),\n                    const SizedBox(width: 8),\n                    Expanded(child: metric('Recebido por NF', _fmtLiters(refineryLiters))),\n                  ]),\n                  if (saleTotal != null || profitTotal != null) ...[\n                    const SizedBox(height: 8),\n                    Row(children: [\n                      if (saleTotal != null) Expanded(child: metric('Valor abastecido/vendido', _fmtMoney(saleTotal))),\n                      if (saleTotal != null && profitTotal != null) const SizedBox(width: 8),\n                      if (profitTotal != null) Expanded(child: metric('Lucro no período', _fmtMoney(profitTotal))),\n                    ]),\n                  ],\n                  const SizedBox(height: 10),\n                  const Text('Importante: transferências internas e recebimentos de NF não entram no Total abastecido, evitando contar o mesmo combustível mais de uma vez.', style: TextStyle(fontSize: 11.5, color: Colors.black54)),\n                  const SizedBox(height: 10),\n                  const Text('PDF: cada registro pode ser exportado individualmente pelo ícone ao lado. Também continua disponível a seleção de vários registros para exportação conjunta no padrão oficial aprovado.', style: TextStyle(fontSize: 11.5, color: Colors.black54)),\n                ]),\n              ));\n            }),\n          ],\n        ],\n      ),\n    );\n  }\n}\n\nclass MovementDetailScreen"""
rep(old_end,new_end,'summary footer')

p.write_text(s)
print('v27 general records summary staged',len(s))
