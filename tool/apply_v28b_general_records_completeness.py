from pathlib import Path
p=Path('lib/main_online.dart')
s=p.read_text()

def rep(old,new,label):
    global s
    if old not in s:
        raise SystemExit(f'anchor missing: {label}')
    s=s.replace(old,new,1)

rep(
"  DateTime? start=DateTime.now().subtract(const Duration(days:30)); DateTime? end=DateTime.now().add(const Duration(days:1)); int? workId; String? type; String? fuelType;",
"  DateTime? start; DateTime? end; int? workId; int? companyId; String? type; String? fuelType;",
'general defaults + company state')

rep(
"sourceCode:source.text.trim(),invoice:invoice.text.trim(),responsible:responsible.text.trim(),fuelType:fuelType,limit:1000)",
"sourceCode:source.text.trim(),invoice:invoice.text.trim(),responsible:responsible.text.trim(),companyId:companyId,fuelType:fuelType,limit:1000)",
'general company filter api')

rep(
"start=null;end=null;workId=null;type=null;fuelType=null;",
"start=null;end=null;workId=null;companyId=null;type=null;fuelType=null;",
'clear company filter')

anchor="  String workLabel(){if(workId==null)return'Todas as obras';for(final w in works){if(_intOrNull(w['id'])==workId)return'${w['name']}';}return'Obra selecionada';}\n"
rep(anchor,anchor+"  List<Map<String,dynamic>> clientCompanies(){final seen=<int>{};final out=<Map<String,dynamic>>[];for(final w in works){final id=_intOrNull(w['contracting_company_id']);if(id!=null&&seen.add(id))out.add({'id':id,'name':w['company_name']??'Empresa $id'});}out.sort((a,b)=>'${a['name']}'.compareTo('${b['name']}'));return out;}\n",'company choices helper')

rep(
"      SizedBox(width:double.infinity,child:OutlinedButton.icon(onPressed:chooseWork,icon:const Icon(Icons.location_city_outlined),label:Text('Obra: ${workLabel()}'))),const SizedBox(height:8),\n      TextField(controller:asset",
"      SizedBox(width:double.infinity,child:OutlinedButton.icon(onPressed:chooseWork,icon:const Icon(Icons.location_city_outlined),label:Text('Obra: ${workLabel()}'))),const SizedBox(height:8),\n      DropdownButtonFormField<int?>(value:companyId,isExpanded:true,decoration:const InputDecoration(labelText:'Empresa cliente / contratante',prefixIcon:Icon(Icons.business_outlined)),items:[const DropdownMenuItem<int?>(value:null,child:Text('Todas as empresas')),...clientCompanies().map((c)=>DropdownMenuItem<int?>(value:_intOrNull(c['id']),child:Text('${c['name']}')))],onChanged:(v)=>setState(()=>companyId=v)),const SizedBox(height:8),\n      TextField(controller:asset",
'company filter ui')

rep(
"if(_rows(summary['fuel_breakdown']).isNotEmpty)...[const SizedBox(height:12),const Text('Por combustível',style:TextStyle(fontWeight:FontWeight.w900)),const SizedBox(height:5),..._rows(summary['fuel_breakdown']).map((x)=>Padding(padding:const EdgeInsets.only(bottom:3),child:Row(children:[Expanded(child:Text('${x['fuel_type']}')),Text(_fmtLiters(x['liters']),style:const TextStyle(fontWeight:FontWeight.w800))])) )],const SizedBox(height:9),const Text('Transferências",
"if(_rows(summary['fuel_breakdown']).isNotEmpty)...[const SizedBox(height:12),const Text('Por combustível',style:TextStyle(fontWeight:FontWeight.w900)),const SizedBox(height:5),..._rows(summary['fuel_breakdown']).map((x)=>Padding(padding:const EdgeInsets.only(bottom:3),child:Row(children:[Expanded(child:Text('${x['fuel_type']}')),Text(_fmtLiters(x['liters']),style:const TextStyle(fontWeight:FontWeight.w800))])) )],if(_rows(summary['asset_breakdown']).isNotEmpty)...[const SizedBox(height:12),const Text('Por ativo / equipamento',style:TextStyle(fontWeight:FontWeight.w900)),const SizedBox(height:5),..._rows(summary['asset_breakdown']).map((x)=>Padding(padding:const EdgeInsets.only(bottom:3),child:Row(children:[Expanded(child:Text('${x['asset']}')),Text('${_fmtLiters(x['liters'])} • ${x['count']??0} reg.',style:const TextStyle(fontWeight:FontWeight.w800))])) )],const SizedBox(height:9),const Text('Transferências",
'asset breakdown ui')

p.write_text(s)
print('v28b general records completeness staged',len(s))
