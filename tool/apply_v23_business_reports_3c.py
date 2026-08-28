from pathlib import Path
p=Path("lib/main_online.dart")
s=p.read_text()

def replace_once(old,new,label):
    global s
    if old not in s:
        raise SystemExit(f"anchor missing: {label}")
    s=s.replace(old,new,1)

def replace_between(start,end,new,label):
    global s
    i=s.find(start)
    if i<0: raise SystemExit(f"start missing: {label}")
    j=s.find(end,i)
    if j<0: raise SystemExit(f"end missing: {label}")
    s=s[:i]+new+s[j:]

third_code=r'''class ThirdPartyAdminScreen extends StatefulWidget {
  const ThirdPartyAdminScreen({super.key});
  @override State<ThirdPartyAdminScreen> createState()=>_ThirdPartyAdminScreenState();
}
class _ThirdPartyAdminScreenState extends State<ThirdPartyAdminScreen> {
  List<Map<String,dynamic>>? items;List<Map<String,dynamic>> companies=[];bool loading=false;
  @override void initState(){super.initState();load();}
  Future<void> load() async {if(mounted)setState(()=>loading=true);try{final r=await Future.wait<dynamic>([api.referenceData(),api.managedCompanies()]);final c=List<Map<String,dynamic>>.from(r[1] as List<Map<String,dynamic>>)..removeWhere((x)=>x['active']==false);c.sort((a,b)=>'${a['name']}'.toLowerCase().compareTo('${b['name']}'.toLowerCase()));if(mounted)setState((){items=_rows(_map(r[0])['third_party_vehicles']);companies=c;});}catch(e){if(mounted)ScaffoldMessenger.of(context).showSnackBar(SnackBar(content:Text('Erro ao carregar equipamentos/empresas: ${_friendlyError(e)}')));}finally{if(mounted)setState(()=>loading=false);}}
  int? companyIdFor(String name){for(final c in companies){if('${c['name']}'.trim().toLowerCase()==name.trim().toLowerCase())return _intOrNull(c['id']);}return null;}
  String? companyNameFor(int? id){if(id==null)return null;for(final c in companies){if(_intOrNull(c['id'])==id)return '${c['name']}';}return null;}
  Future<void> edit([Map<String,dynamic>? item]) async {
    final plate=TextEditingController(text:'${item?['plate']??''}'),desc=TextEditingController(text:'${item?['description']??''}');int? companyId=companyIdFor('${item?['company_name']??''}');
    if(companies.isEmpty){ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content:Text('Nenhuma empresa vinculada cadastrada. Cadastre a empresa proprietária antes do equipamento.')));plate.dispose();desc.dispose();return;}
    final ok=await showDialog<bool>(context:context,builder:(ctx)=>StatefulBuilder(builder:(ctx,setD)=>AlertDialog(title:Text(item==null?'Cadastrar equipamento de terceiros':'Editar equipamento de terceiros'),content:SingleChildScrollView(child:Column(mainAxisSize:MainAxisSize.min,children:[
      DropdownButtonFormField<int>(value:companyId,isExpanded:true,decoration:const InputDecoration(labelText:'Empresa proprietária do equipamento *'),items:companies.map((c)=>DropdownMenuItem(value:_intOrNull(c['id']),child:Text('${c['name']}'))).toList(),onChanged:(v)=>setD(()=>companyId=v)),const SizedBox(height:8),
      TextField(controller:plate,textCapitalization:TextCapitalization.characters,decoration:const InputDecoration(labelText:'Placa (quando houver)')),const SizedBox(height:8),TextField(controller:desc,decoration:const InputDecoration(labelText:'Descrição / identificação *')),
      const SizedBox(height:8),const Align(alignment:Alignment.centerLeft,child:Text('A mão de obra é da própria empresa. O cadastro identifica apenas o equipamento contratado e sua empresa proprietária.',style:TextStyle(fontSize:12,color:Colors.black54))),
    ])),actions:[TextButton(onPressed:()=>Navigator.pop(ctx,false),child:const Text('Cancelar')),FilledButton(onPressed:()=>Navigator.pop(ctx,true),child:const Text('Salvar'))])));
    if(ok==true){if(companyId==null){ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content:Text('Preenchimento obrigatório: Empresa proprietária do equipamento')));}else if(plate.text.trim().isEmpty&&desc.text.trim().isEmpty){ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content:Text('Preenchimento obrigatório: Placa ou identificação do equipamento')));}else{try{await api.saveThirdParty(id:_intOrNull(item?['id']),plate:plate.text.trim(),company:companyNameFor(companyId),description:desc.text.trim(),driverName:null);await load();if(mounted)ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content:Text('Equipamento de terceiros salvo com sucesso ✓')));}catch(e){if(mounted)ScaffoldMessenger.of(context).showSnackBar(SnackBar(content:Text('Erro ao salvar equipamento: ${_friendlyError(e)}')));}}}
    plate.dispose();desc.dispose();
  }
  @override Widget build(BuildContext context)=>Scaffold(appBar:AppBar(title:const Text('Equipamentos de terceiros')),floatingActionButton:FloatingActionButton(onPressed:loading?null:()=>edit(),child:const Icon(Icons.add)),body:items==null?const Center(child:CircularProgressIndicator()):RefreshIndicator(onRefresh:load,child:ListView(padding:const EdgeInsets.all(12),children:[
    if(companies.isEmpty)const Card(child:ListTile(leading:Icon(Icons.business_outlined,color:_blue),title:Text('Nenhuma empresa proprietária cadastrada'),subtitle:Text('Cadastre a empresa na área “Empresas vinculadas” antes de cadastrar o equipamento de terceiros.'))),
    ...items!.map((x)=>Card(child:ListTile(title:Text('${_hasValue(x['plate'])?x['plate']:'Sem placa'} • ${x['description']??''}',style:const TextStyle(fontWeight:FontWeight.w900)),subtitle:Text('Empresa proprietária: ${x['company_name']??'Não informada'}'),onTap:loading?null:()=>edit(x),trailing:const Icon(Icons.edit_outlined)))),
  ])));
}
'''
i=s.find('class ThirdPartyAdminScreen')
if i<0: raise SystemExit('third party start missing')
s=s[:i]+third_code+'\n'

p.write_text(s)
print("business reports part 3c applied",len(s),"chars")
