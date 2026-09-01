from pathlib import Path

p=Path('lib/main_online.dart')
s=p.read_text()

# Aceitar precisão GPS de até 30 m e dar mais tempo para estabilização.
old="""      Position? best;
      for(var attempt=0;attempt<3;attempt++){
        try{
          final p=await Geolocator.getCurrentPosition(locationSettings:const LocationSettings(accuracy:LocationAccuracy.bestForNavigation,timeLimit:Duration(seconds:15)));
          if(best==null||p.accuracy<best.accuracy)best=p;
          if(p.accuracy<=15)return p;
        }catch(_){}
        if(attempt<2)await Future<void>.delayed(const Duration(seconds:1));
      }
      return best!=null&&best.accuracy<=15?best:null;
"""
new="""      Position? best;
      for(var attempt=0;attempt<3;attempt++){
        try{
          final p=await Geolocator.getCurrentPosition(locationSettings:const LocationSettings(accuracy:LocationAccuracy.bestForNavigation,timeLimit:Duration(seconds:20)));
          if(best==null||p.accuracy<best.accuracy)best=p;
          if(p.accuracy<=30)return p;
        }catch(_){}
        if(attempt<2)await Future<void>.delayed(const Duration(seconds:2));
      }
      return best!=null&&best.accuracy<=30?best:null;
"""
if s.count(old)!=1:
    raise SystemExit(f'v45 GPS anchor unexpected: {s.count(old)}')
s=s.replace(old,new,1)

p.write_text(s)

checks=[
    'for(var attempt=0;attempt<3;attempt++)',
    'timeLimit:Duration(seconds:20)',
    'if(p.accuracy<=30)return p;',
    'best.accuracy<=30?best:null',
    "helperText:'Preencha manualmente porque a captura automática não foi possível.'",
    "labelText:'Observação'",
]
for x in checks:
    if x not in s:
        raise SystemExit('v45 missing marker: '+x)
if 'p.accuracy<=15' in s or 'best.accuracy<=15' in s:
    raise SystemExit('v45 old 15m threshold remains')
print('V45_LOCATION_30M_OK')
