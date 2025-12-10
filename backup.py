# -*- coding: utf-8 -*-
"""
Platformer Game - PgZero
Um jogo de plataforma completo com menu, animacoes e inimigos.

Para executar:
1. Instale Pygame Zero: pip install pgzero
2. Execute: pgzrun main.py
"""

import math
import random
from pgzero.rect import Rect

# Configuracoes da janela
WIDTH = 800
HEIGHT = 600
TITLE = "Adventure Platformer"

# Constantes do jogo
GRAVITY = 0.8
JUMP_STRENGTH = -15
PLAYER_SPEED = 5
ENEMY_SPEED = 2
GROUND_Y = 550
ANIMATION_SPEED = 0.15


class GameState:
    """Estados do jogo."""
    MENU = "menu"
    PLAYING = "playing"
    GAME_OVER = "game_over"
    VICTORY = "victory"


class AnimatedSprite:
    """Classe base para sprites animados."""
    
    def __init__(self, x, y, animation_speed=ANIMATION_SPEED):
        self.x = x
        self.y = y
        self.animation_speed = animation_speed
        self.current_frame = 0
        self.animation_timer = 0
        self.facing_right = True
        self.velocity_x = 0
        self.velocity_y = 0
        
    def update_animation(self, dt):
        """Atualiza o frame da animacao."""
        self.animation_timer += dt
        if self.animation_timer >= self.animation_speed:
            self.animation_timer = 0
            self.current_frame += 1
    
    def get_rect(self):
        """Retorna o retangulo de colisao."""
        return Rect(self.x - 20, self.y - 30, 40, 60)


class Player(AnimatedSprite):
    """Classe do jogador com fisica e controles."""
    
    def __init__(self, x, y):
        super().__init__(x, y)
        self.on_ground = False
        self.lives = 3
        self.invincible = False
        self.invincible_timer = 0
        self.is_moving = False
        
    def update(self, dt, platforms, keyboard):
        """Atualiza o jogador a cada frame."""
        # Movimento horizontal
        self.velocity_x = 0
        self.is_moving = False
        
        if keyboard.left or keyboard.a:
            self.velocity_x = -PLAYER_SPEED
            self.facing_right = False
            self.is_moving = True
        elif keyboard.right or keyboard.d:
            self.velocity_x = PLAYER_SPEED
            self.facing_right = True
            self.is_moving = True
        
        # Pulo
        sound_to_play = None
        if (keyboard.space or keyboard.up or keyboard.w) and self.on_ground:
            self.velocity_y = JUMP_STRENGTH
            self.on_ground = False
            sound_to_play = "jump"
        
        # Aplicar gravidade
        self.velocity_y += GRAVITY
        
        # Atualizar posicao
        self.x += self.velocity_x
        self.y += self.velocity_y
        
        # Limitar aos limites da tela
        self.x = max(25, min(WIDTH - 25, self.x))
        
        # Colisao com plataformas
        self.on_ground = False
        
        for platform in platforms:
            if self.check_platform_collision(platform):
                if self.velocity_y > 0:
                    self.y = platform.top - 30
                    self.velocity_y = 0
                    self.on_ground = True
        
        # Chao
        if self.y >= GROUND_Y:
            self.y = GROUND_Y
            self.velocity_y = 0
            self.on_ground = True
        
        # Atualizar invencibilidade
        if self.invincible:
            self.invincible_timer -= dt
            if self.invincible_timer <= 0:
                self.invincible = False
        
        # Atualizar animacao
        self.update_animation(dt)
        
        return sound_to_play
    
    def check_platform_collision(self, platform):
        """Verifica colisao com uma plataforma."""
        player_rect = self.get_rect()
        return (
            player_rect.right > platform.left and
            player_rect.left < platform.right and
            player_rect.bottom >= platform.top and
            player_rect.bottom <= platform.top + 20 and
            self.velocity_y >= 0
        )
    
    def take_damage(self):
        """Recebe dano se nao estiver invencivel."""
        if not self.invincible:
            self.lives -= 1
            self.invincible = True
            self.invincible_timer = 2.0
            return True
        return False


