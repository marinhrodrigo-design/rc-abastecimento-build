from pathlib import Path
p=Path('lib/main_online.dart')
s=p.read_text()

if "Text('v92'," not in s:
    raise SystemExit('v92 label anchor missing')
s=s.replace("Text('v92',", "Text('v93',", 1)

if "client.rpc('rca_record_refinery_load_v22'" not in s:
    raise SystemExit('refinery v22 rpc anchor missing')
s=s.replace("client.rpc('rca_record_refinery_load_v22'", "client.rpc('rca_record_refinery_load_v93'", 1)
if "client.rpc('rca_edit_received_invoice_v92'" not in s:
    raise SystemExit('edit v92 rpc anchor missing')
s=s.replace("client.rpc('rca_edit_received_invoice_v92'", "client.rpc('rca_edit_received_invoice_v93'", 1)

old_controllers="""  final nf = TextEditingController(),
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
"""
new_controllers="""  final supplier = TextEditingController(),
      nf = TextEditingController(),
      liters = TextEditingController(),
      cost = TextEditingController(),
      batch = TextEditingController(),
      notes = TextEditingController();
  String fuel = 'Diesel';
  XFile? truckPlatePhoto, invoicePhoto;
  Map<String, dynamic> buyerCompany = {};
  bool busy = false, loadingRefs = true;
"""
if old_controllers not in s: raise SystemExit('receipt controller anchor missing')
s=s.replace(old_controllers,new_controllers,1)

old_load="""  Future<void> loadRefs() async {
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
"""
new_load="""  Future<void> loadRefs() async {
    try {
      final r = await api.reportCompany();
      if (mounted)
        setState(() {
          buyerCompany = _map(r);
          loadingRefs = false;
        });
    } catch (e) {
      if (mounted) {
        setState(() => loadingRefs = false);
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(
            content: Text('Erro ao carregar empresa compradora: ${_friendlyError(e)}')));
      }
    }
  }

  String supplierName() => supplier.text.trim();
"""
if old_load not in s: raise SystemExit('receipt load anchor missing')
s=s.replace(old_load,new_load,1)

old_validation="""    if (supplierId == null || supplier.isEmpty) {
      message('Preenchimento obrigatório: Fornecedor do combustível');
      return;
    }
"""
new_validation="""    if (supplier.isEmpty) {
      message('Preenchimento obrigatório: Fornecedor do combustível');
      return;
    }
"""
if old_validation not in s: raise SystemExit('receipt supplier validation anchor missing')
s=s.replace(old_validation,new_validation,1)

old_dispose="""    for (final c in [nf, liters, cost, batch, notes]) {
"""
new_dispose="""    for (final c in [supplier, nf, liters, cost, batch, notes]) {
"""
if old_dispose not in s: raise SystemExit('receipt dispose anchor missing')
s=s.replace(old_dispose,new_dispose,1)

old_help="""                const Text(
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
"""
new_help="""                const Text(
                    'Toda chegada entra primeiro pela Nota Fiscal. A empresa fornecedora do combustível faz parte dos dados da própria NF e deve ser informada neste registro.'),
                const SizedBox(height: 14),
                TextField(
                    controller: supplier,
                    enabled: !busy,
                    textCapitalization: TextCapitalization.words,
                    decoration: const InputDecoration(
                        labelText: 'Empresa fornecedora do combustível *',
                        hintText: 'Digite a empresa que consta na Nota Fiscal')),
                const SizedBox(height: 8),
"""
if old_help not in s: raise SystemExit('receipt supplier widget anchor missing')
s=s.replace(old_help,new_help,1)

old_button="""                    onPressed: busy || suppliers.isEmpty ? null : submit,
"""
new_button="""                    onPressed: busy ? null : submit,
"""
if old_button not in s: raise SystemExit('receipt button anchor missing')
s=s.replace(old_button,new_button,1)

old_edit_fields="""  Map<String, dynamic>? detail;
  List<Map<String, dynamic>> suppliers = [];
  int? supplierId;
  String fuel = 'Diesel S10';
"""
new_edit_fields="""  Map<String, dynamic>? detail;
  final supplier = TextEditingController();
  String fuel = 'Diesel S10';
"""
if old_edit_fields not in s: raise SystemExit('edit fields anchor missing')
s=s.replace(old_edit_fields,new_edit_fields,1)

old_edit_dispose="""    for (final c in [nf, batch, liters, cost, reason]) {
      c.dispose();
    }
"""
new_edit_dispose="""    for (final c in [nf, batch, liters, cost, reason, supplier]) {
      c.dispose();
    }
"""
if old_edit_dispose not in s: raise SystemExit('edit dispose anchor missing')
s=s.replace(old_edit_dispose,new_edit_dispose,1)

old_edit_load="""      final values = await Future.wait<dynamic>([
        api.nfEditDetailV92(widget.lotId),
        api.companiesByRole('fuel_supplier'),
      ]);
      final d = _map(values[0]);
      final list = (values[1] as List).cast<Map<String, dynamic>>();
      int? selected = _intOrNull(d['supplier_company_id']);
      if (selected == null || !list.any((x) => _intOrNull(x['id']) == selected)) {
        for (final x in list) {
          if ('${x['name']}'.trim().toLowerCase() ==
              '${d['supplier_name'] ?? ''}'.trim().toLowerCase()) {
            selected = _intOrNull(x['id']);
            break;
          }
        }
      }
      nf.text = '${d['invoice_number'] ?? ''}';
"""
new_edit_load="""      final d = await api.nfEditDetailV92(widget.lotId);
      supplier.text = '${d['supplier_name'] ?? ''}'.trim();
      nf.text = '${d['invoice_number'] ?? ''}';
"""
if old_edit_load not in s: raise SystemExit('edit load anchor missing')
s=s.replace(old_edit_load,new_edit_load,1)

old_edit_state="""          detail = d;
          suppliers = list;
          supplierId = selected;
          loading = false;
"""
new_edit_state="""          detail = d;
          loading = false;
"""
if old_edit_state not in s: raise SystemExit('edit setstate anchor missing')
s=s.replace(old_edit_state,new_edit_state,1)

old_supplier_method="""  String supplierName() {
    for (final x in suppliers) {
      if (_intOrNull(x['id']) == supplierId) return '${x['name']}'.trim();
    }
    return '';
  }
"""
new_supplier_method="""  String supplierName() => supplier.text.trim();
"""
if old_supplier_method not in s: raise SystemExit('edit supplier method anchor missing')
s=s.replace(old_supplier_method,new_supplier_method,1)

old_edit_widget="""                    DropdownButtonFormField<int>(
                        initialValue: supplierId,
                        isExpanded: true,
                        decoration: const InputDecoration(labelText: 'Fornecedor do combustível *'),
                        items: suppliers.map((x) => DropdownMenuItem(value: _intOrNull(x['id']), child: Text('${x['name']}'))).toList(),
                        onChanged: saving ? null : (v) => setState(() => supplierId = v)),
"""
new_edit_widget="""                    TextField(
                        controller: supplier,
                        enabled: !saving,
                        textCapitalization: TextCapitalization.words,
                        decoration: const InputDecoration(
                            labelText: 'Empresa fornecedora do combustível *',
                            hintText: 'Empresa informada na Nota Fiscal')),
"""
if old_edit_widget not in s: raise SystemExit('edit supplier widget anchor missing')
s=s.replace(old_edit_widget,new_edit_widget,1)

p.write_text(s)
print('V93_SUPPLIER_NF_FIELD_PATCH_PASS')
