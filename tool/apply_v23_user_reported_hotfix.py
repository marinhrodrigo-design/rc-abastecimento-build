from pathlib import Path
p=Path('lib/main_online.dart')
s=p.read_text()
old="""  @override Widget build(BuildContext context)=>Scaffold(
    appBar:AppBar(title:Text(selectionMode?'${selectedCodes.length} selecionado(s)':'Meus registros'),actions:[if(selectionMode)IconButton(onPressed:busy?null:exportPdf,tooltip:'Exportar selecionados em PDF',icon:const Icon(Icons.picture_as_pdf_outlined)),if(selectionMode)IconButton(onPressed:busy?null:clearSelection,tooltip:'Cancelar seleção',icon:const Icon(Icons.close_rounded))]),
    body:items==null&&loading?const Center(child:CircularProgressIndicator()):items==null&&loadError!=null?Center(child:Padding(padding:const EdgeInsets.all(24),child:Column(mainAxisSize:MainAxisSize.min,children:[const Icon(Icons.cloud_off_rounded,size:56,color:_blue),const SizedBox(height:16),Text(loadError!,textAlign:TextAlign.center),const SizedBox(height:16),FilledButton.icon(onPressed:()=>load(),icon:const Icon(Icons.refresh_rounded),label:const Text('Tentar novamente'))])):recordList(),
  );
}"""
new="""  Widget bodyContent(){
    if(items==null&&loading)return const Center(child:CircularProgressIndicator());
    if(items==null&&loadError!=null){
      return Center(child:Padding(padding:const EdgeInsets.all(24),child:Column(mainAxisSize:MainAxisSize.min,children:[
        const Icon(Icons.cloud_off_rounded,size:56,color:_blue),const SizedBox(height:16),
        Text(loadError!,textAlign:TextAlign.center),const SizedBox(height:16),
        FilledButton.icon(onPressed:()=>load(),icon:const Icon(Icons.refresh_rounded),label:const Text('Tentar novamente')),
      ])));
    }
    return recordList();
  }

  @override Widget build(BuildContext context)=>Scaffold(
    appBar:AppBar(title:Text(selectionMode?'${selectedCodes.length} selecionado(s)':'Meus registros'),actions:[if(selectionMode)IconButton(onPressed:busy?null:exportPdf,tooltip:'Exportar selecionados em PDF',icon:const Icon(Icons.picture_as_pdf_outlined)),if(selectionMode)IconButton(onPressed:busy?null:clearSelection,tooltip:'Cancelar seleção',icon:const Icon(Icons.close_rounded))]),
    body:bodyContent(),
  );
}"""
if old not in s: raise SystemExit('Meus registros hotfix anchor missing')
p.write_text(s.replace(old,new,1))
print('user reported hotfix applied')
