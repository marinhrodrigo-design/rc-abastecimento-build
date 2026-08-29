part of 'main_online.dart';

extension FuelApiV31 on FuelApi {
  Future<Map<String,dynamic>> referenceDataV31() async => _map(await client.rpc('rca_reference_data_v31'));
  Future<Map<String,dynamic>> claimUnitV31(int tankId) async => _map(await client.rpc('rca_claim_unit_v31',params:{'p_tank_id':tankId}));
  Future<Map<String,dynamic>> releaseMyUnitV31() async => _map(await client.rpc('rca_release_my_unit_v31'));
  Future<Map<String,dynamic>> operatorUserActionV31(Map<String,dynamic> body) async {
    final r=await client.functions.invoke('fuel-users-v31',body:body);
    final m=_map(r.data);
    if(r.status<200||r.status>=300||m['error']!=null) throw Exception(m['error']??'Falha ao gerenciar usuário.');
    return m;
  }
}

class OperationalHomeV31Screen extends StatefulWidget {
  final Map<String,dynamic> profile;
  final Future<void> Function() onLogout;
  const OperationalHomeV31Screen({super.key,required this.profile,required this.onLogout});
  @override State<OperationalHomeV31Screen> createState()=>_OperationalHomeV31ScreenState();
}

class _OperationalHomeV31ScreenState extends State<OperationalHomeV31Screen> {
  Map<String,dynamic>? ref;
  Map<String,dynamic> currentUnit={};
  List<Map<String,dynamic>> statuses=[];
  bool canFuel=true,canView=true,loading=true,refreshing=false;
  String? error;

  @override void initState(){super.initState();load();}

  Future<void> load() async {
    if(refreshing)return;
    refreshing=true;
    try{
      if(!offlineStore.online.value){
        final cached=offlineStore.cachedReferenceData;
        if(mounted)setState((){ref=cached;loading=false;error=null;});
        return;
      }
      final r=await Future.wait<dynamic>([
        api.referenceDataV31(),
        api.hasPermissionV29('fueling.create'),
        api.hasPermissionV29('movements.view'),
        api.myUnitV30(),
        api.unitStatusV30(),
      ]);
      final mine=_map(r[3]);
      final tid=_intOrNull(mine['tank_id']);
      await offlineStore.setLastTankId(tid);
      if(mounted)setState((){
        ref=r[0] as Map<String,dynamic>;
        canFuel=r[1]==true;
        canView=r[2]==true;
        currentUnit=mine;
        statuses=List<Map<String,dynamic>>.from(r[4] as List<Map<String,dynamic>>);
        loading=false;
        error=null;
      });
    }catch(e){if(mounted)setState((){loading=false;error=_friendlyError(e);});}
    finally{refreshing=false;}
  }

  List<Map<String,dynamic>> get sources=>_sortedFuelUnits(ref?['tanks']).where((t)=>t['authorized']!=false&&const {'stationary','comboio','truck'}.contains('${t['tank_type']}')).toList();
  Map<String,dynamic>? statusFor(int id){for(final s in statuses){if(_intOrNull(s['tank_id'])==id)return s;}return null;}
  Map<String,dynamic>? tankFor(int? id){if(id==null)return null;for(final t in sources){if(_intOrNull(t['id'])==id)return t;}return null;}

