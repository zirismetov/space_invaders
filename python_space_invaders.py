import json
import math
import os
import random
import time
from subprocess import call
import app
# pip3 install pynput
# pip install pynput
from typing import List

from pynput import keyboard
from pynput.keyboard import Key

SCENE_WIDTH = 11
SCENE_HEIGHT = 15


class Position2D(object):
    def __init__(self, val_x, val_y, is_check_scene=True):
        super().__init__()
        self.__is_check_scene = is_check_scene
        self.__x = val_x
        self.__y = val_y

    @property
    def x(self):  # get_x
        return self.__x

    @x.setter
    def x(self, val):  # set_x
        if not self.__is_check_scene or 0 <= val < SCENE_WIDTH:
            self.__x = val

    @property
    def y(self):  # get_y
        return self.__y

    @y.setter
    def y(self, val):  # set_y
        if not self.__is_check_scene or 0 <= val < SCENE_HEIGHT:
            self.__y = val


class Vector2D(Position2D):
    def __init__(self, val_x, val_y):
        super().__init__(val_x, val_y, is_check_scene=False)


class Element(object):
    def __init__(self):  # constructor
        super().__init__()
        self._position = Position2D(0, 0)
        self._char = '⬜️'

    @property
    def char(self):
        return self._char

    @property
    def position(self):
        return self._position

    @position.setter
    def position(self, pos):
        self._position = pos

    def draw(self, scene):
        pos_x = int(self.position.x)
        pos_y = int(self.position.y)
        scene[pos_y][pos_x] = self.char

    def update(self, delta_time):
        pass

    def check_collsion(self, other):
        is_collision = False
        if int(other.position.x) == int(self.position.x) and \
                int(other.position.y) == int(self.position.y):
            is_collision = True
        return is_collision


class Wall(Element):
    def __init__(self, position):  # constructor
        super().__init__()
        self._char = '🏛'
        self._position = position


class Explosion(Element):
    def __init__(self, position):  # constructor
        super().__init__()
        self._char = '💥'
        self._position = position
        self._life = 0.5

    def update(self, delta_time):
        self._life -= delta_time
        if self._life < 0:
            GameState.instance().elements.remove(self)


class MovableElement(Element):
    def __init__(self):  # constructor
        super().__init__()
        self._char = '🛸'
        self._speed = 1.0
        self._direction = Position2D(0, 0, is_check_scene=False)

    @property
    def direction(self):
        return self._direction

    def update(self, delta_time):
        self.position.x += self._direction.x * self._speed * delta_time
        self.position.y += self._direction.y * self._speed * delta_time

    def stop(self):
        self._direction.x = 0
        self._direction.y = 0

    def left(self):
        self._direction.x = -1
        self._direction.y = 0

    def right(self):
        self._direction.x = 1
        self._direction.y = 0

    def up(self):
        self._direction.x = 0
        self._direction.y = -1

    def down(self):
        self._direction.x = 0
        self._direction.y = 1


class Player(MovableElement):
    def __init__(self):
        super().__init__()
        self._speed = 1.5
        self._char = '📤'

    def fire_rocket(self):
        rocket = Rocket(pos=Position2D(int(self.position.x), int(self.position.y)))
        rocket.up()
        GameState.instance().elements.append(rocket)

    def check_collsion(self, other):
        if type(other) == Rocket:
            if other.direction.y > 0:
                coll = super(Player, self).check_collsion(other)
                return coll


class Rocket(MovableElement):
    def __init__(self, pos: Position2D, is_up=True):
        super().__init__()
        self.position = pos
        self._speed = 1.5
        self._char = '🔺'
        if not is_up:
            self._char = '🔻'

    def update(self, delta_time):
        super().update(delta_time)
        if int(self.position.y) == 0:
            GameState.instance().elements.remove(self)


class Alien(MovableElement):
    def __init__(
            self,
            pos: Position2D,
            dir: Vector2D,
            listeners_aliens
    ):
        super().__init__()
        self.position = pos
        self._speed = 0.5
        self._char = '👾'
        self._direction = dir
        self._listeners_aliens = listeners_aliens  # event listeners or observers
        self._listeners_aliens.append(self.notify)  # not calling function but adding function as a pointer

        self._patience = 0
        self.reset_patience()

    def reset_patience(self):
        self._patience = 5 + random.random() * 10

    def notify(self, event):
        if type(event) == EventAlienDirection:
            self._direction = event.new_dir
            self._position.y += 1
        elif type(event) == EventAlienFire:
            self.reset_patience()

    def check_border(self):
        is_at_border = False
        if round(self.position.x) == 0 or round(self.position.x) == SCENE_WIDTH:
            is_at_border = True
            self._direction.x *= -1
            event = EventAlienDirection(
                new_dir=self._direction
            )
            for listener in self._listeners_aliens:
                listener(event)
        return is_at_border

    def fire_rocket(self):
        event = EventAlienFire()
        for listener in self._listeners_aliens:
            listener(event)
        rocket = Rocket(pos=Position2D(int(self.position.x), int(self.position.y) + 1), is_up=False)
        rocket.down()
        GameState.instance().elements.append(rocket)

    def update(self, delta_time):
        super(Alien, self).update(delta_time)

        is_alien_below = True
        for element in GameState.instance().elements:
            if type(element) == Alien:
                if element != self:
                    if int(element.position.x) == int(self.position.x):
                        if int(element.position.y) > int(self.position.y):
                            is_alien_below = False
                            break

        self._patience -= delta_time
        if self._patience < 0:
            self.reset_patience()
            if is_alien_below:
                self.fire_rocket()


class EventAlien():
    def __init__(self):
        super().__init__()
        pass


