from pathlib import Path
p=Path('lib/main_online.dart')
s=p.read_text()

# v33 reference data includes per-asset measurement configuration, both on normal refresh and queue refresh.
s=s.replace("client.rpc('rca_reference_data')", "client.rpc('rca_reference_data_v33')")

# Offline optimistic bookkeeping recognizes the v33 fueling RPC.
s=s.replace("rpc == 'rca_record_fueling_v32'))", "rpc == 'rca_record_fueling_v32' || rpc == 'rca_record_fueling_v33'))", 1)

# Replace saveMachine API with measurement type aware v33 RPC.
api_start=s.index('  Future<int?> saveMachine({')
api_end=s.index('\n  Future<void> saveThirdParty({', api_start)
new_save_api="""  Future<int?> saveMachine({
    int? id,
    required String assetNumber,
    String? model,
    String? plate,
    String? type,
    String? location,
    bool active = true,
    double? comboioCapacityLiters,
    double? fuelTankCapacityLiters,
    required String measurementType,
  }) async {
    final value = await client.rpc('rca_save_machine_v33', params: {
      'p_id': id,
      'p_asset_number': assetNumber,
      'p_model': model,
      'p_plate': plate,
      'p_type': type,
      'p_location': location,
      'p_active': active,
      'p_comboio_capacity_liters': comboioCapacityLiters,
      'p_fuel_tank_capacity_liters': fuelTankCapacityLiters,
      'p_measurement_type': measurementType,
    });
    return _intOrNull(value);
  }
"""
s=s[:api_start]+new_save_api+s[api_end:]

# Replace fueling API with nullable meter evidence and v33 server-side validation.
fuel_api_start=s.index('  Future<Map<String,dynamic>> fuelingV22({')
fuel_api_end=s.index('\n  Future<Map<String,dynamic>> dashboardV22()', fuel_api_start)
new_fuel_api="""  Future<Map<String,dynamic>> fuelingV22({required int sourceTankId,int? workId,int? machineId,int? thirdId,required double liters,double? km,double? hourmeter,required String receiver,required String receiverSignature,required String operatorSignature,String? meterPhoto,required String totalizerPhoto,required String identityPhoto,required String identityKind,String? extraPhoto,double? salePrice,String? notes,required String fuelType,required String location,double? latitude,double? longitude,DateTime? locationCapturedAt,double? locationAccuracyM}) async => offlineStore.executeOrQueue('rca_record_fueling_v33',{'p_source_tank_id':sourceTankId,'p_work_id':workId,'p_machine_id':machineId,'p_third_party_vehicle_id':thirdId,'p_third_party_plate':null,'p_third_party_company':null,'p_third_party_description':null,'p_liters':liters,'p_km_value':km,'p_hourmeter_value':hourmeter,'p_receiver_name':receiver,'p_receiver_company':null,'p_receiver_signature_path':receiverSignature,'p_operator_signature_path':operatorSignature,'p_meter_photo_path':meterPhoto,'p_totalizer_photo_path':totalizerPhoto,'p_identity_photo_path':identityPhoto,'p_identity_evidence_kind':identityKind,'p_extra_photo_path':extraPhoto,'p_sale_price_per_liter':salePrice,'p_notes':notes,'p_lubricated':false,'p_latitude':latitude,'p_longitude':longitude,'p_fuel_type':fuelType,'p_location_address':location,'p_location_captured_at':locationCapturedAt?.toUtc().toIso8601String(),'p_location_accuracy_m':locationAccuracyM});"""
s=s[:fuel_api_start]+new_fuel_api+s[fuel_api_end:]

