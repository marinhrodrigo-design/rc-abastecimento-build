from pathlib import Path
p=Path('lib/main_online.dart')
t=p.read_text()
imp="import 'package:supabase_flutter/supabase_flutter.dart';\n"
if "part 'v29_features.dart';" not in t:
    if imp not in t: raise SystemExit('import point missing')
    t=t.replace(imp,imp+"\npart 'v29_features.dart';\n",1)
old="""    final lastTankId = offlineStore.lastTankId;
    final staff = profile!['is_admin'] == true || profile!['is_manager'] == true || profile!['is_supervisor'] == true;
    if (staff) return AdminHomeScreen(profile: profile!, onLogout: _logout);
    if (lastTankId != null) return FieldHomeScreen(profile: profile!, tankId: lastTankId, onLogout: _logout);
    return UnitSelectionScreen(profile: profile!, onLogout: _logout);"""
new="""    final staff = profile!['is_admin'] == true || profile!['is_manager'] == true || profile!['is_supervisor'] == true;
    if (staff) return AdminHomeScreen(profile: profile!, onLogout: _logout);
    final role = '${profile!['role'] ?? ''}'.trim().toLowerCase();
    final operational = role == 'fuel_driver' || role == 'operator' || role == 'operational';
    if (operational) return OperationalHomeV29Screen(profile: profile!, onLogout: _logout);
    final lastTankId = offlineStore.lastTankId;
    if (lastTankId != null) return FieldHomeScreen(profile: profile!, tankId: lastTankId, onLogout: _logout);
    return UnitSelectionScreen(profile: profile!, onLogout: _logout);"""
if 'return OperationalHomeV29Screen(profile:' not in t:
    if old not in t: raise SystemExit('route point missing')
    t=t.replace(old,new,1)
old_cards="""      if(isAdmin)quick(Icons.manage_accounts_rounded,'Usuários','Operadores',()=>open(AdminUsersOnlineScreen(referenceData:ref!))),
      if(isAdmin)quick(Icons.admin_panel_settings_outlined,'Permissões','Supervisor e gerente',()=>open(const StaffPermissionsV23Screen())),"""
new_cards="""      if(isAdmin)quick(Icons.manage_accounts_rounded,'Usuários','Supervisor, Gerente e Operacional',()=>open(UnifiedUsersV29Screen(referenceData:ref!))),"""
if 'UnifiedUsersV29Screen(referenceData:ref!)' not in t:
    if old_cards not in t: raise SystemExit('users point missing')
    t=t.replace(old_cards,new_cards,1)
for x in ["part 'v29_features.dart';",'return OperationalHomeV29Screen(profile:','UnifiedUsersV29Screen(referenceData:ref!)']:
    if x not in t: raise SystemExit('marker missing: '+x)
p.write_text(t)
print('v29 patch ok')
