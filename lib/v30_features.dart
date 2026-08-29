part of 'main_online.dart';

extension OfflineStoreV30 on OfflineStore {
  String? get appSessionIdV30 { final v='${_state['app_session_id_v30'] ?? ''}'.trim(); return v.isEmpty?null:v; }
  Future<String> ensureAppSessionIdV30({bool renew=false}) async { var id=appSessionIdV30; if(renew||id==null){final uid=Supabase.instance.client.auth.currentUser?.id??'user';id='$uid-${DateTime.now().microsecondsSinceEpoch}';_state['app_session_id_v30']=id;await _persist();}return id; }
  Future<void> clearAppSessionIdV30() async {_state.remove('app_session_id_v30');await _persist();}
}

extension FuelApiV30 on FuelApi {
  Future<bool> sessionClaimV30(String id,{required bool explicitLogin}) async => (await client.rpc('rca_session_claim_v30',params:{'p_session_id':id,'p_explicit_login':explicitLogin}))==true;
  Future<bool> sessionValidV30(String id) async => (await client.rpc('rca_session_valid_v30',params:{'p_session_id':id}))==true;
  Future<Map<String,dynamic>> claimUnitV30(int id) async => _map(await client.rpc('rca_claim_unit_v30',params:{'p_tank_id':id}));
  Future<List<Map<String,dynamic>>> unitStatusV30() async => _rows(await client.rpc('rca_unit_status_v30'));
  Future<Map<String,dynamic>> myUnitV30() async => _map(await client.rpc('rca_my_unit_v30'));
  Future<Map<String,dynamic>> logoutV30(String id) async => _map(await client.rpc('rca_logout_v30',params:{'p_session_id':id}));
  Future<Map<String,dynamic>> adminDisconnectUserV30(String id) async => _map(await client.rpc('rca_admin_disconnect_user_v30',params:{'p_user_id':id}));
}

class OperationalHomeV30Screen extends StatefulWidget {
  final Map<String,dynamic> profile; final Future<void> Function() onLogout;
  const OperationalHomeV30Screen({super.key,required this.profile,required this.onLogout});
  @override State<OperationalHomeV30Screen> createState()=>_OperationalHomeV30ScreenState();
}

class _OperationalHomeV30ScreenState extends State<OperationalHomeV30Screen> {
  Map<String,dynamic>? ref; Map<String,dynamic> currentUnit={}; List<Map<String,dynamic>> statuses=[];
  bool canFuel=true,canView=true,loading=true,refreshing=false; String? error;
  @override void initState(){super.initState();load();}

  Future<void> load() async {
    if(refreshing)return;refreshing=true;
    try{
      if(!offlineStore.online.value){if(mounted)setState((){ref=offlineStore.cachedReferenceData;loading=false;});return;}
      final r=await Future.wait<dynamic>([api.referenceData(),api.hasPermissionV29('fueling.create'),api.hasPermissionV29('movements.view'),api.myUnitV30(),api.unitStatusV30()]);
      final mine=_map(r[3]);final tid=_intOrNull(mine['tank_id']);await offlineStore.setLastTankId(tid);
      if(mounted)setState((){ref=r[0] as Map<String,dynamic>;canFuel=r[1]==true;canView=r[2]==true;currentUnit=mine;statuses=List<Map<String,dynamic>>.from(r[4] as List<Map<String,dynamic>>);loading=false;error=null;});
    }catch(e){if(mounted)setState((){loading=false;error=_friendlyError(e);});}finally{refreshing=false;}
  }

  Map<String,dynamic>? statusFor(int id){for(final s in statuses){if(_intOrNull(s['tank_id'])==id)return s;}return null;}
  List<Map<String,dynamic>> get sources=>_sortedFuelUnits(ref?['tanks']).where((t)=>t['authorized']!=false&&const {'stationary','comboio','truck'}.contains('${t['tank_type']}')).toList();

