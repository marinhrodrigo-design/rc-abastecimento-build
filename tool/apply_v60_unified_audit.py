from pathlib import Path

main=Path('lib/main_online.dart')
s=main.read_text()

# Auditoria do app passa a usar o histórico unificado V60.
s=s.replace("client.rpc('rca_audit_history_v28'", "client.rpc('rca_audit_history_v60'", 1)

# Remove o atalho separado 'Operação dos comboios'.
s=s.replace("      if(isAdmin)quick(Icons.manage_search_rounded,'Operação dos comboios','Linha do tempo de logins, unidades, abastecimentos e conflitos',()=>open(const OperationAuditV59Screen())),\n", "", 1)

# Versão visível.
s=s.replace("child: Text('v59'", "child: Text('v60'", 1)

# Substitui a tela antiga de histórico por um único Registro cronológico.
start=s.index('class AuditHistoryV28Screen extends StatefulWidget')
end=s.index('class GlobalSearchV28Screen', start)
new_screen=r'''class AuditHistoryV28Screen extends StatefulWidget {
  const AuditHistoryV28Screen({super.key});
  @override State<AuditHistoryV28Screen> createState()=>_AuditHistoryV28ScreenState();
}
class _AuditHistoryV28ScreenState extends State<AuditHistoryV28Screen>{
  final q=TextEditingController();
  List<Map<String,dynamic>> items=[];
  bool busy=false;
  @override void initState(){super.initState();load();}
  @override void dispose(){q.dispose();super.dispose();}
  Future<void> load()async{
    setState(()=>busy=true);
    try{
      final x=await api.auditHistoryV28(query:q.text.trim(),limit:1500);
      if(mounted)setState(()=>items=x);
    }catch(e){
      if(mounted)ScaffoldMessenger.of(context).showSnackBar(SnackBar(content:Text(_friendlyError(e))));
    }finally{if(mounted)setState(()=>busy=false);}
  }
  String safe(dynamic v){final x='${v??''}'.trim();return x.isEmpty||x=='undefined'?'—':x;}
  String area(dynamic v){final x=safe(v).toLowerCase();if(x=='registro')return 'Registro';const m={'managers':'Usuários de gestão','drivers':'Usuários operacionais','user_permissions':'Permissões','role_default_permissions':'Permissões padrão','works':'Obras','companies':'Empresas','receipt_lots':'Notas fiscais / lotes','refinery_receipts':'Recebimentos','machines':'Ativos','third_party_vehicles':'Equipamentos de terceiros'};return m[x]??safe(v);}
  @override Widget build(BuildContext context)=>Scaffold(
    appBar:AppBar(title:const Text('Auditoria • Registros')),
    body:Column(children:[
      Padding(padding:const EdgeInsets.all(12),child:TextField(
        controller:q,onSubmitted:(_)=>load(),
        decoration:InputDecoration(labelText:'Pesquisar nos registros',hintText:'Usuário, comboio, abastecimento, login, saída...',prefixIcon:const Icon(Icons.search),suffixIcon:IconButton(onPressed:load,icon:const Icon(Icons.search))),
      )),
      const Padding(padding:EdgeInsets.fromLTRB(12,0,12,8),child:Card(child:ListTile(
        leading:Icon(Icons.history_rounded,color:_blue),
        title:Text('Histórico geral em ordem cronológica',style:TextStyle(fontWeight:FontWeight.w900)),
        subtitle:Text('Login, seleção/troca/liberação de comboio, abastecimentos, conflitos e decisões, logout e demais alterações ficam concentrados aqui.'),
      ))),
      if(busy)const LinearProgressIndicator(minHeight:2),
      Expanded(child:RefreshIndicator(
        onRefresh:load,
        child:ListView(padding:const EdgeInsets.fromLTRB(12,4,12,30),children:[
          if(items.isEmpty&&!busy)const Card(child:ListTile(title:Text('Nenhum registro encontrado.'))),
          ...items.map((x){final detail=safe(x['detail_text']);final user=safe(x['user_name']);final ref=safe(x['record_id']);final table=area(x['table_name']);return Card(child:ListTile(
            leading:const CircleAvatar(child:Icon(Icons.receipt_long_outlined)),
            title:Text(detail,style:const TextStyle(fontWeight:FontWeight.w900)),
            subtitle:Text('${_fmtDate(x['created_at'])}\nUsuário: $user\nÁrea: $table${ref=='—'?'':' • Referência: $ref'}'),
            isThreeLine:false,
            onTap:()=>showDialog(
              context:context,
              builder:(ctx)=>AlertDialog(
                title:const Text('Detalhes do registro'),
                content:SingleChildScrollView(child:SelectableText(
                  'Data/hora: ${_fmtDate(x['created_at'])}\nUsuário: $user\nRegistro: $detail\nÁrea: $table\nReferência: $ref\n\nDados anteriores:\n${const JsonEncoder.withIndent('  ').convert(x['old_data'])}\n\nDados do evento:\n${const JsonEncoder.withIndent('  ').convert(x['new_data'])}',
                )),
                actions:[TextButton(onPressed:()=>Navigator.pop(ctx),child:const Text('Fechar'))],
              ),
            ),
          ));}),
        ]),
      )),
    ]),
  );
}

'''
s=s[:start]+new_screen+s[end:]
main.write_text(s)

# Remove completamente a tela separada de Operação dos comboios adicionada na V59.
v=Path('lib/v29_features.dart')
t=v.read_text()
marker='class OperationAuditV59Screen extends StatefulWidget'
if marker in t:
    t=t[:t.index(marker)].rstrip()+"\n"
v.write_text(t)

print('PATCH_V60_UNIFIED_AUDIT_OK')