class Enemy(AnimatedSprite):
    """Classe de inimigos com patrulha territorial."""
    
    def __init__(self, x, y, patrol_left, patrol_right):
        super().__init__(x, y)
        self.patrol_left = patrol_left
        self.patrol_right = patrol_right
        self.velocity_x = ENEMY_SPEED
        
    def update(self, dt):
        """Atualiza o inimigo com movimento de patrulha."""
        self.x += self.velocity_x
        
        # Inverter direcao nos limites de patrulha
        if self.x <= self.patrol_left:
            self.x = self.patrol_left
            self.velocity_x = ENEMY_SPEED
            self.facing_right = True
        elif self.x >= self.patrol_right:
            self.x = self.patrol_right
            self.velocity_x = -ENEMY_SPEED
            self.facing_right = False
        
        self.update_animation(dt)
    
    def check_collision_with_player(self, player):
        """Verifica colisao com o jogador."""
        enemy_rect = self.get_rect()
        player_rect = player.get_rect()
        return enemy_rect.colliderect(player_rect)


class Platform:
    """Classe para plataformas do jogo."""
    
    def __init__(self, x, y, width, height=20):
        self.rect = Rect(x, y, width, height)
        self.x = x
        self.y = y
        self.width = width
        self.height = height
    
    @property
    def left(self):
        return self.rect.left
    
    @property
    def right(self):
        return self.rect.right
    
    @property
    def top(self):
        return self.rect.top
    
    @property
    def bottom(self):
        return self.rect.bottom


