import random
import math
import pygame

# ---------------------------
# CONFIG
# ---------------------------
WIDTH = 800
HEIGHT = 600
TITLE = "Roguelike Example"

TILE = 48
GRID_W = WIDTH // TILE
GRID_H = HEIGHT // TILE

STATE_MENU = "menu"
STATE_GAME = "game"
STATE_EXIT = "exit"

# VAR GLOBAL DO MOUSE (necessário para PgZero)
mouse_pos = (0, 0)

# ---------------------------
# CLASSES
# ---------------------------

class SpriteAnimator:
    def __init__(self, images, speed=0.15):
        self.images = images
        self.index = 0
        self.speed = speed

    def update(self):
        self.index += self.speed
        if self.index >= len(self.images):
            self.index = 0

    def get_image(self):
        return self.images[int(self.index)]


class Entity:
    def __init__(self, x, y, animations):
        self.x = x
        self.y = y
        self.animations = animations
        self.state = "idle"
        self.dir = "down"

    def get_sprite(self):
        return self.animations[self.state][self.dir].get_image()

    def draw(self):
        img = self.get_sprite()
        screen.blit(img, (self.x * TILE, self.y * TILE))

    def update_animation(self):
        self.animations[self.state][self.dir].update()


class Hero(Entity):
    def __init__(self, x, y, animations):
        super().__init__(x, y, animations)
        self.target_x = x
        self.target_y = y
        self.speed = 0.1

    def move(self, dx, dy):
        self.target_x = max(0, min(GRID_W - 1, self.x + dx))
        self.target_y = max(0, min(GRID_H - 1, self.y + dy))

        # atualizar direção
        if dx > 0:
            self.dir = "right"
        elif dx < 0:
            self.dir = "left"
        elif dy < 0:
            self.dir = "up"
        elif dy > 0:
            self.dir = "down"

        self.state = "move"

    def update(self):
        if abs(self.x - self.target_x) < 0.01 and abs(self.y - self.target_y) < 0.01:
            self.x = self.target_x
            self.y = self.target_y
            self.state = "idle"
        else:
            self.x += (self.target_x - self.x) * self.speed
            self.y += (self.target_y - self.y) * self.speed

        self.update_animation()


class Enemy(Entity):
    def __init__(self, x, y, animations):
        super().__init__(x, y, animations)
        self.patrol_timer = 0

    def update(self):
        self.patrol_timer += 1

        if self.patrol_timer % 120 == 0:
            dx, dy = random.choice([(1,0),(-1,0),(0,1),(0,-1)])
            self.x = max(0, min(GRID_W - 1, self.x + dx))
            self.y = max(0, min(GRID_H - 1, self.y + dy))

            if dx > 0:
                self.dir = "right"
            elif dx < 0:
                self.dir = "left"
            elif dy < 0:
                self.dir = "up"
            elif dy > 0:
                self.dir = "down"

        self.update_animation()


# ---------------------------
# WORLD
# ---------------------------

class World:
    def __init__(self):
        self.state = STATE_MENU
        self.sound_on = True

        self.load_assets()
        self.create_game()

        self.menu_buttons = [
            ("Start Game", Rect(300, 250, 200, 50)),
            ("Sound ON/OFF", Rect(300, 320, 200, 50)),
            ("Exit", Rect(300, 390, 200, 50)),
        ]

    def load_assets(self):
        def make_anim(color):
            surf = pygame.Surface((TILE, TILE))
            surf.fill(color)
            return surf

        # Usamos cores sólidas só para teste
        dummy_idle = [make_anim((200, 200, 200))]
        dummy_walk = [make_anim((150, 150, 150)), make_anim((180, 180, 180))]

        def anim_set():
            return {
                "idle": {
                    "up": SpriteAnimator(dummy_idle),
                    "down": SpriteAnimator(dummy_idle),
                    "left": SpriteAnimator(dummy_idle),
                    "right": SpriteAnimator(dummy_idle),
                },
                "move": {
                    "up": SpriteAnimator(dummy_walk),
                    "down": SpriteAnimator(dummy_walk),
                    "left": SpriteAnimator(dummy_walk),
                    "right": SpriteAnimator(dummy_walk),
                }
            }

        self.hero_animations = anim_set()
        self.enemy_animations = anim_set()

    def create_game(self):
        self.hero = Hero(5, 5, self.hero_animations)
        self.enemies = [
            Enemy(10, 10, self.enemy_animations),
            Enemy(12, 6, self.enemy_animations),
            Enemy(7, 14, self.enemy_animations)
        ]

    def update(self):
        if self.state == STATE_GAME:
            self.update_game()

    def update_game(self):
        self.hero.update()
        for e in self.enemies:
            e.update()

    def draw(self):
        if self.state == STATE_MENU:
            self.draw_menu()
        elif self.state == STATE_GAME:
            self.draw_game()

    def draw_game(self):
        screen.clear()
        screen.fill((20, 30, 40))

        for e in self.enemies:
            e.draw()

        self.hero.draw()

    def draw_menu(self):
        screen.clear()
        screen.fill((40, 40, 60))

        for label, rect in self.menu_buttons:
            color = (180, 180, 180)
            if rect.collidepoint(mouse_pos):
                color = (230, 230, 230)
            screen.draw.filled_rect(rect, color)
            screen.draw.text(
                label,
                center=rect.center,
                fontsize=32,
                color="black"
            )

    def click_menu(self, pos):
        for label, rect in self.menu_buttons:
            if rect.collidepoint(pos):

                if label == "Start Game":
                    self.state = STATE_GAME
                elif label == "Sound ON/OFF":
                    self.sound_on = not self.sound_on
                elif label == "Exit":
                    exit()


world = World()

# ---------------------------
# PZERO HOOKS
# ---------------------------

def update():
    world.update()

def draw():
    world.draw()

def on_key_down(key):
    if world.state == STATE_GAME:
        if key == keys.UP:
            world.hero.move(0, -1)
        elif key == keys.DOWN:
            world.hero.move(0, 1)
        elif key == keys.LEFT:
            world.hero.move(-1, 0)
        elif key == keys.RIGHT:
            world.hero.move(1, 0)

def on_mouse_down(pos):
    if world.state == STATE_MENU:
        world.click_menu(pos)

def on_mouse_move(pos):
    global mouse_pos
    mouse_pos = pos
