import 'package:flutter/material.dart';

class RCTheme {
  const RCTheme._();

  static const navy = Color(0xFF0B2F4F);
  static const blue = Color(0xFF075EA8);
  static const lightBlue = Color(0xFFEAF4FC);
  static const surface = Color(0xFFF7F9FC);
  static const border = Color(0xFFD9E2EC);

  static ThemeData build() {
    final scheme = ColorScheme.fromSeed(
      seedColor: blue,
      brightness: Brightness.light,
      surface: surface,
    );
    return ThemeData(
      useMaterial3: true,
      colorScheme: scheme,
      scaffoldBackgroundColor: surface,
      appBarTheme: const AppBarTheme(
        backgroundColor: Colors.white,
        foregroundColor: navy,
        surfaceTintColor: Colors.transparent,
        elevation: 0,
      ),
      cardTheme: CardThemeData(
        color: Colors.white,
        surfaceTintColor: Colors.transparent,
        elevation: 0,
        margin: EdgeInsets.zero,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(18),
          side: const BorderSide(color: border),
        ),
      ),
      inputDecorationTheme: InputDecorationTheme(
        filled: true,
        fillColor: Colors.white,
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(14),
          borderSide: const BorderSide(color: border),
        ),
        enabledBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(14),
          borderSide: const BorderSide(color: border),
        ),
      ),
    );
  }

  static Color severityColor(String? severity) {
    switch ((severity ?? '').toLowerCase()) {
      case 'critical':
        return const Color(0xFFB42318);
      case 'high':
        return const Color(0xFFE04F16);
      case 'attention':
        return const Color(0xFFB7791F);
      default:
        return const Color(0xFF367588);
    }
  }

  static IconData severityIcon(String? severity) {
    switch ((severity ?? '').toLowerCase()) {
      case 'critical':
        return Icons.error_rounded;
      case 'high':
        return Icons.warning_amber_rounded;
      case 'attention':
        return Icons.info_rounded;
      default:
        return Icons.lightbulb_outline_rounded;
    }
  }

  static String severityLabel(String? severity) {
    switch ((severity ?? '').toLowerCase()) {
      case 'critical':
        return 'Crítico';
      case 'high':
        return 'Alto';
      case 'attention':
        return 'Atenção';
      default:
        return 'Informativo';
    }
  }

  static String statusLabel(String? status) {
    switch ((status ?? '').toLowerCase()) {
      case 'open':
        return 'Aberto';
      case 'in_review':
        return 'Em análise';
      case 'confirmed':
        return 'Confirmado';
      case 'dismissed':
        return 'Não procede';
      case 'resolved':
        return 'Resolvido';
      default:
        return status ?? '-';
    }
  }

  static String roleLabel(String? role) {
    switch ((role ?? '').toLowerCase()) {
      case 'admin':
        return 'Administrador';
      case 'manager':
        return 'Gerente';
      case 'supervisor':
        return 'Supervisor';
      case 'fuel_driver':
        return 'Operacional';
      default:
        return role ?? 'Usuário';
    }
  }
}
