from pathlib import Path
p=Path('lib/main_online.dart')
s=p.read_text()

# Version label
s=s.replace("Text('v93',", "Text('v94',", 1)

# Add unified receipt API
marker="""  Future<Map<String, dynamic>> refineryToTeV22(
"""
api=r'''  Future<Map<String, dynamic>> registerFuelInvoiceV94({
    required String arrivalMode,
    required int destinationTankId,
    required double liters,
    required String supplier,
    required String invoice,
    required double unitCost,
    required String fuelType,
    required String platePhoto,
    required String invoiceDocument,
    String? externalTruckPlate,
    String? batch,
    String? notes,
  }) async =>
      _map(await client.rpc('rca_register_fuel_invoice_v94', params: {
        'p_arrival_mode': arrivalMode,
        'p_destination_tank_id': destinationTankId,
        'p_liters': liters,
        'p_supplier_name': supplier,
        'p_invoice_number': invoice,
        'p_batch_number': batch,
        'p_unit_cost': unitCost,
        'p_fuel_type': fuelType,
        'p_external_truck_plate': externalTruckPlate,
        'p_plate_photo_path': platePhoto,
        'p_invoice_document_path': invoiceDocument,
        'p_notes': notes,
      }));

'''
if marker not in s: raise SystemExit('API marker missing')
s=s.replace(marker, api+marker, 1)

