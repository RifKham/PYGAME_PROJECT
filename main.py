import os
import sqlite3
import sys
from pygame import mixer
from random import randrange, choice

import pygame
import time

from pygame import USEREVENT

pygame.init()
mixer.init()
size = width, height = 576, 512
screen = pygame.display.set_mode(size)
clock = pygame.time.Clock()
font = pygame.font.Font(None, 36)
FPS = 50
STEP = 64
sp = ["build1.png", "build2.png", "camera.png"]
buildings = []
npcs = []


def load_image(name, colorkey=None):
    fullname = os.path.join('data', name)
    # если файл не существует, то выходим
    if not os.path.isfile(fullname):
        print(f"Файл с изображением '{fullname}' не найден")
        sys.exit()
    image = pygame.image.load(fullname)
    if colorkey is not None:
        image = image.convert()
        if colorkey == -1:
            colorkey = image.get_at((0, 0))
        image.set_colorkey(colorkey)
    else:
        image = image.convert_alpha()
    return image


def load_level(filename):
    filename = "data/" + filename
    # читаем уровень, убирая символы перевода строки
    with open(filename, 'r') as mapFile:
        level_map = [line.strip() for line in mapFile]

    # и подсчитываем максимальную длину
    max_width = max(map(len, level_map))

    # дополняем каждую строку пустыми клетками ('.')
    return list(map(lambda x: x.ljust(max_width, '.'), level_map))


def save_game():
    con = sqlite3.connect("save")
    cur = con.cursor()
    cur.execute("DELETE FROM npcs")
    con.commit()
    cur.execute("DELETE FROM buildings")
    con.commit()
    cur.execute("DELETE FROM player")
    con.commit()
    cur.execute("DELETE FROM barrack")
    con.commit()
    n = 0
    for i in range(len(npcs)):
        cords = npcs[i].get_cords()[0] + player.x * 64, npcs[i].get_cords()[1] + player.y * 64
        cur.execute("""
            INSERT OR REPLACE INTO npcs (id, type, pos)
            VALUES (?, ?, ?)
       """, (i + 1, str(type(npcs[i])), str(cords)))
    for i in range(len(buildings)):
        if not buildings[i].o:
            cords = buildings[i].get_cords()[0] + player.x * 64, buildings[i].get_cords()[1] + player.y * 64
        else:
            cords = buildings[i].get_cords()[0] + player.x * 64, buildings[i].get_cords()[1] + (player.y - 0.5) * 64
        cur.execute("""
            INSERT OR REPLACE INTO buildings (id, type, pos, whose)
            VALUES (?, ?, ?, ?)
        """, (i + 1, str(type(buildings[i])), str(cords), buildings[i].wp))
        if type(buildings[i]) == Farm:
            if buildings[i].wp:
                cur.execute("""REPLACE INTO player (food)
                                VALUES (?)""", (buildings[i].get_res(),))
        if type(buildings[i]) == Mine:
            if buildings[i].wp:
                cur.execute("""REPLACE INTO player (stone)
                                VALUES (?)""", (buildings[i].get_res()[0],))
                cur.execute("""REPLACE INTO player (metal)
                                VALUES (?)""", (buildings[i].get_res()[1],))
        if type(buildings[i]) == Barrack:
            if buildings[i].wp:
                cur.execute("""INSERT OR REPLACE INTO barrack (units)
                                VALUES (?)""", (buildings[i].get_units(),))
        if type(buildings[i]) == Sawmill:
            if buildings[i].wp:
                cur.execute("""REPLACE INTO player (wood)
                                VALUES (?)""", (buildings[i].get_res(),))
        if type(buildings[i]) == Houses:
            if buildings[i].wp:
                cur.execute("""REPLACE INTO player (people)
                VALUES (?)""", (buildings[i].get_people(),))
    con.commit()
    con.close()


tile_images = {
    'water': load_image('water.png'),
    'empty': load_image('grass.png'),
    "i_wall": load_image('water.png'),
    "rock": load_image("rock.png"),
    "forest": load_image("forest.png")
}
player_image = load_image('camera.png')
build_images = {
    "farm": load_image('farm.png'),
    "mine": load_image('mine.png'),
    "sawmill": load_image("sawmill.png"),
    "barrack": load_image('barrack.png'),
    "trade_area": load_image("tradearea.png"),
    "castle": load_image("castle.png"),
    "houses": load_image("houses.png"),
    "castle_e": load_image("castle_e.png")
}

stat_images = {
    "food": load_image("food.png"),
    "wood": load_image("wood.png"),
    "stone": load_image("stone.png"),
    "metal": load_image("metal.png"),
    "people": load_image("people.png")
}

npc_images = {
    "enemy": load_image('enemy.png'),
    "unit": load_image('knight.png')
}
tile_width = tile_height = 64
soldiers = load_image("soldier.png")
weapon = load_image("weapon.png")

images = ["farm_plan", "mine_plan", "barrack_plan", "sawmill_plan", "houses_plan"]
im = []
for i in images:
    image = pygame.image.load(f'data/{i}.png')
    im.append(image)
image_check_res = []
for i in ["wood_check", "stone_check", "metal_check"]:
    image = pygame.image.load(f'data/{i}.png')
    image_check_res.append(image)

buttons = [load_image("b2.png"), load_image("b1.png")]
fon = load_image("afaf.png")


