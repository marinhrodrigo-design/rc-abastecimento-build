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

old="""          if (media.isNotEmpty) ...[
"""
new="""          if (fueling && _intOrNull(item['id']) != null) ...[
            const SizedBox(height: 14),
            SizedBox(width: double.infinity, child: FilledButton.icon(onPressed: () => Navigator.push(context, MaterialPageRoute(builder: (_) => MovementTraceV23Screen(movementId: _intOrNull(item['id'])!))), icon: const Icon(Icons.route_rounded), label: const Text('Rastrear origem do combustível'))),
          ],
          if (media.isNotEmpty) ...[
"""
replace_once(old,new,'movement trace button')

works_code=r'''class WorksAdminScreen extends StatefulWidget {
  final Map<String,dynamic> profile;
  const WorksAdminScreen({super.key,required this.profile});
  @override State<WorksAdminScreen> createState()=>_WorksAdminScreenState();
}
class _WorksAdminScreenState extends State<WorksAdminScreen> {
  List<Map<String,dynamic>>? items;
  List<Map<String,dynamic>> companies=[];
  bool busy=false;
  bool get canEdit=>widget.profile['is_admin']==true;
  bool get canFinalize=>widget.profile['is_admin']==true||widget.profile['is_manager']==true;
  @override void initState(){super.initState();load();}
  Future<void> load() async {try{final works=await api.worksCatalogV23().timeout(const Duration(seconds:15));var c=<Map<String,dynamic>>[];if(canEdit){try{c=await api.managedCompanies().timeout(const Duration(seconds:15));}catch(e){if(mounted)ScaffoldMessenger.of(context).showSnackBar(SnackBar(content:Text('As obras foram carregadas, mas houve erro ao carregar as empresas: ${_friendlyError(e)}')));}}c.sort((a,b)=>'${a['name']}'.toLowerCase().compareTo('${b['name']}'.toLowerCase()));if(mounted)setState((){items=works;companies=c;});}catch(e){if(mounted){setState(()=>items??=const <Map<String,dynamic>>[]);ScaffoldMessenger.of(context).showSnackBar(SnackBar(content:Text('Erro ao carregar obras: ${_friendlyError(e)}')));}}}
  Future<void> openCompanies() async {await Navigator.push(context,MaterialPageRoute(builder:(_)=>const CompaniesAdminScreen()));if(mounted)await load();}
  String companyName(dynamic id){final target=_intOrNull(id);for(final c in companies){if(_intOrNull(c['id'])==target)return '${c['name']}';}return 'Sem empresa vinculada';}

  Future<void> edit([Map<String,dynamic>? item]) async {
    if(!canEdit){ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content:Text('Somente Admin pode cadastrar ou editar os dados da obra.')));return;}
    final name=TextEditingController(text:'${item?['name']??''}'),location=TextEditingController(text:'${item?['location']??''}'),responsible=TextEditingController(text:'${item?['responsible']??''}');int? companyId=_intOrNull(item?['contracting_company_id']);
    final ok=await showDialog<bool>(context:context,builder:(ctx)=>StatefulBuilder(builder:(ctx,setD)=>AlertDialog(title:Text(item==null?'Cadastrar obra':'Editar obra'),content:SingleChildScrollView(child:Column(mainAxisSize:MainAxisSize.min,children:[
      TextField(controller:name,decoration:const InputDecoration(labelText:'Nome da obra *')),const SizedBox(height:8),TextField(controller:responsible,decoration:const InputDecoration(labelText:'Responsável da obra *')),const SizedBox(height:8),
      DropdownButtonFormField<int>(value:companyId,isExpanded:true,decoration:const InputDecoration(labelText:'Empresa da obra *'),items:companies.where((x)=>x['active']!=false).map((c)=>DropdownMenuItem(value:_intOrNull(c['id']),child:Text('${c['name']}'))).toList(),onChanged:(v)=>setD(()=>companyId=v)),
      const SizedBox(height:8),TextField(controller:location,decoration:const InputDecoration(labelText:'Local')),
    ])),actions:[TextButton(onPressed:()=>Navigator.pop(ctx,false),child:const Text('Cancelar')),FilledButton(onPressed:()=>Navigator.pop(ctx,true),child:const Text('Salvar'))])));
    if(ok==true){if(name.text.trim().isEmpty){ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content:Text('Preenchimento obrigatório: Nome da obra')));}else if(responsible.text.trim().isEmpty){ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content:Text('Preenchimento obrigatório: Responsável da obra')));}else if(companyId==null){ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content:Text('Preenchimento obrigatório: Empresa da obra')));}else{setState(()=>busy=true);try{await api.saveWork(id:_intOrNull(item?['id']),name:name.text.trim(),location:location.text.trim(),responsible:responsible.text.trim(),companyId:companyId).timeout(const Duration(seconds:15));await load();if(mounted)ScaffoldMessenger.of(context).showSnackBar(SnackBar(content:Text(item==null?'Obra cadastrada com sucesso ✓':'Obra atualizada com sucesso ✓')));}catch(e){if(mounted)ScaffoldMessenger.of(context).showSnackBar(SnackBar(content:Text('Erro ao salvar obra: ${_friendlyError(e)}')));}finally{if(mounted)setState(()=>busy=false);}}}
    name.dispose();location.dispose();responsible.dispose();
  }

  Future<void> finalize(Map<String,dynamic> item) async {
    if(!canFinalize)return;
    if(!offlineStore.online.value){ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content:Text('Conexão com a internet obrigatória para gerar, armazenar e finalizar o Relatório Final da obra.')));return;}
    final id=_intOrNull(item['id']);if(id==null)return;
    final ok=await showDialog<bool>(context:context,builder:(ctx)=>AlertDialog(title:const Text('Finalizar obra?'),content:Text('Obra: ${item['name']}\nResponsável: ${item['responsible']??'-'}\n\nApós a confirmação, o Relatório Final em PDF será gerado e armazenado imediatamente. Novos abastecimentos não poderão mais ser vinculados a esta obra.'),actions:[TextButton(onPressed:()=>Navigator.pop(ctx,false),child:const Text('Cancelar')),FilledButton(onPressed:()=>Navigator.pop(ctx,true),child:const Text('Finalizar obra'))]));
    if(ok!=true||!mounted)return;
    setState(()=>busy=true);
    try{
      final snapshot=await api.workFinalReportDataV23(id).timeout(const Duration(seconds:20));
      final now=DateTime.now().toUtc().toIso8601String();_map(snapshot['work'])['finalized_at']=now;_map(snapshot['work'])['status']='finalized';snapshot['generated_at']=now;
      final bytes=await WorkFinalPdf.build(snapshot);
      final path=await api.uploadBytes(bytes,'relatorio_final_obra_$id',mime:'application/pdf');
      if(path.startsWith('local://'))throw Exception('O PDF não foi enviado ao servidor. Verifique a conexão e tente novamente.');
      final result=await api.finalizeWorkV23(id,path).timeout(const Duration(seconds:20));
      await load();
      if(!mounted)return;
      final share=await showDialog<bool>(context:context,builder:(ctx)=>AlertDialog(title:const Text('Obra finalizada ✓'),content:Text('Obra finalizada e Relatório Final gerado com sucesso ✓\n\nRelatório: ${result['report_id']??'-'}'),actions:[TextButton(onPressed:()=>Navigator.pop(ctx,false),child:const Text('Fechar')),FilledButton.icon(onPressed:()=>Navigator.pop(ctx,true),icon:const Icon(Icons.share_outlined),label:const Text('Compartilhar PDF'))]));
      if(share==true)await Printing.sharePdf(bytes:bytes,filename:'RC-Relatorio-Final-${item['name']}.pdf');
    }catch(e){if(mounted)ScaffoldMessenger.of(context).showSnackBar(SnackBar(content:Text('Não foi possível finalizar a obra: ${_friendlyError(e)}')));}
    finally{if(mounted)setState(()=>busy=false);}
  }

  @override Widget build(BuildContext context){
    final list=items??const <Map<String,dynamic>>[],active=list.where((x)=>'${x['status']}'=='active').toList(),finished=list.where((x)=>'${x['status']}'=='finalized').toList();
    Widget card(Map<String,dynamic> x,bool finalized)=>Card(child:Padding(padding:const EdgeInsets.all(4),child:ListTile(leading:CircleAvatar(child:Icon(finalized?Icons.task_alt_rounded:Icons.location_city_outlined)),title:Text('${x['name']}',style:const TextStyle(fontWeight:FontWeight.w900)),subtitle:Text('Empresa da obra: ${x['company_name']??companyName(x['contracting_company_id'])}\nResponsável: ${x['responsible']??'-'}\n${finalized?'Finalizada em ${_fmtDate(x['finalized_at'])}':'Ativa'}'),isThreeLine:true,onTap:finalized?null:(canEdit&&!busy?()=>edit(x):null),trailing:finalized?IconButton(tooltip:'Abrir Relatório Final',onPressed:_hasValue(x['final_report_pdf_path'])&&!busy?()async{final b=await api.downloadMedia('${x['final_report_pdf_path']}');if(b!=null)await Printing.sharePdf(bytes:b,filename:'RC-Relatorio-Final-${x['name']}.pdf');}:null,icon:const Icon(Icons.picture_as_pdf_outlined)):canFinalize?PopupMenuButton<String>(enabled:!busy,onSelected:(v){if(v=='edit')edit(x);if(v=='finalize')finalize(x);},itemBuilder:(_)=>[if(canEdit)const PopupMenuItem(value:'edit',child:Text('Editar obra')),const PopupMenuItem(value:'finalize',child:Text('Finalizar obra e gerar PDF'))]):const Icon(Icons.chevron_right_rounded))));
    return Scaffold(appBar:AppBar(title:const Text('Obras')),floatingActionButton:canEdit?FloatingActionButton(onPressed:busy?null:()=>companies.isEmpty?openCompanies():edit(),child:const Icon(Icons.add)):null,body:items==null?const Center(child:CircularProgressIndicator()):RefreshIndicator(onRefresh:load,child:ListView(padding:const EdgeInsets.fromLTRB(12,12,12,90),children:[
      if(companies.isEmpty)Card(child:Padding(padding:const EdgeInsets.all(14),child:Column(children:[const ListTile(contentPadding:EdgeInsets.zero,leading:Icon(Icons.info_outline_rounded),title:Text('Cadastre uma empresa vinculada'),subtitle:Text('A empresa da obra é independente do cadastro institucional e continuará disponível mesmo depois da finalização da obra.')),SizedBox(width:double.infinity,child:FilledButton.icon(onPressed:openCompanies,icon:const Icon(Icons.add_business_outlined),label:const Text('Cadastrar empresa')))]))),
      Text('Obras ativas (${active.length})',style:const TextStyle(fontSize:17,fontWeight:FontWeight.w900)),const SizedBox(height:6),if(active.isEmpty)const Card(child:ListTile(title:Text('Nenhuma obra ativa.'))),...active.map((x)=>card(x,false)),
      const SizedBox(height:14),Text('Obras finalizadas (${finished.length})',style:const TextStyle(fontSize:17,fontWeight:FontWeight.w900)),const SizedBox(height:6),if(finished.isEmpty)const Card(child:ListTile(title:Text('Nenhuma obra finalizada.'))),...finished.map((x)=>card(x,true)),
    ])));
  }
}

'''
replace_between('class WorksAdminScreen','class MachinesAdminScreen',works_code,'works screen')

p.write_text(s)
print("business reports part 3b applied",len(s),"chars")
