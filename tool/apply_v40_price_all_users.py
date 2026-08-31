from pathlib import Path

p=Path('lib/main_online.dart')
s=p.read_text()

old="  bool get financial=>widget.profile['is_admin']==true||widget.profile['is_manager']==true||widget.profile['can_financial']==true;"
new="  bool get financial=>true;"
if s.count(old)!=1:
    raise SystemExit(f'Esperava 1 regra financial do formulário; encontrado: {s.count(old)}')
s=s.replace(old,new,1)

old2="salePrice:financial&&sale.text.trim().isNotEmpty?_num(sale.text.replaceAll(',','.')):null"
new2="salePrice:sale.text.trim().isNotEmpty?_num(sale.text.replaceAll(',','.')):null"
if s.count(old2)!=1:
    raise SystemExit(f'Esperava 1 envio condicionado de preço; encontrado: {s.count(old2)}')
s=s.replace(old2,new2,1)

p.write_text(s)
print('V40_PRICE_ALL_USERS_OK')
