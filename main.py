import math
import random
import tkinter as tk
from tkinter import simpledialog
import pygame
from arrow import draw_arrow
from screeninfo import get_monitors
from collections import deque
import numpy as np

# Constants
FPS = 60
G = 5
sf = 50
virtual_universe = 1
UNIVERSALDENSITY = 5
frequency = 400
BARNES_HUT_THETA = 10000
max_radius = 200
min_radius = 1
max_random_radius = 1
max_merged_radius = 400
spin_radius = 400
spin_bodies = 1000

# Don't Changef
increment = 2
body_max = 10 ** 9
drawmode = False

BLACK = 0, 0, 0
WHITE = 255, 255, 255
RED = 255, 0, 0
GREEN = 0, 255, 0
BLUE = 0, 0, 255
YELLOW = 255, 255, 0

# Pygame initialization
pygame.init()
CLOCK = pygame.time.Clock()
m = get_monitors()[0]
s_width = virtual_universe * m.width
s_height = virtual_universe * (m.height) - 60
s_height = int(s_height)
s_width = int(s_width)

screen = pygame.display.set_mode((s_width, s_height))
pygame.display.set_caption("GRAV SIM")
create = False
new_planet = None


def get_randomcolor():
    return random.randint(100, 255), random.randint(100, 255), random.randint(100, 255)


def change_size():
    root = tk.Tk()
    root.withdraw()
    user_input = simpledialog.askinteger("Input", "Please enter the maximum size of random planets:")
    if user_input is not None:
        return min(max(1, user_input), max_radius)
    return max_radius


def change_spin_rad():
    root = tk.Tk()
    root.withdraw()
    user_input = simpledialog.askinteger("Input", "Please enter the galaxy's radius:")
    if user_input is not None:
        return min(user_input, 1000)
    return 100


def change_spin_bod():
    root = tk.Tk()
    root.withdraw()
    user_input = simpledialog.askinteger("Input", "Please enter the number of bodies in the galaxy:")
    if user_input is not None:
        return min(user_input, 8000)
    return 100


def change_THETA():
    root = tk.Tk()
    root.withdraw()
    user_input = simpledialog.askfloat("Input",
                                       "Please enter the BARNES_HUT coefficient θ. \n The higher the value, the less accurate but faster")
    if user_input is not None:
        return max(0, user_input)
    return 0.1


def get_number():
    root = tk.Tk()
    root.withdraw()
    user_input = simpledialog.askinteger("Input", "Please enter the number of planets:")
    if user_input is not None:
        return min(max(0, user_input), body_max)
    return 0


class Body:
    def __init__(self, xs, ys, vx, vy, radius=1, density=UNIVERSALDENSITY, color=get_randomcolor()):
        self.density = density
        self.radius = radius
        self.mass = self.radius * self.radius * self.density * math.pi

        self.x = xs
        self.y = ys
        self.color = color
        self.xa = 0
        self.ya = 0
        self.vx = vx
        self.vy = vy

    def is_out_of_bounds(self, width, height):
        flag = self.x < -self.radius or self.x > width + self.radius or self.y < -self.radius or self.y > height + self.radius
        if flag:
            self.x = -100 * s_width
            self.y = -100 * s_height
            self.mass = 0
            self.radius = 0
            self.vx = 0
            self.vy = 0
        return 0

    def collision(self, B2):
        distance = ((self.x - B2.x) ** 2 + (self.y - B2.y) ** 2) ** 0.5
        if distance < self.radius + B2.radius:
            return True
        future_x_self = self.x + self.vx
        future_y_self = self.y + self.vy
        future_x_B2 = B2.x + B2.vx
        future_y_B2 = B2.y + B2.vy

        distance = ((future_x_self - future_x_B2) ** 2 + (future_y_self - future_y_B2) ** 2) ** 0.5

        if distance < self.radius + B2.radius:
            return True
        return False

    def set_orbitalvelocity(self, B2):
        sign = random.choice([-1, 1])
        dx = B2.x - self.x
        dy = B2.y - self.y
        r = math.sqrt(dx ** 2 + dy ** 2)
        if r != 0:
            v = math.sqrt(G * B2.mass / r)
            theta = None
            if dx == 0:
                if dx == 0 and dy == 0:
                    theta = 0
                if dx == 0 and dy > 0:
                    theta = math.radians(90)
                if dx == 0 and dy < 0:
                    theta = math.radians(-90)
            else:
                theta = math.atan2(dy, dx)
            self.vx = v * math.cos(theta) * sign
            self.vy = v * math.sin(theta) * sign


        else:
            self.vx = 0
            self.vy = 0

    def get_attraction(self, B2):
        if B2.mass == 0 or self.mass == 0:
            return
        b2x, b2y = B2.x, B2.y
        dx = b2x - self.x
        dy = b2y - self.y
        r = math.sqrt(dx ** 2 + dy ** 2)
        if r != 0:
            rsqrd = r * r
            F_g = G * self.mass * B2.mass / rsqrd
            theta = None
            if dx == 0:
                if dx == 0 and dy == 0:
                    theta = 0
                if dx == 0 and dy > 0:
                    theta = math.radians(90)
                if dx == 0 and dy < 0:
                    theta = math.radians(-90)
            else:
                theta = math.atan2(dy, dx)
            F_x = F_g * math.cos(theta)
            F_y = F_g * math.sin(theta)
            self.xa += F_x / self.mass
            self.ya += F_y / self.mass

    def update(self):
        self.vx += self.xa
        self.vy += self.ya
        self.x += self.vx
        self.y += self.vy
        self.is_out_of_bounds(s_width, s_height)

    def draw(self, screen):
        px = int(self.x)
        py = int(self.y)
        if (self.is_out_of_bounds(s_width, s_height)):
            return
        pygame.draw.circle(screen, self.color, (px, py), self.radius)


