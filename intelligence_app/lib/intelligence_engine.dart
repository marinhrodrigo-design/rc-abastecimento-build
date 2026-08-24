class IntelligenceEngine {
  const IntelligenceEngine._();

  static double hoursToPreventive({
    required double currentHours,
    required double lastServiceHours,
    required double intervalHours,
  }) {
    final dueAt = lastServiceHours + intervalHours;
    return dueAt - currentHours;
  }

  static double expectedFuelLiters({
    required double workedHours,
    required double baselineLitersPerHour,
  }) {
    return workedHours * baselineLitersPerHour;
  }

  static double deviationPercent({
    required double observed,
    required double expected,
  }) {
    if (expected == 0) return observed == 0 ? 0 : double.infinity;
    return ((observed - expected) / expected) * 100;
  }

  static double mtbf(List<double> hoursBetweenFailures) {
    if (hoursBetweenFailures.isEmpty) return 0;
    return hoursBetweenFailures.reduce((a, b) => a + b) /
        hoursBetweenFailures.length;
  }

  static double mttr(List<double> repairDurationsHours) {
    if (repairDurationsHours.isEmpty) return 0;
    return repairDurationsHours.reduce((a, b) => a + b) /
        repairDurationsHours.length;
  }

  static double availabilityPercent({
    required double mtbfHours,
    required double mttrHours,
  }) {
    final total = mtbfHours + mttrHours;
    if (total <= 0) return 0;
    return (mtbfHours / total) * 100;
  }

  static double remainingUsefulLifeHours({
    required double firstMeasurement,
    required double latestMeasurement,
    required double limitMeasurement,
    required double elapsedHours,
  }) {
    if (elapsedHours <= 0) return double.infinity;
    final wear = firstMeasurement - latestMeasurement;
    if (wear <= 0) return double.infinity;
    final wearPerHour = wear / elapsedHours;
    final remaining = latestMeasurement - limitMeasurement;
    if (remaining <= 0) return 0;
    return remaining / wearPerHour;
  }

  static int anomalyScore({
    required double deviationPercent,
    required bool meterIncompatible,
    required bool inventoryMismatch,
    required bool duplicateWindow,
    required bool contextualLocationMismatch,
  }) {
    var score = 0;
    final deviation = deviationPercent.abs();
    if (deviation >= 50) {
      score += 30;
    } else if (deviation >= 30) {
      score += 20;
    } else if (deviation >= 15) {
      score += 10;
    }
    if (meterIncompatible) score += 20;
    if (inventoryMismatch) score += 25;
    if (duplicateWindow) score += 15;
    if (contextualLocationMismatch) score += 10;
    return score.clamp(0, 100).toInt();
  }
}
