from pathlib import Path

p=Path('lib/main_online.dart')
s=p.read_text()

# Remover do app as interfaces administrativas adicionadas recentemente.
for line in [
"      if(isAdmin)quick(Icons.warning_amber_rounded,'Conflitos offline','Revisar abastecimentos concorrentes',()=>open(const OfflineConflictsV58Screen())),\n",
"      if(isAdmin)quick(Icons.history_rounded,'Auditoria','Histórico de alterações',()=>open(const AuditHistoryV28Screen())),\n",
]:
    s=s.replace(line,'',1)

# A única alteração nova mantida no app é a proteção automática de conflito offline.
s=s.replace("child: Text('v60'","child: Text('v61'",1)
p.write_text(s)

print('PATCH_V61_KEEP_ONLY_CONFLICT_PROTECTION_OK')
