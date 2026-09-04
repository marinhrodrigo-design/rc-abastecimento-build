from pathlib import Path

# v30: consulta de status da unidade deixa de quebrar a tela inteira.
p=Path('lib/v30_features.dart')
s=p.read_text()
old="""      final r=await Future.wait<dynamic>([api.referenceData(),api.hasPermissionV29('fueling.create'),api.myUnitV30(),api.unitStatusV30()]);\n      final mine=_map(r[2]);final tid=_intOrNull(mine['tank_id']);await offlineStore.setLastTankId(tid);\n      if(mounted)setState((){ref=r[0] as Map<String,dynamic>;canFuel=r[1]==true;canView=true;currentUnit=mine;statuses=List<Map<String,dynamic>>.from(r[3] as List<Map<String,dynamic>>);loading=false;error=null;});\n"""
new="""      final r=await Future.wait<dynamic>([api.referenceData(),api.hasPermissionV29('fueling.create'),api.myUnitV30()]);\n      List<Map<String,dynamic>> st=[];try{st=await api.unitStatusV30();}catch(_){st=[];}\n      final mine=_map(r[2]);final tid=_intOrNull(mine['tank_id']);await offlineStore.setLastTankId(tid);\n      if(mounted)setState((){ref=r[0] as Map<String,dynamic>;canFuel=r[1]==true;canView=true;currentUnit=mine;statuses=st;loading=false;error=null;});\n"""
assert old in s
s=s.replace(old,new,1)
p.write_text(s)

# v31: mesma correção para a tela operacional usada atualmente.
p=Path('lib/v31_features.dart')
s=p.read_text()
old="""      final r=await Future.wait<dynamic>([\n        api.referenceDataV31(),\n        api.hasPermissionV29('fueling.create'),\n        api.myUnitV30(),\n        api.unitStatusV30(),\n      ]);\n      final mine=_map(r[2]);\n      final tid=_intOrNull(mine['tank_id']);\n      await offlineStore.setLastTankId(tid);\n      if(mounted)setState((){\n        ref=r[0] as Map<String,dynamic>;\n        canFuel=r[1]==true;\n        canView=true; // Histórico próprio não depende da permissão global movements.view.\n        currentUnit=mine;\n        statuses=List<Map<String,dynamic>>.from(r[3] as List<Map<String,dynamic>>);\n        loading=false;\n        error=null;\n      });\n"""
new="""      final r=await Future.wait<dynamic>([\n        api.referenceDataV31(),\n        api.hasPermissionV29('fueling.create'),\n        api.myUnitV30(),\n      ]);\n      List<Map<String,dynamic>> st=[];try{st=await api.unitStatusV30();}catch(_){st=[];}\n      final mine=_map(r[2]);\n      final tid=_intOrNull(mine['tank_id']);\n      await offlineStore.setLastTankId(tid);\n      if(mounted)setState((){\n        ref=r[0] as Map<String,dynamic>;\n        canFuel=r[1]==true;\n        canView=true; // Histórico próprio não depende da permissão global movements.view.\n        currentUnit=mine;\n        statuses=st;\n        loading=false;\n        error=null;\n      });\n"""
assert old in s
s=s.replace(old,new,1)
p.write_text(s)

# Traduz mensagens técnicas residuais e atualiza versão.
p=Path('lib/main_online.dart')
s=p.read_text()
anchor="""  if(pg!=null)s=(pg.group(1)??'').trim();\n"""
insert=anchor+"""  if(s.toLowerCase().contains('permission denied for function')) return 'Não foi possível atualizar o status da unidade agora. Tente novamente em instantes.';\n"""
assert anchor in s
s=s.replace(anchor,insert,1)
s=s.replace("child: Text('v63'","child: Text('v64'",1)
p.write_text(s)

print('PATCH_V64_UNIT_STATUS_PERMISSION_FALLBACK_OK')
