import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:shared_preferences/shared_preferences.dart';

import 'package:rc_intelligence/data_store.dart';
import 'package:rc_intelligence/main.dart';
import 'package:rc_intelligence/notifications.dart';

Future<DataStore> _store() async {
  SharedPreferences.setMockInitialValues(<String, Object>{});
  final store = DataStore();
  await store.load();
  return store;
}

Future<void> _pumpApp(WidgetTester tester, DataStore store) async {
  await tester.pumpWidget(
    RCIntelligenceApp(
      store: store,
      notifications: IntelligenceNotifications(),
    ),
  );
  await tester.pumpAndSettle();
}

Future<void> _tapAndCloseDialog(
  WidgetTester tester,
  String buttonText,
  String expectedTitle,
) async {
  final button = find.text(buttonText);
  await tester.ensureVisible(button);
  await tester.tap(button);
  await tester.pumpAndSettle();
  expect(find.textContaining(expectedTitle), findsWidgets);
  final close = find.text('Fechar');
  await tester.ensureVisible(close);
  await tester.tap(close.last);
  await tester.pumpAndSettle();
}

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  testWidgets('navegacao principal abre as cinco areas', (tester) async {
    final store = await _store();
    await _pumpApp(tester, store);

    expect(find.text('R&C Intelligence • SIMULADOR v6'), findsOneWidget);
    expect(find.text('Executar análise agora'), findsOneWidget);

    await tester.tap(find.text('Ativos'));
    await tester.pumpAndSettle();
    expect(find.textContaining('034-020'), findsWidgets);

    await tester.tap(find.text('Central de Dados'));
    await tester.pumpAndSettle();
    expect(find.text('Importar e analisar planilha XLSX'), findsOneWidget);

    await tester.tap(find.text('OEM'));
    await tester.pumpAndSettle();
    expect(find.textContaining('034-020'), findsWidgets);

    await tester.tap(find.text('Alertas'));
    await tester.pumpAndSettle();
    expect(find.textContaining('Série do ativo 034-028'), findsWidgets);

    await tester.tap(find.text('Intelligence'));
    await tester.pumpAndSettle();
    expect(find.text('Executar análise agora'), findsOneWidget);
  });

  testWidgets('ficha do ativo abre os seis botoes de inteligencia', (tester) async {
    final store = await _store();
    await _pumpApp(tester, store);

    await tester.tap(find.text('Ativos'));
    await tester.pumpAndSettle();
    await tester.tap(find.textContaining('034-020').first);
    await tester.pumpAndSettle();

    expect(find.text('Próxima ação recomendada'), findsOneWidget);
    expect(find.textContaining('Confiança'), findsWidgets);

    await _tapAndCloseDialog(tester, 'Saúde por sistemas', 'Saúde por sistemas');
    await _tapAndCloseDialog(tester, 'Linha do tempo', 'Linha do tempo inteligente');
    await _tapAndCloseDialog(tester, 'Comparar semelhantes', 'Comparação entre ativos iguais');
    await _tapAndCloseDialog(tester, 'Preparar preventiva', 'Preparação automática');
    await _tapAndCloseDialog(tester, 'Vida das peças', 'Vida observada das peças');
    await _tapAndCloseDialog(tester, 'Revisar completude', 'Manutenção aparentemente incompleta');

    expect(find.text('Abrir catálogo OEM'), findsOneWidget);
  });

  testWidgets('editar ativo salva a alteracao', (tester) async {
    final store = await _store();
    await _pumpApp(tester, store);

    await tester.tap(find.text('Ativos'));
    await tester.pumpAndSettle();

    final edit = find.byIcon(Icons.edit).first;
    await tester.tap(edit);
    await tester.pumpAndSettle();
    expect(find.textContaining('Editar'), findsOneWidget);

    final fields = find.byType(TextField);
    expect(fields, findsNWidgets(5));
    await tester.enterText(fields.at(1), 'MODELO TESTE UI');
    await tester.tap(find.text('Salvar'));
    await tester.pumpAndSettle();

    expect(store.assets.any((a) => a.model == 'MODELO TESTE UI'), isTrue);
  });

  testWidgets('alerta mostra raciocinio e permite ensinar', (tester) async {
    final store = await _store();
    await _pumpApp(tester, store);

    await tester.tap(find.text('Alertas'));
    await tester.pumpAndSettle();
    final alert = find.textContaining('Série do ativo 034-028').first;
    await tester.tap(alert);
    await tester.pumpAndSettle();

    await tester.tap(find.text('Ver raciocínio'));
    await tester.pumpAndSettle();
    expect(find.text('Por que o Intelligence está dizendo isso?'), findsOneWidget);
    await tester.tap(find.text('Fechar'));
    await tester.pumpAndSettle();

    await tester.tap(alert);
    await tester.pumpAndSettle();
    await tester.tap(find.text('Confirmar e ensinar'));
    await tester.pumpAndSettle();
    expect(find.text('Sua confirmação ensina o Intelligence'), findsOneWidget);

    await tester.enterText(find.byType(TextField), 'SERIE-CONFIRMADA-TESTE');
    await tester.tap(find.text('Confirmar e ensinar'));
    await tester.pumpAndSettle();

    expect(store.rule('asset:034-028:serial')?.value, 'SERIE-CONFIRMADA-TESTE');
    expect(store.anomalies.firstWhere((a) => a.id == 'asset:034-028:serial-conflict').resolved, isTrue);
  });
}
