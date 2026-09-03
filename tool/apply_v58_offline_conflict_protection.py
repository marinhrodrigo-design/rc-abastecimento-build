from pathlib import Path

main=Path('lib/main_online.dart')
s=main.read_text()

# 1) v58 também é abastecimento para saldo/fila local.
s=s.replace("|| rpc == 'rca_record_fueling_v56'))", "|| rpc == 'rca_record_fueling_v56' || rpc == 'rca_record_fueling_v58'))", 1)

# 2) ID único estável para cada abastecimento offline.
anchor="""  Future<Map<String, dynamic>> _queueAndResult(String rpc, Map<String, dynamic> params) async {\n    final queue = _queue;\n"""
insert="""  String _newOfflineEventIdV58() {\n    final uid=(Supabase.instance.client.auth.currentUser?.id??'00000000-0000-0000-0000-000000000000').replaceAll('-','');\n    final time=DateTime.now().microsecondsSinceEpoch.toRadixString(16).padLeft(16,'0');\n    final raw=(uid.substring(0,16)+time).padRight(32,'0').substring(0,32);\n    return '${raw.substring(0,8)}-${raw.substring(8,12)}-${raw.substring(12,16)}-${raw.substring(16,20)}-${raw.substring(20,32)}';\n  }\n\n  Future<Map<String, dynamic>> _queueAndResult(String rpc, Map<String, dynamic> params) async {\n    if(_fuelingRpc(rpc)){\n      params=Map<String,dynamic>.from(params);\n      params['p_is_offline']=true;\n      params['p_offline_event_id']??=_newOfflineEventIdV58();\n    }\n    final queue = _queue;\n"""
assert anchor in s, 'queue anchor não encontrado'
s=s.replace(anchor,insert,1)

# 3) Nova RPC com flags online/offline e ID único.
old="""offlineStore.executeOrQueue('rca_record_fueling_v56',{'p_source_tank_id':sourceTankId"""
new="""offlineStore.executeOrQueue('rca_record_fueling_v58',{'p_source_tank_id':sourceTankId"""
assert old in s, 'fueling rpc v56 não encontrada'
s=s.replace(old,new,1)
old_tail="""'p_location_accuracy_m':locationAccuracyM,'p_occurred_at':occurredAt.toUtc().toIso8601String()});"""
new_tail="""'p_location_accuracy_m':locationAccuracyM,'p_occurred_at':occurredAt.toUtc().toIso8601String(),'p_offline_event_id':null,'p_is_offline':false});"""
assert old_tail in s, 'tail fueling não encontrada'
s=s.replace(old_tail,new_tail,1)

# 4) Não remover da fila quando o backend detectar conflito/rejeição.
old_sync="""          await Supabase.instance.client.rpc(rpc, params: params);\n          _deleteLocalRefs(original);\n"""
new_sync="""          final response=_map(await Supabase.instance.client.rpc(rpc, params: params));\n          if(response['conflict']==true || response['ok']==false){\n            final queue=_queue;\n            for(final q in queue){\n              if('${q['id']}'=='${queued['id']}'){\n                q['sync_error']='${response['message']??'Sincronização aguardando revisão.'}';\n                q['sync_blocked']=true;\n                q['sync_conflict']=response['conflict']==true;\n                q['sync_status']=response['status'];\n                q['last_sync_attempt']=DateTime.now().toUtc().toIso8601String();\n              }\n            }\n            _state['queue']=queue;\n            await _persist();\n            syncRevision.value++;\n            break;\n          }\n          _deleteLocalRefs(original);\n"""
assert old_sync in s, 'sync rpc anchor não encontrado'
s=s.replace(old_sync,new_sync,1)

# 5) API administrativa de conflitos.
api_anchor="""  Future<Map<String,dynamic>> dashboardKpisV28() async => _map(await client.rpc('rca_dashboard_kpis_v28'));\n"""
api_insert="""  Future<List<Map<String,dynamic>>> offlineConflictsV58() async => _rows(await client.rpc('rca_offline_conflicts_v58'));\n  Future<Map<String,dynamic>> reviewOfflineConflictV58(int id,String decision,{String? notes}) async => _map(await client.rpc('rca_review_offline_conflict_v58',params:{'p_conflict_id':id,'p_decision':decision,'p_notes':notes}));\n\n  Future<Map<String,dynamic>> dashboardKpisV28() async => _map(await client.rpc('rca_dashboard_kpis_v28'));\n"""
assert api_anchor in s, 'api anchor não encontrado'
s=s.replace(api_anchor,api_insert,1)

