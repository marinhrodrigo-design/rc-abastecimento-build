import 'dart:io';
import 'package:flutter_test/flutter_test.dart';
import 'package:rc_abastecimento/main_online.dart';

const longToken = '12345678901234567890123456789012345678901234';
String longText(String marker) => '$marker - Avenida Presidente Juscelino Kubitschek de Oliveira, 12345, Setor Industrial, Bairro Muito Extenso, Município de Nome Comprido - MG - complemento galpão administrativo bloco operacional, observação completa para testar quebra automática de linhas sem ultrapassar margens e sem texto em orientação vertical.';

Map<String,dynamic> context({String? nf}) => <String,dynamic>{
  'institutional_company': <String,dynamic>{'company_name':'HYDRA ENGENHARIA PDF QA LTDA','document':'12.345.678/0001-90'},
  'empresa':'HYDRA ENGENHARIA PDF QA LTDA',
  'empresa_fornecedora_vendedora':'HYDRA ENGENHARIA PDF QA LTDA',
  'empresa_recebedora_compradora':'CLIENTE RECEBEDOR PDF QA LTDA COM DENOMINAÇÃO EXTENSA',
  'empresa_compradora':'HYDRA ENGENHARIA PDF QA LTDA',
  'fornecedor_combustivel':'FORNECEDOR REFINARIA PDF QA LTDA',
  'obra':'OBRA PDF QA - Complexo Industrial com Nome Muito Extenso',
  'responsavel_obra':'RESPONSÁVEL DA OBRA PDF QA COM NOME COMPLETO EXTENSO',
  'proprietario_equipamento':'PROPRIETÁRIA EQUIPAMENTO PDF QA LTDA',
  'origem':'CB99','destino':'TE99',
  'nfs': nf == null ? <dynamic>[] : <dynamic>[<String,dynamic>{'invoice_number':nf,'batch_number':'LOTE-$longToken','supplier_name':'FORNECEDOR REFINARIA PDF QA LTDA','liters':123.4,'unit_cost':5.43}],
};