class EventAlienDirection(EventAlien):
    def __init__(self, new_dir):
        super().__init__()
        self.new_dir = new_dir


class EventAlienFire(EventAlien):
    def __init__(self):
        super().__init__()
        pass


class GameState(object):  # singleton
    def __init__(self):
        super().__init__()
        if self._instance is not None:
            raise Exception('cannot init 2 singleton instances')
        self._instance = self

        pos_middle = Position2D(
            val_x=int(SCENE_WIDTH / 2),
            val_y=SCENE_HEIGHT - 1
        )
        self.player = Player()
        self.player.position = pos_middle
        self.elements: List = [
            self.player,
            Wall(position=Position2D(2, SCENE_HEIGHT - 4)),
            Wall(position=Position2D(4, SCENE_HEIGHT - 4)),
            Wall(position=Position2D(6, SCENE_HEIGHT - 4)),
            Wall(position=Position2D(8, SCENE_HEIGHT - 4))
        ]

        self.lives = 1
        self.score = 5

        self.listeners_aliens = []

        rand_x = -1.0
        if random.random() > 0.5:  # 0..1
            rand_x = 1.0
        for i in range(5):
            for j in range(2):
                alien = Alien(
                    pos=Position2D(i + 3, j + 3),
                    dir=Vector2D(rand_x, 0.0),
                    listeners_aliens=self.listeners_aliens
                )
                self.elements.append(alien)
        self.is_game_running = True

    _instance = None

    @staticmethod
    def instance():
        if GameState._instance is None:
            GameState._instance = GameState()
        return GameState._instance



elements = GameState.instance().elements
player = GameState.instance().player

def delete_el(idx_i, idx_j):
    position_expl = elements[idx_i].position
    del elements[idx_j]
    del elements[idx_i ]
    elements.append(Explosion(position_expl))

def game_over():
    data = json.loads(app.get_high_scores_database())
    is_current_score_top10(data)

    upd_data = json.loads(app.get_high_scores_database())
    print_high_scores(upd_data)
    exit()

def is_current_score_top10(data):
    for record in data:
        if GameState.instance().score > record[1] or len(data) < 10:
            app.add_new_score(json.dumps({inpt_name: GameState.instance().score}))
            break


def print_high_scores(data):
    print('Top 10 scores:')
    for record in data:
         print(f'{record[0]}: {record[1]}')


inpt_name = input('Please enter you name:')

while GameState.instance().is_game_running:
    cmd_clear = 'clear'
    if os.name == 'nt':
        cmd_clear = 'cls'
    _ = call('clear')

    scene = []
    for i in range(SCENE_HEIGHT):  # 0...14
        columns = []
        for j in range(SCENE_WIDTH):
            columns.append('⬛️')
        scene.append(columns)

    for element in elements:
        element.draw(scene)

    scene_lines = []
    for line in scene:
        str_line = ''.join(line)
        scene_lines.append(str_line)
    str_scene = '\n'.join(scene_lines)
    print(f'Score: {GameState.instance().score}  Lives: {GameState.instance().lives}')
    print(str_scene)

    delay = 0.2  # seconds
    timestamp = time.time()

    with keyboard.Events() as events:
        key = events.get(delay)

        if key is not None:  # key != null
            key_code = key.key
            if key_code == Key.left:
                player.left()
            elif key_code == Key.right:  # else if
                player.right()
            elif key_code == Key.space:
                player.fire_rocket()
            elif key_code == Key.esc:
                GameState.instance().is_game_running = False
        else:
            player.stop()

    dt = delay - (time.time() - timestamp)
    if dt > 0:
        time.sleep(dt)

    for element in elements:
        if type(element) == Alien:
            if element.check_border():
                break

    dt = time.time() - timestamp
    for element in elements:
        element.update(dt)

    is_collision = False
    is_all_aliens_dead = True
    for i in range(len(elements)):
        for j in range(i + 1, len(elements)):
            if (type(elements[i]) != Rocket and type(elements[j]) == Rocket) or \
                    (type(elements[j]) != Rocket and type(elements[i]) == Rocket):
                if elements[i].check_collsion(elements[j]):
                    if type(elements[i]) == Player and type(elements[j]) == Rocket or \
                            type(elements[j]) == Player and type(elements[i]) == Rocket:
                        GameState.instance().lives -= 1
                        delete_el(idx_i= i, idx_j= j)
                        if GameState.instance().lives <= 0:
                            print(f'Game over! You lost, your score: {GameState.instance().score}')
                            game_over()
                        player = Player()
                        player.position = Position2D(
                            val_x=int(SCENE_WIDTH / 2),
                            val_y=SCENE_HEIGHT - 1
                        )
                        elements.append(player)
                    elif type(elements[i]) == Alien and type(elements[j]) == Rocket or \
                            type(elements[j]) == Alien and type(elements[i]) == Rocket:
                        delete_el(idx_i=i, idx_j=j)
                        GameState.instance().score += 1
                        for each in elements:
                            if type(each) == Alien:
                                is_all_aliens_dead = False
                                break
                        if is_all_aliens_dead:
                            print(f"Game Over! You won! Your score: {GameState.instance().score}")
                            game_over()
                    elif type(elements[i]) == Wall and type(elements[j]) == Rocket or \
                            type(elements[j]) == Wall and type(elements[i]) == Rocket:
                        delete_el(idx_i=i, idx_j=j)

                    is_collision = True

                    break
        if is_collision:
            break
    for i in range(len(elements)):
        if type(elements[i]) == Rocket:
            if int(elements[i].position.y) == SCENE_HEIGHT - 1:
                del elements[i]
                break