# 6) Acesso à tela de conflitos para Admin/Gerente/Supervisor.
s=s.replace("final tanks=_sortedFuelUnits(ref?['tanks']);final isAdmin=widget.profile['is_admin']==true;final isManager=widget.profile['is_manager']==true;",
            "final tanks=_sortedFuelUnits(ref?['tanks']);final isAdmin=widget.profile['is_admin']==true;final isManager=widget.profile['is_manager']==true;final isSupervisor=widget.profile['is_supervisor']==true;",1)
menu_anchor="""      if(isAdmin)quick(Icons.history_rounded,'Auditoria','Histórico de alterações',()=>open(const AuditHistoryV28Screen())),\n"""
menu_insert="""      if(isAdmin||isManager||isSupervisor)quick(Icons.warning_amber_rounded,'Conflitos offline','Revisar abastecimentos concorrentes',()=>open(const OfflineConflictsV58Screen())),\n      if(isAdmin)quick(Icons.history_rounded,'Auditoria','Histórico de alterações',()=>open(const AuditHistoryV28Screen())),\n"""
assert menu_anchor in s, 'menu anchor não encontrado'
s=s.replace(menu_anchor,menu_insert,1)

# 7) Versão visível.
s=s.replace("child: Text('v57'","child: Text('v58'",1)
main.write_text(s)

# 8) Melhorar visualização local de conflito e adicionar tela administrativa.
v=Path('lib/v29_features.dart')
t=v.read_text()
t=t.replace("'sync_error':q['sync_error'],", "'sync_error':q['sync_error'],'sync_conflict':q['sync_conflict']==true,'sync_status':q['sync_status'],",1)
t=t.replace("final syncError='${x['sync_error']??''}'.trim();", "final syncError='${x['sync_error']??''}'.trim();final syncConflict=x['sync_conflict']==true;",1)
t=t.replace("final status=legacy?'PENDENTE (OFFLINE) • confirme o usuário':syncError.isNotEmpty?'PENDENTE • falha ao sincronizar':'PENDENTE (OFFLINE)';",
            "final status=legacy?'PENDENTE (OFFLINE) • confirme o usuário':syncConflict?'CONFLITO • revisão necessária':syncError.isNotEmpty?'PENDENTE • falha ao sincronizar':'PENDENTE (OFFLINE)';",1)
t=t.replace("OutlinedButton.icon(onPressed:busy?null:()async{", "OutlinedButton.icon(onPressed:(busy||syncConflict)?null:()async{",1)
t=t.replace("},icon:const Icon(Icons.sync_rounded),label:Text(legacy?'Confirmar e sincronizar':'Tentar sincronizar')),",
            "},icon:Icon(syncConflict?Icons.lock_clock_rounded:Icons.sync_rounded),label:Text(syncConflict?'Aguardando revisão':legacy?'Confirmar e sincronizar':'Tentar sincronizar')),",1)

