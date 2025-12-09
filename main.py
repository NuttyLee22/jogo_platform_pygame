# -*- coding: utf-8 -*-
import math
import random
import pygame
import os
from pgzero.rect import Rect

# Centralizar janela na primeira execucao
os.environ['SDL_VIDEO_CENTERED'] = '1'

# Configuracoes da janela
WIDTH = 800
HEIGHT = 600
TITLE = "Elden Thing"

# Constantes do jogo
GRAVITY = 0.8
JUMP_STRENGTH = -15
PLAYER_SPEED = 5
ENEMY_SPEED = 2
GROUND_Y = 550
ANIMATION_SPEED = 0.15
SPRITE_SCALE = 0.35  # Escala dos sprites (35% do tamanho original - menores e mais responsivos)
ATTACK_RANGE = 80  # Alcance do ataque (aumentado para ser mais facil acertar)
ATTACK_DURATION = 0.3  # Duracao da animacao de ataque
COLLECTIBLES_NEEDED = 3  # Quantos coletaveis sao necessarios para abrir a saida


class GameState:
    """Estados do jogo."""
    MENU = "menu"
    INSTRUCTIONS = "instructions"
    PLAYING = "playing"
    BOSS_ROOM = "boss_room"
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
        # Ajustado para sprites menores (escala 0.35)
        base_width = 40 * SPRITE_SCALE
        base_height = 60 * SPRITE_SCALE
        return Rect(self.x - base_width // 2, self.y - base_height // 2, base_width, base_height)


class Player(AnimatedSprite):
    """Classe do jogador com fisica e controles."""
    
    def __init__(self, x, y):
        super().__init__(x, y)
        self.on_ground = False
        self.lives = 3
        self.invincible = False
        self.invincible_timer = 0
        self.is_moving = False
        self.is_attacking = False
        self.attack_timer = 0
        self.attack_hit_this_frame = False  # Evitar multiplos hits no mesmo ataque
        self.attack_sound_played = False  # Flag para tocar som apenas uma vez
        self.show_impact = False  # Flag para mostrar sprite de impacto
        self.impact_timer = 0  # Timer para o sprite de impacto
        self.impact_x = 0  # Posicao X do impacto
        self.impact_y = 0  # Posicao Y do impacto
        self.collectibles_collected = 0
        # Sprites disponiveis
        self.images_idle = ["hero_paused"]
        self.images_walk = ["hero_walk_01", "hero_walk_02"]
        self.images_attack = ["hero_attack_02"]
        self.images_attack_impact = ["hero_attack_impact"]
        self.current_sprite_index = 0
        self.attack_frame = 0
        
    def update(self, dt, platforms, keyboard):
        """Atualiza o jogador a cada frame."""
        # Movimento horizontal (APENAS SETAS)
        self.velocity_x = 0
        self.is_moving = False
        
        if keyboard.left:
            self.velocity_x = -PLAYER_SPEED
            self.facing_right = False
            self.is_moving = True
        elif keyboard.right:
            self.velocity_x = PLAYER_SPEED
            self.facing_right = True
            self.is_moving = True
        
        # Pulo (APENAS SETA PARA CIMA OU ESPACO)
        sound_to_play = None
        if (keyboard.space or keyboard.up) and self.on_ground:
            self.velocity_y = JUMP_STRENGTH
            self.on_ground = False
            sound_to_play = "jump"
        
        # Aplicar gravidade
        self.velocity_y += GRAVITY
        
        # Atualizar posicao
        self.x += self.velocity_x
        self.y += self.velocity_y
        
        # Limitar aos limites da tela (usando tamanho do sprite)
        sprite_width = 40 * SPRITE_SCALE
        sprite_height = 60 * SPRITE_SCALE
        # Limites mais rigorosos - nao passar das bordas
        min_x = sprite_width // 2 + 5
        max_x = WIDTH - sprite_width // 2 - 5
        self.x = max(min_x, min(max_x, self.x))
        # Limitar altura - nao passar acima do topo
        min_y = sprite_height // 2
        self.y = max(min_y, self.y)
        
        # Colisao com plataformas
        self.on_ground = False
        
        for platform in platforms:
            if self.check_platform_collision(platform):
                if self.velocity_y > 0:
                    # Ajustar posicao para ficar em cima da plataforma (pes na superficie)
                    sprite_height = 60 * SPRITE_SCALE
                    # Centralizar o sprite com os pes na parte superior da plataforma
                    self.y = platform.top - sprite_height // 2
                    self.velocity_y = 0
                    self.on_ground = True
                    break  # Sair apos encontrar primeira colisao
        
        # Chao - nao permitir passar abaixo (ajustar para pes no chao) - VERIFICAR DEPOIS DAS PLATAFORMAS
        ground_surface = GROUND_Y  # A superficie do chao
        sprite_height = 60 * SPRITE_SCALE
        feet_position = self.y + sprite_height // 2  # Posicao dos pes do personagem

        # Verificar se os pes estao no chao ou abaixo dele
        if feet_position > ground_surface:
            # Garantir que o personagem nao passe atraves do chao
            self.y = ground_surface - sprite_height // 2
            # Se estava caindo, parar a queda imediatamente
            if self.velocity_y > 0:
                self.velocity_y = 0
            self.on_ground = True
        elif feet_position == ground_surface:
            # Se os pes estao exatamente no chao, garantir que nao caia mais
            if self.velocity_y > 0:
                self.velocity_y = 0
            self.on_ground = True
        
        # Atualizar invencibilidade
        if self.invincible:
            self.invincible_timer -= dt
            if self.invincible_timer <= 0:
                self.invincible = False
        
        # Atualizar ataque
        if self.is_attacking:
            self.attack_timer -= dt
            if self.attack_timer <= 0:
                self.is_attacking = False
                self.attack_hit_this_frame = False  # Resetar ao terminar ataque
            else:
                # Usar sempre frame 0 (so temos hero_attack_02)
                self.attack_frame = 0
                # Resetar flag de som quando ataque termina
                if self.attack_timer <= 0:
                    self.attack_sound_played = False
        else:
            # Resetar flag de som quando nao esta atacando
            self.attack_sound_played = False
        
        # Atualizar sprite de impacto
        if self.show_impact:
            self.impact_timer += dt
            if self.impact_timer >= 0.15:  # Mostrar por 0.15 segundos
                self.show_impact = False
                self.impact_timer = 0
        
        # Atualizar animacao
        self.update_animation(dt)
        
        # Atualizar indice do sprite baseado no estado
        if self.is_attacking:
            # Usar frame de ataque
            self.current_sprite_index = self.attack_frame
        elif self.is_moving:
            # Alternar entre os dois sprites de caminhada
            self.current_sprite_index = int(self.current_frame) % len(self.images_walk)
        else:
            # Sprite parado
            self.current_sprite_index = 0
        
        return sound_to_play
    
    def attack(self):
        """Inicia um ataque."""
        if not self.is_attacking:
            self.is_attacking = True
            self.attack_timer = ATTACK_DURATION
            self.attack_frame = 0
            self.attack_hit_this_frame = False  # Resetar flag de hit
            self.attack_sound_played = False  # Flag para tocar som apenas uma vez
    
    def get_attack_rect(self):
        """Retorna o retangulo de area de ataque."""
        base_size = 40 * SPRITE_SCALE
        attack_width = ATTACK_RANGE  # Range maior agora (80 pixels)
        attack_height = base_size * 1.5  # Altura maior para facilitar acertar
        offset_x = base_size // 2 + 10  # Comecar um pouco mais longe
        if self.facing_right:
            return Rect(self.x + offset_x, self.y - base_size // 2 - 10, attack_width, attack_height)
        else:
            return Rect(self.x - offset_x - attack_width, self.y - base_size // 2 - 10, attack_width, attack_height)
    
    def check_platform_collision(self, platform):
        """Verifica colisao com uma plataforma."""
        player_rect = self.get_rect()
        # Colisao mais precisa - verifica se esta caindo e se os pes estao sobre a plataforma
        return (
            player_rect.right > platform.left + 5 and
            player_rect.left < platform.right - 5 and
            player_rect.bottom >= platform.top - 5 and
            player_rect.bottom <= platform.top + 15 and
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


class Collectible:
    """Classe para coletaveis."""
    
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.collected = False
        self.rotation = 0
    
    def get_rect(self):
        """Retorna o retangulo de colisao."""
        return Rect(self.x - 15, self.y - 15, 30, 30)
    
    def check_collision_with_player(self, player):
        """Verifica colisao com o jogador."""
        if self.collected:
            return False
        collectible_rect = self.get_rect()
        player_rect = player.get_rect()
        return collectible_rect.colliderect(player_rect)


class Boss(AnimatedSprite):
    """Classe para o boss."""
    
    def __init__(self, x, y):
        super().__init__(x, y)
        self.max_health = 100
        self.health = self.max_health
        self.alive = True
        self.velocity_x = 1.5
        self.facing_right = True
        self.hit_effect = False
        self.hit_effect_timer = 0
        # Sprites do boss (usando sprites de inimigo)
        self.images_idle = ["enemy_paused"]
        self.images_walk = ["enemy_walk_01", "enemy_walk_02"]
        self.images_attack = ["enemy_attack_01"]
        self.current_sprite_index = 0
        self.attack_cooldown = 0
        self.attack_range = 40
    
    def update(self, dt, player):
        """Atualiza o boss."""
        if not self.alive:
            return
        
        # Limites da tela - mais rigorosos
        sprite_width = 40 * SPRITE_SCALE
        sprite_height = 60 * SPRITE_SCALE
        min_x = sprite_width // 2 + 5
        max_x = WIDTH - sprite_width // 2 - 5
        
        # Garantir que o boss esta sempre no chao (GROUND_Y e onde os pes devem estar)
        self.y = GROUND_Y
        
        # Movimento melhorado em direcao ao jogador
        distance_to_player = abs(self.x - player.x)
        
        # Sempre perseguir o jogador se estiver longe
        if distance_to_player > 40:  # Se estiver longe, perseguir
            if self.x < player.x:
                self.velocity_x = 1.5  # Velocidade fixa
                self.facing_right = True
            else:
                self.velocity_x = -1.5
                self.facing_right = False
        else:
            # Se estiver perto, parar e atacar
            self.velocity_x = 0
        
        # Aplicar movimento
        self.x += self.velocity_x * dt * 60
        
        # Aplicar limites - nao permitir sair da tela
        self.x = max(min_x, min(max_x, self.x))
        
        # Atualizar efeito de hit
        if self.hit_effect:
            self.hit_effect_timer += dt
            if self.hit_effect_timer >= 0.2:
                self.hit_effect = False
                self.hit_effect_timer = 0
        
        # Atacar se proximo do jogador
        if distance_to_player < self.attack_range and self.attack_cooldown <= 0:
            self.attack_cooldown = 2.0  # 2 segundos entre ataques
            # Causar dano ao jogador
            if player.take_damage():
                pass  # Som ja e tocado na funcao take_damage
        
        if self.attack_cooldown > 0:
            self.attack_cooldown -= dt
        
        self.update_animation(dt)
        self.current_sprite_index = int(self.current_frame) % len(self.images_walk)
    
    def take_damage(self, amount=10):
        """Recebe dano."""
        if self.alive:
            self.health -= amount
            if self.health <= 0:
                self.health = 0
                self.alive = False
    
    def get_rect(self):
        """Retorna o retangulo de colisao."""
        base_width = 40 * SPRITE_SCALE
        base_height = 60 * SPRITE_SCALE
        return Rect(self.x - base_width // 2, self.y - base_height // 2, base_width, base_height)


class Enemy(AnimatedSprite):
    """Classe de inimigos com patrulha territorial."""
    
    def __init__(self, x, y, patrol_left, patrol_right):
        super().__init__(x, y)
        self.patrol_left = patrol_left
        self.patrol_right = patrol_right
        self.velocity_x = ENEMY_SPEED
        self.alive = True
        self.hit_effect = False
        self.hit_effect_timer = 0
        # Sprites disponiveis
        self.images_idle = ["enemy_paused"]
        self.images_walk = ["enemy_walk_01", "enemy_walk_02"]
        self.current_sprite_index = 0
        
    def update(self, dt):
        """Atualiza o inimigo com movimento de patrulha."""
        if not self.alive:
            return
        
        # Limites da tela - mais rigorosos
        sprite_width = 40 * SPRITE_SCALE
        min_x = sprite_width // 2 + 5
        max_x = WIDTH - sprite_width // 2 - 5
        self.x += self.velocity_x
        self.x = max(min_x, min(max_x, self.x))
        
        # Limitar altura tambem
        sprite_height = 60 * SPRITE_SCALE
        max_y = GROUND_Y - sprite_height // 2
        self.y = min(max_y, max(sprite_height // 2, self.y))
        
        # Inverter direcao nos limites de patrulha
        if self.x <= self.patrol_left:
            self.x = self.patrol_left
            self.velocity_x = ENEMY_SPEED
            self.facing_right = True
        elif self.x >= self.patrol_right:
            self.x = self.patrol_right
            self.velocity_x = -ENEMY_SPEED
            self.facing_right = False
        
        # Atualizar efeito de hit
        if self.hit_effect:
            self.hit_effect_timer += dt
            if self.hit_effect_timer >= 0.2:
                self.hit_effect = False
                self.hit_effect_timer = 0
        
        self.update_animation(dt)
        
        # Atualizar indice do sprite de caminhada
        self.current_sprite_index = int(self.current_frame) % len(self.images_walk)
    
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
        # Inicializar mixer do pygame para garantir que funcione
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
        except:
            pass
        self.load_sprites()
        self.reset_game()
        self.create_menu_buttons()
        # Sistema de ondas de inimigos (estilo Castlevania)
        self.current_wave = 0
        self.total_waves = 3  # 3 inimigos no total
        self.enemy_spawn_timer = 0
        self.enemy_spawn_delay = 1.0  # Delay entre spawns
    
    def load_sprites(self):
        """Pre-carrega todos os sprites do jogo."""
        try:
            # Funcao auxiliar para redimensionar sprites
            def scale_sprite(img):
                new_width = int(img.get_width() * SPRITE_SCALE)
                new_height = int(img.get_height() * SPRITE_SCALE)
                return pygame.transform.scale(img, (new_width, new_height))
            
            # Carregar sprites do jogador (direita e esquerda) - apenas attack_02
            idle_r = scale_sprite(pygame.image.load("images/hero_paused.png").convert_alpha())
            walk0_r = scale_sprite(pygame.image.load("images/hero_walk_01.png").convert_alpha())
            walk1_r = scale_sprite(pygame.image.load("images/hero_walk_02.png").convert_alpha())
            attack1_r = scale_sprite(pygame.image.load("images/hero_attack_02.png").convert_alpha())
            
            self.player_sprites = {
                'idle_r': idle_r,
                'idle_l': pygame.transform.flip(idle_r, True, False),
                'walk_0_r': walk0_r,
                'walk_0_l': pygame.transform.flip(walk0_r, True, False),
                'walk_1_r': walk1_r,
                'walk_1_l': pygame.transform.flip(walk1_r, True, False),
                'attack_0_r': attack1_r,
                'attack_0_l': pygame.transform.flip(attack1_r, True, False),
            }
            
            # Carregar sprites dos inimigos (direita e esquerda)
            enemy_walk0_r = scale_sprite(pygame.image.load("images/enemy_walk_01.png").convert_alpha())
            enemy_walk1_r = scale_sprite(pygame.image.load("images/enemy_walk_02.png").convert_alpha())
            
            self.enemy_sprites = {
                'walk_0_r': enemy_walk0_r,
                'walk_0_l': pygame.transform.flip(enemy_walk0_r, True, False),
                'walk_1_r': enemy_walk1_r,
                'walk_1_l': pygame.transform.flip(enemy_walk1_r, True, False),
            }
            
            # Sprites do boss (usando sprites de inimigo, tamanho 1x1 = mesmo tamanho)
            try:
                enemy_attack_r = scale_sprite(pygame.image.load("images/enemy_attack_01.png").convert_alpha())
                self.boss_sprites = {
                    'walk_0_r': enemy_walk0_r,
                    'walk_0_l': pygame.transform.flip(enemy_walk0_r, True, False),
                    'walk_1_r': enemy_walk1_r,
                    'walk_1_l': pygame.transform.flip(enemy_walk1_r, True, False),
                    'attack_0_r': enemy_attack_r,
                    'attack_0_l': pygame.transform.flip(enemy_attack_r, True, False),
                }
            except:
                # Se nao tiver sprite de ataque, usar apenas os de caminhada
                self.boss_sprites = {
                    'walk_0_r': enemy_walk0_r,
                    'walk_0_l': pygame.transform.flip(enemy_walk0_r, True, False),
                    'walk_1_r': enemy_walk1_r,
                    'walk_1_l': pygame.transform.flip(enemy_walk1_r, True, False),
                }
        except Exception as e:
            print(f"Erro ao carregar sprites: {e}")
            self.player_sprites = None
            self.enemy_sprites = None
            self.boss_sprites = None
        
    def create_menu_buttons(self):
        """Cria os botoes do menu."""
        self.btn_play = Button(WIDTH // 2, 250, "JOGAR")
        self.btn_sound = Button(WIDTH // 2, 320, "SOM: LIGADO")
        self.btn_exit = Button(WIDTH // 2, 390, "SAIR")
        
    def reset_game(self):
        """Reinicia o jogo para o estado inicial."""
        self.player = Player(100, GROUND_Y)
        self.player.collectibles_collected = 0
        self.enemies = []
        self.platforms = []  # Sem plataformas - estilo Castlevania
        self.collectibles = []  # Sem coletaveis
        self.boss = None
        self.exit_locked = True
        self.current_wave = 0
        self.enemy_spawn_timer = 0
        self.create_level()
        
    def create_level(self):
        """Cria o nivel estilo Castlevania - corredor horizontal sem plataformas."""
        # Sem plataformas - estilo Castlevania
        self.platforms = []
        self.collectibles = []
        
        # Inimigos serao spawnados sequencialmente (sistema de ondas)
        self.enemies = []
        self.current_wave = 0
        self.enemy_spawn_timer = 0
        
        # Porta do boss trancada ate matar todos os inimigos
        self.exit_locked = True
    
    def update(self, dt, keyboard):
        """Atualiza o estado do jogo."""
        if self.state == GameState.PLAYING:
            sound_to_play = self.player.update(dt, self.platforms, keyboard)
            if sound_to_play == "jump" and self.sound_enabled:
                try:
                    sounds.jump.play()
                except:
                    pass
            
            # Sistema de ondas de inimigos (estilo Castlevania)
            # Spawnar primeiro inimigo se nao houver nenhum
            if len(self.enemies) == 0 and self.current_wave == 0:
                sprite_height = 60 * SPRITE_SCALE
                spawn_x = 600  # Spawnar a direita
                spawn_y = GROUND_Y  # No chao
                patrol_left = spawn_x - 150
                patrol_right = min(WIDTH - 100, spawn_x + 150)
                self.enemies.append(Enemy(spawn_x, spawn_y, patrol_left, patrol_right))
                self.current_wave = 1
                self.enemy_spawn_timer = 0
            
            # Spawnar proximo inimigo se nao houver inimigos vivos e ainda houver ondas
            alive_enemies = [e for e in self.enemies if e.alive]
            if len(alive_enemies) == 0 and self.current_wave < self.total_waves:
                self.enemy_spawn_timer += dt
                if self.enemy_spawn_timer >= self.enemy_spawn_delay:
                    # Spawnar proximo inimigo
                    sprite_height = 60 * SPRITE_SCALE
                    spawn_x = 600 + (self.current_wave * 50)  # Spawnar mais a direita
                    spawn_y = GROUND_Y  # No chao
                    patrol_left = spawn_x - 150
                    patrol_right = min(WIDTH - 100, spawn_x + 150)
                    self.enemies.append(Enemy(spawn_x, spawn_y, patrol_left, patrol_right))
                    self.current_wave += 1
                    self.enemy_spawn_timer = 0
            
            # Desbloquear saida quando todos os inimigos forem mortos
            if len([e for e in self.enemies if e.alive]) == 0 and self.current_wave >= self.total_waves:
                self.exit_locked = False
            
            # Verificar ataque do jogador (apenas uma vez por ataque)
            if self.player.is_attacking and not self.player.attack_hit_this_frame:
                attack_rect = self.player.get_attack_rect()
                hit_something = False
                for enemy in self.enemies[:]:  # Copia da lista para permitir remocao
                    if enemy.alive and enemy.get_rect().colliderect(attack_rect):
                        enemy.alive = False
                        # Efeito visual de hit (sera desenhado no proximo frame)
                        enemy.hit_effect = True
                        hit_something = True
                        # Mostrar sprite de impacto na posicao do hit
                        self.player.show_impact = True
                        self.player.impact_timer = 0
                        self.player.impact_x = enemy.x
                        self.player.impact_y = enemy.y
                        # Tocar som de slash quando acerta (sempre tocar, sem flag)
                        if self.sound_enabled:
                            try:
                                sounds.slash_sound.play()
                            except:
                                pass
                        if self.sound_enabled:
                            try:
                                sounds.hurt.play()
                            except:
                                pass
                if hit_something:
                    self.player.attack_hit_this_frame = True
            
            # Atualizar e verificar colisao com inimigos vivos
            for enemy in self.enemies:
                if enemy.alive:
                    enemy.update(dt)
                    
                    if enemy.check_collision_with_player(self.player):
                        if self.player.take_damage():
                            if self.sound_enabled:
                                try:
                                    sounds.hurt.play()
                                except:
                                    pass
            
            # Remover inimigos mortos
            self.enemies = [e for e in self.enemies if e.alive]
            
            if self.player.lives <= 0:
                self.state = GameState.GAME_OVER
            
            # Verificar entrada na porta do boss (nao trancada)
            exit_x = WIDTH - 50  # Centro da porta
            exit_y = GROUND_Y - 50  # Posicao da porta (no chao)
            if not self.exit_locked and abs(self.player.x - exit_x) < 50 and abs(self.player.y - exit_y) < 60:
                # Entrar na boss room
                self.enter_boss_room()
        
        elif self.state == GameState.BOSS_ROOM:
            sound_to_play = self.player.update(dt, self.platforms, keyboard)
            if sound_to_play == "jump" and self.sound_enabled:
                try:
                    sounds.jump.play()
                except:
                    pass
            
            # Atualizar boss
            if self.boss and self.boss.alive:
                self.boss.update(dt, self.player)
            
            # Verificar ataque do jogador no boss (apenas uma vez por ataque)
            if self.player.is_attacking and not self.player.attack_hit_this_frame and self.boss and self.boss.alive:
                attack_rect = self.player.get_attack_rect()
                if self.boss.get_rect().colliderect(attack_rect):
                    self.boss.take_damage(10)
                    # Efeito visual de hit no boss
                    self.boss.hit_effect = True
                    self.boss.hit_effect_timer = 0
                    self.player.attack_hit_this_frame = True  # Marcar que ja acertou neste ataque
                    # Mostrar sprite de impacto na posicao do hit
                    self.player.show_impact = True
                    self.player.impact_timer = 0
                    self.player.impact_x = self.boss.x
                    self.player.impact_y = self.boss.y
                    # Tocar som de slash quando acerta (sempre tocar, sem flag)
                    if self.sound_enabled:
                        try:
                            sounds.slash_sound.play()
                        except:
                            pass
                    if self.sound_enabled:
                        try:
                            sounds.hurt.play()
                        except:
                            pass
            
            # Verificar colisao com boss
            if self.boss and self.boss.alive and self.boss.get_rect().colliderect(self.player.get_rect()):
                if self.player.take_damage():
                    if self.sound_enabled:
                        try:
                            sounds.hurt.play()
                        except:
                            pass
            
            if self.player.lives <= 0:
                self.state = GameState.GAME_OVER
            
            # Vitoria se boss morrer
            if self.boss and not self.boss.alive:
                self.state = GameState.VICTORY
    
    def enter_boss_room(self):
        """Entra na sala do boss."""
        self.state = GameState.BOSS_ROOM
        # Parar musica atual e tocar musica do boss
        self.stop_music()
        if self.sound_enabled:
            try:
                # Inicializar mixer se necessario
                if not pygame.mixer.get_init():
                    pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
                
                # Tentar carregar e tocar a musica do boss usando pygame.mixer diretamente
                import os
                music_path = os.path.join("music", "boss_theme.wav")
                if os.path.exists(music_path):
                    pygame.mixer.music.load(music_path)
                    pygame.mixer.music.play(-1)  # -1 para loop infinito
                    pygame.mixer.music.set_volume(0.35)
                    self.music_playing = True
                    print(f"Musica do boss carregada com sucesso: {music_path}")
                else:
                    print(f"Arquivo de musica nao encontrado: {music_path}")
                    print(f"Diretorio atual: {os.getcwd()}")
                    if os.path.exists("music"):
                        print(f"Arquivos em music/: {os.listdir('music')}")
                    else:
                        print("Diretorio music/ nao existe")
            except Exception as e:
                print(f"Erro ao tocar musica do boss: {e}")
                import traceback
                traceback.print_exc()
        # Criar boss no centro da tela - posicao inicial corrigida
        sprite_height = 60 * SPRITE_SCALE
        sprite_width = 40 * SPRITE_SCALE
        # Posicionar boss no centro, pes no chao (GROUND_Y e onde os pes devem estar)
        self.boss = Boss(WIDTH // 2, GROUND_Y)
        # Resetar velocidade do boss para evitar pulo inicial
        self.boss.velocity_x = 1.5  # Inicializar com velocidade normal
        self.boss.facing_right = False  # Comecar virado para o jogador
        # Resetar posicao do jogador - lado esquerdo
        self.player.x = sprite_width // 2 + 80
        self.player.y = GROUND_Y
        # Resetar velocidade do jogador
        self.player.velocity_x = 0
        self.player.velocity_y = 0
        # Plataformas melhoradas para a boss room - mais baixas
        self.platforms = [
            Platform(0, GROUND_Y, WIDTH, 20),  # Chao principal
            Platform(100, GROUND_Y - 120, 180, 20),  # Plataforma esquerda (mais baixa)
            Platform(520, GROUND_Y - 120, 180, 20),  # Plataforma direita (mais baixa)
            Platform(200, GROUND_Y - 220, 140, 20),  # Plataforma superior esquerda
            Platform(460, GROUND_Y - 220, 140, 20),  # Plataforma superior direita
            Platform(310, GROUND_Y - 320, 180, 20),  # Plataforma central superior
        ]
    
    def handle_click(self, pos):
        """Processa cliques do mouse."""
        if self.state == GameState.MENU:
            if self.btn_play.is_clicked(pos):
                self.state = GameState.INSTRUCTIONS
            elif self.btn_sound.is_clicked(pos):
                self.sound_enabled = not self.sound_enabled
                self.btn_sound.text = "SOM: " + ("LIGADO" if self.sound_enabled else "DESLIGADO")
                if not self.sound_enabled:
                    self.stop_music()
                else:
                    self.start_music()
            elif self.btn_exit.is_clicked(pos):
                exit()
        
        elif self.state == GameState.INSTRUCTIONS:
            # Qualquer clique na tela de instrucoes inicia o jogo
            self.state = GameState.PLAYING
            self.reset_game()
            self.start_music()
        
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
                music.play("bg_music")
                music.set_volume(0.35)  # Volume reduzido em 30% (de 0.5 para 0.35)
                self.music_playing = True
            except Exception as e:
                print(f"Erro ao tocar musica: {e}")
                pass
    
    def stop_music(self):
        """Para a musica de fundo."""
        try:
            pygame.mixer.music.stop()
            self.music_playing = False
        except:
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
        elif self.state == GameState.INSTRUCTIONS:
            self.draw_instructions(screen)
        elif self.state == GameState.PLAYING:
            self.draw_game(screen)
        elif self.state == GameState.BOSS_ROOM:
            self.draw_boss_room(screen)
        elif self.state == GameState.GAME_OVER:
            self.draw_game_over(screen)
        elif self.state == GameState.VICTORY:
            self.draw_victory(screen)
    
    def draw_menu(self, screen):
        """Desenha o menu principal."""
        screen.draw.text(
            "Elden Thing",
            center=(WIDTH // 2, 120),
            fontsize=48,
            color=(255, 215, 0),
            shadow=(2, 2),
            scolor="black"
        )
        
        screen.draw.text(
            "Uma aventura nas terras das sombras!",
            center=(WIDTH // 2, 170),
            fontsize=20,
            color=(200, 200, 200)
        )
        
        self.btn_play.draw(screen)
        self.btn_sound.draw(screen)
        self.btn_exit.draw(screen)
    
    def draw_instructions(self, screen):
        """Desenha a tela de instrucoes."""
        screen.fill((30, 35, 45))
        
        screen.draw.text(
            "CONTROLES",
            center=(WIDTH // 2, 100),
            fontsize=42,
            color=(255, 215, 0),
            shadow=(2, 2),
            scolor="black"
        )
        
        # Instrucoes de movimento
        y_pos = 180
        spacing = 50
        
        screen.draw.text(
            "← → Setas Esquerda/Direita: Mover",
            center=(WIDTH // 2, y_pos),
            fontsize=24,
            color="white"
        )
        
        screen.draw.text(
            "↑ Seta para Cima ou ESPACO: Pular",
            center=(WIDTH // 2, y_pos + spacing),
            fontsize=24,
            color="white"
        )
        
        screen.draw.text(
            "X: Atacar",
            center=(WIDTH // 2, y_pos + spacing * 2),
            fontsize=24,
            color="white"
        )
        
        screen.draw.text(
            "ESC: Menu",
            center=(WIDTH // 2, y_pos + spacing * 3),
            fontsize=24,
            color="white"
        )
        
        screen.draw.text(
            "OBJETIVO",
            center=(WIDTH // 2, y_pos + spacing * 3 + 30),
            fontsize=36,
            color=(255, 215, 0),
            shadow=(2, 2),
            scolor="black"
        )
        
        screen.draw.text(
            "1. Elimine os inimigos que aparecem",
            center=(WIDTH // 2, y_pos + spacing * 4 + 30),
            fontsize=20,
            color=(200, 200, 200)
        )
        
        screen.draw.text(
            "2. Entre na porta desbloqueada",
            center=(WIDTH // 2, y_pos + spacing * 4 + 55),
            fontsize=20,
            color=(200, 200, 200)
        )
        
        screen.draw.text(
            "3. Derrote o REI ESQUELETO!",
            center=(WIDTH // 2, y_pos + spacing * 4 + 80),
            fontsize=20,
            color=(255, 100, 100)
        )
        
        screen.draw.text(
            "CLIQUE PARA COMECAR",
            center=(WIDTH // 2, HEIGHT - 40),
            fontsize=28,
            color=(100, 255, 100),
            shadow=(2, 2),
            scolor="black"
        )
    
    def draw_game(self, screen):
        """Desenha o jogo durante a partida."""
        # Desenhar background gradiente (ceu)
        for y in range(HEIGHT):
            # Gradiente do azul claro ao azul escuro
            ratio = y / HEIGHT
            r = int(135 + (40 - 135) * ratio)
            g = int(206 + (44 - 206) * ratio)
            b = int(250 + (52 - 250) * ratio)
            screen.draw.line((0, y), (WIDTH, y), (r, g, b))
        
        # Desenhar nuvens decorativas
        self.draw_clouds(screen)
        
        # Desenhar chao com grama (ajustado para corresponder a colisao)
        screen.draw.filled_rect(Rect(0, GROUND_Y, WIDTH, HEIGHT - GROUND_Y), (60, 100, 60))
        screen.draw.filled_rect(Rect(0, GROUND_Y, WIDTH, 5), (40, 80, 40))  # Grama no topo
        
        # Desenhar porta do boss (estilo Castlevania - no chao a direita)
        goal_y = GROUND_Y - 50  # Porta no chao (centro vertical)
        goal_rect = Rect(WIDTH - 80, goal_y - 50, 60, 100)
        if self.exit_locked:
            # Saida trancada (vermelha escura com brilho)
            screen.draw.filled_rect(goal_rect, (100, 30, 30))
            # Borda vermelha brilhante
            for i in range(3):
                screen.draw.line((goal_rect.left + i, goal_rect.top), (goal_rect.right - i, goal_rect.top), (200, 50, 50))
                screen.draw.line((goal_rect.left + i, goal_rect.bottom), (goal_rect.right - i, goal_rect.bottom), (200, 50, 50))
                screen.draw.line((goal_rect.left, goal_rect.top + i), (goal_rect.left, goal_rect.bottom - i), (200, 50, 50))
                screen.draw.line((goal_rect.right, goal_rect.top + i), (goal_rect.right, goal_rect.bottom - i), (200, 50, 50))
            # Cadeado central
            screen.draw.filled_circle((WIDTH - 50, goal_y), 15, (150, 150, 150))
            screen.draw.filled_rect(Rect(WIDTH - 60, goal_y - 15, 20, 15), (100, 100, 100))
        else:
            # Portal desbloqueado (verde brilhante com efeito)
            # Gradiente verde
            for i in range(goal_rect.height):
                ratio = i / goal_rect.height
                r = int(50 + (100 - 50) * ratio)
                g = int(200 + (255 - 200) * ratio)
                b = int(100 + (200 - 100) * ratio)
                screen.draw.line((goal_rect.left, goal_rect.top + i), (goal_rect.right, goal_rect.top + i), (r, g, b))
            # Borda dourada brilhante
            for i in range(4):
                screen.draw.line((goal_rect.left + i, goal_rect.top), (goal_rect.right - i, goal_rect.top), (255, 215, 0))
                screen.draw.line((goal_rect.left + i, goal_rect.bottom), (goal_rect.right - i, goal_rect.bottom), (255, 215, 0))
                screen.draw.line((goal_rect.left, goal_rect.top + i), (goal_rect.left, goal_rect.bottom - i), (255, 215, 0))
                screen.draw.line((goal_rect.right, goal_rect.top + i), (goal_rect.right, goal_rect.bottom - i), (255, 215, 0))
            # Simbolo de portal no centro
            screen.draw.filled_circle((WIDTH - 50, goal_y), 20, (100, 255, 150))
            screen.draw.circle((WIDTH - 50, goal_y), 20, (50, 200, 100))
            screen.draw.circle((WIDTH - 50, goal_y), 15, (150, 255, 200))
            # Texto "PORTAL"
            screen.draw.text("PORTAL", center=(WIDTH - 50, goal_y + 35), fontsize=16, color=(255, 255, 200), shadow=(1, 1), scolor="black")
        
        # Estilo Castlevania - sem plataformas, apenas chao
        
        # Desenhar inimigos vivos
        for enemy in self.enemies:
            if enemy.alive:
                # Efeito visual de hit (flash branco)
                if enemy.hit_effect:
                    screen.draw.filled_circle((int(enemy.x), int(enemy.y)), int(30 * SPRITE_SCALE), (255, 255, 255))
            self.draw_enemy(screen, enemy)
        
        # Desenhar sprite de impacto se houver hit (escalado corretamente)
        if self.player.show_impact and self.player_sprites:
            try:
                direction = 'r' if self.player.facing_right else 'l'
                impact_key = f'attack_impact_{direction}'
                if impact_key in self.player_sprites:
                    img_surface = self.player_sprites[impact_key]
                    # Garantir que o sprite esta escalado - se nao estiver, escalar agora
                    max_size = 150  # Tamanho maximo para o sprite de impacto
                    if img_surface.get_width() > max_size or img_surface.get_height() > max_size:
                        scale_factor = min(max_size / img_surface.get_width(), max_size / img_surface.get_height())
                        new_width = int(img_surface.get_width() * scale_factor)
                        new_height = int(img_surface.get_height() * scale_factor)
                        img_surface = pygame.transform.scale(img_surface, (new_width, new_height))
                    # O sprite ja esta escalado em load_sprites, entao usar diretamente
                    pos_x = int(self.player.impact_x - img_surface.get_width() // 2)
                    pos_y = int(self.player.impact_y - img_surface.get_height() // 2)
                    if hasattr(screen, 'surface'):
                        screen.surface.blit(img_surface, (pos_x, pos_y))
                    else:
                        pygame_screen = pygame.display.get_surface()
                        if pygame_screen:
                            pygame_screen.blit(img_surface, (pos_x, pos_y))
            except Exception as e:
                # Se der erro, nao desenhar (evitar bug visual)
                pass
        
        # Desenhar jogador
        if not (self.player.invincible and int(self.player.invincible_timer * 10) % 2 == 0):
            self.draw_player(screen)
        
        # HUD - Vidas (coracoes)
        for i in range(self.player.lives):
            screen.draw.filled_circle((30 + i * 30, 30), 10, (220, 50, 50))
            screen.draw.circle((30 + i * 30, 30), 10, (180, 30, 30))
        
        # HUD - Mostrar progresso das ondas (estilo Castlevania)
        alive_count = len([e for e in self.enemies if e.alive])
        screen.draw.text(
            f"Inimigos: {alive_count}",
            topleft=(20, 60),
            fontsize=18,
            color="white",
            shadow=(1, 1),
            scolor="black"
        )
        
        screen.draw.text(
            f"Onda: {self.current_wave}/{self.total_waves}",
            topleft=(20, 85),
            fontsize=18,
            color="white",
            shadow=(1, 1),
            scolor="black"
        )
        
        screen.draw.text(
            "ESC: Menu",
            topright=(WIDTH - 20, 20),
            fontsize=16,
            color=(150, 150, 150)
        )
        
    
    def draw_clouds(self, screen):
        """Desenha nuvens decorativas no fundo."""
        # Nuvens simples usando circulos
        cloud_positions = [
            (150, 100, 40),
            (400, 80, 50),
            (650, 120, 45),
            (250, 150, 35),
            (550, 140, 40),
        ]
        for x, y, size in cloud_positions:
            # Nuvem usando multiplos circulos
            screen.draw.filled_circle((x, y), size, (255, 255, 255))
            screen.draw.filled_circle((x + size * 0.7, y), size * 0.8, (255, 255, 255))
            screen.draw.filled_circle((x - size * 0.7, y), size * 0.8, (255, 255, 255))
            screen.draw.filled_circle((x, y - size * 0.5), size * 0.7, (255, 255, 255))
    
    def draw_player(self, screen):
        """Desenha o jogador usando sprites."""
        color = (80, 150, 220)  # Inicializar color antes do try
        try:
            if self.player_sprites is None:
                raise Exception("Sprites nao carregados")
            
            # Determinar qual sprite usar com direcao
            direction = 'r' if self.player.facing_right else 'l'
            if self.player.is_attacking:
                # Usar sempre hero_attack_02 (frame 0)
                sprite_key = f'attack_0_{direction}'
            elif self.player.is_moving:
                sprite_key = f'walk_{self.player.current_sprite_index}_{direction}'
            else:
                sprite_key = f'idle_{direction}'
            
            img_surface = self.player_sprites[sprite_key]
            
            # Calcular posicao (ajustar para centralizar o sprite)
            pos_x = int(self.player.x - img_surface.get_width() // 2)
            pos_y = int(self.player.y - img_surface.get_height() // 2)
            
            # Desenhar usando o surface do screen
            try:
                # Tentar acessar o surface diretamente
                if hasattr(screen, 'surface'):
                    screen.surface.blit(img_surface, (pos_x, pos_y))
                else:
                    # Usar pygame.display.get_surface()
                    pygame_screen = pygame.display.get_surface()
                    if pygame_screen:
                        pygame_screen.blit(img_surface, (pos_x, pos_y))
                    else:
                        raise AttributeError("Nao foi possivel acessar o surface")
            except:
                # Fallback: usar screen.blit com string (sem flip)
                sprite_name = self.player.images_walk[self.player.current_sprite_index] if self.player.is_moving else self.player.images_idle[0]
                screen.blit(f"images/{sprite_name}.png", (pos_x, pos_y))
        except Exception as e:
            # Fallback para desenho procedural se o sprite nao carregar
            screen.draw.filled_circle((int(self.player.x), int(self.player.y - 20)), 18, color)
            screen.draw.filled_rect(Rect(self.player.x - 12, self.player.y - 8, 24, 32), color)
        
    def draw_enemy(self, screen, enemy):
        """Desenha um inimigo usando sprites."""
        try:
            if self.enemy_sprites is None:
                raise Exception("Sprites nao carregados")
            
            # Usar sprite de caminhada com direcao
            direction = 'r' if enemy.facing_right else 'l'
            sprite_key = f'walk_{enemy.current_sprite_index}_{direction}'
            img_surface = self.enemy_sprites[sprite_key]
            
            # Calcular posicao (ajustar para centralizar o sprite)
            pos_x = int(enemy.x - img_surface.get_width() // 2)
            pos_y = int(enemy.y - img_surface.get_height() // 2)
            
            # Desenhar usando o surface do screen
            try:
                # Tentar acessar o surface diretamente
                if hasattr(screen, 'surface'):
                    screen.surface.blit(img_surface, (pos_x, pos_y))
                else:
                    # Usar pygame.display.get_surface()
                    pygame_screen = pygame.display.get_surface()
                    if pygame_screen:
                        pygame_screen.blit(img_surface, (pos_x, pos_y))
                    else:
                        raise AttributeError("Nao foi possivel acessar o surface")
            except:
                # Fallback: usar screen.blit com string (sem flip)
                sprite_name = enemy.images_walk[enemy.current_sprite_index]
                screen.blit(f"images/{sprite_name}.png", (pos_x, pos_y))
        except Exception as e:
            # Fallback para desenho procedural se o sprite nao carregar
            color = (200, 80, 80)
            screen.draw.filled_circle((int(enemy.x), int(enemy.y - 15)), 20, color)
            screen.draw.filled_rect(Rect(enemy.x - 15, enemy.y - 5, 30, 35), color)
    
    def draw_boss_room(self, screen):
        """Desenha a sala do boss."""
        # Background preto simples
        screen.fill((0, 0, 0))
        
        # Desenhar plataformas flutuantes melhoradas
        for platform in self.platforms[1:]:  # Pular o chao
            # Corpo da plataforma
            screen.draw.filled_rect(platform.rect, (120, 80, 50))
            # Borda superior (multiplas linhas para simular largura)
            for i in range(3):
                screen.draw.line(
                    (platform.left, platform.top + i),
                    (platform.right, platform.top + i),
                    (150, 100, 60)
                )
            # Sombra abaixo
            shadow_rect = Rect(platform.x + 2, platform.y + 2, platform.width, platform.height)
            screen.draw.filled_rect(shadow_rect, (80, 50, 30))
            # Pilares decorativos (linhas verticais nas bordas)
            screen.draw.line((platform.left, platform.top), (platform.left, platform.top + 10), (100, 60, 30))
            screen.draw.line((platform.right - 1, platform.top), (platform.right - 1, platform.top + 10), (100, 60, 30))
        
        # Desenhar boss se vivo
        if self.boss and self.boss.alive:
            self.draw_boss(screen, self.boss)
        
        # Desenhar jogador
        if not (self.player.invincible and int(self.player.invincible_timer * 10) % 2 == 0):
            self.draw_player(screen)
        
        # Barra de vida do boss (estilo Dark Souls)
        if self.boss and self.boss.alive:
            self.draw_boss_health_bar(screen)
        
        # HUD - Vidas do jogador
        for i in range(self.player.lives):
            screen.draw.filled_circle((30 + i * 30, 30), 10, (220, 50, 50))
            screen.draw.circle((30 + i * 30, 30), 10, (180, 30, 30))
        
        screen.draw.text(
            "ESC: Menu",
            topright=(WIDTH - 20, 20),
            fontsize=16,
            color=(150, 150, 150)
        )
    
    def draw_boss_health_bar(self, screen):
        """Desenha a barra de vida do boss estilo Dark Souls."""
        bar_width = 400
        bar_height = 40
        bar_x = (WIDTH - bar_width) // 2
        bar_y = 30
        
        # Background da barra (preto)
        screen.draw.filled_rect(Rect(bar_x - 4, bar_y - 4, bar_width + 8, bar_height + 8), (0, 0, 0))
        
        # Barra de vida (vermelho escuro)
        screen.draw.filled_rect(Rect(bar_x, bar_y, bar_width, bar_height), (100, 0, 0))
        
        # Vida atual (vermelho)
        health_ratio = self.boss.health / self.boss.max_health
        health_width = int(bar_width * health_ratio)
        screen.draw.filled_rect(Rect(bar_x, bar_y, health_width, bar_height), (200, 0, 0))
        
        # Borda dourada
        screen.draw.line((bar_x, bar_y), (bar_x + bar_width, bar_y), (255, 215, 0))
        screen.draw.line((bar_x, bar_y), (bar_x, bar_y + bar_height), (255, 215, 0))
        screen.draw.line((bar_x + bar_width, bar_y), (bar_x + bar_width, bar_y + bar_height), (255, 215, 0))
        screen.draw.line((bar_x, bar_y + bar_height), (bar_x + bar_width, bar_y + bar_height), (255, 215, 0))
        
        # Nome do boss
        screen.draw.text(
            "REI ESQUELETO",
            center=(WIDTH // 2, bar_y + bar_height + 25),
            fontsize=28,
            color=(255, 215, 0),
            shadow=(2, 2),
            scolor="black"
        )
    
    def draw_boss(self, screen, boss):
        """Desenha o boss usando sprites."""
        try:
            if self.boss_sprites is None:
                raise Exception("Sprites do boss nao carregados")
            
            # Usar sprite de caminhada com direcao
            direction = 'r' if boss.facing_right else 'l'
            sprite_key = f'walk_{boss.current_sprite_index}_{direction}'
            img_surface = self.boss_sprites[sprite_key]
            
            # Calcular posicao
            pos_x = int(boss.x - img_surface.get_width() // 2)
            pos_y = int(boss.y - img_surface.get_height() // 2)
            
            # Desenhar usando o surface do screen
            try:
                if hasattr(screen, 'surface'):
                    screen.surface.blit(img_surface, (pos_x, pos_y))
                else:
                    pygame_screen = pygame.display.get_surface()
                    if pygame_screen:
                        pygame_screen.blit(img_surface, (pos_x, pos_y))
                    else:
                        raise AttributeError("Nao foi possivel acessar o surface")
            except:
                sprite_name = boss.images_walk[boss.current_sprite_index]
                screen.blit(f"images/{sprite_name}.png", (pos_x, pos_y))
        except Exception as e:
            # Fallback para desenho procedural
            color = (150, 50, 50)
            screen.draw.filled_circle((int(boss.x), int(boss.y - 15)), 25, color)
            screen.draw.filled_rect(Rect(boss.x - 18, boss.y - 5, 36, 40), color)
    
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
    # Fixar tamanho da janela (chamar sempre para garantir)
    try:
        pygame_screen = pygame.display.get_surface()
        if pygame_screen:
            current_size = pygame_screen.get_size()
            if current_size != (WIDTH, HEIGHT):
                pygame.display.set_mode((WIDTH, HEIGHT))
    except:
        pass
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
        if game.state == GameState.PLAYING or game.state == GameState.BOSS_ROOM:
            game.state = GameState.MENU
            game.stop_music()
    elif key == keys.X:
        # Tecla X para atacar
        if game.state == GameState.PLAYING or game.state == GameState.BOSS_ROOM:
            game.player.attack()
