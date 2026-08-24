from pathlib import Path

path = Path('lib/main_online.dart')
text = path.read_text()

snackbar = """      toggleSelected(x);
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Modo de seleção ativado. Toque em outros registros para marcar ou desmarcar.')),
      );
"""
snackbar_compact = """      toggleSelected(x);
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Modo de seleção ativado. Toque em outros registros para marcar ou desmarcar.')));
"""
if snackbar in text:
    text = text.replace(snackbar, "      toggleSelected(x);\n", 1)
elif snackbar_compact in text:
    text = text.replace(snackbar_compact, "      toggleSelected(x);\n", 1)

instruction = """          if (items != null && list.isNotEmpty && !selectionMode)
            const Padding(
              padding: EdgeInsets.fromLTRB(6, 0, 6, 8),
              child: Text('Pressione um registro por 2 segundos para selecionar. Depois, toque nos demais registros que deseja exportar em PDF.', style: TextStyle(color: Colors.black54)),
            ),
"""
text = text.replace(instruction, '', 1)

if 'Modo de seleção ativado. Toque em outros registros para marcar ou desmarcar.' in text:
    raise SystemExit('Falha ao remover snackbar de seleção')
if 'Pressione um registro por 2 segundos para selecionar.' in text:
    raise SystemExit('Falha ao remover instrução fixa de seleção')

path.write_text(text)
print('v10: textos auxiliares de seleção removidos; gesto de 2 segundos preservado.')
