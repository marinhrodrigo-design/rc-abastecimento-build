from pathlib import Path
p=Path('lib/main_online.dart')
s=p.read_text()

def rep(old,new,label,count=1):
    global s
    if old not in s:
        raise SystemExit(f'anchor missing: {label}')
    s=s.replace(old,new,count)

anchor="const _blue = Color(0xFF123A78);"
if anchor not in s:
    anchor="String _fmtLiters(dynamic value)"
    i=s.find(anchor)
    if i<0: raise SystemExit('helper insertion anchor missing')
    helper="""PreferredSizeWidget _v30AppBar(String title,String description,{List<Widget>? actions})=>AppBar(\n  title:Text(title,maxLines:1,overflow:TextOverflow.ellipsis),\n  actions:actions,\n  bottom:PreferredSize(\n    preferredSize:const Size.fromHeight(34),\n    child:Container(width:double.infinity,padding:const EdgeInsets.fromLTRB(16,0,16,9),child:Text(description,maxLines:2,overflow:TextOverflow.ellipsis,style:const TextStyle(fontSize:11.5,color:Colors.black54,fontWeight:FontWeight.w500))),\n  ),\n);\n\n"""
    s=s[:i]+helper+s[i:]
else:
    helper="""\nPreferredSizeWidget _v30AppBar(String title,String description,{List<Widget>? actions})=>AppBar(\n  title:Text(title,maxLines:1,overflow:TextOverflow.ellipsis),\n  actions:actions,\n  bottom:PreferredSize(\n    preferredSize:const Size.fromHeight(34),\n    child:Container(width:double.infinity,padding:const EdgeInsets.fromLTRB(16,0,16,9),child:Text(description,maxLines:2,overflow:TextOverflow.ellipsis,style:const TextStyle(fontSize:11.5,color:Colors.black54,fontWeight:FontWeight.w500))),\n  ),\n);\n"""
    s=s.replace(anchor,anchor+helper,1)

old="Widget quick(IconData icon,String title,String subtitle,VoidCallback onTap)=>Card(margin:EdgeInsets.zero,child:InkWell(onTap:onTap,borderRadius:BorderRadius.circular(12),child:Padding(padding:const EdgeInsets.symmetric(horizontal:7,vertical:11),child:Column(mainAxisAlignment:MainAxisAlignment.center,children:[Icon(icon,color:_blue,size:29),const SizedBox(height:7),Text(title,textAlign:TextAlign.center,maxLines:2,overflow:TextOverflow.ellipsis,style:const TextStyle(fontWeight:FontWeight.w900,fontSize:12.2)),const SizedBox(height:3),Text(subtitle,textAlign:TextAlign.center,maxLines:2,overflow:TextOverflow.ellipsis,style:const TextStyle(fontSize:9.5,color:Colors.black54))]))));"
new="Widget quick(IconData icon,String title,String subtitle,VoidCallback onTap)=>Card(margin:EdgeInsets.zero,child:InkWell(onTap:onTap,borderRadius:BorderRadius.circular(12),child:Padding(padding:const EdgeInsets.symmetric(horizontal:8,vertical:14),child:Column(mainAxisAlignment:MainAxisAlignment.center,children:[Icon(icon,color:_blue,size:31),const SizedBox(height:10),Text(title,textAlign:TextAlign.center,maxLines:3,overflow:TextOverflow.ellipsis,style:const TextStyle(fontWeight:FontWeight.w900,fontSize:13.2,height:1.15))]))));"
rep(old,new,'home quick cards')