# Measurement logic: own assets obey saved configuration; third-party keeps v32 fallback until its own setting exists.
metric_start=s.index('  bool vehicleLike(Map<String,dynamic> x,{bool thirdParty=false}){')
metric_end=s.index('  String sourceTypeLabel()', metric_start)
new_metric=r'''  bool vehicleLike(Map<String,dynamic> x,{bool thirdParty=false}){
    final raw='${x['tipo']??x['type']??''} ${x['modelo']??x['model']??''} ${x['description']??''}'.toLowerCase();
    const vehicleTerms=['automóvel','automovel','caminhão','caminhao','microonibus','micro-ônibus','microônibus','ônibus','onibus','cavalo mecânico','cavalo mecanico','pickup','pick up','van','veículo','veiculo','carro'];
    if(vehicleTerms.any(raw.contains))return true;
    const machineTerms=['retroescavadeira','escavadeira','carregadeira','fresadora','rolo ','rolo compactador','motoniveladora','vibro acabadora','máquina','maquina','trator','gerador','extrusora'];
    if(machineTerms.any(raw.contains))return false;
    final plate=thirdParty?x['plate']:x['placa'];
    return _hasValue(plate);
  }

  Set<String> metricKinds(){
    final out=<String>{};
    final ms=_rows(widget.ref['machines']),ts=_rows(widget.ref['third_party_vehicles']);
    final sm=selected(ms,machine),st=selected(ts,third);
    if(sm!=null){
      final configured='${sm['measurement_type']??''}'.trim().toLowerCase();
      if(configured=='km')out.add('km');
      else if(configured=='hourmeter')out.add('hour');
      else if(configured=='both')out.addAll(const ['km','hour']);
      else if(configured=='none'){}
      else out.add(vehicleLike(sm)?'km':'hour');
    }
    if(st!=null)out.add(vehicleLike(st,thirdParty:true)?'km':'hour');
    return out;
  }

'''
s=s[:metric_start]+new_metric+s[metric_end:]

# No fake measurement/photo for assets configured as Not applicable.
s=s.replace("    if(meter==null){requiredMessage(kinds.length>1?'Foto de KM/Horímetro':kinds.contains('km')?'Foto do KM':'Foto do Horímetro');return;}",
            "    if(kinds.isNotEmpty&&meter==null){requiredMessage(kinds.length>1?'Foto de KM/Horímetro':kinds.contains('km')?'Foto do KM':'Foto do Horímetro');return;}",1)
s=s.replace("final u=await Future.wait<String?>([up(meter!,'km_horimetro'),up(totalizer!,'totalizador'),up(identity!,'placa_identificacao'),extra==null?Future<String?>.value(null):up(extra!,'abastecimento_extra'),api.uploadBytes(rs!,'assinatura_recebedor'),api.uploadBytes(os!,'assinatura_abastecedor')]);",
            "final u=await Future.wait<String?>([meter==null?Future<String?>.value(null):up(meter!,'km_horimetro'),up(totalizer!,'totalizador'),up(identity!,'placa_identificacao'),extra==null?Future<String?>.value(null):up(extra!,'abastecimento_extra'),api.uploadBytes(rs!,'assinatura_recebedor'),api.uploadBytes(os!,'assinatura_abastecedor')]);",1)

old_build_head="""    final sm=selected(ms,machine),st=selected(ts,third),sw=selected(ws,work),hasPlate=_hasValue(sm?['placa'])||_hasValue(st?['plate']);
    final needsWork=const ['comboio','truck'].contains('${widget.source['tank_type']}');final kinds=metricKinds(),needsKm=kinds.contains('km'),needsHour=kinds.contains('hour');"""
new_build_head="""    final sm=selected(ms,machine),st=selected(ts,third),sw=selected(ws,work),hasPlate=_hasValue(sm?['placa'])||_hasValue(st?['plate']);
    final needsWork=const ['comboio','truck'].contains('${widget.source['tank_type']}');final kinds=metricKinds(),needsKm=kinds.contains('km'),needsHour=kinds.contains('hour');
    final measurementNotApplicable=sm!=null&&st==null&&'${sm['measurement_type']??''}'.trim().toLowerCase()=='none';"""
if old_build_head not in s: raise SystemExit('v33 build head marker missing')
s=s.replace(old_build_head,new_build_head,1)

s=s.replace("      else const Text('O campo de KM ou Horímetro será definido depois que o destino for selecionado.',style:TextStyle(fontSize:12,color:Colors.black54)),\n      if(kinds.isNotEmpty)const Padding(padding:EdgeInsets.only(top:5),child:Text('O sistema solicita somente a medição aplicável ao equipamento selecionado.',style:TextStyle(fontSize:12,color:Colors.black54))),",
            "      else if(measurementNotApplicable)const Text('Tipo de medição: Não se aplica.',style:TextStyle(fontSize:12,color:Colors.black54))\n      else const Text('O campo de KM ou Horímetro será definido depois que o destino for selecionado.',style:TextStyle(fontSize:12,color:Colors.black54)),\n      if(kinds.isNotEmpty)const Padding(padding:EdgeInsets.only(top:5),child:Text('O sistema solicita a medição configurada no cadastro do ativo.',style:TextStyle(fontSize:12,color:Colors.black54))),",1)
