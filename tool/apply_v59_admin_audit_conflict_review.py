from pathlib import Path

main=Path('lib/main_online.dart')
s=main.read_text()

# API de auditoria operacional V59.
anchor="""  Future<List<Map<String,dynamic>>> offlineConflictsV58() async => _rows(await client.rpc('rca_offline_conflicts_v58'));\n  Future<Map<String,dynamic>> reviewOfflineConflictV58(int id,String decision,{String? notes}) async => _map(await client.rpc('rca_review_offline_conflict_v58',params:{'p_conflict_id':id,'p_decision':decision,'p_notes':notes}));\n"""
insert="""  Future<List<Map<String,dynamic>>> offlineConflictsV58() async => _rows(await client.rpc('rca_offline_conflicts_v58'));\n  Future<Map<String,dynamic>> reviewOfflineConflictV58(int id,String decision,{String? notes}) async => _map(await client.rpc('rca_review_offline_conflict_v58',params:{'p_conflict_id':id,'p_decision':decision,'p_notes':notes}));\n  Future<Map<String,dynamic>> operationAuditFiltersV59() async => _map(await client.rpc('rc_web_operation_audit_filters_v59'));\n  Future<List<Map<String,dynamic>>> operationAuditV59({String? userId,int? tankId,String? eventType,DateTime? start,DateTime? end,String? query}) async => _rows(await client.rpc('rc_web_operation_audit_v59',params:{'p_user_id':userId,'p_user_name':null,'p_tank_id':tankId,'p_event_type':eventType,'p_start':start?.toUtc().toIso8601String(),'p_end':end?.toUtc().toIso8601String(),'p_query':query,'p_limit':1000}));\n"""
assert anchor in s, 'api v58 não encontrada'
s=s.replace(anchor,insert,1)

# Conflitos offline passam a ser visíveis/revisáveis somente pelo Admin.
s=s.replace("if(isAdmin||isManager||isSupervisor)quick(Icons.warning_amber_rounded,'Conflitos offline','Revisar abastecimentos concorrentes',()=>open(const OfflineConflictsV58Screen())),",
            "if(isAdmin)quick(Icons.warning_amber_rounded,'Conflitos offline','Revisar abastecimentos concorrentes',()=>open(const OfflineConflictsV58Screen())),",1)

# Nova auditoria operacional exclusiva do Admin.
audit_anchor="""      if(isAdmin)quick(Icons.history_rounded,'Auditoria','Histórico de alterações',()=>open(const AuditHistoryV28Screen())),\n"""
audit_insert="""      if(isAdmin)quick(Icons.history_rounded,'Auditoria','Histórico de alterações',()=>open(const AuditHistoryV28Screen())),\n      if(isAdmin)quick(Icons.manage_search_rounded,'Operação dos comboios','Linha do tempo de logins, unidades, abastecimentos e conflitos',()=>open(const OperationAuditV59Screen())),\n"""
assert audit_anchor in s, 'menu auditoria não encontrado'
s=s.replace(audit_anchor,audit_insert,1)

# Versão visível.
s=s.replace("child: Text('v58'","child: Text('v59'",1)
main.write_text(s)

v=Path('lib/v29_features.dart')
t=v.read_text()

