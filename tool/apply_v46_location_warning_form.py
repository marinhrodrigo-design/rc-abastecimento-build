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
if marker not in s:
    raise SystemExit('v46 warning marker missing')
# O aviso específico deve estar dentro da tela FuelingV23Screen, antes do campo Origem do combustível.
start=s.index('class FuelingV23Screen')
end=s.index('class ',start+10)
chunk=s[start:end]
assert "Localização deve estar ativada" in chunk
assert marker in chunk
assert chunk.index("Localização deve estar ativada") < chunk.index("labelText:'Origem do combustível'")
print('V46_LOCATION_WARNING_FORM_OK')