s=s.replace("      OutlinedButton(onPressed:saving?null:()async{final x=await cam();if(x!=null)setState(()=>meter=x);},child:Text(meter==null?metricPhotoLabel(kinds):'Medição registrada ✓')),",
            "      if(kinds.isNotEmpty)OutlinedButton(onPressed:saving?null:()async{final x=await cam();if(x!=null)setState(()=>meter=x);},child:Text(meter==null?metricPhotoLabel(kinds):'Medição registrada ✓')),",1)

# Helper used by the asset management list/form.
class_marker='class MachinesAdminScreen extends StatefulWidget {'
helper="""String _measurementTypeLabel(dynamic value){
  switch('${value??''}'.trim().toLowerCase()){
    case 'km':return 'KM';
    case 'hourmeter':return 'Horímetro';
    case 'both':return 'KM + Horímetro';
    case 'none':return 'Não se aplica';
    default:return 'Não definido';
  }
}

"""
if helper.strip() not in s:
    if class_marker not in s: raise SystemExit('v33 machines class marker missing')
    s=s.replace(class_marker,helper+class_marker,1)

# Replace asset edit flow to include mandatory measurement type while preserving all existing data.
edit_start=s.index('  Future<void> edit([Map<String, dynamic>? item]) async {', s.index('class _MachinesAdminScreenState'))
edit_end=s.index('  @override\n  Widget build(BuildContext context)', edit_start)
new_edit=r'''  Future<void> edit([Map<String, dynamic>? item]) async {
    final number = TextEditingController(text: '${item?['numeroAtivo'] ?? ''}');
    final model = TextEditingController(text: '${item?['modelo'] ?? ''}');
    final plate = TextEditingController(text: '${item?['placa'] ?? ''}');
    final type = TextEditingController(text: '${item?['tipo'] ?? ''}');
    final location = TextEditingController(text: '${item?['localizacao'] ?? ''}');
    final capacity = TextEditingController(text: item?['comboio_capacity_liters'] == null ? '' : _num(item?['comboio_capacity_liters']).toStringAsFixed(0));
    final fuelCapacity = TextEditingController(text: item?['fuel_tank_capacity_liters'] == null ? '' : _num(item?['fuel_tank_capacity_liters']).toStringAsFixed(0));
    final measurementRaw='${item?['measurement_type']??''}'.trim();
    String? measurement=measurementRaw.isEmpty?null:measurementRaw;
    final ok = await showDialog<bool>(context: context, builder: (ctx) => StatefulBuilder(builder: (ctx, setLocal) {
      final isComboio = number.text.trim().startsWith('008');
      return AlertDialog(title: Text(item == null ? 'Cadastrar ativo' : 'Editar ativo'), content: SingleChildScrollView(child: Column(mainAxisSize: MainAxisSize.min, children: [
        TextField(controller: number, onChanged: (_) => setLocal(() {}), decoration: const InputDecoration(labelText: 'Número do ativo *')),
        const SizedBox(height: 8), TextField(controller: model, decoration: const InputDecoration(labelText: 'Modelo')),
        const SizedBox(height: 8), TextField(controller: plate, decoration: const InputDecoration(labelText: 'Placa')),
        const SizedBox(height: 8), TextField(controller: type, decoration: const InputDecoration(labelText: 'Tipo')),
        const SizedBox(height: 8),DropdownButtonFormField<String>(value:measurement,decoration:const InputDecoration(labelText:'Tipo de medição *'),items:const [
          DropdownMenuItem(value:'km',child:Text('KM')),
          DropdownMenuItem(value:'hourmeter',child:Text('Horímetro')),
          DropdownMenuItem(value:'both',child:Text('KM + Horímetro')),
          DropdownMenuItem(value:'none',child:Text('Não se aplica')),
        ],onChanged:(v)=>setLocal(()=>measurement=v)),
        const Padding(padding:EdgeInsets.only(top:5),child:Align(alignment:Alignment.centerLeft,child:Text('Define qual medição será exigida ao abastecer este ativo.',style:TextStyle(fontSize:12,color:Colors.black54)))),
        if (isComboio) ...[
          const SizedBox(height: 8),
          TextField(controller: capacity, keyboardType: const TextInputType.numberWithOptions(decimal: true), decoration: const InputDecoration(labelText: 'Capacidade do comboio (litros) *')),
          if (_hasValue(item?['comboio_code'])) Padding(padding: const EdgeInsets.only(top: 8), child: Align(alignment: Alignment.centerLeft, child: Text('Unidade: ${item?['comboio_code']} • Saldo: ${_fmtLiters(item?['comboio_balance_liters'])}', style: const TextStyle(fontWeight: FontWeight.w700)))),
        ],
        const SizedBox(height: 8), TextField(controller: fuelCapacity, keyboardType: const TextInputType.numberWithOptions(decimal: true), decoration: const InputDecoration(labelText: 'Capacidade do tanque de combustível do ativo (litros)')),
        const SizedBox(height: 8), TextField(controller: location, decoration: const InputDecoration(labelText: 'Localização')),
      ])), actions: [TextButton(onPressed: () => Navigator.pop(ctx, false), child: const Text('Cancelar')), FilledButton(onPressed: () => Navigator.pop(ctx, true), child: const Text('Salvar'))]);
    }));
    if (ok == true && number.text.trim().isNotEmpty) {
      if(measurement==null){
        if(mounted)ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content:Text('Selecione o tipo de medição do ativo.')));
      }else{
        final isComboio = number.text.trim().startsWith('008');
        final parsed = double.tryParse(capacity.text.trim().replaceAll(',', '.'));
        if (isComboio && (parsed == null || parsed <= 0)) {
          if (mounted) ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Informe a capacidade do comboio.')));
        } else {
          try {
            final parsedFuel = fuelCapacity.text.trim().isEmpty ? null : double.tryParse(fuelCapacity.text.trim().replaceAll(',', '.'));
            if (fuelCapacity.text.trim().isNotEmpty && (parsedFuel == null || parsedFuel <= 0)) throw Exception('Informe uma capacidade válida para o tanque de combustível do ativo.');
            await api.saveMachine(id: _intOrNull(item?['id']), assetNumber: number.text.trim(), model: model.text.trim(), plate: plate.text.trim(), type: type.text.trim(), location: location.text.trim(), comboioCapacityLiters: isComboio ? parsed : null, fuelTankCapacityLiters: parsedFuel,measurementType:measurement!);
            await load();
            if (mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(isComboio?'Ativo e comboio sincronizados.':'Ativo salvo com sucesso ✓')));
          } catch (e) { if (mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(_friendlyError(e)))); }
        }
      }
    }
    number.dispose(); model.dispose(); plate.dispose(); type.dispose(); location.dispose(); capacity.dispose(); fuelCapacity.dispose();
  }
'''
s=s[:edit_start]+new_edit+s[edit_end:]

