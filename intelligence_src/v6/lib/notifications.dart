import 'package:flutter_local_notifications/flutter_local_notifications.dart';

import 'models.dart';

class IntelligenceNotifications {
  final FlutterLocalNotificationsPlugin plugin = FlutterLocalNotificationsPlugin();
  bool ready = false;

  Future<void> initialize() async {
    const settings = InitializationSettings(
      android: AndroidInitializationSettings('@mipmap/ic_launcher'),
    );
    await plugin.initialize(settings);
    final android = plugin.resolvePlatformSpecificImplementation<AndroidFlutterLocalNotificationsPlugin>();
    await android?.requestNotificationsPermission();
    ready = true;
  }

  Future<void> showAnomaly(Anomaly anomaly) async {
    if (!ready) return;
    const details = NotificationDetails(
      android: AndroidNotificationDetails(
        'rc_intelligence_anomalias',
        'R&C Intelligence - Anomalias',
        channelDescription: 'Anomalias e confirmacoes do Intelligence',
        importance: Importance.high,
        priority: Priority.high,
      ),
    );
    await plugin.show(
      anomaly.id.hashCode.abs() % 2000000000,
      anomaly.needsConfirmation
          ? 'R&C Intelligence precisa da sua confirmacao'
          : anomaly.title,
      anomaly.message,
      details,
      payload: anomaly.id,
    );
  }
}