# Substitui a decisão V58 por diálogo com observação obrigatória e textos mais claros.
start=t.index("  Future<void> decide(Map<String,dynamic> x,String decision)async{", t.index('class _OfflineConflictsV58ScreenState'))
end=t.index("  @override Widget build", start)
new_decide=r'''  Future<void> decide(Map<String,dynamic> x,String decision)async{
    final approve=decision=='approve';
    final notes=TextEditingController();
    final reviewNote=await showDialog<String>(context:context,builder:(ctx)=>StatefulBuilder(builder:(ctx,setLocal){
      final valid=notes.text.trim().isNotEmpty;
      return AlertDialog(
        title:Text(approve?'Aprovar abastecimento':'Rejeitar abastecimento'),
        content:Column(mainAxisSize:MainAxisSize.min,crossAxisAlignment:CrossAxisAlignment.start,children:[
          Text(approve?'Confirme que as evidências foram analisadas. A decisão ficará registrada permanentemente na auditoria.':'O abastecimento não será consolidado. O motivo ficará preservado permanentemente para auditoria.'),
          const SizedBox(height:12),
          TextField(controller:notes,maxLines:4,onChanged:(_)=>setLocal((){}),decoration:InputDecoration(labelText:'Observação obrigatória *',hintText:approve?'Ex.: Fotos, localização e totalizador conferidos.':'Ex.: Totalizador incompatível com os demais registros.',errorText:valid?null:'Informe a justificativa da decisão.')),
        ]),
        actions:[
          TextButton(onPressed:()=>Navigator.pop(ctx),child:const Text('Cancelar')),
          FilledButton(onPressed:valid?()=>Navigator.pop(ctx,notes.text.trim()):null,child:Text(approve?'Aprovar abastecimento':'Rejeitar abastecimento')),
        ],
      );
    }));
    notes.dispose();
    if(reviewNote==null||reviewNote.trim().isEmpty)return;
    try{
      setState(()=>busy=true);
      await api.reviewOfflineConflictV58(_intOrNull(x['id'])!,decision,notes:reviewNote.trim());
      if(mounted)ScaffoldMessenger.of(context).showSnackBar(SnackBar(content:Text(approve?'Abastecimento aprovado. A decisão e a justificativa foram registradas.':'Abastecimento rejeitado. O registro e a justificativa foram preservados para auditoria.')));
      await load();
    }catch(e){if(mounted)ScaffoldMessenger.of(context).showSnackBar(SnackBar(content:Text(_friendlyError(e))));}
    finally{if(mounted)setState(()=>busy=false);}
  }
'''
t=t[:start]+new_decide+t[end:]