class Tile(pygame.sprite.Sprite):
    def __init__(self, tile_type, pos_x, pos_y):

        if tile_type == 'i_wall':
            super().__init__(tiles_group, walls_group, all_sprites)
        else:
            super().__init__(tiles_group, all_sprites)
        self.tile_type = tile_type
        self.image = tile_images[tile_type]
        self.rect = self.image.get_rect().move(
            tile_width * pos_x, tile_height * pos_y - 32)

    def get_cords(self):
        return self.rect.x, self.rect.y


class InvisibleWall(pygame.sprite.Sprite):
    def __init__(self, pos_x, pos_y):
        super().__init__(all_sprites, walls_group)
        self.image = tile_images["i_wall"]
        self.rect = self.image.get_rect().move(
            tile_width * pos_x, tile_height * pos_y)


class NPC(pygame.sprite.Sprite):
    """
    общий класс для всех неигровых персонажей
    """

    def __init__(self, pos_x, pos_y, npc_type="enemy", heal_points=5):
        super().__init__(tiles_group, all_sprites, npc_group)
        self.image = npc_images[npc_type]
        self.hp = heal_points
        self.rect = self.image.get_rect().move(
            tile_width * pos_x, tile_height * pos_y)

    def get_heal_points(self):
        return self.hp

    def get_cords(self):
        return self.rect.x, self.rect.y