screen=r'''

class OfflineConflictsV58Screen extends StatefulWidget{
  const OfflineConflictsV58Screen({super.key});
  @override State<OfflineConflictsV58Screen> createState()=>_OfflineConflictsV58ScreenState();
}
class _OfflineConflictsV58ScreenState extends State<OfflineConflictsV58Screen>{
  List<Map<String,dynamic>> items=[];bool busy=false;String? error;
  @override void initState(){super.initState();load();}
  Future<void> load()async{setState((){busy=true;error=null;});try{final x=await api.offlineConflictsV58();if(mounted)setState(()=>items=x);}catch(e){if(mounted)setState(()=>error=_friendlyError(e));}finally{if(mounted)setState(()=>busy=false);}}
  String tank(dynamic id){for(final t in _rows(offlineStore.cachedReferenceData?['tanks'])){if(_intOrNull(t['id'])==_intOrNull(id))return '${t['code']??''}${('${t['name']??''}'.trim()).isNotEmpty?' • ${t['name']}':''}';}return 'Unidade #$id';}
  Future<void> decide(Map<String,dynamic> x,String decision)async{
    final approve=decision=='approve';final notes=TextEditingController();
    final ok=await showDialog<bool>(context:context,builder:(ctx)=>AlertDialog(title:Text(approve?'Aprovar conflito?':'Rejeitar abastecimento?'),content:Column(mainAxisSize:MainAxisSize.min,children:[Text(approve?'O abastecimento será liberado para o usuário original sincronizar novamente.':'O registro ficará preservado para auditoria, mas não será consolidado no estoque.'),const SizedBox(height:12),TextField(controller:notes,maxLines:3,decoration:const InputDecoration(labelText:'Observação da revisão'))]),actions:[TextButton(onPressed:()=>Navigator.pop(ctx,false),child:const Text('Cancelar')),FilledButton(onPressed:()=>Navigator.pop(ctx,true),child:Text(approve?'Aprovar':'Rejeitar'))]))??false;
    if(!ok){notes.dispose();return;}try{setState(()=>busy=true);await api.reviewOfflineConflictV58(_intOrNull(x['id'])!,decision,notes:notes.text.trim().isEmpty?null:notes.text.trim());if(mounted)ScaffoldMessenger.of(context).showSnackBar(SnackBar(content:Text(approve?'Conflito aprovado. Aguarda sincronização do usuário original.':'Abastecimento rejeitado e preservado para auditoria.')));await load();}catch(e){if(mounted)ScaffoldMessenger.of(context).showSnackBar(SnackBar(content:Text(_friendlyError(e))));}finally{notes.dispose();if(mounted)setState(()=>busy=false);}
  }
  @override Widget build(BuildContext context)=>Scaffold(appBar:AppBar(title:const Text('Conflitos offline')),body:RefreshIndicator(onRefresh:load,child:ListView(padding:const EdgeInsets.all(12),children:[
    const Card(child:ListTile(leading:Icon(Icons.shield_outlined,color:_blue),title:Text('Proteção contra concorrência offline',style:TextStyle(fontWeight:FontWeight.w900)),subtitle:Text('Registros conflitantes não alteram estoque nem totalizador até revisão.'))),
    if(busy)const LinearProgressIndicator(minHeight:2),if(error!=null)Padding(padding:const EdgeInsets.all(18),child:Text(error!,style:const TextStyle(color:Colors.red))),
    if(!busy&&error==null&&items.isEmpty)const Padding(padding:EdgeInsets.all(40),child:Center(child:Text('Nenhum conflito pendente.'))),
    ...items.map((x){final p=_map(x['payload']);final mids=(x['conflicting_movement_ids'] is List)?(x['conflicting_movement_ids'] as List).join(', '):'${x['conflicting_movement_ids']??''}';return Card(child:Padding(padding:const EdgeInsets.all(14),child:Column(crossAxisAlignment:CrossAxisAlignment.stretch,children:[
      Row(children:[const Icon(Icons.warning_amber_rounded,color:Colors.orange),const SizedBox(width:8),Expanded(child:Text(tank(x['source_tank_id']),style:const TextStyle(fontWeight:FontWeight.w900))),const Text('REVISÃO',style:TextStyle(fontSize:11,fontWeight:FontWeight.w900,color:Colors.orange))]),
      const SizedBox(height:8),Text('Usuário: ${x['user_name']??'-'}\nHorário do abastecimento: ${_fmtDate(x['occurred_at'])}\nVolume: ${_fmtLiters(p['liters'])}\nLocalização: ${p['location_address']??'-'}\nRegistros concorrentes: ${mids.isEmpty?'-':mids}'),
      const SizedBox(height:8),Text('${x['reason']??''}',style:const TextStyle(fontWeight:FontWeight.w700)),const SizedBox(height:12),
      Row(children:[Expanded(child:OutlinedButton.icon(onPressed:busy?null:()=>decide(x,'reject'),icon:const Icon(Icons.close_rounded),label:const Text('Rejeitar'))),const SizedBox(width:8),Expanded(child:FilledButton.icon(onPressed:busy?null:()=>decide(x,'approve'),icon:const Icon(Icons.check_rounded),label:const Text('Aprovar')))])
    ])));})
  ])));
}
'''
t += screen
v.write_text(t)
print('PATCH_V58_OFFLINE_CONFLICT_OK')