  Future<void> chooseUnitAndFuel(Map<String,dynamic> tank) async {
    final id=_intOrNull(tank['id']);if(id==null)return;
    if(!offlineStore.online.value){
      if(offlineStore.lastTankId!=id){ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content:Text('Conecte-se à internet para trocar de unidade. A unidade atual continua reservada.')));return;}
    }else{
      try{final x=await api.claimUnitV30(id);if(x['ok']!=true){if(mounted)ScaffoldMessenger.of(context).showSnackBar(SnackBar(content:Text('${x['message']??'Esta unidade já está em uso.'}')));return;}await offlineStore.setLastTankId(id);currentUnit={'tank_id':id,'unit_code':tank['code'],'unit_name':tank['name']};}
      catch(e){if(mounted)ScaffoldMessenger.of(context).showSnackBar(SnackBar(content:Text(_friendlyError(e))));return;}
    }
    if(!mounted||ref==null)return;await Navigator.push(context,MaterialPageRoute(builder:(_)=>FuelingV23Screen(source:tank,ref:ref!,profile:widget.profile)));if(mounted)await load();
  }

  Future<void> newFueling() async {
    if(!canFuel){ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content:Text('Seu acesso para registrar abastecimentos está restrito pelo administrador.')));return;}
    if(ref==null){await load();if(ref==null)return;}final list=sources;if(list.isEmpty){ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content:Text('Nenhuma origem de combustível está liberada para este usuário.')));return;}
    final selected=await showModalBottomSheet<Map<String,dynamic>>(context:context,showDragHandle:true,isScrollControlled:true,builder:(ctx)=>SafeArea(child:ConstrainedBox(constraints:BoxConstraints(maxHeight:MediaQuery.of(ctx).size.height*.72),child:Column(mainAxisSize:MainAxisSize.min,crossAxisAlignment:CrossAxisAlignment.stretch,children:[
      const Padding(padding:EdgeInsets.fromLTRB(18,4,18,12),child:Text('Origem do combustível',style:TextStyle(fontWeight:FontWeight.w900,fontSize:19))),
      Flexible(child:ListView.separated(shrinkWrap:true,padding:const EdgeInsets.fromLTRB(12,4,12,18),itemCount:list.length,separatorBuilder:(_,__)=>const SizedBox(height:4),itemBuilder:(_,i){final t=list[i],id=_intOrNull(t['id']);final st=id==null?null:statusFor(id);final mine=st?['is_mine']==true,inUse=st?['in_use']==true;return Card(child:ListTile(contentPadding:const EdgeInsets.symmetric(horizontal:14,vertical:9),leading:Icon('${t['tank_type']}'=='stationary'?Icons.oil_barrel_outlined:Icons.local_shipping_outlined,color:_blue),title:Text('${t['code']} • ${t['name']}',style:const TextStyle(fontWeight:FontWeight.w900)),trailing:mine?const Icon(Icons.check_circle_rounded,color:Colors.green):inUse?const Icon(Icons.lock_outline_rounded):const Icon(Icons.chevron_right_rounded),onTap:()=>Navigator.pop(ctx,t)));}))
    ]))));
    if(!mounted||selected==null)return;await chooseUnitAndFuel(selected);
  }

  void openMine(){if(!canView){ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content:Text('Seu acesso aos registros está restrito pelo administrador.')));return;}Navigator.push(context,MaterialPageRoute(builder:(_)=>const MyFuelingsV29Screen()));}
  @override Widget build(BuildContext context){final code='${currentUnit['unit_code']??''}'.trim(),name='${currentUnit['unit_name']??''}'.trim();return Scaffold(appBar:AppBar(title:const Text('R&C Abastecimento',style:TextStyle(fontWeight:FontWeight.w900)),actions:[IconButton(onPressed:()=>_logoutToLogin(context,widget.onLogout),tooltip:'Sair',icon:const Icon(Icons.logout_rounded))]),body:loading?const Center(child:CircularProgressIndicator()):RefreshIndicator(onRefresh:load,child:ListView(physics:const AlwaysScrollableScrollPhysics(),padding:const EdgeInsets.all(20),children:[GreetingLine(name:'${widget.profile['display_name']}'),if(code.isNotEmpty)...[const SizedBox(height:8),Row(children:[const Icon(Icons.link_rounded,size:18,color:_blue),const SizedBox(width:6),Expanded(child:Text('Unidade atual: $code${name.isNotEmpty?' • $name':''}',style:const TextStyle(fontWeight:FontWeight.w800)))])],if(error!=null)...[const SizedBox(height:10),Text(error!,style:const TextStyle(color:Colors.redAccent))],const SizedBox(height:20),HomeActionCard(icon:Icons.local_gas_station_rounded,title:'Novo abastecimento',subtitle:'',onTap:newFueling),const SizedBox(height:12),HomeActionCard(icon:Icons.history_rounded,title:'Meus abastecimentos',subtitle:'',onTap:openMine)])));}
}
