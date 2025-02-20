import os
import pygame
import pygame_menu

pygame.init()
surface = pygame.display.set_mode((500, 500))


def new_game():
    menu = pygame_menu.Menu("Menu", 500, 500)

    input_style = {
        'background_color': (100, 50, 10),
        'color': (0, 0, 0),
        'selection_color': (0, 0, 0)
    }

    image = pygame_menu.BaseImage(
        image_path=os.path.join("data/start_b.png")
    ).scale(0.25, 0.25)
    menu.add.banner(image, start)

    image = pygame_menu.BaseImage(
        image_path=os.path.join("data/back_b.png")
    ).scale(0.25, 0.25)
    menu.add.banner(image, start_menu)

    menu.mainloop(surface)


def start():
    global running
    running = True


def load_the_game():
    pass


def setting():
    pass


def start_menu():
    menu = pygame_menu.Menu("Menu", 500, 500)
    image = pygame_menu.BaseImage(
        image_path=os.path.join("data/n_game_b.png")
    ).scale(0.25, 0.25)
    menu.add.banner(image, new_game)

    image = pygame_menu.BaseImage(
        image_path=os.path.join("data/setting_b.png")
    ).scale(0.25, 0.25)
    menu.add.banner(image, setting)

    image = pygame_menu.BaseImage(
        image_path=os.path.join("data/exit_b.png")
    ).scale(0.25, 0.25)
    menu.add.banner(image, pygame_menu.events.EXIT)

    menu.mainloop(surface)


start_menu()
