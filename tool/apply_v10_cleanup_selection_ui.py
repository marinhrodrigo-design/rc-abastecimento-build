from pathlib import Path

path = Path('lib/main_online.dart')
text = path.read_text()

# Reduz somente o temporizador do gesto de seleção: 2s -> 1s.
hold_old = "holdTimer = Timer(const Duration(seconds: 2), () {"
hold_new = "holdTimer = Timer(const Duration(seconds: 1), () {"
if hold_old not in text:
    raise SystemExit('Falha ao localizar temporizador de seleção de 2 segundos')
text = text.replace(hold_old, hold_new, 1)

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
if hold_old in text:
    raise SystemExit('Falha ao alterar o temporizador de seleção para 1 segundo')
if hold_new not in text:
    raise SystemExit('Temporizador de seleção de 1 segundo não encontrado')

path.write_text(text)
print('v10: textos auxiliares removidos e seleção por pressão alterada para 1 segundo.')
