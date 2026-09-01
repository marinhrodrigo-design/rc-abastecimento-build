from pathlib import Path

p=Path('lib/main_online.dart')
s=p.read_text()

old="""  Future<Position?> currentPosition() async {
    try{
      if(!await Geolocator.isLocationServiceEnabled())return null;
      var permission=await Geolocator.checkPermission();
      if(permission==LocationPermission.denied)permission=await Geolocator.requestPermission();
      if(permission==LocationPermission.denied||permission==LocationPermission.deniedForever)return null;
      return Geolocator.getCurrentPosition(locationSettings:const LocationSettings(accuracy:LocationAccuracy.high,timeLimit:Duration(seconds:12)));
    }catch(_){return null;}
  }

  String formatPlacemark(Placemark p){
    final street=[p.street,p.subLocality].where((v)=>v!=null&&v!.trim().isNotEmpty).map((v)=>v!.trim()).join(', ');
    final city=[p.locality,p.administrativeArea].where((v)=>v!=null&&v!.trim().isNotEmpty).map((v)=>v!.trim()).join(' - ');
    final tail=[city,p.postalCode].where((v)=>v!=null&&v!.trim().isNotEmpty).map((v)=>v!.trim()).join(', ');
    return [street,tail].where((v)=>v.trim().isNotEmpty).join(', ');
  }
"""
new="""  Future<Position?> currentPosition() async {
    try{
      if(!await Geolocator.isLocationServiceEnabled())return null;
      var permission=await Geolocator.checkPermission();
      if(permission==LocationPermission.denied)permission=await Geolocator.requestPermission();
      if(permission==LocationPermission.denied||permission==LocationPermission.deniedForever)return null;
      Position? best;
      for(var attempt=0;attempt<3;attempt++){
        try{
          final p=await Geolocator.getCurrentPosition(locationSettings:const LocationSettings(accuracy:LocationAccuracy.bestForNavigation,timeLimit:Duration(seconds:15)));
          if(best==null||p.accuracy<best.accuracy)best=p;
          if(p.accuracy<=15)return p;
        }catch(_){}
        if(attempt<2)await Future<void>.delayed(const Duration(seconds:1));
      }
      return best!=null&&best.accuracy<=15?best:null;
    }catch(_){return null;}
  }

  String formatPlacemark(Placemark p){
    final road=[p.thoroughfare,p.subThoroughfare].where((v)=>v!=null&&v!.trim().isNotEmpty).map((v)=>v!.trim()).join(', ');
    final street=road.isNotEmpty?road:'${p.street??''}'.trim();
    final district='${p.subLocality??''}'.trim();
    final city=[p.locality,p.administrativeArea].where((v)=>v!=null&&v!.trim().isNotEmpty).map((v)=>v!.trim()).join(' - ');
    final tail=[district,city,p.postalCode,p.country].where((v)=>v!=null&&v!.trim().isNotEmpty).map((v)=>v!.trim()).join(', ');
    return [street,tail].where((v)=>v.trim().isNotEmpty).join(', ');
  }
"""
if s.count(old)!=1: raise SystemExit('v43 location acquisition anchor missing')
s=s.replace(old,new,1)

old="""      final p=await currentPosition();
      if(p==null){if(mounted)ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content:Text('Não foi possível obter a localização atual. Ative o GPS e tente registrar novamente.')));return false;}
      capturedPosition=p;
      locationCapturedAt=DateTime.now().toUtc();
      locationAccuracyM=p.accuracy;
      String value='';
      try{final places=await placemarkFromCoordinates(p.latitude,p.longitude);if(places.isNotEmpty)value=formatPlacemark(places.first);}catch(_){}
      if(value.trim().isEmpty)value='GPS: ${p.latitude.toStringAsFixed(6)}, ${p.longitude.toStringAsFixed(6)}';
      location.text=value;
"""
new="""      final p=await currentPosition();
      if(p==null){if(mounted)ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content:Text('Não foi possível obter uma localização precisa (até 15 m). Ative a localização, aguarde o GPS estabilizar e tente novamente em uma área com melhor sinal.')));return false;}
      capturedPosition=p;
      locationCapturedAt=DateTime.now().toUtc();
      locationAccuracyM=p.accuracy;
      String value='';
      for(var attempt=0;attempt<2&&value.trim().isEmpty;attempt++){
        try{final places=await placemarkFromCoordinates(p.latitude,p.longitude);if(places.isNotEmpty)value=formatPlacemark(places.first);}catch(_){}
        if(value.trim().isEmpty&&attempt==0)await Future<void>.delayed(const Duration(milliseconds:700));
      }
      if(value.trim().isEmpty){if(mounted)ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content:Text('O GPS encontrou o ponto, mas não foi possível identificar o endereço. Verifique a internet e tente novamente.')));return false;}
      location.text=value;
"""
if s.count(old)!=1: raise SystemExit('v43 capture anchor missing')
s=s.replace(old,new,1)

