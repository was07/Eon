import pygame
import math

WIDTH, HEIGHT = 1200, 600

pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
CX, CY = WIDTH/2, HEIGHT/2

CAMX, CAMY = 0, 0  # m

ZOOM = 8e-10  # pixels for 1 m

G = 6.67428e-11
TIMESTEP = 2600*12  # 1 day

ORBIT_TRAIL_LENGTH = 800  # positions of last X frames are stored and shown as trail

class Reasources:
    font = pygame.font.SysFont('Consolas', 12)
    space_image = pygame.transform.scale(
        pygame.image.load("stars.jpg").convert(),
        (WIDTH, WIDTH)
    )

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

        if len(self.orbit) > 1:
            # scaled_points = []
            lx, ly = self.orbit[0]
            for i, (ox, oy) in enumerate(self.orbit[1:]):
                # scaled_points.append((CX + ox * ZOOM, CY + oy * ZOOM))
                pygame.draw.line(screen, [n * i / ORBIT_TRAIL_LENGTH for n in self.color], (CX+lx*ZOOM, CY+ly*ZOOM), (CX+ox*ZOOM, CY+oy*ZOOM))
                lx, ly = ox, oy
        
            # pygame.draw.lines(screen, self.color, False, scaled_points)
        
        if self.name == "Mercury": print(self.color)
        pygame.draw.circle(screen, self.color, (x, y), max(self.radious*ZOOM, 1))

        text = Reasources.font.render(self.name, True, (255, 255, 255))
        rect = text.get_rect()
        rect.center = (x, y + (self.radious * ZOOM) + 20)
        screen.blit(text, rect)
    
    def attraction(self, other):  # physics and math
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
    
    def update_position(self):  # more math
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
        
        if len(self.orbit) > ORBIT_TRAIL_LENGTH:
            self.orbit = self.orbit[-ORBIT_TRAIL_LENGTH:]


def setup_perspective():
    """Sets up up CX, CY from CAMX, CAMX"""
    global CX, CY
    CX = WIDTH/2 + CAMX * ZOOM
    CY = HEIGHT/2 + CAMY * ZOOM

def track(obj: Object):
    global CAMX, CAMY
    CAMX, CAMY = -obj.x, -obj.y  # idk why negative but it works


class Sym:
    def __init__(self):
        """Units: Meter, Second, KG"""

        Object("Sun", 0, 0, 1.989e30, 696340e3, (253, 184, 19), 8e3)
        
        Object("Mercury", 57.9e9, 0, 3.285e23, 2439e3, (179, 104, 18), -47.4e3)

        Object("Venus", -107.4e9, 0, 4.867e24, 6051e3, (204, 148, 29), 35.02e3)

        Object("Earth", 149.9e9, 0, 5.972e24, 6378e3, (79, 146, 255), -29.8e3)

        Object("Mars", -228e9, 0, 0.642e24, 6792e3/2, (237, 77, 14), 24.1e3)

        Object("Jupiter", 778.5e9, 0, 1898e24, 142984e3/2, (216, 202, 157), -13.1e3)

        Object("Saturn", -1432e9, 0 ,568e24, 120536e3/2, (206,206,206), 9.7e3)

        Object("Uranus", 2867e9, 0, 86.8e24, 51118e3/2, (209,231,231), -6.8e3)

        Object("Neptune", -4515e9, 0, 102e14, 49528e3/2, (91,93,223), 5.4e3)

    def _zoom(self, zn: 1 | -1):
        global ZOOM
        if 8e-6 > (ZOOM + (ZOOM / 10) * zn) > 1e-12:  # close limit / far limit
            ZOOM += (ZOOM / 10) * zn
        
    def run(self):
        global ZOOM, CX, CY, CAMX, CAMY
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
            if keys[pygame.K_RIGHT]:
                CAMX -= 10 / ZOOM  # meters in 10px
            if keys[pygame.K_LEFT]:
                CAMX += 10 / ZOOM
            if keys[pygame.K_DOWN]:
                CAMY -= 10 / ZOOM  # meters in 10px
            if keys[pygame.K_UP]:
                CAMY += 10 / ZOOM
            
            setup_perspective()
            
            screen.fill((0, 0, 0))

            rect = Reasources.space_image.get_rect()
            rect.center = WIDTH/2, HEIGHT/2
            # screen.blit(Reasources.space_image, rect)

            for obj in OBJECTS:
                obj.update_position()
                if obj.name == "Sun":
                    track(obj)
                    setup_perspective()
                obj.draw()

            fps = str(int(clock.get_fps()))
            text = Reasources.font.render("FPS: " + fps, True, (255, 255, 255))
            screen.blit(text, (10, 10))

            pygame.display.flip()
            clock.tick(60)




Sym().run()
pygame.quit()
