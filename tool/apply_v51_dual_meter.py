from pathlib import Path
p=Path('lib/main_online.dart')
s=p.read_text()
old="""  bool manualLocationV44=false;\n  bool autoLocationAttemptedV44=false;\n  bool locating=false,saving=false;\n  String savingStep='Concluir abastecimento';\n"""
new="""  bool manualLocationV44=false;\n  bool autoLocationAttemptedV44=false;\n  bool locating=false,saving=false;\n  String savingStep='Concluir abastecimento';\n  final Map<int,String> measurementOverridesV51=<int,String>{};\n"""
assert old in s
s=s.replace(old,new,1)
old="""  Set<String> metricKinds(){\n    final out=<String>{};\n    final ms=_rows(widget.ref['machines']),ts=_rows(widget.ref['third_party_vehicles']);\n    final sm=selected(ms,machine),st=selected(ts,third);\n    if(sm!=null){\n      final configured='${sm['measurement_type']??''}'.trim().toLowerCase();\n      if(configured=='km')out.add('km');\n      else if(configured=='hourmeter')out.add('hour');\n      else if(configured=='both')out.addAll(const ['km','hour']);\n      else if(configured=='none'){}\n      else out.add(vehicleLike(sm)?'km':'hour');\n    }\n    if(st!=null)out.add(vehicleLike(st,thirdParty:true)?'km':'hour');\n    return out;\n  }\n"""
new="""  bool munckLikeV51(Map<String,dynamic> x){\n    final raw='${x['tipo']??x['type']??''} ${x['modelo']??x['model']??''}'.toLowerCase();\n    return raw.contains('munck')||raw.contains('guindauto');\n  }\n\n  Future<void> refreshMeasurementV51(int? machineId) async {\n    if(machineId==null)return;\n    try{\n      final fresh=await api.referenceData();\n      for(final x in _rows(fresh['machines'])){\n        if(_intOrNull(x['id'])!=machineId)continue;\n        final mt='${x['measurement_type']??''}'.trim().toLowerCase();\n        if(mt.isNotEmpty){measurementOverridesV51[machineId]=mt;if(mounted)setState((){});}\n        break;\n      }\n    }catch(_){}\n  }\n\n  Set<String> metricKinds(){\n    final out=<String>{};\n    final ms=_rows(widget.ref['machines']),ts=_rows(widget.ref['third_party_vehicles']);\n    final sm=selected(ms,machine),st=selected(ts,third);\n    if(sm!=null){\n      final id=_intOrNull(sm['id']);\n      final rawMeasurement=id==null?sm['measurement_type']:(measurementOverridesV51[id]??sm['measurement_type']);\n      final configured='${rawMeasurement??''}'.trim().toLowerCase();\n      if(configured=='both'||munckLikeV51(sm))out.addAll(const ['km','hour']);\n      else if(configured=='km')out.add('km');\n      else if(configured=='hourmeter')out.add('hour');\n      else if(configured=='none'){}\n      else out.add(vehicleLike(sm)?'km':'hour');\n    }\n    if(st!=null)out.add(vehicleLike(st,thirdParty:true)?'km':'hour');\n    return out;\n  }\n"""
assert old in s
s=s.replace(old,new,1)
old="""onChanged:(saving||third!=null)?null:(v)=>setState((){machine=v;if(v!=null){third=null;thirdPlate.clear();thirdDescription.clear();}})),const SizedBox(height:8),"""
new="""onChanged:(saving||third!=null)?null:(v){setState((){machine=v;if(v!=null){third=null;thirdPlate.clear();thirdDescription.clear();}});unawaited(refreshMeasurementV51(v));}),const SizedBox(height:8),"""
assert old in s
s=s.replace(old,new,1)
old="""    final measurementNotApplicable=sm!=null&&st==null&&'${sm['measurement_type']??''}'.trim().toLowerCase()=='none';"""
new="""    final smId=_intOrNull(sm?['id']);\n    final rawSmMeasurement=smId==null?sm?['measurement_type']:(measurementOverridesV51[smId]??sm?['measurement_type']);\n    final smMeasurement='${rawSmMeasurement??''}'.trim().toLowerCase();\n    final measurementNotApplicable=sm!=null&&st==null&&smMeasurement=='none';"""
assert old in s
s=s.replace(old,new,1)
p.write_text(s)
print('VALIDACAO_PATCH_V51_OK')