Map<String,dynamic> base(String code) => <String,dynamic>{
  'id': null,'code':code,'movement_code':code,'type':'fueling','created_at':'2026-09-06T22:05:00-03:00','occurred_at':'2026-09-06T22:05:00-03:00','status':'finalized',
  'liters':123.4,'fuel_type':'Diesel S10','source_tank':'CB99','source_tank_name':'Comboio QA 99','source_tank_type':'comboio',
  'work':'OBRA PDF QA - Complexo Industrial com Nome Muito Extenso','work_responsible':'RESPONSÁVEL DA OBRA PDF QA COM NOME COMPLETO EXTENSO',
  'operator':'OPERADOR PDF QA COM NOME COMPLETO EXTENSO','receiver':'RECEBEDOR PDF QA COM NOME COMPLETO EXTENSO','receiver_company':'CLIENTE RECEBEDOR PDF QA LTDA COM DENOMINAÇÃO EXTENSA',
  'location_address':longText('LOCALIZACAO_QA'),'notes':longText('OBSERVACAO_QA'),'sale_price_per_liter':7.89,'unit_cost':5.43,'total_value':973.63,
  'asset_number':'034-999','asset_plate':'ABC1D23','asset_model':'MARCA MODELO EXTENSO PDF QA','lubricated':true,'report_context':context(),
};

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();
  testWidgets('generate v90 stress PDFs', (tester) async {
    await tester.runAsync(() async {
      final km=base('CB99-AB-000001')..addAll({'measurement_type':'km','km_value':123456,'hourmeter_value':null});
      final hour=base('CB99-AB-000002')..addAll({'measurement_type':'hourmeter','km_value':null,'hourmeter_value':9876.5,'asset_number':'034-998','asset_plate':''});
      final both=base('CB99-AB-000003')..addAll({'measurement_type':'both','km_value':222222,'hourmeter_value':12345.6});
      final none=base('CB99-AB-000004')..addAll({'measurement_type':'none','km_value':null,'hourmeter_value':null,'asset_number':null,'asset_plate':null,'asset_model':null,'third_party_plate':'XYZ9Z99','third_party_description':'EQUIPAMENTO TERCEIRO PDF QA COM DESCRIÇÃO MUITO EXTENSA'});
      final transfer=base('CB99-TR-000001')..addAll({'type':'tank_transfer','transfer_kind':'comboio_to_comboio','destination_tank':'CB98','receiver_responsible':'RECEBEDOR TRANSFERÊNCIA QA','donor_responsible':'DOADOR TRANSFERÊNCIA QA','report_context':context(nf:'NF-$longToken')});
      final refinery=base('TE99-ER-000001')..addAll({'type':'refinery_entry','source_tank':null,'destination_tank':'TE99','asset_number':null,'asset_plate':null,'asset_model':null,'report_context':context(nf:'NF-$longToken')});
      final items=<Map<String,dynamic>>[km,hour,both,none,transfer,refinery];
      await File('qa_output/fuel_report_v90.pdf').writeAsBytes(await FuelPdfReport.build(items),flush:true);

      final snapshot=<String,dynamic>{
        'work':<String,dynamic>{'name':'OBRA FINAL PDF QA COM NOME MUITO EXTENSO PARA VALIDAR QUEBRA DE LINHA','responsible':'RESPONSÁVEL FINAL PDF QA COM NOME COMPLETO MUITO EXTENSO','location':longText('LOCAL_OBRA_FINAL_QA'),'company_name':'CLIENTE FINAL PDF QA LTDA COM DENOMINAÇÃO EMPRESARIAL MUITO EXTENSA','company_document':'12.345.678/0001-90','status':'finalized','finalized_at':'2026-09-06T22:10:00-03:00'},
        'summary':<String,dynamic>{'movement_count':6,'fueling_count':4,'fueling_liters':493.6,'purchase_cost_total':2680.25,'sale_total':3894.52,'profit_total':1214.27},
        'fuel_summary':<dynamic>[<String,dynamic>{'fuel_type':'Diesel S10','liters':493.6,'fueling_count':4}],
        'assets':<dynamic>[<String,dynamic>{'kind':'own','label':'034-999 • ATIVO PRÓPRIO PDF QA COM MODELO EXTREMAMENTE COMPRIDO','asset_number':'034-999','plate':'ABC1D23','owner_company':'PROPRIETARIA FINAL QA LTDA','fueling_count':3,'liters':370.2},<String,dynamic>{'kind':'third_party','label':'XYZ9Z99 • EQUIPAMENTO TERCEIRO PDF QA COM DESCRIÇÃO EXTREMAMENTE COMPRIDA','plate':'XYZ9Z99','description':'EQUIPAMENTO TERCEIRO PDF QA','owner_company':'TERCEIRA FINAL QA LTDA','fueling_count':1,'liters':123.4}],
        'movements':items,
        'nfs':<dynamic>[<String,dynamic>{'invoice_number':'NF-$longToken','batch_number':'LOTE-$longToken','supplier_name':'FORNECEDOR FINAL PDF QA LTDA','fuel_type':'Diesel S10','liters_used_by_work':493.6,'cost_used_by_work':2680.25,'received_at':'2026-09-06T20:00:00-03:00','total_liters':1000,'remaining_liters':506.4,'status':'open'}],
        'lineage':<dynamic>[<String,dynamic>{'movement_id':9006,'code':'TE99-ER-000001','created_at':'2026-09-06T20:00:00-03:00','type':'refinery_entry','lot_id':777,'invoice_number':'NF-$longToken','liters':1000,'source':'REFINARIA','destination':'TE99'}],
        'audit':<dynamic>[<String,dynamic>{'created_at':'2026-09-06T22:12:00-03:00','user_name':'ADMINISTRADOR PDF QA','action':'CORREÇÃO DE TESTE COM TEXTO EXTENSO PARA VALIDAR LAYOUT','record_id':'9001'}],
      };
      await File('qa_output/work_final_v90.pdf').writeAsBytes(await WorkFinalPdf.build(snapshot),flush:true);
    });
  });
}
