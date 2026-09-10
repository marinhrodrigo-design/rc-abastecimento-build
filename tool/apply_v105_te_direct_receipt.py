from pathlib import Path

p = Path('lib/main_online.dart')
t = p.read_text()

if "Text('v104'" not in t:
    raise SystemExit('Expected exact V104 source marker not found')
t = t.replace("Text('v104'", "Text('v105'", 1)

old = """class RefineryLoadV23Screen extends StatefulWidget {
  final Map<String, dynamic> ref;
  final int? initialCompanyTruckId;
  const RefineryLoadV23Screen(
      {super.key, required this.ref, this.initialCompanyTruckId});"""
new = """class RefineryLoadV23Screen extends StatefulWidget {
  final Map<String, dynamic> ref;
  final int? initialCompanyTruckId;
  final int? initialDestinationTankId;
  final String? initialArrivalMode;
  const RefineryLoadV23Screen(
      {super.key,
      required this.ref,
      this.initialCompanyTruckId,
      this.initialDestinationTankId,
      this.initialArrivalMode});"""
if old not in t:
    raise SystemExit('V104 receipt constructor anchor not found')
t = t.replace(old, new, 1)

old = """  void initState() {
    super.initState();
    if (widget.initialCompanyTruckId != null) {
      arrivalMode = 'company_truck';
      destinationTankId = widget.initialCompanyTruckId;
    }
    loadRefs();
  }"""
new = """  void initState() {
    super.initState();
    if (widget.initialArrivalMode != null) {
      arrivalMode = widget.initialArrivalMode;
    }
    if (widget.initialDestinationTankId != null) {
      destinationTankId = widget.initialDestinationTankId;
    }
    if (widget.initialCompanyTruckId != null) {
      arrivalMode ??= 'company_truck';
      destinationTankId ??= widget.initialCompanyTruckId;
    }
    loadRefs();
  }"""
if old not in t:
    raise SystemExit('V104 receipt initState anchor not found')
t = t.replace(old, new, 1)

old = """                  ] else if (stationary) ...[
                    HomeActionCard(
                        icon: Icons.local_gas_station_rounded,
                        title: 'Novo abastecimento',
                        subtitle:
                            'T.E. → Ativo próprio ou equipamento de terceiros',
                        onTap: () => open(FuelingV23Screen(
                            source: t, ref: ref!, profile: widget.profile))),
                  ],"""
new = """                  ] else if (stationary) ...[
                    HomeActionCard(
                        icon: Icons.receipt_long_rounded,
                        title: 'Entrada da refinaria / NF',
                        subtitle: 'Refinaria/fornecedor → T.E.',
                        onTap: () => open(RefineryLoadV23Screen(
                            ref: ref!,
                            initialDestinationTankId: _intOrNull(t['id']),
                            initialArrivalMode: 'supplier_truck'))),
                    const SizedBox(height: 12),
                    HomeActionCard(
                        icon: Icons.local_gas_station_rounded,
                        title: 'Novo abastecimento',
                        subtitle:
                            'T.E. → Ativo próprio ou equipamento de terceiros',
                        onTap: () => open(FuelingV23Screen(
                            source: t, ref: ref!, profile: widget.profile))),
                  ],"""
if old not in t:
    raise SystemExit('V104 stationary home anchor not found')
t = t.replace(old, new, 1)

t = t.replace(
    "labelText: 'Destino do combustível na empresa *',\n                        helperText:\n                            'Selecione onde a carga foi descarregada e incorporada ao estoque.'",
    "labelText: 'Destino do diesel *',\n                        helperText: 'T.E. ou caminhão-tanque da empresa'",
    1,
)

p.write_text(t)
print('V105 direct refinery-to-TE receipt patch applied')
