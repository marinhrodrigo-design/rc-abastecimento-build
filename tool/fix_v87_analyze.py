from pathlib import Path

main_path = Path('app/lib/main_online.dart')
v29_path = Path('app/lib/v29_features.dart')

main = main_path.read_text()
v29 = v29_path.read_text()

# The session id returned by ensureAppSessionIdV30 is non-null here.
# Keep the comparison explicit so Flutter Analyze does not report a dead null-aware expression.
main = main.replace(
    "'${e['session_id'] ?? ''}' == '${sessionId ?? ''}'",
    "'${e['session_id'] ?? ''}' == '$sessionId'",
)

signature = '  Future<void> resolveUnitConflictV87(Map<String, dynamic> x) async {'
first = v29.find(signature)
offline_class = v29.find('class _OfflineConflictsV58ScreenState')
if first < 0:
    raise SystemExit('resolveUnitConflictV87 method not found')
if offline_class < 0:
    raise SystemExit('Offline conflicts state class not found')

# The initial v87 patch inserted the unit-conflict review method in OperationalHome,
# where tank()/busy are not available. Move that exact method into the conflicts screen.
if first < offline_class:
    end = v29.find('\n  @override\n  Widget build(BuildContext context) => Scaffold(', first)
    if end < 0 or end > offline_class:
        raise SystemExit('Could not delimit misplaced resolveUnitConflictV87 method')
    method = v29[first:end]
    v29 = v29[:first] + v29[end:]
    offline_class = v29.find('class _OfflineConflictsV58ScreenState')
    insert_at = v29.find('\n  @override\n  Widget build(BuildContext context) => Scaffold(', offline_class)
    if insert_at < 0:
        raise SystemExit('Could not find OfflineConflicts build method')
    v29 = v29[:insert_at] + '\n' + method + v29[insert_at:]
else:
    # Already in the correct class: make the script idempotent.
    count = v29.count(signature)
    if count != 1:
        raise SystemExit(f'Unexpected resolveUnitConflictV87 count: {count}')

main_path.write_text(main)
v29_path.write_text(v29)
print('v87_analyze_source_fix=True')
