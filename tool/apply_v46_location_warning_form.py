from pathlib import Path

p=Path('lib/main_online.dart')
s=p.read_text()

old="""    return Scaffold(appBar:AppBar(title:Text(widget.source['tank_type']=='truck'?'Abastecer como comboio':'Novo abastecimento')),body:SafeArea(child:ListView(padding:const EdgeInsets.fromLTRB(18,18,18,36),children:[
      InputDecorator(decoration:const InputDecoration(labelText:'Origem do combustível',prefixIcon:Icon(Icons.local_gas_station_outlined)),child:Text('${widget.source['code']} • ${widget.source['name']} • ${sourceTypeLabel()}',style:const TextStyle(fontWeight:FontWeight.w800))),const SizedBox(height:10),
"""
new="""    return Scaffold(appBar:AppBar(title:Text(widget.source['tank_type']=='truck'?'Abastecer como comboio':'Novo abastecimento')),body:SafeArea(child:ListView(padding:const EdgeInsets.fromLTRB(18,18,18,36),children:[
      const Card(child:ListTile(leading:Icon(Icons.location_on_outlined,color:Colors.orange),title:Text('Localização deve estar ativada',style:TextStyle(fontWeight:FontWeight.w900)),subtitle:Text('A localização será buscada automaticamente primeiro. Se não for possível, o endereço poderá ser informado manualmente.'))),
      const SizedBox(height:12),
      InputDecorator(decoration:const InputDecoration(labelText:'Origem do combustível',prefixIcon:Icon(Icons.local_gas_station_outlined)),child:Text('${widget.source['code']} • ${widget.source['name']} • ${sourceTypeLabel()}',style:const TextStyle(fontWeight:FontWeight.w800))),const SizedBox(height:10),
"""
if s.count(old)!=1:
    raise SystemExit(f'v46 fueling form anchor unexpected: {s.count(old)}')
s=s.replace(old,new,1)

p.write_text(s)

marker="A localização será buscada automaticamente primeiro. Se não for possível, o endereço poderá ser informado manualmente."
warning="Localização deve estar ativada"
origin="labelText:'Origem do combustível'"
if marker not in s:
    raise SystemExit('v46 warning marker missing')
if warning not in s:
    raise SystemExit('v46 warning title missing')
# Validação robusta: o cartão foi inserido exatamente no Scaffold do Novo abastecimento,
# imediatamente antes do campo Origem do combustível.
scaffold_anchor="return Scaffold(appBar:AppBar(title:Text(widget.source['tank_type']=='truck'?'Abastecer como comboio':'Novo abastecimento'))"
start=s.index(scaffold_anchor)
origin_pos=s.index(origin,start)
warning_pos=s.rfind(warning,start,origin_pos)
marker_pos=s.rfind(marker,start,origin_pos)
assert warning_pos >= start
assert marker_pos >= start
assert warning_pos < origin_pos
assert marker_pos < origin_pos
assert origin_pos-warning_pos < 900
print('V46_LOCATION_WARNING_FORM_OK')
