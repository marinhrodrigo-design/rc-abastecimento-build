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

# Release compiler catches part-file syntax too; fix the exact v29 detail-card closure.
f=Path('lib/v29_features.dart')
s=f.read_text()
bad="onTap:()=>Navigator.push(context,MaterialPageRoute(builder:(_)=>MovementDetailScreen(item:x))));"
good="onTap:()=>Navigator.push(context,MaterialPageRoute(builder:(_)=>MovementDetailScreen(item:x)))));"
if bad in s:
    s=s.replace(bad,good,1)
if bad in s or good not in s:
    raise SystemExit('v29 feature syntax fix failed')
f.write_text(s)
print('v29 patch ok; My Fuelings syntax fixed')