class Button:
    """Classe para botoes do menu."""
    
    def __init__(self, x, y, text, width=200, height=50):
        self.rect = Rect(x - width // 2, y - height // 2, width, height)
        self.text = text
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.hovered = False
        
    def is_clicked(self, pos):
        """Verifica se o botao foi clicado."""
        return self.rect.collidepoint(pos)
    
    def update_hover(self, pos):
        """Atualiza estado de hover."""
        self.hovered = self.rect.collidepoint(pos)
    
    def draw(self, screen):
        """Desenha o botao."""
        color = (100, 150, 200) if self.hovered else (70, 120, 170)
        border_color = (150, 200, 255) if self.hovered else (100, 150, 200)
        
        screen.draw.filled_rect(self.rect, color)
        screen.draw.rect(self.rect, border_color)
        
        screen.draw.text(
            self.text,
            center=(self.x, self.y),
            fontsize=24,
            color="white",
            shadow=(1, 1),
            scolor="black"
        )


class Game:
    """Classe principal do jogo."""
    
    def __init__(self):
        self.state = GameState.MENU
        self.sound_enabled = True
        self.music_playing = False
        self.reset_game()
        self.create_menu_buttons()
        
    def create_menu_buttons(self):
        """Cria os botoes do menu."""
        self.btn_play = Button(WIDTH // 2, 250, "JOGAR")
        self.btn_sound = Button(WIDTH // 2, 320, "SOM: LIGADO")
        self.btn_exit = Button(WIDTH // 2, 390, "SAIR")
        
    def reset_game(self):
        """Reinicia o jogo para o estado inicial."""
        self.player = Player(100, GROUND_Y)
        self.enemies = []
        self.platforms = []
        self.create_level()
        
    def create_level(self):
        """Cria as plataformas e inimigos do nivel."""
        self.platforms = [
            Platform(150, 450, 200),
            Platform(450, 400, 200),
            Platform(250, 300, 150),
            Platform(500, 250, 200),
            Platform(100, 200, 150),
            Platform(600, 150, 150),
        ]
        
        self.enemies = [
            Enemy(200, 420, 150, 330),
            Enemy(500, 370, 450, 630),
            Enemy(300, 270, 250, 380),
            Enemy(550, 220, 500, 680),
        ]
    
    def update(self, dt, keyboard):
        """Atualiza o estado do jogo."""
        if self.state == GameState.PLAYING:
            sound_to_play = self.player.update(dt, self.platforms, keyboard)
            if sound_to_play == "jump" and self.sound_enabled:
                try:
                    sounds.jump.play()
                except:
                    pass
            
            for enemy in self.enemies:
                enemy.update(dt)
                
                if enemy.check_collision_with_player(self.player):
                    if self.player.take_damage():
                        if self.sound_enabled:
                            try:
                                sounds.hurt.play()
                            except:
                                pass
            
            if self.player.lives <= 0:
                self.state = GameState.GAME_OVER
            
            if self.player.x > 700 and self.player.y < 180:
                self.state = GameState.VICTORY
    
    def handle_click(self, pos):
        """Processa cliques do mouse."""
        if self.state == GameState.MENU:
            if self.btn_play.is_clicked(pos):
                self.state = GameState.PLAYING
                self.reset_game()
                self.start_music()
            elif self.btn_sound.is_clicked(pos):
                self.sound_enabled = not self.sound_enabled
                self.btn_sound.text = "SOM: " + ("LIGADO" if self.sound_enabled else "DESLIGADO")
                if not self.sound_enabled:
                    self.stop_music()
                else:
                    self.start_music()
            elif self.btn_exit.is_clicked(pos):
                exit()
        
        elif self.state in (GameState.GAME_OVER, GameState.VICTORY):
            self.state = GameState.MENU
            self.stop_music()
    
    def handle_mouse_move(self, pos):
        """Processa movimento do mouse para hover."""
        if self.state == GameState.MENU:
            self.btn_play.update_hover(pos)
            self.btn_sound.update_hover(pos)
            self.btn_exit.update_hover(pos)
    
    def start_music(self):
        """Inicia a musica de fundo."""
        if self.sound_enabled and not self.music_playing:
            try:
                music.play("background")
                music.set_volume(0.5)
                self.music_playing = True
            except:
                pass
    
    def stop_music(self):
        """Para a musica de fundo."""
        try:
            music.stop()
            self.music_playing = False
        except:
            pass
    
    def draw(self, screen):
        """Desenha o jogo na tela."""
        screen.fill((40, 44, 52))
        
        if self.state == GameState.MENU:
            self.draw_menu(screen)
        elif self.state == GameState.PLAYING:
            self.draw_game(screen)
        elif self.state == GameState.GAME_OVER:
            self.draw_game_over(screen)
        elif self.state == GameState.VICTORY:
            self.draw_victory(screen)
    
    def draw_menu(self, screen):
        """Desenha o menu principal."""
        screen.draw.text(
            "ADVENTURE PLATFORMER",
            center=(WIDTH // 2, 120),
            fontsize=48,
            color=(255, 215, 0),
            shadow=(2, 2),
            scolor="black"
        )
        
        screen.draw.text(
            "Uma aventura emocionante te espera!",
            center=(WIDTH // 2, 170),
            fontsize=20,
            color=(200, 200, 200)
        )
        
        self.btn_play.draw(screen)
        self.btn_sound.draw(screen)
        self.btn_exit.draw(screen)
        
        screen.draw.text(
            "Controles: WASD ou Setas para mover, ESPACO para pular",
            center=(WIDTH // 2, 500),
            fontsize=16,
            color=(150, 150, 150)
        )
        screen.draw.text(
            "Objetivo: Chegue ao topo direito sem perder todas as vidas!",
            center=(WIDTH // 2, 530),
            fontsize=16,
            color=(150, 150, 150)
        )
    
    def draw_game(self, screen):
        """Desenha o jogo durante a partida."""
        # Desenhar chao
        screen.draw.filled_rect(Rect(0, GROUND_Y + 30, WIDTH, HEIGHT - GROUND_Y), (60, 70, 80))
        screen.draw.line((0, GROUND_Y + 30), (WIDTH, GROUND_Y + 30), (100, 120, 140))
        
        # Desenhar area de vitoria
        screen.draw.filled_rect(Rect(700, 100, 100, 80), (50, 200, 100))
        screen.draw.text("META", center=(750, 140), fontsize=20, color="white")
        
        # Desenhar plataformas
        for platform in self.platforms:
            screen.draw.filled_rect(platform.rect, (80, 90, 100))
            screen.draw.rect(platform.rect, (120, 130, 140))
        
        # Desenhar inimigos
        for enemy in self.enemies:
            self.draw_enemy(screen, enemy)
        
        # Desenhar jogador
        if not (self.player.invincible and int(self.player.invincible_timer * 10) % 2 == 0):
            self.draw_player(screen)
        
        # HUD - Vidas (coracoes)
        for i in range(self.player.lives):
            screen.draw.filled_circle((30 + i * 30, 30), 10, (220, 50, 50))
        
        screen.draw.text(
            "ESC: Menu",
            topright=(WIDTH - 20, 20),
            fontsize=16,
            color=(150, 150, 150)
        )
    
    def draw_player(self, screen):
        """Desenha o jogador com animacao."""
        color = (80, 150, 220)
        
        # Corpo
        screen.draw.filled_circle((int(self.player.x), int(self.player.y - 20)), 18, color)
        screen.draw.filled_rect(Rect(self.player.x - 12, self.player.y - 8, 24, 32), color)
        
        # Olhos
        eye_offset = 4 if self.player.facing_right else -4
        screen.draw.filled_circle((int(self.player.x + eye_offset - 4), int(self.player.y - 24)), 3, "white")
        screen.draw.filled_circle((int(self.player.x + eye_offset + 4), int(self.player.y - 24)), 3, "white")
        screen.draw.filled_circle((int(self.player.x + eye_offset - 4), int(self.player.y - 24)), 1, "black")
        screen.draw.filled_circle((int(self.player.x + eye_offset + 4), int(self.player.y - 24)), 1, "black")
        
        # Pernas animadas
        if self.player.is_moving:
            leg_offset = int(math.sin(self.player.current_frame * 0.5) * 8)
        else:
            # Animacao de respiracao quando parado
            leg_offset = int(math.sin(self.player.current_frame * 0.3) * 2)
        
        leg_y = self.player.y + 20
        screen.draw.line(
            (self.player.x - 6, leg_y),
            (self.player.x - 6 - leg_offset, leg_y + 18),
            color
        )
        screen.draw.line(
            (self.player.x + 6, leg_y),
            (self.player.x + 6 + leg_offset, leg_y + 18),
            color
        )
        
        # Bracos animados
        arm_offset = int(math.sin(self.player.current_frame * 0.4) * 4)
        screen.draw.line(
            (self.player.x - 12, self.player.y),
            (self.player.x - 20, self.player.y + 10 + arm_offset),
            color
        )
        screen.draw.line(
            (self.player.x + 12, self.player.y),
            (self.player.x + 20, self.player.y + 10 - arm_offset),
            color
        )
    
    def draw_enemy(self, screen, enemy):
        """Desenha um inimigo com animacao."""
        color = (200, 80, 80)
        
        # Corpo
        screen.draw.filled_circle((int(enemy.x), int(enemy.y - 15)), 20, color)
        screen.draw.filled_rect(Rect(enemy.x - 15, enemy.y - 5, 30, 35), color)
        
        # Olhos
        eye_offset = 5 if enemy.facing_right else -5
        screen.draw.filled_circle((int(enemy.x + eye_offset - 5), int(enemy.y - 20)), 4, "white")
        screen.draw.filled_circle((int(enemy.x + eye_offset + 5), int(enemy.y - 20)), 4, "white")
        screen.draw.filled_circle((int(enemy.x + eye_offset - 5), int(enemy.y - 20)), 2, "black")
        screen.draw.filled_circle((int(enemy.x + eye_offset + 5), int(enemy.y - 20)), 2, "black")
        
        # Pernas animadas
        leg_offset = int(math.sin(enemy.current_frame * 0.5) * 6)
        screen.draw.line(
            (enemy.x - 8, enemy.y + 25),
            (enemy.x - 8 - leg_offset, enemy.y + 45),
            color
        )
        screen.draw.line(
            (enemy.x + 8, enemy.y + 25),
            (enemy.x + 8 + leg_offset, enemy.y + 45),
            color
        )
    
    def draw_game_over(self, screen):
        """Desenha tela de game over."""
        screen.draw.text(
            "GAME OVER",
            center=(WIDTH // 2, HEIGHT // 2 - 40),
            fontsize=64,
            color=(220, 50, 50),
            shadow=(3, 3),
            scolor="black"
        )
        screen.draw.text(
            "Clique para voltar ao menu",
            center=(WIDTH // 2, HEIGHT // 2 + 40),
            fontsize=24,
            color="white"
        )
    
    def draw_victory(self, screen):
        """Desenha tela de vitoria."""
        screen.draw.text(
            "VITORIA!",
            center=(WIDTH // 2, HEIGHT // 2 - 40),
            fontsize=64,
            color=(50, 220, 100),
            shadow=(3, 3),
            scolor="black"
        )
        screen.draw.text(
            "Parabens! Voce completou o nivel!",
            center=(WIDTH // 2, HEIGHT // 2 + 20),
            fontsize=24,
            color="white"
        )
        screen.draw.text(
            "Clique para voltar ao menu",
            center=(WIDTH // 2, HEIGHT // 2 + 60),
            fontsize=20,
            color=(200, 200, 200)
        )


# Instancia global do jogo
game = Game()


def update():
    """Funcao de atualizacao chamada pelo PgZero."""
    dt = 1/60
    game.update(dt, keyboard)


def draw():
    """Funcao de desenho chamada pelo PgZero."""
    game.draw(screen)


def on_mouse_down(pos):
    """Evento de clique do mouse."""
    game.handle_click(pos)


def on_mouse_move(pos):
    """Evento de movimento do mouse."""
    game.handle_mouse_move(pos)


def on_key_down(key):
    """Evento de tecla pressionada."""
    if key == keys.ESCAPE:
        if game.state == GameState.PLAYING:
            game.state = GameState.MENU
            game.stop_music()