class PlanetSet:
    def __init__(self):
        self.elems_init = {}
        self.elems_container = []

    def add(self, value):
        if id(value) not in self.elems_init:
            self.elems_container.append(value)
            self.elems_init[id(value)] = len(self.elems_container) - 1

    def remove(self, value):
        key = id(value)
        if key in self.elems_init:
            position = self.elems_init.pop(key)
            last_value = self.elems_container.pop()
            if position != len(self.elems_container):
                self.elems_container[position] = last_value
                self.elems_init[id(last_value)] = position

    def optimisedrandom(self):
        return random.choice(self.elems_container)

    def clear(self):
        self.elems_init = {}
        self.elems_container = []

    def __iter__(self):
        return iter(self.elems_container)

    def __len__(self):
        return len(self.elems_container)

    def getfirst(self):
        assert len(self.elems_container) != 0
        return self.elems_container[0]


inbound = PlanetSet()
planet_hash = {}


class QuadTrees:
    def __init__(self, x, y, w, h):
        self.x = x  # always top left like pygames
        self.y = y
        self.width = w
        self.height = h
        self.planet = None
        self.nw = None
        self.ne = None
        self.sw = None
        self.se = None
        self.parent = None
        self.children = []  # Initialize children as an empty list
        self.leaf = True
        self.total_mx = 0
        self.total_my = 0
        self.total_mass = 0
        self.cx = None
        self.cy = None

    def set_children(self):
        if self.width <= 1 or self.height <= 1:
            return
        fw = self.width // 2
        fh = self.height // 2
        self.nw = QuadTrees(self.x, self.y, fw, fh)
        self.ne = QuadTrees(self.x + fw, self.y, self.width - fw, fh)
        self.sw = QuadTrees(self.x, self.y + fh, fw, self.height - fh)
        self.se = QuadTrees(self.x + fw, self.y + fh, self.width - fw, self.height - fh)
        self.children = [self.nw, self.ne, self.sw, self.se]
        self.leaf = False

    def get_bounds(self):
        return (self.x, self.y, self.x + self.width, self.y + self.height)

    def draw_bounds(self):
        stack = deque()
        stack.append(self)
        while stack:
            # print("dra")
            # print("drawing")
            current_node = stack.pop()
            bounds = current_node.get_bounds()
            pygame.draw.line(screen, GREEN, (bounds[0], bounds[1]), (bounds[2], bounds[1]), 1)
            pygame.draw.line(screen, GREEN, (bounds[2], bounds[1]), (bounds[2], bounds[3]), 1)
            pygame.draw.line(screen, GREEN, (bounds[2], bounds[3]), (bounds[0], bounds[3]), 1)
            pygame.draw.line(screen, GREEN, (bounds[0], bounds[3]), (bounds[0], bounds[1]), 1)
            if not current_node.leaf:
                for child in current_node.children:
                    stack.append(child)

    def checkplanet(self, planet: Body):
        if planet.x >= self.x and planet.x < self.x + self.width and planet.y >= self.y and planet.y < self.y + self.height:
            return True


QT = QuadTrees(0, 0, s_width, s_height)


def QTree_point_update(body):
    try:
        if not QT.checkplanet(body):
            return

        ptr = planet_hash[body]
        while ptr is not None:
            # print("something...")
            ptr.total_mx += body.x * body.mass
            ptr.total_my += body.y * body.mass
            ptr.total_mass += body.mass
            ptr.cx = ptr.total_mx / ptr.total_mass
            ptr.cy = ptr.total_my / ptr.total_mass
            ptr.cy = ptr.total_my / ptr.total_mass
            if ptr is not None:
                ptr = ptr.parent
        # print()
    except KeyError:
        pass


