from pathlib import Path

p=Path('lib/main_online.dart')
s=p.read_text()

old="""      const Card(child:ListTile(leading:Icon(Icons.location_on_outlined,color:Colors.orange),title:Text('Localização deve estar ativada',style:TextStyle(fontWeight:FontWeight.w900)),subtitle:Text('A localização será buscada automaticamente primeiro. Se não for possível, o endereço poderá ser informado manualmente.'))),"""
new="""      const Card(child:ListTile(leading:Icon(Icons.location_on_outlined,color:Colors.orange),title:Text('Localização deve estar ativada',style:TextStyle(fontWeight:FontWeight.w900)))),"""
assert old in s
s=s.replace(old,new,1)

old="""    final sm=selected(ms,machine),st=selected(ts,third),sw=selected(ws,work),manualThird=machine==null&&third==null&&(thirdDescription.text.trim().isNotEmpty||thirdPlate.text.trim().isNotEmpty),hasPlate=_hasValue(sm?['placa'])||_hasValue(st?['plate'])||manualThird;"""
new="""    final sm=selected(ms,machine),st=selected(ts,third),sw=selected(ws,work),manualThird=machine==null&&third==-1,hasPlate=_hasValue(sm?['placa'])||_hasValue(st?['plate'])||(manualThird&&_hasValue(thirdPlate.text));"""
assert old in s
s=s.replace(old,new,1)

old="""      DropdownButtonFormField<int?>(value:machine,decoration:const InputDecoration(labelText:'Ativo'),items:[const DropdownMenuItem<int?>(value:null,child:Text('Nenhum')),...ms.map((x)=>DropdownMenuItem<int?>(value:_intOrNull(x['id']),child:Text('${x['numeroAtivo']} • ${x['modelo']??''}')))],onChanged:(saving||third!=null||manualThird)?null:(v)=>setState((){machine=v;if(v!=null){third=null;thirdPlate.clear();thirdDescription.clear();}})),const SizedBox(height:8),
      DropdownButtonFormField<int?>(value:third,decoration:const InputDecoration(labelText:'Selecionar equipamento de terceiros cadastrado (opcional)'),items:[const DropdownMenuItem<int?>(value:null,child:Text('Nenhum')),...ts.map((x)=>DropdownMenuItem<int?>(value:_intOrNull(x['id']),child:Text('${_hasValue(x['plate'])?x['plate']:'Sem placa'} • ${x['description']??''}')))],onChanged:(saving||machine!=null)?null:(v){setState((){third=v;if(v!=null)machine=null;});final t=selected(ts,v);if(t!=null){thirdPlate.text='${t['plate']??''}';thirdDescription.text='${t['description']??''}';}else{thirdPlate.clear();thirdDescription.clear();}}),
      const SizedBox(height:8),TextField(controller:thirdDescription,enabled:!saving&&third==null&&machine==null,onChanged:(_)=>setState((){}),decoration:const InputDecoration(labelText:'Equipamento de terceiros')),
      const SizedBox(height:8),TextField(controller:thirdPlate,enabled:!saving&&third==null&&machine==null,onChanged:(_)=>setState((){}),decoration:const InputDecoration(labelText:'Placa/Identificação')),
      const Padding(padding:EdgeInsets.only(top:6,bottom:10),child:Text('Selecione um ativo, escolha um equipamento de terceiros cadastrado ou preencha os dados do equipamento de terceiros.',style:TextStyle(fontSize:12,color:Colors.black54))),"""
new="""      DropdownButtonFormField<int?>(value:machine,isExpanded:true,decoration:const InputDecoration(labelText:'Ativo próprio'),items:[const DropdownMenuItem<int?>(value:null,child:Text('Nenhum')),...ms.map((x){final label='${x['numeroAtivo']??'-'} • ${_hasValue(x['placa'])?x['placa']:'Sem placa'} • ${x['modelo']??'-'}';return DropdownMenuItem<int?>(value:_intOrNull(x['id']),child:Text(label,maxLines:1,overflow:TextOverflow.ellipsis));})],onChanged:(saving||third!=null)?null:(v)=>setState((){machine=v;if(v!=null){third=null;thirdPlate.clear();thirdDescription.clear();}})),const SizedBox(height:8),
      DropdownButtonFormField<int?>(value:third,isExpanded:true,decoration:const InputDecoration(labelText:'Equipamento de terceiros'),items:[const DropdownMenuItem<int?>(value:null,child:Text('Nenhum')),const DropdownMenuItem<int?>(value:-1,child:Text('Não cadastrado')),...ts.map((x)=>DropdownMenuItem<int?>(value:_intOrNull(x['id']),child:Text('${_hasValue(x['plate'])?x['plate']:'Sem placa'} • ${x['description']??''}',maxLines:1,overflow:TextOverflow.ellipsis)))],onChanged:(saving||machine!=null)?null:(v){setState((){third=v;if(v!=null)machine=null;});final t=v==-1?null:selected(ts,v);if(t!=null){thirdPlate.text='${t['plate']??''}';thirdDescription.text='${t['description']??''}';}else{thirdPlate.clear();thirdDescription.clear();}}),
      if(manualThird)...[
        const SizedBox(height:8),TextField(controller:thirdDescription,enabled:!saving,onChanged:(_)=>setState((){}),decoration:const InputDecoration(labelText:'Descrição do equipamento')),
        const SizedBox(height:8),TextField(controller:thirdPlate,enabled:!saving,onChanged:(_)=>setState((){}),decoration:const InputDecoration(labelText:'Placa/Identificação *')),
        const Padding(padding:EdgeInsets.only(top:6,bottom:10),child:Text('Informe a descrição e a placa ou identificação do equipamento não cadastrado.',style:TextStyle(fontSize:12,color:Colors.black54))),
      ],"""
assert old in s
s=s.replace(old,new,1)

old="""    final manualThird=machine==null&&third==null&&(thirdDescription.text.trim().isNotEmpty||thirdPlate.text.trim().isNotEmpty);
    if(machine==null&&third==null&&!manualThird){requiredMessage('Ativo ou Equipamento de terceiros');return;}"""
new="""    final manualThird=machine==null&&third==-1;
    if(machine==null&&third==null){requiredMessage('Ativo ou Equipamento de terceiros');return;}
    if(manualThird&&thirdPlate.text.trim().isEmpty){requiredMessage('Placa/Identificação do equipamento não cadastrado');return;}"""
assert old in s
s=s.replace(old,new,1)

old="""      final manualThird=machine==null&&third==null&&thirdPlate.text.trim().isNotEmpty;
      final r=await api.fuelingV22(sourceTankId:_intOrNull(widget.source['id'])!,workId:work,machineId:machine,thirdId:third,thirdPartyPlate:manualThird?thirdPlate.text.trim():null,thirdPartyDescription:manualThird?thirdDescription.text.trim():null,"""
new="""      final manualThird=machine==null&&third==-1;
      final r=await api.fuelingV22(sourceTankId:_intOrNull(widget.source['id'])!,workId:work,machineId:machine,thirdId:manualThird?null:third,thirdPartyPlate:manualThird?thirdPlate.text.trim():null,thirdPartyDescription:manualThird&&thirdDescription.text.trim().isNotEmpty?thirdDescription.text.trim():null,"""
assert old in s
s=s.replace(old,new,1)

p.write_text(s)
print('VALIDACAO_PATCH_V49_OK')
