from pathlib import Path
p=Path('lib/main_online.dart')
s=p.read_text()
old="""                const SizedBox(height: 14),
                const Text('Esta versão usa o banco online. Alterações feitas em um aparelho aparecem nos demais.', textAlign: TextAlign.center),
                const SizedBox(height: 8),
                const Text('Use o usuário e a senha cadastrados pelo administrador.', textAlign: TextAlign.center, style: TextStyle(fontWeight: FontWeight.w700, color: Color(0xFF60758D))),
"""
new="""                const SizedBox(height: 14),
                const Text('Use o usuário e a senha cadastrados pelo administrador.', textAlign: TextAlign.center, style: TextStyle(fontWeight: FontWeight.w700, color: Color(0xFF60758D))),
                const SizedBox(height: 10),
                const Align(
                  alignment: Alignment.centerRight,
                  child: Text('v54', style: TextStyle(fontSize: 11, color: Color(0xFF8A98A8), fontWeight: FontWeight.w500)),
                ),
"""
assert old in s, 'Bloco de texto do login não encontrado'
s=s.replace(old,new,1)
p.write_text(s)
print('VALIDACAO_PATCH_V54_OK')