def QTree_insert(body):
    # try:
    if not QT.checkplanet(body):
        # print("yo?")
        return
    stack = deque()
    stack.append((body, QT))
    while stack:
        # print("ins", len(stack))
        curr_node, curr_tree = stack.pop()
        if curr_tree.leaf:
            if curr_tree.planet is None:
                curr_tree.planet = curr_node
                planet_hash[curr_node] = curr_tree
                continue
            else:
                if (curr_tree.width <= 1 or curr_tree.height <= 1):
                    body.x = -s_width
                    body.y = -s_height
                    # print("No quadrants")
                    return False
                stack.append((curr_node, curr_tree))
                stack.append((curr_tree.planet, curr_tree))
                curr_tree.planet = None
                curr_tree.set_children()
                for child in curr_tree.children:
                    child.parent = curr_tree
        else:
            # print("that")
            for child in curr_tree.children:
                if child.checkplanet(curr_node):
                    stack.append((curr_node, child))
                    break
    return True


def QTree_range_query(n_body, n_QT):
    if not QT.checkplanet(n_body):
        return
    stack = deque()
    stack.append((n_body, n_QT))
    while stack:
        # print("rq")
        body, node = stack.pop()
        if (node.cx == None or node.cy == None):
            continue
        d = (body.x - node.cx) ** 2 + (body.y - node.cy) ** 2
        s = (node.width ** 2 + node.height ** 2)
        if node.leaf:
            if d != 0 and node.planet is not None and node.planet != body:
                body.get_attraction(node.planet)
        else:
            if s < d * BARNES_HUT_THETA and d != 0:
                new_bod = Body(node.cx, node.cy, 0, 0)
                new_bod.mass = node.total_mass
                body.get_attraction(new_bod)
            else:
                for child in node.children:
                    stack.append((body, child))


def handlecollision(body1, body2, restitution=0.8):
    if body1.mass == 0 or body2.mass == 0:
        return

    newcolor = get_randomcolor()
    newmass = body2.mass + body1.mass
    newradius = (body1.radius ** 2 + body2.radius ** 2) ** 0.5

    total_momentum_x = body1.vx * body1.mass + body2.vx * body2.mass
    total_momentum_y = body1.vy * body1.mass + body2.vy * body2.mass

    body1.vx = total_momentum_x / newmass
    body1.vy = total_momentum_y / newmass

    body1.vx *= restitution
    body1.vy *= restitution

    body1.mass = newmass
    body1.color = newcolor
    body1.radius = min(newradius, max_merged_radius)

    body2.x = -s_width
    body2.y = -s_height
    body2.is_out_of_bounds(s_width, s_height)


def QTree_handle_collisions(n_body, n_QT):
    stack = deque()
    stack.append((n_body, n_QT))
    while stack:
        # print("col")
        n_body, n_QT = stack.pop()
        if n_QT.leaf:
            if n_QT.planet == None or n_body == n_QT.planet:
                return
            if n_body.collision(n_QT.planet):
                handlecollision(n_body, n_QT.planet)
        else:
            for child in n_QT.children:
                if child.checkplanet(n_body):
                    stack.append((n_body, child))
                    break


def creating(new_planet):
    resizing = False
    gettrajectory = False
    new_planet.vx = 0
    new_planet.vy = 0
    while True:
        CLOCK.tick(FPS)
        screen.fill(BLACK)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                exit()
            else:
                if event.type == pygame.KEYDOWN and event.key == pygame.K_r and not gettrajectory:
                    resizing = not resizing
                if event.type == pygame.MOUSEBUTTONDOWN and (event.button == 4 or event.button == 5) and resizing:
                    if event.button == 4:
                        new_planet.radius += increment
                        new_planet.radius = min(max_radius, new_planet.radius)
                    else:
                        new_planet.radius -= increment
                        new_planet.radius = max(1, new_planet.radius)
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 3 and not resizing and not gettrajectory:
                    gettrajectory = True
                if event.type == pygame.MOUSEBUTTONUP and event.button == 3 and gettrajectory:
                    inbound.add(new_planet)
                    QTree_insert(new_planet)
                    QTree_point_update(new_planet)
                    return
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    inbound.add(new_planet)
                    QTree_insert(new_planet)
                    QTree_point_update(new_planet)
                    return

        for body in inbound:
            body.draw(screen)
        new_planet.draw(screen)
        if gettrajectory:
            pos = pygame.mouse.get_pos()
            end = pygame.Vector2(pos)
            draw_arrow(screen, (new_planet.x, new_planet.y), end, RED, 1, 10, 12)
            new_planet.vx = (pos[0] - new_planet.x) / sf
            new_planet.vy = (pos[1] - new_planet.y) / sf
        pygame.display.update()


