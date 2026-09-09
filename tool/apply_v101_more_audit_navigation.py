from pathlib import Path
p=Path('lib/main_online.dart')
s=p.read_text()
old="""                    const Align(
                      alignment: Alignment.centerRight,
                      child: Text('v100',
                          style: TextStyle(
                              fontSize: 11,
                              color: Color(0xFF8A98A8),
                              fontWeight: FontWeight.w500)),
                    ),"""
new=old.replace("Text('v100'", "Text('v101'")
if old not in s:
    raise SystemExit('version marker block not found')
s=s.replace(old,new,1)
old2="""      if (isAdmin)
        quick(Icons.shield_outlined, 'Segurança', 'Senha e proteção do Admin',
            () => open(const AdminSecurityV35Screen())),
    ];"""
new2="""      if (isAdmin)
        quick(Icons.shield_outlined, 'Segurança', 'Senha e proteção do Admin',
            () => open(const AdminSecurityV35Screen())),
      if (isAdmin)
        quick(Icons.more_horiz_rounded, 'Mais',
            'Auditoria e outras funções administrativas',
            () => open(const AdminMoreScreen())),
    ];"""
if old2 not in s:
    raise SystemExit('admin actions anchor not found')
s=s.replace(old2,new2,1)
old3="""          children: [
            HomeActionCard(
              icon: Icons.business_outlined,"""
new3="""          children: [
            HomeActionCard(
              icon: Icons.fact_check_outlined,
              title: 'Auditoria',
              subtitle:
                  'Histórico geral e acesso à Variação metrológica com SB/FT e filtros',
              onTap: () => Navigator.push(
                  context,
                  MaterialPageRoute(
                      builder: (_) => const AuditHistoryV28Screen())),
            ),
            const SizedBox(height: 12),
            HomeActionCard(
              icon: Icons.business_outlined,"""
if old3 not in s:
    raise SystemExit('AdminMore children anchor not found')
s=s.replace(old3,new3,1)
p.write_text(s)
print('V101_MORE_AUDIT_NAVIGATION_PATCH_OK')