old="Text('Localização: ${location.text.trim()}'),Text(locationMeta(),style:const TextStyle(fontSize:12,color:Colors.black54))"
new="Text('Endereço do abastecimento: ${location.text.trim()}',style:const TextStyle(fontWeight:FontWeight.w700)),if(capturedPosition!=null)Text('Coordenadas: ${capturedPosition!.latitude.toStringAsFixed(6)}, ${capturedPosition!.longitude.toStringAsFixed(6)}',style:const TextStyle(fontSize:12,color:Colors.black54)),Text(locationMeta(),style:const TextStyle(fontSize:12,color:Colors.black54))"
if s.count(old)!=1: raise SystemExit('v43 confirm address anchor missing')
s=s.replace(old,new,1)

old="""      InputDecorator(decoration:const InputDecoration(labelText:'Localização do abastecimento *',prefixIcon:Icon(Icons.location_on_outlined)),child:Text(location.text.trim().isEmpty?'Será capturada ao concluir o abastecimento.':location.text.trim(),softWrap:true)),
      Padding(padding:const EdgeInsets.only(top:5,bottom:12),child:Text(locationMeta(),style:const TextStyle(fontSize:11,color:Colors.black54))),
"""
new="""      InputDecorator(decoration:const InputDecoration(labelText:'Localização do abastecimento *',prefixIcon:Icon(Icons.location_on_outlined)),child:Text(location.text.trim().isEmpty?'Será capturada ao concluir o abastecimento.':location.text.trim(),softWrap:true)),
      const SizedBox(height:12),
"""
if s.count(old)!=1: raise SystemExit('v43 redundant location notice anchor missing')
s=s.replace(old,new,1)

old="""                  BalanceCard(tank: t),
                  const SizedBox(height: 18),
                  if (truck) ...[
"""
new="""                  BalanceCard(tank: t),
                  const SizedBox(height: 12),
                  const Card(child:ListTile(leading:Icon(Icons.location_on_outlined,color:Colors.orange),title:Text('Localização deve estar ativada',style:TextStyle(fontWeight:FontWeight.w900)),subtitle:Text('O ponto exato do abastecimento será capturado automaticamente ao concluir.'))),
                  const SizedBox(height: 12),
                  if (truck) ...[
"""
if s.count(old)!=1: raise SystemExit('v43 operational warning anchor missing')
s=s.replace(old,new,1)

old="""      const SizedBox(height:12),Row(children:[kpi(Icons.inventory_2_outlined,'Estoque atual',_fmtLiters(kpis['stock_liters'])),const SizedBox(width:7),kpi(Icons.water_drop_outlined,'Consumo hoje',_fmtLiters(kpis['fueling_liters_today']))]),const SizedBox(height:7),Row(children:[kpi(Icons.local_gas_station_outlined,'Abastecimentos hoje','${kpis['fueling_count_today']??0}'),const SizedBox(width:7),kpi(Icons.location_city_outlined,'Obras ativas','${kpis['active_works']??0}')]),
      const SizedBox(height:14),GridView.count(shrinkWrap:true,physics:const NeverScrollableScrollPhysics(),crossAxisCount:3,crossAxisSpacing:8,mainAxisSpacing:8,childAspectRatio:.92,children:actions),
"""
new="""      const SizedBox(height:12),Row(children:[kpi(Icons.inventory_2_outlined,'Estoque atual',_fmtLiters(kpis['stock_liters'])),const SizedBox(width:7),kpi(Icons.water_drop_outlined,'Consumo hoje',_fmtLiters(kpis['fueling_liters_today']))]),const SizedBox(height:7),Row(children:[kpi(Icons.local_gas_station_outlined,'Abastecimentos hoje','${kpis['fueling_count_today']??0}'),const SizedBox(width:7),kpi(Icons.location_city_outlined,'Obras ativas','${kpis['active_works']??0}')]),
      const SizedBox(height:12),const Card(child:ListTile(leading:Icon(Icons.location_on_outlined,color:Colors.orange),title:Text('Localização deve estar ativada',style:TextStyle(fontWeight:FontWeight.w900)),subtitle:Text('O ponto exato do abastecimento será capturado automaticamente ao concluir.'))),
      const SizedBox(height:10),GridView.count(shrinkWrap:true,physics:const NeverScrollableScrollPhysics(),crossAxisCount:3,crossAxisSpacing:8,mainAxisSpacing:8,childAspectRatio:.92,children:actions),
"""
if s.count(old)!=1: raise SystemExit('v43 admin warning anchor missing')
s=s.replace(old,new,1)

p.write_text(s)
checks=[
  "LocationAccuracy.bestForNavigation",
  "p.accuracy<=15",
  "Endereço do abastecimento:",
  "Coordenadas:",
  "Localização deve estar ativada",
  "O ponto exato do abastecimento será capturado automaticamente ao concluir.",
  "não foi possível identificar o endereço",
]
for x in checks:
    if x not in s: raise SystemExit('v43 missing marker: '+x)
if "Padding(padding:const EdgeInsets.only(top:5,bottom:12),child:Text(locationMeta()" in s:
    raise SystemExit('v43 redundant location notice remains')
print('V43_PRECISE_LOCATION_OK')