def generate_planets(x):
    garbage = [body for body in inbound if body.is_out_of_bounds(s_width, s_height)]
    for body in garbage:
        inbound.remove(body)
    L = len(inbound)
    for i in range(x):
        new_body = Body(random.randint(0, s_width), random.randint(0, s_height), 0, 0, radius=1,
                        color=get_randomcolor())
        new_body.radius = random.randint(1, max_random_radius)
        if (QT.checkplanet(new_body)):
            new_body.xa = 0
            new_body.ya = 0
            inbound.add(new_body)
            can_insert = QTree_insert(new_body)
            if (can_insert):
                QTree_point_update(new_body)
                QTree_handle_collisions(new_body, QT)
            else:
                inbound.remove(new_body)


def update_bodies():
    global inbound, QT
    for elem in inbound:
        elem.xa = 0
        elem.ya = 0
        QTree_range_query(elem, QT)
    for elem in inbound:
        elem.update()


def handle_collisions():
    global inbound, QT
    for body1 in inbound:
        if body1.is_out_of_bounds(s_width, s_height):
            continue
        QTree_handle_collisions(body1, QT)


def spin(n, center_x, center_y, galaxy_radius=spin_radius, spin_speed=0.1):
    for i in range(n):
        radius = random.uniform(0.5 * galaxy_radius, galaxy_radius)
        theta = random.uniform(0, 2 * math.pi)
        x = center_x + radius * math.cos(theta)
        y = center_y + radius * math.sin(theta)
        dx = x - center_x
        dy = y - center_y
        r = math.sqrt(dx ** 2 + dy ** 2)
        v = spin_speed * r
        vx = -v * math.sin(theta)
        vy = v * math.cos(theta)

        new_body = Body(x, y, vx, vy, radius=random.randint(1, max_random_radius), color=get_randomcolor())
        if (QT.checkplanet(new_body)):
            inbound.add(new_body)
            can_insert = QTree_insert(new_body)
            if (can_insert):
                QTree_point_update(new_body)
                QTree_handle_collisions(new_body, QT)
            else:
                inbound.remove(new_body)


if __name__ == '__main__':
    new_planet = None
    create = False
    while True:
        CLOCK.tick(FPS)
        screen.fill(BLACK)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            else:
                if create:
                    creating(new_planet)
                    create = False
                    new_planet = None
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:
                        create = True
                        pos = np.array(pygame.mouse.get_pos())
                        if len(inbound) == 0:
                            new_planet = Body(pos[0], pos[1], 0, 0, 1, color=get_randomcolor())
                        else:
                            new_planet = Body(pos[0], pos[1], 0, 0, 1, color=get_randomcolor())
                    elif event.button == 3 and len(inbound) != 0:
                        pos = np.array(pygame.mouse.get_pos())
                        new_planet = Body(pos[0], pos[1], 0, 0, random.randint(1, max_random_radius),
                                          color=get_randomcolor())
                        new_planet.set_orbitalvelocity(inbound.optimisedrandom())
                        inbound.add(new_planet)
                        QTree_insert(new_planet)
                        QTree_point_update(new_planet)
                        new_planet = None
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_g and len(inbound):
                        x = get_number()
                        generate_planets(x)
                    elif event.key == pygame.K_e:
                        inbound.clear()
                    elif event.key == pygame.K_f:
                        max_random_radius = change_size()
                    elif event.key == pygame.K_d:
                        drawmode = not (drawmode)
                    elif event.key == pygame.K_t:
                        BARNES_HUT_THETA = change_THETA()
                    elif event.key == pygame.K_s:
                        pos = pygame.mouse.get_pos()
                        spin(spin_bodies, pos[0], pos[1], galaxy_radius = spin_radius)
                    elif event.key == pygame.K_x:
                        spin_radius = change_spin_rad()
                        spin_bodies = change_spin_bod()

        QT = QuadTrees(0, 0, s_width, s_height)
        garbage = np.array([body for body in inbound if body.is_out_of_bounds(s_width, s_height)])
        planet_hash.clear()
        for elem in inbound:
            QTree_insert(elem)
            QTree_point_update(elem)
        update_bodies()
        handle_collisions()
        screen.fill(BLACK)
        for body in inbound:
            body.draw(screen)
        if drawmode:
            QT.draw_bounds()
        pygame.display.update()
