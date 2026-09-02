from pathlib import Path

# v29: operational users must not depend on global movements.view to access their own records.
p=Path('lib/v29_features.dart')
s=p.read_text()
old="""      final results=await Future.wait<dynamic>([\n        api.referenceData(),\n        api.hasPermissionV29('fueling.create'),\n        api.hasPermissionV29('movements.view'),\n      ]);\n      if(mounted)setState((){\n        ref=results[0] as Map<String,dynamic>;\n        canFuel=results[1]==true;\n        canView=results[2]==true;\n        loading=false; error=null;\n      });\n"""
new="""      final results=await Future.wait<dynamic>([\n        api.referenceData(),\n        api.hasPermissionV29('fueling.create'),\n      ]);\n      if(mounted)setState((){\n        ref=results[0] as Map<String,dynamic>;\n        canFuel=results[1]==true;\n        canView=true; // Operacional sempre pode consultar somente os próprios registros.\n        loading=false; error=null;\n      });\n"""
assert old in s
s=s.replace(old,new,1)
old="""        ...keys.map((k)=>SwitchListTile(contentPadding:EdgeInsets.zero,title:Text(_permissionLabelV23(k)),value:permissions[k]==true,onChanged:(v)=>setD(()=>permissions[k]=v))),\n"""
new="""        ...keys.map((k){\n          final ownOnly=role=='operator'&&k=='movements.view';\n          return SwitchListTile(\n            contentPadding:EdgeInsets.zero,\n            title:Text(_permissionLabelV23(k)),\n            subtitle:ownOnly?const Text('Operacional vê somente os próprios abastecimentos.'):null,\n            value:ownOnly?false:permissions[k]==true,\n            onChanged:ownOnly?null:(v)=>setD(()=>permissions[k]=v),\n          );\n        }),\n"""
assert old in s
s=s.replace(old,new,1)
old="""          for(final k in keys){await api.adminSetUserPermissionV29(userId,k,permissions[k]==true);}\n"""
new="""          for(final k in keys){\n            final allowed=(role=='operator'&&k=='movements.view')?false:permissions[k]==true;\n            await api.adminSetUserPermissionV29(userId,k,allowed);\n          }\n"""
assert old in s
s=s.replace(old,new,1)
p.write_text(s)

# v30: same separation between own history and global movement visibility.
p=Path('lib/v30_features.dart')
s=p.read_text()
old="""      final r=await Future.wait<dynamic>([api.referenceData(),api.hasPermissionV29('fueling.create'),api.hasPermissionV29('movements.view'),api.myUnitV30(),api.unitStatusV30()]);\n      final mine=_map(r[3]);final tid=_intOrNull(mine['tank_id']);await offlineStore.setLastTankId(tid);\n      if(mounted)setState((){ref=r[0] as Map<String,dynamic>;canFuel=r[1]==true;canView=r[2]==true;currentUnit=mine;statuses=List<Map<String,dynamic>>.from(r[4] as List<Map<String,dynamic>>);loading=false;error=null;});\n"""
new="""      final r=await Future.wait<dynamic>([api.referenceData(),api.hasPermissionV29('fueling.create'),api.myUnitV30(),api.unitStatusV30()]);\n      final mine=_map(r[2]);final tid=_intOrNull(mine['tank_id']);await offlineStore.setLastTankId(tid);\n      if(mounted)setState((){ref=r[0] as Map<String,dynamic>;canFuel=r[1]==true;canView=true;currentUnit=mine;statuses=List<Map<String,dynamic>>.from(r[3] as List<Map<String,dynamic>>);loading=false;error=null;});\n"""
assert old in s
s=s.replace(old,new,1)
p.write_text(s)

# v31: current operational home used by v51+.
p=Path('lib/v31_features.dart')
s=p.read_text()
old="""      final r=await Future.wait<dynamic>([\n        api.referenceDataV31(),\n        api.hasPermissionV29('fueling.create'),\n        api.hasPermissionV29('movements.view'),\n        api.myUnitV30(),\n        api.unitStatusV30(),\n      ]);\n      final mine=_map(r[3]);\n      final tid=_intOrNull(mine['tank_id']);\n      await offlineStore.setLastTankId(tid);\n      if(mounted)setState((){\n        ref=r[0] as Map<String,dynamic>;\n        canFuel=r[1]==true;\n        canView=r[2]==true;\n        currentUnit=mine;\n        statuses=List<Map<String,dynamic>>.from(r[4] as List<Map<String,dynamic>>);\n        loading=false;\n        error=null;\n      });\n"""
new="""      final r=await Future.wait<dynamic>([\n        api.referenceDataV31(),\n        api.hasPermissionV29('fueling.create'),\n        api.myUnitV30(),\n        api.unitStatusV30(),\n      ]);\n      final mine=_map(r[2]);\n      final tid=_intOrNull(mine['tank_id']);\n      await offlineStore.setLastTankId(tid);\n      if(mounted)setState((){\n        ref=r[0] as Map<String,dynamic>;\n        canFuel=r[1]==true;\n        canView=true; // Histórico próprio não depende da permissão global movements.view.\n        currentUnit=mine;\n        statuses=List<Map<String,dynamic>>.from(r[3] as List<Map<String,dynamic>>);\n        loading=false;\n        error=null;\n      });\n"""
assert old in s
s=s.replace(old,new,1)
p.write_text(s)

print('VALIDACAO_PATCH_V52_OK')
