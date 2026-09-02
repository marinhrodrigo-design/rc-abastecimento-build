from pathlib import Path

p = Path('lib/main_online.dart')
s = p.read_text()

old = """      ],
      DropdownButtonFormField<String>(value:fuel,decoration:const InputDecoration(labelText:'Combustível'),items:_fuelTypes.map((x)=>DropdownMenuItem(value:x,child:Text(x))).toList(),onChanged:saving?null:(v)=>setState(()=>fuel=v??'Diesel')),const SizedBox(height:8),"""
new = """      ],
      const SizedBox(height:18),
      DropdownButtonFormField<String>(value:fuel,decoration:const InputDecoration(labelText:'Combustível'),items:_fuelTypes.map((x)=>DropdownMenuItem(value:x,child:Text(x))).toList(),onChanged:saving?null:(v)=>setState(()=>fuel=v??'Diesel')),const SizedBox(height:8),"""

assert old in s, 'Trecho do destino/combustível da v49 não encontrado'
s = s.replace(old, new, 1)

p.write_text(s)
print('VALIDACAO_PATCH_V50_OK')
