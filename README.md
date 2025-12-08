# Adventure Platformer - PgZero

Um jogo de plataforma completo desenvolvido em Python usando Pygame Zero.

## 📋 Requisitos

- Python 3.7+
- Pygame Zero (`pip install pgzero`)

## 🚀 Como Executar

```bash
cd python_game
pgzrun main.py
```

Ou alternativamente:
```bash
python -m pgzrun main.py
```

## 🎮 Controles

- **WASD** ou **Setas**: Mover o personagem
- **Espaço**: Pular
- **ESC**: Voltar ao menu

## 🎯 Objetivo

Chegue até a área verde no canto superior direito sem perder todas as suas vidas!
Evite os inimigos vermelhos que patrulham as plataformas.

## 📁 Estrutura do Projeto

```
python_game/
├── main.py          # Código principal do jogo
├── README.md        # Este arquivo
├── images/          # Pasta para sprites (opcional)
│   └── ...
├── sounds/          # Pasta para efeitos sonoros
│   ├── jump.wav
│   └── hurt.wav
└── music/           # Pasta para música de fundo
    └── background.mp3
```

## ✨ Características

- ✅ Menu principal com botões clicáveis
- ✅ Toggle de som (música e efeitos)
- ✅ Personagem com animação de sprite
- ✅ Múltiplos inimigos com patrulha territorial
- ✅ Sistema de vidas com invencibilidade temporária
- ✅ Plataformas com colisão
- ✅ Física com gravidade e pulo
- ✅ Telas de Game Over e Vitória

## 🎨 Sobre as Animações

O jogo usa animações procedurais para os personagens:
- **Herói**: Animação de pernas ao andar e respiração quando parado
- **Inimigos**: Animação de pernas durante a patrulha
- Os olhos acompanham a direção do movimento

## 📝 Notas Técnicas

- Usa apenas: `pgzero`, `math`, `random`, `Rect` do Pygame
- Segue convenções PEP8
- Classes bem estruturadas e documentadas
- Código totalmente original

## 🎵 Adicionando Sons (Opcional)

Para adicionar sons ao jogo:

1. Crie as pastas `sounds/` e `music/`
2. Adicione arquivos:
   - `sounds/jump.wav` - Som de pulo
   - `sounds/hurt.wav` - Som de dano
   - `music/background.mp3` - Música de fundo

O jogo funciona sem esses arquivos, mas fica mais imersivo com eles!

## 🔧 Personalizações

Você pode ajustar as constantes no início do arquivo `main.py`:

```python
GRAVITY = 0.8          # Força da gravidade
JUMP_STRENGTH = -15    # Força do pulo
PLAYER_SPEED = 5       # Velocidade do jogador
ENEMY_SPEED = 2        # Velocidade dos inimigos
```

---

Desenvolvido como projeto educacional de Pygame Zero.