# Replace receipt screen class completely
start=s.index('class RefineryLoadV23Screen extends StatefulWidget {')
end=s.index('class RefineryToTeV23Screen extends StatefulWidget {')
new_class=r'''class RefineryLoadV23Screen extends StatefulWidget {
  final Map<String, dynamic> ref;
  final int? initialCompanyTruckId;
  const RefineryLoadV23Screen(
      {super.key, required this.ref, this.initialCompanyTruckId});
  @override
  State<RefineryLoadV23Screen> createState() => _RefineryLoadV23ScreenState();
}

class _RefineryLoadV23ScreenState extends State<RefineryLoadV23Screen> {
  final supplier = TextEditingController(),
      nf = TextEditingController(),
      liters = TextEditingController(),
      cost = TextEditingController(),
      batch = TextEditingController(),
      externalTruckPlate = TextEditingController(),
      notes = TextEditingController();
  String fuel = 'Diesel';
  String? arrivalMode;
  int? destinationTankId;
  XFile? truckPlatePhoto, invoicePhoto;
  Map<String, dynamic> buyerCompany = {};
  bool busy = false, loadingRefs = true;
  String step = 'Salvar recebimento';

  @override
  void initState() {
    super.initState();
    if (widget.initialCompanyTruckId != null) {
      arrivalMode = 'company_truck';
      destinationTankId = widget.initialCompanyTruckId;
    }
    loadRefs();
  }

  List<Map<String, dynamic>> get companyTrucks => _rows(widget.ref['tanks'])
      .where((x) => '${x['tank_type']}' == 'truck')
      .toList();

  List<Map<String, dynamic>> get internalDestinations => _rows(widget.ref['tanks'])
      .where((x) => '${x['tank_type']}' == 'truck' || '${x['tank_type']}' == 'stationary')
      .toList();

  Map<String, dynamic>? selectedDestination() {
    for (final x in internalDestinations) {
      if (_intOrNull(x['id']) == destinationTankId) return x;
    }
    return null;
  }

  Future<void> loadRefs() async {
    try {
      final r = await api.reportCompany();
      if (mounted) {
        setState(() {
          buyerCompany = _map(r);
          loadingRefs = false;
        });
      }
    } catch (e) {
      if (mounted) {
        setState(() => loadingRefs = false);
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(
            content: Text(
                'Erro ao carregar empresa compradora: ${_friendlyError(e)}')));
      }
    }
  }

  String supplierName() => supplier.text.trim();

  Future<XFile?> camera() => ImagePicker()
      .pickImage(source: ImageSource.camera, imageQuality: 78, maxWidth: 1800);
  void message(String value) => ScaffoldMessenger.of(context)
      .showSnackBar(SnackBar(content: Text(value)));

  void changeArrivalMode(String? value) {
    setState(() {
      arrivalMode = value;
      if (value == 'company_truck') {
        destinationTankId = widget.initialCompanyTruckId;
        externalTruckPlate.clear();
      } else {
        destinationTankId = null;
      }
      truckPlatePhoto = null;
    });
  }

  Future<void> submit() async {
    if (busy) return;
    final volume = double.tryParse(liters.text.trim().replaceAll(',', '.'));
    final unitCost = double.tryParse(cost.text.trim().replaceAll(',', '.'));
    final supplierValue = supplierName();
    final mode = arrivalMode;
    final dest = selectedDestination();
    final externalPlate = externalTruckPlate.text.trim().toUpperCase();

    if (mode == null) {
      message('Informe como o combustível chegou à empresa');
      return;
    }
    if (destinationTankId == null || dest == null) {
      message(mode == 'company_truck'
          ? 'Selecione o caminhão-tanque da empresa'
          : 'Selecione onde o combustível entrou no estoque da empresa');
      return;
    }
    if (mode == 'company_truck' && '${dest['tank_type']}' != 'truck') {
      message('Selecione um caminhão-tanque cadastrado da empresa');
      return;
    }
    if (mode == 'supplier_truck' && externalPlate.isEmpty) {
      message('Informe a placa/identificação do caminhão da refinaria');
      return;
    }
    if (nf.text.trim().isEmpty) {
      message('Preenchimento obrigatório: Número da Nota Fiscal');
      return;
    }
    if (supplierValue.isEmpty) {
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
      message(mode == 'company_truck'
          ? 'Foto da placa/identificação do caminhão-tanque da empresa obrigatória'
          : 'Foto da placa/identificação do caminhão da refinaria obrigatória');
      return;
    }
    if (invoicePhoto == null) {
      message('Foto legível da Nota Fiscal obrigatória');
      return;
    }

    final arrivalLabel = mode == 'company_truck'
        ? 'Caminhão-tanque da empresa'
        : 'Caminhão da refinaria/fornecedor';
    final vehicleLabel = mode == 'company_truck'
        ? '${dest['code']} • ${dest['name']}'
        : externalPlate;
    final ok = await showDialog<bool>(
        context: context,
        builder: (ctx) => AlertDialog(
              title: const Text('Confirmar recebimento de combustível?'),
              content: SingleChildScrollView(
                  child: Column(
                      mainAxisSize: MainAxisSize.min,
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                    Text(
                        'Empresa compradora: ${buyerCompany['company_name'] ?? '-'}',
                        style: const TextStyle(fontWeight: FontWeight.w700)),
                    Text('Fornecedor do combustível: $supplierValue'),
                    const SizedBox(height: 8),
                    Text('Forma de chegada: $arrivalLabel'),
                    Text('Veículo de chegada: $vehicleLabel'),
                    Text(
                        'Entrada inicial no estoque: ${dest['code']} • ${dest['name']}'),
                    const SizedBox(height: 8),
                    Text('Nota Fiscal: ${nf.text.trim()}'),
                    Text('Combustível: $fuel'),
                    Text('Volume recebido: ${_fmtLiters(volume)}'),
                    Text('Preço de compra/L: ${_fmtMoney(unitCost)}'),
                    const SizedBox(height: 8),
                    const Text(
                        'A data e a hora da chegada serão registradas automaticamente pelo app.'),
                  ])),
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
      step = 'Enviando evidências obrigatórias...';
    });
    try {
      Future<String> up(XFile f, String kind) async =>
          api.uploadBytes(await f.readAsBytes(), kind,
              mime: f.mimeType ?? 'image/jpeg');
      final photos = await Future.wait<String>([
        up(truckPlatePhoto!, mode == 'company_truck'
            ? 'placa_caminhao_tanque_empresa'
            : 'placa_caminhao_refinaria'),
        up(invoicePhoto!, 'nota_fiscal_legivel')
      ]);
      if (!mounted) return;
      setState(() => step = 'Registrando NF, chegada e estoque...');
      final r = await api.registerFuelInvoiceV94(
          arrivalMode: mode,
          destinationTankId: destinationTankId!,
          liters: volume,
          supplier: supplierValue,
          invoice: nf.text.trim(),
          unitCost: unitCost,
          fuelType: fuel,
          externalTruckPlate: mode == 'supplier_truck' ? externalPlate : null,
          platePhoto: photos[0],
          invoiceDocument: photos[1],
          batch: batch.text.trim(),
          notes: notes.text.trim());
      if (!mounted) return;
      message(
          'NF ${r['invoice_number']} registrada ✓ • ${_fmtLiters(r['liters'])} • ${r['arrival_vehicle_label'] ?? arrivalLabel}');
      Navigator.pop(context, true);
    } catch (e) {
      if (mounted) {
        message('Erro ao registrar recebimento: ${_friendlyError(e)}');
      }
    } finally {
      if (mounted) {
        setState(() {
          busy = false;
          step = 'Salvar recebimento';
        });
      }
    }
  }

  @override
  void dispose() {
    for (final c in [
      supplier,
      nf,
      liters,
      cost,
      batch,
      externalTruckPlate,
      notes
    ]) {
      c.dispose();
    }
    super.dispose();
  }

  @override
  Widget build(BuildContext c) {
    final ownTruck = arrivalMode == 'company_truck';
    final supplierTruck = arrivalMode == 'supplier_truck';
    return Scaffold(
      appBar: AppBar(title: const Text('Recebimento de combustível / NF')),
      body: loadingRefs
          ? const Center(child: CircularProgressIndicator())
          : ListView(padding: const EdgeInsets.all(18), children: [
              Card(
                  child: ListTile(
                      leading: const Icon(Icons.business_rounded, color: _blue),
                      title: const Text('Empresa compradora'),
                      subtitle: Text(
                          '${buyerCompany['company_name'] ?? '-'}\nSua empresa operadora recebe o combustível e o incorpora ao estoque.'))),
              const SizedBox(height: 12),
              Text('Como o combustível chegou à empresa?',
                  style: Theme.of(c)
                      .textTheme
                      .titleMedium
                      ?.copyWith(fontWeight: FontWeight.w900)),
              const SizedBox(height: 8),
              DropdownButtonFormField<String>(
                  initialValue: arrivalMode,
                  isExpanded: true,
                  decoration:
                      const InputDecoration(labelText: 'Forma de chegada *'),
                  items: const [
                    DropdownMenuItem(
                        value: 'company_truck',
                        child: Text('Caminhão-tanque da empresa')),
                    DropdownMenuItem(
                        value: 'supplier_truck',
                        child: Text('Caminhão da refinaria / fornecedor')),
                  ],
                  onChanged: busy ? null : changeArrivalMode),
              const SizedBox(height: 8),
              if (ownTruck) ...[
                DropdownButtonFormField<int>(
                    initialValue: destinationTankId,
                    isExpanded: true,
                    decoration: const InputDecoration(
                        labelText: 'Caminhão-tanque da empresa *',
                        helperText:
                            'O combustível entra primeiro no estoque deste caminhão-tanque.'),
                    items: companyTrucks
                        .map((x) => DropdownMenuItem<int>(
                            value: _intOrNull(x['id']),
                            child: Text('${x['code']} • ${x['name']}')))
                        .toList(),
                    onChanged: busy
                        ? null
                        : (v) => setState(() => destinationTankId = v)),
                const SizedBox(height: 8),
              ],
              if (supplierTruck) ...[
                TextField(
                    controller: externalTruckPlate,
                    enabled: !busy,
                    textCapitalization: TextCapitalization.characters,
                    decoration: const InputDecoration(
                        labelText:
                            'Placa/identificação do caminhão da refinaria *',
                        hintText: 'Ex.: ABC1D23')),
                const SizedBox(height: 8),
                DropdownButtonFormField<int>(
                    initialValue: destinationTankId,
                    isExpanded: true,
                    decoration: const InputDecoration(
                        labelText: 'Destino do combustível na empresa *',
                        helperText:
                            'Selecione onde a carga foi descarregada e incorporada ao estoque.'),
                    items: internalDestinations
                        .map((x) => DropdownMenuItem<int>(
                            value: _intOrNull(x['id']),
                            child: Text('${x['code']} • ${x['name']}')))
                        .toList(),
                    onChanged: busy
                        ? null
                        : (v) => setState(() => destinationTankId = v)),
                const SizedBox(height: 8),
              ],
              const Divider(height: 28),
              Text('Dados da Nota Fiscal',
                  style: Theme.of(c)
                      .textTheme
                      .titleMedium
                      ?.copyWith(fontWeight: FontWeight.w900)),
              const SizedBox(height: 5),
              const Text(
                  'A empresa fornecedora do combustível é um dado da própria Nota Fiscal e é informada neste registro.'),
              const SizedBox(height: 12),
              TextField(
                  controller: supplier,
                  enabled: !busy,
                  textCapitalization: TextCapitalization.words,
                  decoration: const InputDecoration(
                      labelText: 'Empresa fornecedora do combustível *',
                      hintText: 'Digite a empresa que consta na Nota Fiscal')),
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
                  decoration: const InputDecoration(labelText: 'Combustível *'),
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
                  decoration: const InputDecoration(labelText: 'Observações')),
              const SizedBox(height: 12),
              OutlinedButton.icon(
                  onPressed: busy || arrivalMode == null
                      ? null
                      : () async {
                          final x = await camera();
                          if (x != null) setState(() => truckPlatePhoto = x);
                        },
                  icon: const Icon(Icons.local_shipping_outlined),
                  label: Text(truckPlatePhoto != null
                      ? 'Foto da placa/identificação do veículo ✓'
                      : ownTruck
                          ? 'Foto da placa/identificação do caminhão-tanque da empresa *'
                          : supplierTruck
                              ? 'Foto da placa/identificação do caminhão da refinaria *'
                              : 'Selecione primeiro a forma de chegada')),
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
                  onPressed: busy ? null : submit,
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
}

'''
s=s[:start]+new_class+s[end:]