old_list="subtitle: Text('Placa: ${x['placa'] ?? '-'} • Tanque: ${x['fuel_tank_capacity_liters']==null?'-':_fmtLiters(x['fuel_tank_capacity_liters'])} • ${x['localizacao'] ?? ''}')"
new_list="subtitle: Text('Placa: ${x['placa'] ?? '-'} • Medição: ${_measurementTypeLabel(x['measurement_type'])} • Tanque: ${x['fuel_tank_capacity_liters']==null?'-':_fmtLiters(x['fuel_tank_capacity_liters'])} • ${x['localizacao'] ?? ''}')"
if old_list not in s: raise SystemExit('v33 machine list marker missing')
s=s.replace(old_list,new_list,1)

checks=[
  "client.rpc('rca_reference_data_v33')",
  "client.rpc('rca_save_machine_v33'",
  "'p_measurement_type': measurementType",
  "offlineStore.executeOrQueue('rca_record_fueling_v33'",
  "measurementType:measurement!",
  "labelText:'Tipo de medição *'",
  "DropdownMenuItem(value:'hourmeter',child:Text('Horímetro'))",
  "configured=='both'",
  "configured=='none'",
  "if(kinds.isNotEmpty&&meter==null)",
  "if(kinds.isNotEmpty)OutlinedButton",
  "Tipo de medição: Não se aplica.",
]
for x in checks:
    if x not in s: raise SystemExit('v33 missing marker: '+x)

p.write_text(s)
print('VALIDACAO_PATCH_V33_OK')
