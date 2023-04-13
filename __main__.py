import pygame
import json
import math

WIDTH, HEIGHT = 1200, 600

pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
CX, CY = WIDTH/2, HEIGHT/2
ZOOM = 8e-10  # pixels for 1 km

G = 6.67428e-11
TIMESTEP = 2600*12 # 1 day

font = pygame.font.SysFont('Consolas', 12)

OBJECTS: list["Object"] = []


class Object:
    def __init__(self, name: str, x, y, mass: int, radious: int, color: tuple, y_vel=0, sun=False) -> None:
        self.name = name
        self.x = x
        self.y = y
        self.mass = mass
        self.radious = radious
        self.color = color

        self.sun = sun

        self.x_vel = 0
        self.y_vel = y_vel
        self.orbit = []

        OBJECTS.append(self)
    
    def get_pos(self):
        return CX + self.x * ZOOM, CY + self.y * ZOOM
    
    def draw(self):
        x = CX + self.x * ZOOM
        y = CY + self.y * ZOOM

        pygame.draw.circle(screen, self.color, (x, y), max(self.radious*ZOOM, 1))

        if len(self.orbit) > 1:
            scaled_points = []
            for ox, oy in self.orbit:
                scaled_points.append((CX + ox * ZOOM, CY + oy * ZOOM))
        
            pygame.draw.lines(screen, self.color, False, scaled_points)

        text = font.render(self.name, True, (255, 255, 255))
        rect = text.get_rect()
        rect.center = (x, y + (self.radious * ZOOM) + 20)
        screen.blit(text, rect)

    def attraction(self, other):
        other_x, other_y = other.x, other.y
        distance_x = other_x - self.x
        distance_y = other_y - self.y
        distance = math.sqrt(distance_x ** 2 + distance_y ** 2)

        # if other.sun:
            # self.distance_to_sun = distance

        force = (G * self.mass * other.mass) / distance**2
        theta = math.atan2(distance_y, distance_x)
        force_x = math.cos(theta) * force
        force_y = math.sin(theta) * force
        return force_x, force_y
    
    def update_position(self):
        total_fx = total_fy = 0
        for obj in OBJECTS:
            if obj == self: continue
            fx, fy = self.attraction(obj)
            total_fx += fx
            total_fy += fy
        
        self.x_vel += total_fx / self.mass * TIMESTEP
        self.y_vel += total_fy / self.mass * TIMESTEP

        self.x += self.x_vel * TIMESTEP
        self.y += self.y_vel * TIMESTEP
        self.orbit.append((self.x, self.y))
        
        # if len(self.orbit) > 500: self.orbit = self.orbit[-500:]

class Sym:
    def __init__(self):
        """Units: Meter, Second, KG"""

        Object("Sun", 0, 0, 1.989e30, 696340e3, (253, 184, 19))
        
        Object("Mercury", -57.9e9, 0, 3.285e23, 2439e3, (179, 104, 18), -47.4e3)

        Object("Venus", -107.4e9, 0, 4.867e24, 6051e3, (204, 148, 29), 35.02e3)

        Object("Earth", 149.9e9, 0, 5.972e24, 6378e3, (79, 146, 255), -29.8e3)

        Object("Mars", -228e9, 0, 0.642e24, 6792/2, (237, 77, 14), 24.1e3)

        Object("Jupiter", 778.5e9, 0, 1898e24, 142984/2, (216, 202, 157), -13.1e3)

        Object("Saturn", -1432e9, 0 ,568e24, 120536e3, (206,206,206), 9.7e3)

        Object("Uranus", 2867e9, 0, 86.8e24, 51118/2, (209,231,231), -6.8e3)

        Object("Neptune", -4515e9, 0, 102e14, 49528/2, (91,93,223), 5.4e3)

    
    def _zoom(self, zn: 1 | -1):
        global ZOOM
        if 8e-8 > (ZOOM + (ZOOM / 10) * zn) > 1e-10:
            ZOOM += (ZOOM / 10) * zn
        
    def run(self):
        global ZOOM, CX
        clock = pygame.time.Clock()
        running = True

        while running:
            for eve in pygame.event.get():
                if eve.type == pygame.QUIT:
                    running = False
            keys = pygame.key.get_pressed()
            if keys[pygame.K_EQUALS]:
                self._zoom(+1)
            elif keys[pygame.K_MINUS]:
                self._zoom(-1)
            elif keys[pygame.K_RIGHT]:
                CX -= 10
            elif keys[pygame.K_LEFT]:
                CX += 10
            
            screen.fill((0, 0, 0))
            for obj in OBJECTS:
                obj.update_position()
                obj.draw()

            fps = str(int(clock.get_fps()))
            text = font.render("FPS: " + fps, True, (255, 255, 255))
            screen.blit(text, (10, 10))

            pygame.display.flip()
            clock.tick(60)




Sym().run()
pygame.quit()