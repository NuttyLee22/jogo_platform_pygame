# Adventure Platformer - Elden Thing

Um jogo de plataforma completo desenvolvido em Python usando a biblioteca Pygame Zero.

## 📋 Requisitos

- Python 3.7+
- Pygame Zero (`pip install pgzero`)

## 📦 Instalação e Ambiente Virtual

Para evitar conflitos de dependências, recomenda-se utilizar um ambiente virtual.

### 1 Criar o ambiente virtual

**Windows:**
```bash
python -m venv .venv
.venv\Scripts\activate
```

**Linux/MacOS:**
```bash
python -m venv .venv
source .venv/bin/activate
```

### 2 Instalar dependências
```bash
pip install pygame pygame-zero
```

## 3 Executar jogo 🚀

```bash
cd jogo_roguelike_pygame
set PYTHONUTF8=1
pgzrun main.py
```

Ou alternativamente:
```bash
python -m pgzrun main.py
```

<!-- Ou clique no arquivo executavel dentro da pasta dist:
```bash
main.exe
``` -->

## 🎮 Controles

- **Setas laterais**: Mover o personagem
- **Seta pra cima**: Pular
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