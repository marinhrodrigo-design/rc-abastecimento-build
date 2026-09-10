from pathlib import Path

p = Path('lib/main_online.dart')
t = p.read_text()

if "Text('v105'" not in t:
    raise SystemExit('Expected exact V105 source marker not found')
t = t.replace("Text('v105'", "Text('v106'", 1)

anchor = """  Future<void> _transfer() async {
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

"""
if anchor not in t:
    raise SystemExit('Admin transfer anchor not found in V105')
insert = anchor + """  Future<void> _truckToTeV106() async {
    if (!_requireOnlineV69() || ref == null) return;
    final t = await _operationUnit(
        const {'truck'},
        'Transferir para T.E.',
        'Selecione o caminhão-tanque de origem.');
    if (!mounted || t == null || ref == null) return;
    await Navigator.push(
        context,
        MaterialPageRoute(
            builder: (_) => RefineryToTeV23Screen(truck: t, ref: ref!)));
    if (mounted) refresh();
  }

"""
t = t.replace(anchor, insert, 1)

actions_anchor = """      quick(Icons.swap_horiz_rounded, 'Transferir', 'Registrar transferência',
          _transfer),
      quick(Icons.receipt_long_rounded, 'Recebimento (NF)', 'Registrar entrada',
          _receipt),
"""
if actions_anchor not in t:
    raise SystemExit('Admin actions anchor not found in V105')
actions_replacement = """      quick(Icons.swap_horiz_rounded, 'Transferir', 'Registrar transferência',
          _transfer),
      quick(Icons.oil_barrel_outlined, 'Transferir para T.E.', 'CT → T.E.',
          _truckToTeV106),
      quick(Icons.receipt_long_rounded, 'Recebimento (NF)', 'Registrar entrada',
          _receipt),
"""
t = t.replace(actions_anchor, actions_replacement, 1)

# Keep the field CT screen wording aligned with the admin dashboard.
t = t.replace("title: 'Descarregar no T.E.',", "title: 'Transferir para T.E.',", 1)
t = t.replace("subtitle: 'Caminhão-tanque → Tanque estacionário',", "subtitle: 'CT → T.E.',", 1)

p.write_text(t)
print('V106 CT to TE admin patch applied')