class EnemyKing(pygame.sprite.Sprite):
    def __init__(self, pos_x, pos_y):
        super().__init__(player_group, all_sprites)
        self.image = player_image
        self.rect = self.image.get_rect().move(
            tile_width * pos_x, tile_height * pos_y)
        self.cb = {"f": 1, "m": 1, "s": 1, "h": 1}
        self.building = ["f", "m", "s", "h"]
        self.time = 0
        self.wb = 5
        self.b = 0

    def what_build(self):
        """
        Определяет, какой тип здания строить.
        Учитывает наличие войны и количество уже построенных зданий.
        """
        if self.time == 4:
            if not self.start_war():
                min_count = min(self.cb.values())
                possible_builds = [k for k, v in self.cb.items() if
                                   v == min_count]
                b = choice(possible_builds)
            else:
                self.b += 1
                return "b"
            self.cb[b] += 1
            return b

    def start_war(self):
        a = 0
        for i in self.building:
            a += self.cb[i]
        if a >= 15:
            return True

    def build(self):
        """
        Пытается построить здание выбранного типа.
        """

        a = []
        wb = self.what_build()
        if wb == "f":
            bu = "Farm"
        elif wb == "m":
            bu = "Mine"
        elif wb == "s":
            bu = "Sawmill"
        elif wb == "b":
            bu = "Barrack"
        elif wb == "h":
            bu = "Houses"
        if self.time == 4:
            self.time = 0
            for i in range(5):
                for j in range(5):
                    if i >= 3:
                        i = i * -1 + 2
                    if j >= 3:
                        j = j * -1 + 2
                    tile_x = i
                    tile_y = j
                    if can_build((self.rect.x - tile_x * 64, self.rect.y - tile_y * 64), bu):
                        posx = self.rect.x // 64 - tile_x
                        posy = self.rect.y // 64 - tile_y
                        if bu == "Farm":
                            buildings.append(Farm(True, posx, posy, wp=False))
                        elif bu == "Mine":
                            buildings.append(Mine(True, posx, posy, wp=False))
                        elif bu == "Sawmill":
                            buildings.append(Sawmill(True, posx, posy, wp=False))
                        elif bu == "Barrack":
                            buildings.append(Barrack(True, posx, posy, wp=False))
                        elif bu == "Houses":
                            buildings.append(Houses(True, posx, posy, wp=False))
                        return
        self.time += 1

    def war(self):
        if self.start_war():
            if self.b > 3:
                n = 0
                for i in buildings:
                    if type(i) == Barrack:
                        n += 1
                w = randrange(0, n)
                n = 0
                for i in range(len(buildings)):
                    if type(buildings[i]) == Barrack:
                        if n == w:
                            print(n)
                            e = Enemy(buildings[i].get_cords()[0] // 64, buildings[i].get_cords()[1] // 64)
                            npcs.append(e)
                            return
                        n += 1

    def start_attack(self):
        n = 0
        for i in npcs:
            if type(i) == Enemy:
                n += 1
        return n

    def attack(self):
        if self.start_attack() >= 2:
            for i in npcs:
                if type(i) == Enemy:
                    i.move(player.get_cords()[0] // 64, player.get_cords()[1] // 64)


class Enemy(NPC):
    """
    общий класс для всех противников
    """

    def __init__(self, pos_x, pos_y, heal_points=10):
        super().__init__(pos_x, pos_y, "enemy")

    def move(self, x=None, y=None):
        if x is not None:
            min_x = 100
            min_y = 100
            for i in npcs:
                if type(i) == UnitP:
                    if abs(self.rect.x // 64 - i.rect.x // 64) + abs(self.rect.y // 64 - i.rect.y // 64) < min_x + min_y:
                        min_x = self.rect.x // 64 - i.rect.x // 64
                        min_y = self.rect.y // 64 - i.rect.y // 64
        else:
            min_x = x
            min_y = y
        if abs(min_x) + abs(min_y) <= 3:
            if abs(min_x) > abs(min_y):
                if min_x < 0:
                    self.rect.x += STEP
                    if pygame.sprite.spritecollideany(self, walls_group):
                        self.rect.x -= STEP
                else:
                    self.rect.x -= STEP
                    if pygame.sprite.spritecollideany(self, walls_group):
                        self.rect.x += STEP
            else:
                if min_y < 0:
                    self.rect.y += STEP
                    if pygame.sprite.spritecollideany(self, walls_group):
                        self.rect.y -= STEP
                else:
                    self.rect.y -= STEP
                    if pygame.sprite.spritecollideany(self, walls_group):
                        self.rect.y += STEP

    def take_damage(self):
        self.hp -= 3
        self.check_life()

    def check_life(self):
        if self.hp <= 0:
            self.kill()

    def attack(self):
        f = True
        for i in npcs:
            if type(i) == UnitP:
                if (abs(i.get_cords()[0] - self.get_cords()[0]) <= 64 or
                        abs(i.get_cords()[1] - self.get_cords()[1]) <= 64):
                    i.take_damage(1)
                    f = False
                    return
        if f:
            for i in buildings:
                if (abs(i.get_cords()[0] - self.get_cords()[0]) <= 64 or
                        abs(i.get_cords()[1] - self.get_cords()[1]) <= 64):
                    i.take_damage(2)
                    return


class UnitP(NPC):
    controlled = False
    len_x = 0
    len_y = 0
    atck = False
    can = ""

    def control(self):
        if self.controlled:
            self.controlled = False
            self.image = load_image("knight.png")
        else:
            self.controlled = True
            self.image = load_image('knight_C.png')

    def set_point(self, pos_x, pos_y, atck=False):
        self.atck = atck
        if self.controlled:
            self.len_x = self.rect.x - pos_x
            self.len_y = self.rect.y - pos_y

    def u_move(self):
        if self.controlled:
            if abs(self.len_x) > abs(self.len_y) or self.can == "x":
                if self.len_x < 0:
                    for i in npcs:
                        x, y = i.get_cords()
                        if x == self.get_cords()[0] + 64 and y == self.get_cords()[1]:
                            self.can = "y"
                            return
                    self.rect.x += STEP
                    self.len_x += STEP
                    self.can = ""
                    if pygame.sprite.spritecollideany(self, walls_group):
                        self.rect.x -= STEP
                        self.len_x -= STEP
                        self.can = "y"
                        return
                else:
                    for i in npcs:
                        x, y = i.get_cords()
                        if x == self.get_cords()[0] - 64 and y == self.get_cords()[1]:
                            self.can = "y"
                            return
                    self.rect.x -= STEP
                    self.len_x -= STEP
                    self.can = ""
                    if pygame.sprite.spritecollideany(self, walls_group):
                        self.rect.x += STEP
                        self.len_x += STEP
                        self.can = "y"
                        return
            elif abs(self.len_x) <= abs(self.len_y) or self.can == "y":
                if self.len_y < 0:
                    for i in npcs:
                        x, y = i.get_cords()
                        if y == self.get_cords()[1] + 64 and x == self.get_cords()[0]:
                            self.len_x += 64
                            self.can = "x"
                            return
                    self.rect.y += STEP
                    self.len_y += STEP
                    self.can = ""
                    if pygame.sprite.spritecollideany(self, walls_group):
                        self.rect.y -= STEP
                        self.len_y -= STEP
                        self.can = "x"
                        return
                else:
                    for i in npcs:
                        x, y = i.get_cords()
                        if y == self.get_cords()[1] - 64 and x == self.get_cords()[0]:
                            self.len_x += 64
                            self.can = "x"
                            return
                    self.rect.y -= STEP
                    self.len_y -= STEP
                    self.can = ""
                    if pygame.sprite.spritecollideany(self, walls_group):
                        self.rect.y += STEP
                        self.len_y += STEP
                        self.can = "x"
                        return

    def attack(self):
        if self.atck:
            n = -1
            for i in npcs:
                n += 1
                if type(i) == Enemy:
                    if (abs(i.get_cords()[0] - self.get_cords()[0]) <= 64 or
                            abs(i.get_cords()[1] - self.get_cords()[1]) <= 64):
                        i.take_damage(2)
            for i in buildings:
                if (abs(i.get_cords()[0] - self.get_cords()[0]) <= 64 or
                        abs(i.get_cords()[1] - self.get_cords()[1]) <= 64):
                    i.take_damage(2)
                    return

    def take_damage(self, d):
        self.hp -= d
        self.check_life()

    def check_life(self):
        if self.hp <= 0:
            for i in range(len(npcs)):
                if npcs[i].get_cords() == self.get_cords():
                    del npcs[i]
                    self.kill()
                    return


class Building(pygame.sprite.Sprite):
    def __init__(self, built=False, pos_x=None, pos_y=None, build_type="farm", heal_points=5, wp=True, o=False):
        if built:
            super().__init__(tiles_group, all_sprites, build_group)
            self.image = build_images[build_type]
            self.heal_points = heal_points
            self.wp = wp
            self.o = o
            self.rect = self.image.get_rect().move(
                tile_width * pos_x, tile_height * pos_y)
            self.condition = 0.5

    def get_heal(self):
        return self.heal_points

    def get_cords(self):
        return self.rect.x, self.rect.y

    def get_con(self):
        return self.condition

    def set_con(self, n=1):
        self.condition = n

    def check_life(self):
        if self.heal_points <= 0:
            for i in range(len(buildings)):
                if buildings[i].get_cords() == self.get_cords():
                    del buildings[i]
                    self.kill()
                    return

    def take_damage(self, d):
        self.heal_points -= d
        self.check_life()

    def whose(self):
        return self.wp


class Player(pygame.sprite.Sprite):
    def __init__(self, pos_x, pos_y):
        super().__init__(player_group, all_sprites)
        self.image = player_image
        self.rect = self.image.get_rect().move(
            tile_width * pos_x, tile_height * pos_y)
        self.key_press = 0
        self.x = 8
        self.y = 9.5

    def update(self, *args):
        if self.key_press != pygame.key.get_pressed():
            if pygame.key.get_pressed()[pygame.K_LEFT]:
                self.rect.x -= STEP
                self.x += 1
                if pygame.sprite.spritecollideany(self, walls_group):
                    self.rect.x += STEP
                    self.x -= 1
            if pygame.key.get_pressed()[pygame.K_RIGHT]:
                self.rect.x += STEP
                self.x -= 1
                if pygame.sprite.spritecollideany(self, walls_group):
                    self.rect.x -= STEP
                    self.x += 1
            if pygame.key.get_pressed()[pygame.K_UP]:
                self.rect.y -= STEP
                self.y += 1
                if pygame.sprite.spritecollideany(self, walls_group):
                    self.rect.y += STEP
                    self.y -= 1
            if pygame.key.get_pressed()[pygame.K_DOWN]:
                self.rect.y += STEP
                self.y -= 1
                if pygame.sprite.spritecollideany(self, walls_group):
                    self.rect.y -= STEP
                    self.y += 1
            self.key_press = pygame.key.get_pressed()

    def get_cords(self):
        return self.rect.x, self.rect.y


class Farm(Building):
    food = 0

    @classmethod
    def farming(cls):
        cls.food += int(randrange(7, 10))

    @classmethod
    def get_res(cls):
        return cls.food


    @classmethod
    def eat(cls):
        cls.food -= int(randrange(0, 2) * houses.people * 0.5)


class Mine(Building):
    stone = 15
    metal = 10

    def __init__(self, built=False, pos_x=None, pos_y=None, wp=True, o=False):
        super().__init__(built, pos_x, pos_y, "mine")
        self.wp = wp
        self.o = o

    @classmethod
    def mining(cls, c=0.7):
        cls.stone += int(randrange(7, 11) * c)
        cls.metal += int(randrange(3, 7) * c)

    @classmethod
    def build(cls, n):
        cls.stone -= n + 5
        cls.metal -= n

    @classmethod
    def get_res(cls):
        return cls.stone, cls.metal

    @classmethod
    def use(cls):
        cls.stone -= int(randrange(0, 2) * houses.people * 0.5)
        cls.metal -= int(randrange(0, 2) * 2)


class Barrack(Building):
    units = 0

    def __init__(self, built=False, pos_x=None, pos_y=None, wp=True, o=False):
        super().__init__(built, pos_x, pos_y, "barrack")
        self.x = pos_x
        self.y = pos_y
        self.wp = wp
        self.o = o

    def training(self):
        if self.units < 20:
            self.units += randrange(0, 3) * (houses.people // 5)

    def eat(self):
        farm.food -= (self.units // 5 - 5)

    def set_unit(self):
        if self.units >= 20 and mine.metal >= 10:
            npcs.append(UnitP(self.rect.x // 64, self.rect.y // 64, "unit"))
            self.units -= 20
            mine.metal -= 10

    @classmethod
    def get_units(cls):
        return cls.units


class Sawmill(Building):
    wood = 20

    def __init__(self, built=False, pos_x=None, pos_y=None, wp=True, o=False):
        super().__init__(built, pos_x, pos_y, "sawmill")
        self.wp = wp
        self.o = o

    @classmethod
    def sawing(cls, c=0.7):
        cls.wood += int(randrange(3, 6) * c)

    @classmethod
    def build(cls, n):
        cls.wood -= n

    @classmethod
    def use(cls):
        cls.wood -= int(randrange(0, 2) * houses.people * 0.1)

    @classmethod
    def get_res(cls):
        return cls.wood


class Castle(Building):
    def __init__(self, built=False, pos_x=None, pos_y=None, wp=True):
        if wp:
            super().__init__(built, pos_x, pos_y, "castle", wp=wp)
        else:
            super().__init__(built, pos_x, pos_y, "castle_e", wp=wp)


class Houses(Building):
    people = 10
    max_people = 10

    def __init__(self, built=False, pos_x=None, pos_y=None, wp=True, o=False):
        super().__init__(built, pos_x, pos_y, "houses")
        self.wp = wp
        self.o = o

    @classmethod
    def do_people(cls):
        if cls.max_people >= cls.people:
            if cls.people == 0:
                cls.people += randrange(0, 3)
            else:
                cls.people += randrange(-1, 5)

    @classmethod
    def die_people(cls):
        f = 0
        if farm.food - cls.people <= 5:
            f += 1
        elif farm.food - cls.people > 10:
            f -= 1
        if f > 0:
            cls.people -= f

    @classmethod
    def do_max_people(cls):
        cls.max_people += 10

    @classmethod
    def consume(cls):
        farm.eat()
        mine.use()
        sawmill.use()

    @classmethod
    def get_people(cls):
        return cls.people


class Camera:
    # зададим начальный сдвиг камеры
    def __init__(self):
        self.dx = 0
        self.dy = 0

    def apply(self, obj):
        obj.rect.x += self.dx
        obj.rect.y += self.dy

    def update(self, target):
        self.dx = -(target.rect.x + target.rect.w // 2 - width // 2)
        self.dy = -(target.rect.y + target.rect.h // 2 - height // 2)


def draw_images():
    for index, i in enumerate(im):
        screen.blit(i, (index * 64, 0))
    n = 0
    for i in image_check_res:
        screen.blit(i, (n * 64 + 320, 0))
        n += 1


def load_game():
    con = sqlite3.connect("save")
    cur = con.cursor()
    b = cur.execute("SELECT * FROM buildings").fetchall()
    n = cur.execute("SELECT * FROM npcs").fetchall()
    farm.food = max(cur.execute("SELECT food FROM player").fetchall())[0]
    mine.stone = max(cur.execute("SELECT stone FROM player").fetchall())[0]
    mine.metal = max(cur.execute("SELECT metal FROM player").fetchall())[0]
    houses.people = max(cur.execute("SELECT people FROM player").fetchall())[0]
    sawmill.wood = max(cur.execute("SELECT wood FROM player").fetchall())[0]
    c = 0
    for i in buildings:
        if type(i) == Barrack:
            i.units = 0
            c += 1
    for i in b[:]:
        pos = i[2][1:-1].split(", ")
        if "Farm" in i[1]:
            if can_build((int(pos[0]), float(pos[1])), "Farm"):
                buildings.append(Farm(True, int(pos[0]) // 64, float(pos[1]) // 64, wp=i[-1]))
        if "Mine" in i[1]:
            if can_build((int(pos[0]), float(pos[1])), "Mine"):
                buildings.append(Mine(True, int(pos[0]) // 64, float(pos[1]) // 64, wp=i[-1]))
        if "Sawmill" in i[1]:
            if can_build((int(pos[0]), float(pos[1])), "Sawmill"):
                buildings.append(Sawmill(True, int(pos[0]) // 64, float(pos[1]) // 64, wp=i[-1]))
        if "Houses" in i[1]:
            if can_build((int(pos[0]), float(pos[1])), "Houses"):
                buildings.append(Houses(True, int(pos[0]) // 64, float(pos[1]) // 64, wp=i[-1]))
        if "Barrack" in i[1]:
            if can_build((int(pos[0]), float(pos[1])), "Barrack"):
                buildings.append(Barrack(True, int(pos[0]) // 64, float(pos[1]) // 64, wp=i[-1]))
        if "Castle" in i[1]:
            if can_build((int(pos[0]), float(pos[1])), "Castle"):
                buildings.append(Castle(True, int(pos[0]) // 64, float(pos[1]) // 64, wp=i[-1]))
    for i in n[:]:
        pos = i[2][1:-1].split(",")
        if "UnitP" in i[1]:
            npcs.append(UnitP(int(pos[0]) // 64, float(pos[1]) // 64, "unit", i[-1]))
            print(npcs)
        elif "Enemy" in i[1]:
            npcs.append(Enemy(int(pos[0]) // 64, float(pos[1]) // 64, int(i[-1])))


def handle_mouse_click(pos):
    global build_type, cursor_image
    x, y = pos
    col = x // 64
    row = y // 64
    if row == 0 <= col < len(images):
        if build_type == 0:
            build_type = col + 1
            cursor_image = load_image(f"{images[col].split("_")[0]}.png")
        else:
            build_type = 0
            cursor_image = load_image(f"camera.png")
        return True
    return False


def build_res():
    res_wood = "white" if sawmill.get_res() >= 15 else "red"
    res_stone = "white" if mine.get_res()[0] >= 10 else "red"
    res_metal = "white" if mine.get_res()[1] >= 5 else "red"
    text = font.render("15", True, res_wood)
    text_rect = text.get_rect(center=(width - 224, 32))
    screen.blit(text, text_rect)
    text = font.render("10", True, res_stone)
    text_rect = text.get_rect(center=(width - 162, 32))
    screen.blit(text, text_rect)
    text = font.render("5", True, res_metal)
    text_rect = text.get_rect(center=(width - 96, 32))
    screen.blit(text, text_rect)


# основной персонаж
player = None

# группы спрайтов
all_sprites = pygame.sprite.Group()
tiles_group = pygame.sprite.Group()
player_group = pygame.sprite.Group()
build_group = pygame.sprite.Group()
walls_group = pygame.sprite.Group()
npc_group = pygame.sprite.Group()


def generate_level(level):
    new_player, x, y, new_enemy = None, None, None, None
    for y in range(len(level)):
        for x in range(len(level[y])):
            if level[y][x] == '.':
                Tile('empty', x, y)
            elif level[y][x] == '#':
                Tile('water', x, y)
            elif level[y][x] == '@':
                Tile('empty', x, y)
                new_player = Player(x, y)
                buildings.append(Castle(True, x, y - 0.5))
            elif level[y][x] == '*':
                Tile('i_wall', x, y)
            elif level[y][x] == '^':
                Tile('rock', x, y)
            elif level[y][x] == '8':
                Tile('rock', x, y)
                buildings.append(Mine(True, x, y - 0.5))
            elif level[y][x] == '%':
                Tile('empty', x, y)
                buildings.append(Farm(True, x, y - 0.5))
            elif level[y][x] == '9':
                Tile('empty', x, y)
                buildings.append(Sawmill(True, x, y - 0.5))
            elif level[y][x] == '$':
                Tile('empty', x, y)
                houses = Houses(True, x, y - 0.5)
                buildings.append(houses)
            elif level[y][x] == '1':
                Tile('rock', x, y)
                buildings.append(Mine(True, x, y - 0.5, False))
            elif level[y][x] == '2':
                Tile('empty', x, y)
                buildings.append(Farm(True, x, y - 0.5, wp=False))
            elif level[y][x] == '3':
                Tile('empty', x, y)
                buildings.append(Sawmill(True, x, y - 0.5, False))
            elif level[y][x] == '4':
                Tile('empty', x, y)
                houses = Houses(True, x, y - 0.5, False)
                buildings.append(houses)
            elif level[y][x] == '!':
                Tile('forest', x, y)
            elif level[y][x] == '0':
                Tile('empty', x, y)
                new_enemy = EnemyKing(x, y)
                buildings.append(Castle(True, x, y - 0.5, wp=False))
    return new_player, x, y, new_enemy


def can_build(c, b, *args):
    """
    можно ли строить в этой клетке?
    """
    for i in tiles_group:
        if type(i) == Tile:
            n = i.get_cords()[0] // 64 == c[0] // 64 and i.get_cords()[1] // 64 == c[1] // 64
            if (i.tile_type == "water" or i.tile_type == "i_wall") and n:
                return False
    for i in buildings:
        if i.get_cords()[0] // 64 == c[0] // 64 and i.get_cords()[1] // 64 == c[1] // 64:
            return False
    for i in args:
        if "wood" in i.keys():
            if i["wood"] > sawmill.wood:
                return False
        if "stone" in i.keys():
            if i["stone"] > mine.stone:
                return False
        if "metal" in i.keys():
            if i["metal"] > mine.metal:
                return False
    for i in all_sprites:
        if type(i) == Tile:
            n = (c[0] // 64 * 64, c[1] // 64 * 64) == (i.rect.x, i.rect.y)
            if b != "Mine":
                if i.tile_type == "forest" or i.tile_type == "empty" and n:
                    return True
            if i.tile_type == "rock" and b == "Mine" and n:
                return True
            elif i.tile_type == "rock" and b != "Mine" and n:
                return False
    return False


def ext():
    for i in buildings:
        if i.wp:
            if type(i) == Farm:
                i.farming()
            elif type(i) == Mine:
                i.mining()
            elif type(i) == Sawmill:
                i.sawing()
            elif type(i) == Barrack:
                i.training()
            elif type(i) == Houses:
                i.do_people()


def counters():
    res = [str(farm.get_res()), str(sawmill.get_res()), str(mine.get_res()[0]), str(mine.get_res()[1]),
           str(houses.get_people())]
    x = 112
    y = 436
    n = 0
    screen.blit(load_image('kaka.png'), (0, 432))
    for i in stat_images:
        text = font.render(res[n], True, "white")
        text_rect = text.get_rect()
        screen.blit(stat_images[i], (x * n, y))
        text_rect.bottomright = (x * (n + 1) - 8, 480)
        screen.blit(text, text_rect)
        n += 1


def condition():
    for i in buildings:
        for j in all_sprites:
            if type(j) == Tile:
                if type(i) == Sawmill:
                    if i.get_cords() == (j.rect.x, j.rect.y):
                        if j.tile_type == "forest":
                            i.set_con()
                if type(i) == Mine:
                    if i.get_cords() == (j.rect.x, j.rect.y):
                        if j.tile_type == "rock":
                            i.set_con()
                if type(i) == Farm:
                    if i.get_cords() == (j.rect.x, j.rect.y):
                        if j.tile_type == "empty":
                            i.set_con()


def build(pos):
    global build_type, cursor_image
    if not handle_mouse_click(pos):
        mixer.music.load('data/build_voice.mp3')
        mixer.music.set_volume(0.15)
        if build_type == 1:
            if can_build(pos, "Farm", {"wood": 15, "stone": 10, "metal": 5}):
                build_type = 0
                cursor_image = load_image(f"camera.png")
                sawmill.build(15)
                mine.build(5)
                buildings.append(Farm(True, pos[0] // 64, pos[1] // 64, o=True))
                mixer.music.play()
        elif build_type == 2:
            if can_build(pos, "Mine", {"wood": 15, "stone": 10, "metal": 5}):
                build_type = 0
                cursor_image = load_image(f"camera.png")
                sawmill.build(15)
                mine.build(5)
                buildings.append(Mine(True, pos[0] // 64, pos[1] // 64, o=True))
                mixer.music.play()
        elif build_type == 4:
            if can_build(pos, "Sawmill", {"wood": 15, "stone": 10, "metal": 5}):
                build_type = 0
                cursor_image = load_image(f"camera.png")
                sawmill.build(15)
                mine.build(5)
                buildings.append(Sawmill(True, pos[0] // 64, pos[1] // 64, o=True))
                mixer.music.play()
        elif build_type == 3:
            if can_build(pos, "", {"wood": 15, "stone": 10, "metal": 5}):
                build_type = 0
                cursor_image = load_image(f"camera.png")
                sawmill.build(15)
                mine.build(5)
                buildings.append(Barrack(True, pos[0] // 64, pos[1] // 64, o=True))
                mixer.music.play()
        elif build_type == 5:
            if can_build(pos, "", {"wood": 15, "stone": 10, "metal": 5}):
                build_type = 0
                cursor_image = load_image(f"camera.png")
                sawmill.build(15)
                mine.build(5)
                buildings.append(Houses(True, pos[0] // 64, pos[1] // 64, o=True))
                mixer.music.play()
                houses.do_max_people()


def animate(pos):
    for i in sp:
        im = load_image(i)
        screen.blit(im, (pos[0] // 64 * 64, pos[1] // 64 * 64))
        pygame.display.flip()
        time.sleep(0.2)


def terminate():
    pygame.quit()
    sys.exit()


def start_screen():
    fon = pygame.transform.scale(load_image('fon.png'), (width, height))
    screen.blit(fon, (0, 0))

    button1_rect = pygame.Rect(width // 2 - 400 // 2, 100, 400, 100)
    button2_rect = pygame.Rect(width // 2 - 400 // 2, 210, 400, 100)
    button3_rect = pygame.Rect(width // 2 - 400 // 2, 320, 400, 100)

    button1_image = pygame.transform.scale(load_image('n_game_b.png'), (400, 100))
    button2_image = pygame.transform.scale(load_image('l_game_b.png'), (400, 100))
    button3_image = pygame.transform.scale(load_image('exit_b.png'), (400, 100))

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                terminate()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if button1_rect.collidepoint(event.pos):
                    training_window()
                    return
                elif button2_rect.collidepoint(event.pos):
                    load_game()
                    return
                elif button3_rect.collidepoint(event.pos):
                    terminate()
        screen.blit(button1_image, button1_rect)
        screen.blit(button2_image, button2_rect)
        screen.blit(button3_image, button3_rect)

        pygame.display.flip()
        clock.tick(FPS)


def save_window():
    fon = pygame.transform.scale(load_image('fon.png'), (width, height))
    screen.blit(fon, (0, 0))

    button1_rect = pygame.Rect(width // 2 - 400 // 2, 100, 400, 100)
    button2_rect = pygame.Rect(width // 2 - 400 // 2, 210, 400, 100)
    button3_rect = pygame.Rect(width // 2 - 400 // 2, 320, 400, 100)

    button1_image = pygame.transform.scale(load_image('back_b.png'), (400, 100))
    button2_image = pygame.transform.scale(load_image('save_b.png'), (400, 100))
    button3_image = pygame.transform.scale(load_image('exit_b.png'), (400, 100))

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                terminate()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if button1_rect.collidepoint(event.pos):
                    return
                elif button2_rect.collidepoint(event.pos):
                    save_game()
                    return
                elif button3_rect.collidepoint(event.pos):
                    terminate()
        screen.blit(button1_image, button1_rect)
        screen.blit(button2_image, button2_rect)
        screen.blit(button3_image, button3_rect)

        pygame.display.flip()
        clock.tick(FPS)


def training_window():
    fon = pygame.transform.scale(load_image('fon.png'), (width, height))
    screen.blit(fon, (0, 0))

    button1_rect = pygame.Rect(width // 2 - 192, 100, 200, 100)
    button2_rect = pygame.Rect(width // 2 - 256, 240, 200, 100)
    button3_rect = pygame.Rect(width // 2 + 32, 240, 200, 100)

    button1_image = pygame.transform.scale(load_image('question_b.png'), (368, 128))
    button2_image = pygame.transform.scale(load_image('yes_b.png'), (224, 100))
    button3_image = pygame.transform.scale(load_image('no_b.png'), (224, 100))

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                terminate()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if button2_rect.collidepoint(event.pos):
                    training(0)
                    return
                elif button3_rect.collidepoint(event.pos):
                    return
        screen.blit(button1_image, button1_rect)
        screen.blit(button2_image, button2_rect)
        screen.blit(button3_image, button3_rect)

        pygame.display.flip()
        clock.tick(FPS)


def training(step):
    if step == 0:
        t1 = "Чтобы продолжить обучение"
        t2 = "нажимайте на SPACE"
        t3 = ""
    elif step == 1:
        t1 = "Вашей главной целью является"
        t2 = "разрушение и захват"
        t3 = "вражеского замка"
    elif step == 2:
        t1 = "Для этого вам нужно строить"
        t2 = "здания и тренировать юнитов"
        t3 = "а также следить за ресурсами"
    elif step == 3:
        t1 = "Чтобы строить здания НАЖМИТЕ"
        t2 = "на план здания, наведитесь"
        t3 = "на клетку и ещё раз нажмите"
    elif step == 4:
        t1 = "Рядом с планами есть числа"
        t2 = "они показывают хватает ли "
        t3 = "вам ресурсов для строительства"
    elif step == 5:
        t1 = "Снизу вы можете увидеть"
        t2 = "сколько у вас: еды, древесины,"
        t3 = "камня, металла и население"
    elif step == 6:
        t1 = "Еду едят люди;"
        t2 = "дерево, камень и металл"
        t3 = "нужен для строительства"
    elif step == 5:
        t1 = "Чтобы создать юнита вам нужно"
        t2 = "построить казарму и подождать"
        t3 = "пока войска тренируются"
    elif step == 6:
        t1 = "Когда тренировка закончится вы"
        t2 = "должны нажать на казарму, после"
        t3 = "чего появится солдат"
    elif step == 7:
        t1 = "Чтобы управлять нажмите на него."
        t2 = "Он завсетится и если вы нажмёте на"
        t3 = "клетку, то он пойдёт туда"
    elif step == 8:
        t1 = "Если вы нажмёте на вражеское"
        t2 = "здание или противника то юниты"
        t3 = "будут атаковать их"
    elif step == 9:
        t1 = "Если ваши юниты сломают"
        t2 = "вражескую крепость, то вы"
        t3 = "победите!"
    else:
        return
    text = font.render(t1, True, (220, 220, 220), "black")
    text2 = font.render(t2, True, (220, 220, 220), "black")
    text3 = font.render(t3, True, (220, 220, 220), "black")
    text_rect = text.get_rect()
    text_rect.bottomright = (450, 130)
    screen.blit(text, text_rect)
    text_rect2 = text2.get_rect()
    text_rect2.bottomright = (450, 160)
    screen.blit(text2, text_rect)
    text_rect3 = text3.get_rect()
    text_rect3.bottomright = (450, 190)
    screen.blit(text3, text_rect)
    while True:
        screen.fill("black")
        camera.update(player)
        tiles_group.draw(screen)
        player_group.draw(screen)
        all_sprites.update()
        for sprite in all_sprites:
            camera.apply(sprite)
        npc_group.draw(screen)
        counters()
        draw_images()
        build_res()
        screen.blit(text, text_rect)
        screen.blit(text2, text_rect2)
        screen.blit(text3, text_rect3)
        pygame.display.flip()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                terminate()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    training(step + 1)
                    return


tax = 4
font = pygame.font.Font(None, 36)
player, level_x, level_y, enemy = generate_level(load_level('map.txt'))
running = True
camera = Camera()
start_time = time.time()
farm, mine, sawmill, barrack = Farm(False), Mine(False), Sawmill(False), Barrack(False)
castle, houses = Castle(False), Houses(False)
elapsed_time = 0
build_type = 0
start_screen()
factor = 0
x = True
f = True
cursor_image = 0
last_click_time = 0
click_cooldown = 150
y = 0
speed = 60
attack = False
start_the_game = False
pygame.time.set_timer(USEREVENT + 1, 1000)
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                save_window()
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                build(event.pos)
                condition()
                for i in buildings:
                    if type(i) == Barrack:
                        if (event.pos[0] // 64, event.pos[1] // 64) == (i.get_cords()[0] // 64,
                                                                        i.get_cords()[1] // 64):
                            i.set_unit()
            if event.button == 3:
                f = False
                for i in npcs:
                    if type(i) == UnitP:
                        if (event.pos[0] // 64, event.pos[1] // 64) == (i.get_cords()[0] // 64, i.get_cords()[1] // 64):
                            i.control()
                            f = True
                if not f:
                    e_c = 0
                    x = True
                    for i in npcs:
                        if type(i) == Enemy:
                            e_c = i.get_cords()
                        for i in npcs:
                            if type(i) == UnitP and x:
                                if e_c != 0:
                                    if (event.pos[0] // 64, event.pos[1] // 64) == (e_c[0] // 64, e_c[1] // 64):
                                        i.set_point(event.pos[0] // 64 * 64, event.pos[1] // 64 * 64, True)
                                        x = False
                                    else:
                                        i.set_point(event.pos[0] // 64 * 64, event.pos[1] // 64 * 64)
                    b_c = 0
                    x = True
                    for i in buildings:
                        b_c = i.get_cords()
                        b_t = i
                        for i in npcs:
                            if type(i) == UnitP and x:
                                if b_c != 0:
                                    if (event.pos[0] // 64, event.pos[1] // 64) == (b_c[0] // 64, b_c[1] // 64):
                                        if type(b_t) == Farm:
                                            if not b_t.can_farm():
                                                i.set_point(event.pos[0] // 64 * 64, event.pos[1] // 64 * 64, True)
                                                x = False
                                            else:
                                                i.set_point(event.pos[0] // 64 * 64, event.pos[1] // 64 * 64)
                                        if type(b_t) == Mine:
                                            if not b_t.can_mine():
                                                i.set_point(event.pos[0] // 64 * 64, event.pos[1] // 64 * 64, True)
                                                x = False
                                            else:
                                                i.set_point(event.pos[0] // 64 * 64, event.pos[1] // 64 * 64)
                                        if type(b_t) == Sawmill:
                                            if not b_t.can_saw():
                                                i.set_point(event.pos[0] // 64 * 64, event.pos[1] // 64 * 64, True)
                                                x = False
                                            else:
                                                i.set_point(event.pos[0] // 64 * 64, event.pos[1] // 64 * 64)
                                        if type(b_t) == Barrack:
                                            if not b_t.can_train():
                                                i.set_point(event.pos[0] // 64 * 64, event.pos[1] // 64 * 64, True)
                                                x = False
                                            else:
                                                i.set_point(event.pos[0] // 64 * 64, event.pos[1] // 64 * 64)
                                        if type(b_t) == Houses:
                                            if not b_t.can_do_people():
                                                i.set_point(event.pos[0] // 64 * 64, event.pos[1] // 64 * 64, True)
                                                x = False
                                            else:
                                                i.set_point(event.pos[0] // 64 * 64, event.pos[1] // 64 * 64)
                                    else:
                                        i.set_point(event.pos[0] // 64 * 64, event.pos[1] // 64 * 64)

    screen.fill((255, 255, 255))
    tiles_group.draw(screen)
    player_group.draw(screen)
    all_sprites.update()
    npc_group.draw(screen)
    current_time = time.time()
    elapsed_time = current_time - start_time
    draw_images()
    build_res()
    camera.update(player)
    counters()
    for sprite in all_sprites:
        camera.apply(sprite)
    if elapsed_time >= 3:
        enemy.build()
        enemy.war()
        houses.consume()
        for i in npcs:
            if type(i) == UnitP:
                i.attack()
                if i.len_x != 0 or i.len_y != 0:
                    i.u_move()
        for i in buildings:
            if type(i) == Barrack:
                i.eat()
        houses.die_people()
        start_time = time.time()
        ext()
    if pygame.mouse.get_focused() and cursor_image != 0:
        cursor_pos = pygame.mouse.get_pos()
        screen.blit(cursor_image, (cursor_pos[0], cursor_pos[1]))
    pygame.display.flip()
    clock.tick(speed)
