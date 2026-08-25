import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:rc_intelligence/main.dart';

void main() {
  testWidgets('abre planejamento de revisões pelo dashboard', (tester) async {
    await tester.pumpWidget(const RCIntelligenceApp());
    await tester.tap(find.text('Revisões em ≤15 dias'));
    await tester.pumpAndSettle();
    expect(find.text('Próximas revisões'), findsOneWidget);
  });

  testWidgets('configura destinatário Pedro', (tester) async {
    await tester.pumpWidget(const RCIntelligenceApp());
    await tester.tap(find.byIcon(Icons.notifications_none));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Pedro'));
    await tester.pumpAndSettle();
    expect(find.text('Alertas de Pedro'), findsOneWidget);
  });

  testWidgets('abre RUL na manutenção', (tester) async {
    await tester.pumpWidget(const RCIntelligenceApp());
    await tester.tap(find.byIcon(Icons.build_outlined));
    await tester.pumpAndSettle();
    await tester.tap(find.text('RUL monitorado'));
    await tester.pumpAndSettle();
    expect(find.text('Componentes monitorados'), findsOneWidget);
  });

  testWidgets('abre identificação técnica', (tester) async {
    await tester.pumpWidget(const RCIntelligenceApp());
    await tester.tap(find.byIcon(Icons.psychology_outlined));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Identificação Técnica Automática'));
    await tester.pumpAndSettle();
    expect(find.text('Identificação Técnica Automática'), findsWidgets);
  });
}