# Unit dashboard: open receipt flow with selected own truck only as an initial value, not fixed header.
old="onTap: () => open(RefineryLoadV23Screen(truck: t)))"
new="onTap: () => open(RefineryLoadV23Screen(ref: ref!, initialCompanyTruckId: _intOrNull(t['id']))))"
if old not in s: raise SystemExit('unit dashboard receipt usage missing')
s=s.replace(old,new,1)

# Admin/home receipt: no forced CT selection.
old_func=r'''  Future<void> _receipt() async {
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
'''
new_func=r'''  Future<void> _receipt() async {
    if (!_requireOnlineV69() || ref == null) return;
    await Navigator.push(
        context,
        MaterialPageRoute(
            builder: (_) => RefineryLoadV23Screen(ref: ref!)));
    if (mounted) refresh();
  }
'''
if old_func not in s: raise SystemExit('home receipt function missing')
s=s.replace(old_func,new_func,1)

# Add arrival information to NF traceability card.
trace_anchor=r'''              ListTile(
                  title: const Text('Fornecedor do combustível'),
                  subtitle: Padding(
                      padding: const EdgeInsets.only(top: 4),
                      child: Text('${lot['supplier_name'] ?? '-'}',
                          style:
                              const TextStyle(fontWeight: FontWeight.w700)))),
'''
trace_extra=trace_anchor+r'''              if (_hasValue(lot['arrival_mode']))
                ListTile(
                    title: const Text('Forma de chegada'),
                    subtitle: Text(lot['arrival_mode'] == 'supplier_truck'
                        ? 'Caminhão da refinaria / fornecedor'
                        : 'Caminhão-tanque da empresa')),
              if (_hasValue(lot['arrival_vehicle_label']))
                ListTile(
                    title: const Text('Veículo de chegada'),
                    subtitle: Text('${lot['arrival_vehicle_label']}')),
              if (_hasValue(lot['initial_destination_code']))
                ListTile(
                    title: const Text('Entrada inicial no estoque'),
                    subtitle: Text(
                        '${lot['initial_destination_code']} • ${lot['initial_destination_name'] ?? ''}')),
'''
if trace_anchor not in s: raise SystemExit('trace anchor missing')
s=s.replace(trace_anchor,trace_extra,1)

# Sanity checks
required=[
    "Text('v94'",
    "rca_register_fuel_invoice_v94",
    "Como o combustível chegou à empresa?",
    "Caminhão-tanque da empresa",
    "Caminhão da refinaria / fornecedor",
    "Placa/identificação do caminhão da refinaria *",
    "Destino do combustível na empresa *",
    "Entrada inicial no estoque",
    "RefineryLoadV23Screen(ref: ref!)",
    "arrival_vehicle_label",
]
missing=[x for x in required if x not in s]
if missing: raise SystemExit(f'missing {missing}')
if "RefineryLoadV23Screen(truck:" in s:
    raise SystemExit('old forced truck constructor remains')
p.write_text(s)
print('V94_PATCH_OK')