# Tela de auditoria operacional exclusiva do Admin.
screen=r'''

class OperationAuditV59Screen extends StatefulWidget{
  const OperationAuditV59Screen({super.key});
  @override State<OperationAuditV59Screen> createState()=>_OperationAuditV59ScreenState();
}
class _OperationAuditV59ScreenState extends State<OperationAuditV59Screen>{
  final search=TextEditingController();
  Map<String,dynamic> filters={};
  List<Map<String,dynamic>> items=[];
  String? userId,eventType;int? tankId;DateTime? startDate,endDate;
  bool busy=false;String? error;
  @override void initState(){super.initState();bootstrap();}
  @override void dispose(){search.dispose();super.dispose();}
  Future<void> bootstrap()async{setState(()=>busy=true);try{filters=await api.operationAuditFiltersV59();await load();}catch(e){if(mounted)setState(()=>error=_friendlyError(e));}finally{if(mounted)setState(()=>busy=false);}}
  Future<void> load()async{setState((){busy=true;error=null;});try{final x=await api.operationAuditV59(userId:userId,tankId:tankId,eventType:eventType,start:startDate,end:endDate,query:search.text.trim().isEmpty?null:search.text.trim());if(mounted)setState(()=>items=x);}catch(e){if(mounted)setState(()=>error=_friendlyError(e));}finally{if(mounted)setState(()=>busy=false);}}
  Future<void> pickDate(bool start)async{final now=DateTime.now();final initial=(start?startDate:endDate)??now;final d=await showDatePicker(context:context,initialDate:initial,firstDate:DateTime(now.year-3),lastDate:DateTime(now.year+1));if(d==null)return;setState((){if(start){startDate=DateTime(d.year,d.month,d.day);}else{endDate=DateTime(d.year,d.month,d.day,23,59,59,999);}});}
  String eventLabel(String? v){for(final e in _rows(filters['event_types'])){if('${e['value']}'==v)return '${e['label']}';}return v??'-';}
  String dateText(DateTime? d)=>d==null?'Qualquer data':'${d.day.toString().padLeft(2,'0')}/${d.month.toString().padLeft(2,'0')}/${d.year}';
  void clear(){setState((){userId=null;tankId=null;eventType=null;startDate=null;endDate=null;search.clear();});load();}
  @override Widget build(BuildContext context){final users=_rows(filters['users']),tanks=_rows(filters['units']),events=_rows(filters['event_types']);return Scaffold(appBar:AppBar(title:const Text('Operação dos comboios')),body:RefreshIndicator(onRefresh:load,child:ListView(padding:const EdgeInsets.all(12),children:[
    const Card(child:ListTile(leading:Icon(Icons.admin_panel_settings_rounded,color:_blue),title:Text('Auditoria exclusiva do Admin',style:TextStyle(fontWeight:FontWeight.w900)),subtitle:Text('Reconstrua login, seleção de unidade, abastecimentos, conflitos, decisões e logout em ordem cronológica.'))),
    Card(child:Padding(padding:const EdgeInsets.all(12),child:Column(children:[
      TextField(controller:search,onSubmitted:(_)=>load(),decoration:InputDecoration(prefixIcon:const Icon(Icons.search),labelText:'Buscar',hintText:'Usuário, comboio, abastecimento, status...',suffixIcon:IconButton(onPressed:(){search.clear();load();},icon:const Icon(Icons.clear)))),
      const SizedBox(height:10),
      DropdownButtonFormField<String>(value:userId,isExpanded:true,decoration:const InputDecoration(labelText:'Usuário'),items:[const DropdownMenuItem<String>(value:null,child:Text('Todos os usuários')),...users.map((u)=>DropdownMenuItem<String>(value:'${u['user_id']}',child:Text('${u['name']??'-'} • ${u['role']??'-'}')))],onChanged:(v)=>setState(()=>userId=v)),
      const SizedBox(height:10),
      DropdownButtonFormField<int>(value:tankId,isExpanded:true,decoration:const InputDecoration(labelText:'Comboio / unidade'),items:[const DropdownMenuItem<int>(value:null,child:Text('Todas as unidades')),...tanks.map((u)=>DropdownMenuItem<int>(value:_intOrNull(u['id']),child:Text('${u['code']??''} • ${u['name']??''}')))],onChanged:(v)=>setState(()=>tankId=v)),
      const SizedBox(height:10),
      DropdownButtonFormField<String>(value:eventType,isExpanded:true,decoration:const InputDecoration(labelText:'Tipo de evento'),items:[const DropdownMenuItem<String>(value:null,child:Text('Todos os eventos')),...events.map((e)=>DropdownMenuItem<String>(value:'${e['value']}',child:Text('${e['label']}')))],onChanged:(v)=>setState(()=>eventType=v)),
      const SizedBox(height:10),
      Row(children:[Expanded(child:OutlinedButton.icon(onPressed:()=>pickDate(true),icon:const Icon(Icons.calendar_today_outlined),label:Text('De: ${dateText(startDate)}'))),const SizedBox(width:8),Expanded(child:OutlinedButton.icon(onPressed:()=>pickDate(false),icon:const Icon(Icons.event_outlined),label:Text('Até: ${dateText(endDate)}')))]),
      const SizedBox(height:10),
      Row(children:[Expanded(child:OutlinedButton.icon(onPressed:clear,icon:const Icon(Icons.filter_alt_off_outlined),label:const Text('Limpar filtros'))),const SizedBox(width:8),Expanded(child:FilledButton.icon(onPressed:busy?null:load,icon:const Icon(Icons.search_rounded),label:const Text('Aplicar filtros')))]),
    ]))),
    if(busy)const LinearProgressIndicator(minHeight:2),
    if(error!=null)Padding(padding:const EdgeInsets.all(16),child:Text(error!,style:const TextStyle(color:Colors.red))),
    if(!busy&&error==null&&items.isEmpty)const Padding(padding:EdgeInsets.all(36),child:Center(child:Text('Nenhum evento encontrado para estes filtros.'))),
    ...items.map((x){final metadata=_map(x['metadata']);final who='${x['subject_name']??x['actor_name']??'Sistema'}';final unit=[x['unit_code'],x['unit_name']].where((e)=>e!=null&&'$e'.trim().isNotEmpty).join(' • ');final code='${x['movement_code']??''}'.trim();final status='${x['status']??''}'.trim();final extra=[if(unit.isNotEmpty)'Unidade: $unit',if(code.isNotEmpty)'Abastecimento: $code',if(status.isNotEmpty)'Status: $status',if(metadata.isNotEmpty)'Detalhes: ${metadata.entries.take(4).map((e)=>'${e.key}: ${e.value}').join(' • ')}'].join('\n');return Card(child:ListTile(leading:const CircleAvatar(child:Icon(Icons.history_rounded)),title:Text(eventLabel('${x['event_type']}'),style:const TextStyle(fontWeight:FontWeight.w900)),subtitle:Text('$who${extra.isEmpty?'':'\n$extra'}'),trailing:Text(_fmtDate(x['event_at']),textAlign:TextAlign.right,style:const TextStyle(fontSize:10))));}),
  ])));
  }
}
'''
t += screen
v.write_text(t)
print('PATCH_V59_ADMIN_AUDIT_CONFLICT_OK')
