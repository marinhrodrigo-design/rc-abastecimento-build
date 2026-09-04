from pathlib import Path

# 1) Status da unidade não pode derrubar a tela quando o RPC de status estiver sem permissão.
p=Path('lib/v30_features.dart')
s=p.read_text()
old="""      final r=await Future.wait<dynamic>([api.referenceData(),api.hasPermissionV29('fueling.create'),api.myUnitV30(),api.unitStatusV30()]);
      final mine=_map(r[2]);final tid=_intOrNull(mine['tank_id']);await offlineStore.setLastTankId(tid);
      if(mounted)setState((){ref=r[0] as Map<String,dynamic>;canFuel=r[1]==true;canView=true;currentUnit=mine;statuses=List<Map<String,dynamic>>.from(r[3] as List<Map<String,dynamic>>);loading=false;error=null;});
"""
new="""      final r=await Future.wait<dynamic>([api.referenceData(),api.hasPermissionV29('fueling.create'),api.myUnitV30()]);
      List<Map<String,dynamic>> st=[];try{st=await api.unitStatusV30();}catch(_){st=[];}
      final mine=_map(r[2]);final tid=_intOrNull(mine['tank_id']);await offlineStore.setLastTankId(tid);
      if(mounted)setState((){ref=r[0] as Map<String,dynamic>;canFuel=r[1]==true;canView=true;currentUnit=mine;statuses=st;loading=false;error=null;});
"""
assert old in s
s=s.replace(old,new,1)
p.write_text(s)

p=Path('lib/v31_features.dart')
s=p.read_text()
old="""      final r=await Future.wait<dynamic>([
        api.referenceDataV31(),
        api.hasPermissionV29('fueling.create'),
        api.myUnitV30(),
        api.unitStatusV30(),
      ]);
      final mine=_map(r[2]);
      final tid=_intOrNull(mine['tank_id']);
      await offlineStore.setLastTankId(tid);
      if(mounted)setState((){
        ref=r[0] as Map<String,dynamic>;
        canFuel=r[1]==true;
        canView=true; // Histórico próprio não depende da permissão global movements.view.
        currentUnit=mine;
        statuses=List<Map<String,dynamic>>.from(r[3] as List<Map<String,dynamic>>);
        loading=false;
        error=null;
      });
"""
new="""      final r=await Future.wait<dynamic>([
        api.referenceDataV31(),
        api.hasPermissionV29('fueling.create'),
        api.myUnitV30(),
      ]);
      List<Map<String,dynamic>> st=[];try{st=await api.unitStatusV30();}catch(_){st=[];}
      final mine=_map(r[2]);
      final tid=_intOrNull(mine['tank_id']);
      await offlineStore.setLastTankId(tid);
      if(mounted)setState((){
        ref=r[0] as Map<String,dynamic>;
        canFuel=r[1]==true;
        canView=true; // Histórico próprio não depende da permissão global movements.view.
        currentUnit=mine;
        statuses=st;
        loading=false;
        error=null;
      });
"""
assert old in s
s=s.replace(old,new,1)
p.write_text(s)

# 2) Sincronização automática: erros anteriores não relacionados a conflito não podem deixar o item bloqueado para sempre.
p=Path('lib/main_online.dart')
s=p.read_text()
s=s.replace("if (reachable && (changed || pendingCount.value > 0)) unawaited(syncPending());",
            "if (reachable && (changed || pendingCount.value > 0)) unawaited(syncPending(force:changed));",1)
s=s.replace("if (changed && pendingCount.value > 0) unawaited(syncPending());",
            "if (changed && pendingCount.value > 0) unawaited(syncPending(force:true));",1)
s=s.replace("if(queued['sync_blocked']==true&&!force)continue;",
            "if(queued['sync_blocked']==true&&queued['sync_conflict']==true&&!force)continue;",1)

# Em erro não de rede, só bloqueia permanentemente quando for conflito real. Demais erros ficam disponíveis para nova tentativa automática.
oldcatch="""          final queue=_queue;
          for(final q in queue){if('${q['id']}'=='${queued['id']}'){q['sync_error']=_friendlyError(e);q['sync_blocked']=true;q['last_sync_attempt']=DateTime.now().toUtc().toIso8601String();}}
          _state['queue']=queue;
"""
newcatch="""          final queue=_queue;
          for(final q in queue){if('${q['id']}'=='${queued['id']}'){q['sync_error']=_friendlyError(e);q['sync_blocked']=q['sync_conflict']==true;q['last_sync_attempt']=DateTime.now().toUtc().toIso8601String();}}
          _state['queue']=queue;
"""
assert oldcatch in s
s=s.replace(oldcatch,newcatch,1)

# Mensagem técnica em inglês nunca deve aparecer ao usuário.
anchor="""  if(pg!=null)s=(pg.group(1)??'').trim();
"""
assert anchor in s
s=s.replace(anchor,anchor+"""  if(s.toLowerCase().contains('permission denied for function')) return 'Não foi possível atualizar o status da unidade agora. O abastecimento continua salvo e a sincronização será tentada novamente.';
""",1)

# Quando houver reconexão, tenta novamente os registros pendentes não conflitantes sem exigir toque manual.
s=s.replace("unawaited(offlineStore.syncPending());","unawaited(offlineStore.syncPending(force:true));",2)
s=s.replace("child: Text('v63'","child: Text('v65'",1)
p.write_text(s)

print('PATCH_V65_SYNC_AND_PERMISSION_FIX_OK')