  Future<Map<String,dynamic>?> pickUnit({required String title,bool excludeCurrent=false}) async {
    if(!offlineStore.online.value){
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content:Text('Conecte-se à internet para selecionar ou trocar de unidade.')));
      return null;
    }
    try{statuses=await api.unitStatusV30();}catch(_){}
    if(!mounted)return null;
    final currentId=_intOrNull(currentUnit['tank_id']);
    final list=sources.where((t)=>!excludeCurrent||_intOrNull(t['id'])!=currentId).toList();
    return showModalBottomSheet<Map<String,dynamic>>(
      context:context,
      showDragHandle:true,
      isScrollControlled:true,
      builder:(ctx)=>SafeArea(child:ConstrainedBox(
        constraints:BoxConstraints(maxHeight:MediaQuery.of(ctx).size.height*.75),
        child:Column(mainAxisSize:MainAxisSize.min,crossAxisAlignment:CrossAxisAlignment.stretch,children:[
          Padding(padding:const EdgeInsets.fromLTRB(18,4,18,4),child:Text(title,style:const TextStyle(fontWeight:FontWeight.w900,fontSize:19))),
          const Padding(padding:EdgeInsets.fromLTRB(18,0,18,10),child:Text('Escolha uma unidade disponível.')),
          Flexible(child:ListView.separated(
            shrinkWrap:true,
            padding:const EdgeInsets.fromLTRB(12,4,12,18),
            itemCount:list.length,
            separatorBuilder:(_,__)=>const SizedBox(height:4),
            itemBuilder:(_,i){
              final t=list[i];
              final id=_intOrNull(t['id']);
              final st=id==null?null:statusFor(id);
              final mine=st?['is_mine']==true;
              final inUse=st?['in_use']==true;
              final owner='${st?['user_name']??''}'.trim();
              return Card(child:ListTile(
                contentPadding:const EdgeInsets.symmetric(horizontal:14,vertical:9),
                leading:Icon('${t['tank_type']}'=='stationary'?Icons.oil_barrel_outlined:Icons.local_shipping_outlined,color:_blue),
                title:Text('${t['code']} • ${t['name']}',style:const TextStyle(fontWeight:FontWeight.w900)),
                subtitle:Text(inUse&&!mine?'Em uso por $owner':'Saldo: ${_fmtLiters(t['current_balance_liters'])}'),
                trailing:mine?const Icon(Icons.check_circle_rounded,color:Colors.green):inUse?const Icon(Icons.lock_outline_rounded):const Icon(Icons.chevron_right_rounded),
                onTap:(){
                  if(inUse&&!mine){
                    ScaffoldMessenger.of(ctx).showSnackBar(SnackBar(content:Text('Esta unidade já está sendo usada pelo usuário $owner.')));
                    return;
                  }
                  Navigator.pop(ctx,t);
                },
              ));
            },
          )),
        ]),
      )),
    );
  }

  Future<bool> claim(Map<String,dynamic> tank) async {
    final id=_intOrNull(tank['id']);if(id==null)return false;
    if(!offlineStore.online.value){
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content:Text('Conecte-se à internet para selecionar ou trocar de unidade.')));
      return false;
    }
    try{
      final x=await api.claimUnitV31(id);
      if(x['ok']!=true){
        if(mounted)ScaffoldMessenger.of(context).showSnackBar(SnackBar(content:Text('${x['message']??'Esta unidade já está em uso.'}')));
        return false;
      }
      await offlineStore.setLastTankId(id);
      if(mounted)setState(()=>currentUnit={'tank_id':id,'unit_code':tank['code'],'unit_name':tank['name'],'tank_type':tank['tank_type']});
      return true;
    }catch(e){if(mounted)ScaffoldMessenger.of(context).showSnackBar(SnackBar(content:Text(_friendlyError(e))));return false;}
  }

  Future<void> openFueling(Map<String,dynamic> tank) async {
    if(!mounted||ref==null)return;
    await Navigator.push(context,MaterialPageRoute(builder:(_)=>FuelingV23Screen(source:tank,ref:ref!,profile:widget.profile)));
    if(mounted)await load();
  }

  Future<void> newFueling() async {
    if(!canFuel){ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content:Text('Seu acesso para registrar abastecimentos está restrito pelo administrador.')));return;}
    if(ref==null){await load();if(ref==null)return;}
    final currentId=_intOrNull(currentUnit['tank_id'])??offlineStore.lastTankId;
    if(currentId!=null){
      final t=tankFor(currentId);
      if(t!=null){await openFueling(t);return;}
      if(!offlineStore.online.value){ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content:Text('Os dados da unidade atual não estão disponíveis offline. Conecte-se à internet uma vez para atualizar.')));return;}
      await load();final refreshed=tankFor(currentId);if(refreshed!=null){await openFueling(refreshed);return;}
    }
    final selected=await pickUnit(title:'Escolher unidade de abastecimento');
    if(selected==null||!mounted)return;
    if(await claim(selected))await openFueling(selected);
  }

  Future<void> switchUnit() async {
    final currentId=_intOrNull(currentUnit['tank_id'])??offlineStore.lastTankId;
    if(currentId==null){
      final selected=await pickUnit(title:'Escolher unidade de abastecimento');
      if(selected!=null&&await claim(selected))await load();
      return;
    }
    final selected=await pickUnit(title:'Trocar unidade',excludeCurrent:true);
    if(selected==null)return;
    if(await claim(selected)){
      await load();
      if(mounted)ScaffoldMessenger.of(context).showSnackBar(SnackBar(content:Text('Unidade alterada para ${selected['code']} ✓')));
    }
  }

  Future<void> releaseUnit() async {
    final id=_intOrNull(currentUnit['tank_id'])??offlineStore.lastTankId;
    if(id==null)return;
    if(!offlineStore.online.value){ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content:Text('Conecte-se à internet para liberar a unidade.')));return;}
    final code='${currentUnit['unit_code']??tankFor(id)?['code']??''}';
    final ok=await showDialog<bool>(context:context,builder:(ctx)=>AlertDialog(
      title:const Text('Liberar unidade?'),
      content:Text(code.isEmpty?'A unidade ficará disponível para outro usuário.':'A unidade $code ficará disponível para outro usuário.'),
      actions:[TextButton(onPressed:()=>Navigator.pop(ctx,false),child:const Text('Cancelar')),FilledButton(onPressed:()=>Navigator.pop(ctx,true),child:const Text('Liberar'))],
    ));
    if(ok!=true)return;
    try{
      final r=await api.releaseMyUnitV31();
      await offlineStore.setLastTankId(null);
      if(mounted)setState(()=>currentUnit={});
      await load();
      if(mounted)ScaffoldMessenger.of(context).showSnackBar(SnackBar(content:Text(r['released']==true?'Unidade liberada ✓':'Nenhuma unidade estava vinculada.')));
    }catch(e){if(mounted)ScaffoldMessenger.of(context).showSnackBar(SnackBar(content:Text(_friendlyError(e))));}
  }

  void openMine(){if(!canView){ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content:Text('Seu acesso aos registros está restrito pelo administrador.')));return;}Navigator.push(context,MaterialPageRoute(builder:(_)=>const MyFuelingsV29Screen()));}

  @override Widget build(BuildContext context){
    final code='${currentUnit['unit_code']??''}'.trim();
    final name='${currentUnit['unit_name']??''}'.trim();
    return Scaffold(
      appBar:AppBar(title:const Text('R&C Abastecimento',style:TextStyle(fontWeight:FontWeight.w900)),actions:[IconButton(onPressed:()=>_logoutToLogin(context,widget.onLogout),tooltip:'Sair',icon:const Icon(Icons.logout_rounded))]),
      body:loading?const Center(child:CircularProgressIndicator()):RefreshIndicator(
        onRefresh:load,
        child:ListView(physics:const AlwaysScrollableScrollPhysics(),padding:const EdgeInsets.all(20),children:[
          GreetingLine(name:'${widget.profile['display_name']}'),
          if(code.isNotEmpty)...[
            const SizedBox(height:10),
            Card(child:Padding(padding:const EdgeInsets.all(14),child:Column(crossAxisAlignment:CrossAxisAlignment.stretch,children:[
              Row(children:[const Icon(Icons.link_rounded,size:19,color:_blue),const SizedBox(width:7),Expanded(child:Text('Unidade atual: $code${name.isNotEmpty?' • $name':''}',style:const TextStyle(fontWeight:FontWeight.w900)))]),
              const SizedBox(height:10),
              Row(children:[Expanded(child:OutlinedButton.icon(onPressed:switchUnit,icon:const Icon(Icons.swap_horiz_rounded),label:const Text('Trocar unidade'))),const SizedBox(width:8),Expanded(child:OutlinedButton.icon(onPressed:releaseUnit,icon:const Icon(Icons.link_off_rounded),label:const Text('Liberar unidade')))]),
            ]))),
          ] else ...[
            const SizedBox(height:10),
            OutlinedButton.icon(onPressed:switchUnit,icon:const Icon(Icons.add_link_rounded),label:const Text('Escolher unidade')),
          ],
          if(error!=null)...[const SizedBox(height:10),Text(error!,style:const TextStyle(color:Colors.redAccent))],
          const SizedBox(height:20),
          HomeActionCard(icon:Icons.local_gas_station_rounded,title:'Novo abastecimento',subtitle:'',onTap:newFueling),
          const SizedBox(height:12),
          HomeActionCard(icon:Icons.history_rounded,title:'Meus abastecimentos',subtitle:'',onTap:openMine),
        ]),
      ),
    );
  }
}
