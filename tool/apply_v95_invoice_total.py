from pathlib import Path
p=Path('lib/main_online.dart')
s=p.read_text()

s=s.replace("Text('v94'", "Text('v95'", 1)

old="""  @override
  Widget build(BuildContext c) {
    final ownTruck = arrivalMode == 'company_truck';
    final supplierTruck = arrivalMode == 'supplier_truck';
    return Scaffold(
"""
new="""  @override
  Widget build(BuildContext c) {
    final ownTruck = arrivalMode == 'company_truck';
    final supplierTruck = arrivalMode == 'supplier_truck';
    final volumePreview =
        double.tryParse(liters.text.trim().replaceAll(',', '.')) ?? 0;
    final unitCostPreview =
        double.tryParse(cost.text.trim().replaceAll(',', '.')) ?? 0;
    final invoiceTotalPreview =
        volumePreview > 0 && unitCostPreview >= 0
            ? volumePreview * unitCostPreview
            : 0.0;
    return Scaffold(
"""
if old not in s: raise SystemExit('build anchor missing')
s=s.replace(old,new,1)

old="""              TextField(
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
"""
new="""              TextField(
                  controller: liters,
                  enabled: !busy,
                  onChanged: (_) => setState(() {}),
                  keyboardType:
                      const TextInputType.numberWithOptions(decimal: true),
                  decoration: const InputDecoration(
                      labelText: 'Volume recebido (L) *')),
              const SizedBox(height: 8),
              TextField(
                  controller: cost,
                  enabled: !busy,
                  onChanged: (_) => setState(() {}),
                  keyboardType:
                      const TextInputType.numberWithOptions(decimal: true),
                  decoration: const InputDecoration(
                      labelText: 'Preço de compra/L *')),
              const SizedBox(height: 8),
              InputDecorator(
                  decoration: const InputDecoration(
                      labelText: 'Valor total do volume recebido',
                      helperText:
                          'Calculado automaticamente: volume recebido × preço de compra/L.'),
                  child: Text(_fmtMoney(invoiceTotalPreview),
                      style: const TextStyle(
                          fontSize: 20, fontWeight: FontWeight.w900))),
              const SizedBox(height: 8),
              TextField(
"""
if old not in s: raise SystemExit('receipt fields anchor missing')
s=s.replace(old,new,1)

old="""                    Text('Volume recebido: ${_fmtLiters(volume)}'),
                    Text('Preço de compra/L: ${_fmtMoney(unitCost)}'),
                    const SizedBox(height: 8),
"""
new="""                    Text('Volume recebido: ${_fmtLiters(volume)}'),
                    Text('Preço de compra/L: ${_fmtMoney(unitCost)}'),
                    Text('Valor total: ${_fmtMoney(volume * unitCost)}',
                        style: const TextStyle(fontWeight: FontWeight.w900)),
                    const SizedBox(height: 8),
"""
if old not in s: raise SystemExit('confirmation anchor missing')
s=s.replace(old,new,1)

old="""        'p_unit_cost': unitCost,
        'p_fuel_type': fuelType,
"""
new="""        'p_unit_cost': unitCost,
        'p_invoice_total_value': liters * unitCost,
        'p_fuel_type': fuelType,
"""
if old not in s: raise SystemExit('rpc params anchor missing')
s=s.replace(old,new,1)

p.write_text(s)
print('V95_INVOICE_TOTAL_PATCH_APPLIED')