repls=[
("appBar:AppBar(title:const Text('Recebimento de combustível / NF'))","appBar:_v30AppBar('Recebimento de combustível / NF','Registre a entrada do combustível com a Nota Fiscal e as evidências.')",'receipt'),
("appBar:AppBar(title:const Text('Transferir'))","appBar:_v30AppBar('Transferir','Transfira combustível entre unidades mantendo saldo e rastreabilidade.')",'transfer'),
("appBar:AppBar(title:Text(widget.source['tank_type']=='truck'?'Abastecer como comboio':'Novo abastecimento'))","appBar:_v30AppBar(widget.source['tank_type']=='truck'?'Abastecer como comboio':'Novo abastecimento','Registre o abastecimento do equipamento com todos os dados e evidências.')",'fueling'),
("appBar:AppBar(title:const Text('Registro Diário'))","appBar:_v30AppBar('Registro Diário','Acompanhe todas as movimentações do dia selecionado.')",'daily'),
("appBar:AppBar(title:const Text('Relatórios'))","appBar:_v30AppBar('Relatórios','Consulte e exporte os PDFs e relatórios finais das obras.')",'reports'),
("appBar: AppBar(title: const Text('Empresas'))","appBar: _v30AppBar('Empresas','Cadastre clientes, locadoras e fornecedores de combustível.')",'companies'),
("appBar: AppBar(title: const Text('Ativos próprios'))","appBar: _v30AppBar('Ativos próprios','Cadastre e consulte os equipamentos pertencentes à empresa.')",'assets'),
("appBar:AppBar(title:const Text('Equipamentos de terceiros'))","appBar:_v30AppBar('Equipamentos de terceiros','Cadastre equipamentos contratados e suas empresas proprietárias.')",'third'),
("appBar: AppBar(title: const Text('Tanques estacionários'))","appBar: _v30AppBar('Tanques estacionários','Gerencie capacidade, identificação e saldo dos tanques estacionários.')",'tanks'),
("appBar:AppBar(title:const Text('Função Caminhão-tanque'))","appBar:_v30AppBar('Função Caminhão-tanque','Defina quais ativos podem operar como caminhão-tanque.')",'truck'),
("appBar: AppBar(title: const Text('Gerenciar usuários'))","appBar: _v30AppBar('Usuários','Cadastre operadores e controle seus acessos ao sistema.')",'users'),
("appBar:AppBar(title:const Text('Supervisor, gerente e permissões'))","appBar:_v30AppBar('Supervisor, gerente e permissões','Cadastre a equipe e defina somente as permissões necessárias.')",'permissions'),
("appBar:AppBar(title:const Text('Histórico de alterações'))","appBar:_v30AppBar('Auditoria','Consulte quem alterou, cadastrou, excluiu ou restaurou informações.')",'audit'),
("appBar: AppBar(title: const Text('Dados da empresa'))","appBar: _v30AppBar('Dados da empresa','Edite a identificação institucional usada nos PDFs e relatórios.')",'company data'),
]
for a,b,l in repls: rep(a,b,l)

g_old="appBar:AppBar(title:Text(selected.isEmpty?'Registro Geral':'${selected.length} selecionado(s)'),actions:[if(selected.isNotEmpty)IconButton(onPressed:()=>preview(items.where((x)=>selected.contains(key(x))).toList()),tooltip:'Prévia / Exportar selecionados',icon:const Icon(Icons.picture_as_pdf_outlined)),if(selected.isNotEmpty)IconButton(onPressed:()=>setState(()=>selected.clear()),icon:const Icon(Icons.close))])"
g_new="appBar:_v30AppBar(selected.isEmpty?'Registro Geral':'${selected.length} selecionado(s)','Pesquise todo o histórico por data, obra, empresa, ativo e outros filtros.',actions:[if(selected.isNotEmpty)IconButton(onPressed:()=>preview(items.where((x)=>selected.contains(key(x))).toList()),tooltip:'Prévia / Exportar selecionados',icon:const Icon(Icons.picture_as_pdf_outlined)),if(selected.isNotEmpty)IconButton(onPressed:()=>setState(()=>selected.clear()),icon:const Icon(Icons.close))])"
rep(g_old,g_new,'general records')

w_old="Widget tab(List<Map<String,dynamic>> l,String empty)=>RefreshIndicator(onRefresh:load,child:ListView(padding:const EdgeInsets.fromLTRB(12,12,12,90),children:[if(l.isEmpty)Card(child:ListTile(title:Text(empty))),...l.map(workCard)]));"
w_new="Widget tab(List<Map<String,dynamic>> l,String empty)=>RefreshIndicator(onRefresh:load,child:ListView(padding:const EdgeInsets.fromLTRB(12,12,12,90),children:[const Card(child:ListTile(leading:Icon(Icons.info_outline_rounded,color:_blue),title:Text('Gerencie obras ativas, finalizadas e excluídas em um só lugar.'))),const SizedBox(height:6),if(l.isEmpty)Card(child:ListTile(title:Text(empty))),...l.map(workCard)]));"
rep(w_old,w_new,'works intro')

p.write_text(s)
print('v30 home titles + destination intros applied',len(s))
