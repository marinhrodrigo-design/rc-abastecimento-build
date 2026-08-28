from pathlib import Path
p=Path('lib/main_online.dart')
s=p.read_text()

def rep(old,new,label):
    global s
    if old not in s:
        raise SystemExit(f'anchor missing: {label}')
    s=s.replace(old,new,1)

# API RPC for admin-only work deletion.
rep(
"  Future<Map<String,dynamic>> finalizeWorkV23(int workId,String pdfPath) async => _map(await client.rpc('rca_finalize_work_v23',params:{'p_work_id':workId,'p_pdf_path':pdfPath}));\n",
"  Future<Map<String,dynamic>> finalizeWorkV23(int workId,String pdfPath) async => _map(await client.rpc('rca_finalize_work_v23',params:{'p_work_id':workId,'p_pdf_path':pdfPath}));\n  Future<Map<String,dynamic>> deleteWorkV25(int workId) async => _map(await client.rpc('rca_delete_work_v25',params:{'p_work_id':workId}));\n",
'api delete work')

anchor="""  Future<void> finalize(Map<String,dynamic> item) async {
"""
method=r'''  Future<void> deleteWork(Map<String,dynamic> item) async {
    if(!canEdit)return;
    final id=_intOrNull(item['id']);if(id==null)return;
    final ok=await showDialog<bool>(context:context,builder:(ctx)=>AlertDialog(
      title:const Text('Excluir obra?'),
      content:Text('Obra: ${item['name']}\n\nA obra será removida das telas operacionais e não poderá receber novos registros. Abastecimentos, transferências, PDFs, relatórios e rastreabilidade já existentes serão preservados.'),
      actions:[
        TextButton(onPressed:()=>Navigator.pop(ctx,false),child:const Text('Cancelar')),
        FilledButton.icon(
          style:FilledButton.styleFrom(backgroundColor:Colors.red.shade700),
          onPressed:()=>Navigator.pop(ctx,true),
          icon:const Icon(Icons.delete_outline_rounded),
          label:const Text('Excluir obra'),
        ),
      ],
    ));
    if(ok!=true||!mounted)return;
    setState(()=>busy=true);
    try{
      final result=await api.deleteWorkV25(id).timeout(const Duration(seconds:15));
      await load();
      if(!mounted)return;
      final movements=_intOrNull(result['movements_preserved'])??0;
      final reports=_intOrNull(result['reports_preserved'])??0;
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content:Text('Obra excluída ✓ Histórico preservado: $movements registro(s) e $reports relatório(s).')));
    }catch(e){
      if(mounted)ScaffoldMessenger.of(context).showSnackBar(SnackBar(content:Text('Não foi possível excluir a obra: ${_friendlyError(e)}')));
    }finally{if(mounted)setState(()=>busy=false);}
  }

'''+anchor
rep(anchor,method,'delete work handler')

old=r'''    Widget card(Map<String,dynamic> x,bool finalized)=>Card(child:Padding(padding:const EdgeInsets.all(4),child:ListTile(leading:CircleAvatar(child:Icon(finalized?Icons.task_alt_rounded:Icons.location_city_outlined)),title:Text('${x['name']}',style:const TextStyle(fontWeight:FontWeight.w900)),subtitle:Text('Empresa cliente/contratante: ${x['company_name']??companyName(x['contracting_company_id'])}\nResponsável: ${x['responsible']??'-'}\n${finalized?'Finalizada em ${_fmtDate(x['finalized_at'])}':'Ativa'}'),isThreeLine:true,onTap:finalized?null:(canEdit&&!busy?()=>edit(x):null),trailing:finalized?IconButton(tooltip:'Abrir Relatório Final',onPressed:_hasValue(x['final_report_pdf_path'])&&!busy?()async{final b=await api.downloadMedia('${x['final_report_pdf_path']}');if(b!=null)await Printing.sharePdf(bytes:b,filename:'RC-Relatorio-Final-${x['name']}.pdf');}:null,icon:const Icon(Icons.picture_as_pdf_outlined)):canFinalize?PopupMenuButton<String>(enabled:!busy,onSelected:(v){if(v=='edit')edit(x);if(v=='finalize')finalize(x);},itemBuilder:(_)=>[if(canEdit)const PopupMenuItem(value:'edit',child:Text('Editar obra')),const PopupMenuItem(value:'finalize',child:Text('Finalizar obra e gerar PDF'))]):const Icon(Icons.chevron_right_rounded))));
'''
new=r'''    Widget card(Map<String,dynamic> x,bool finalized)=>Card(child:Padding(padding:const EdgeInsets.all(4),child:ListTile(
      leading:CircleAvatar(child:Icon(finalized?Icons.task_alt_rounded:Icons.location_city_outlined)),
      title:Text('${x['name']}',style:const TextStyle(fontWeight:FontWeight.w900)),
      subtitle:Text('Empresa cliente/contratante: ${x['company_name']??companyName(x['contracting_company_id'])}\nResponsável: ${x['responsible']??'-'}\n${finalized?'Finalizada em ${_fmtDate(x['finalized_at'])}':'Ativa'}'),
      isThreeLine:true,
      onTap:finalized?null:(canEdit&&!busy?()=>edit(x):null),
      trailing:(canEdit||canFinalize)?PopupMenuButton<String>(
        enabled:!busy,
        onSelected:(v)async{
          if(v=='edit')await edit(x);
          if(v=='finalize')await finalize(x);
          if(v=='pdf'){
            final b=await api.downloadMedia('${x['final_report_pdf_path']}');
            if(b!=null)await Printing.sharePdf(bytes:b,filename:'RC-Relatorio-Final-${x['name']}.pdf');
          }
          if(v=='delete')await deleteWork(x);
        },
        itemBuilder:(_)=>[
          if(!finalized&&canEdit)const PopupMenuItem(value:'edit',child:ListTile(contentPadding:EdgeInsets.zero,leading:Icon(Icons.edit_outlined),title:Text('Editar obra'))),
          if(!finalized&&canFinalize)const PopupMenuItem(value:'finalize',child:ListTile(contentPadding:EdgeInsets.zero,leading:Icon(Icons.task_alt_outlined),title:Text('Finalizar obra e gerar PDF'))),
          if(finalized&&_hasValue(x['final_report_pdf_path']))const PopupMenuItem(value:'pdf',child:ListTile(contentPadding:EdgeInsets.zero,leading:Icon(Icons.picture_as_pdf_outlined),title:Text('Abrir Relatório Final'))),
          if(canEdit)const PopupMenuItem(value:'delete',child:ListTile(contentPadding:EdgeInsets.zero,leading:Icon(Icons.delete_outline_rounded,color:Colors.red),title:Text('Excluir obra',style:TextStyle(color:Colors.red)))),
        ],
      ):const Icon(Icons.chevron_right_rounded),
    )));
'''
rep(old,new,'works card menu')

p.write_text(s)
print('v25 admin delete work staged',len(s))
