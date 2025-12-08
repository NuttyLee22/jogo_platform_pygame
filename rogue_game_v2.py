import random
import math
from pygame import Rect  # permitido pelas regras

WIDTH = 640
HEIGHT = 480

# ---------------------------------------------
# GLOBAL GAME STATE
# ---------------------------------------------
state = "menu"  # menu, game
sound_enabled = True

# ---------------------------------------------
# LOAD MUSIC
# ---------------------------------------------
def play_music():
    if sound_enabled:
        music.play("bg_music")
        music.set_volume(0.6)
    else:
        music.stop()

# ---------------------------------------------
# BUTTON CLASS
# ---------------------------------------------
class Button:
    def __init__(self, text, x, y, w, h):
        self.text = text
        self.rect = Rect(x, y, w, h)

    def draw(self):
        screen.draw.filled_rect(self.rect, (40, 40, 60))
        screen.draw.rect(self.rect, (200, 200, 200))
        screen.draw.text(
            self.text,
            center=self.rect.center,
            fontsize=32,
            color="white"
        )

    def clicked(self, pos):
        return self.rect.collidepoint(pos)

# ---------------------------------------------
# HERO CLASS
# ---------------------------------------------
class Hero:
    def __init__(self):
        self.x = 100
        self.y = 100
        self.speed = 2

        # animation
        self.frame = 0
        self.timer = 0

        self.state = "idle"  # idle, walk, attack

        self.images_idle = ["hero_paused"]
        self.images_walk = ["hero_walk_01", "hero_walk_02"]
        self.images_attack = ["hero_attack_01", "hero_attack_02"]

    def animate(self):
        self.timer += 1
        if self.timer >= 15:
            self.timer = 0
            self.frame = (self.frame + 1) % 2

    def update(self):
        keys = keyboard

        moving = False

        if keys.left:
            self.x -= self.speed
            moving = True
        if keys.right:
            self.x += self.speed
            moving = True
        if keys.up:
            self.y -= self.speed
            moving = True
        if keys.down:
            self.y += self.speed
            moving = True

        # attack
        if keys.space:
            self.state = "attack"
        else:
            if moving:
                self.state = "walk"
            else:
                self.state = "idle"

        self.animate()

    def draw(self):
        if self.state == "idle":
            img = self.images_idle[0]
        elif self.state == "walk":
            img = self.images_walk[self.frame]
        else:  # attack
            img = self.images_attack[self.frame]

        screen.blit(f"images/{img}.png", (self.x, self.y))

# ---------------------------------------------
# ENEMY CLASS
# ---------------------------------------------
class Enemy:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.speed = 1
        self.frame = 0
        self.timer = 0
        self.state = "walk"

        self.images_idle = ["enemy_paused"]
        self.images_walk = ["enemy_walk_01", "enemy_walk_02"]

        # random movement direction
        self.dx = random.choice([-1, 1])
        self.dy = random.choice([-1, 1])

        # territory limits
        self.min_x = x - 50
        self.max_x = x + 50
        self.min_y = y - 50
        self.max_y = y + 50

    def animate(self):
        self.timer += 1
        if self.timer >= 20:
            self.timer = 0
            self.frame = (self.frame + 1) % 2

    def update(self):
        self.x += self.dx * self.speed
        self.y += self.dy * self.speed

        # bounce inside territory
        if self.x < self.min_x or self.x > self.max_x:
            self.dx *= -1
        if self.y < self.min_y or self.y > self.max_y:
            self.dy *= -1

        self.animate()

    def draw(self):
        img = self.images_walk[self.frame]
        screen.blit(f"images/{img}.png", (self.x, self.y))

# ---------------------------------------------
# GAME ACTORS
# ---------------------------------------------
hero = Hero()
enemies = [Enemy(400, 300), Enemy(300, 200), Enemy(500, 250)]

# ---------------------------------------------
# MENU BUTTONS
# ---------------------------------------------
btn_start = Button("Start Game", 220, 150, 200, 50)
btn_sound = Button("Sound ON/OFF", 220, 230, 200, 50)
btn_exit = Button("Exit", 220, 310, 200, 50)

# ---------------------------------------------
# MAIN LOOP
# ---------------------------------------------
def update():
    global state, sound_enabled

    if state == "menu":
        return

    if state == "game":
        hero.update()
        for e in enemies:
            e.update()

def draw():
    screen.clear()

    if state == "menu":
        screen.draw.text("Roguelike Game", center=(WIDTH//2, 60), fontsize=48, color="white")
        btn_start.draw()
        btn_sound.draw()
        btn_exit.draw()
        return

    # game
    hero.draw()
    for e in enemies:
        e.draw()

# ---------------------------------------------
# MOUSE HANDLING
# ---------------------------------------------
def on_mouse_down(pos):
    global state, sound_enabled

    if state == "menu":
        if btn_start.clicked(pos):
            state = "game"
            play_music()
        elif btn_sound.clicked(pos):
            sound_enabled = not sound_enabled
            play_music()
        elif btn_exit.clicked(pos):
            quit()
