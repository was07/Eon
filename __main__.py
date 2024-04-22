import pygame
import math
import random

WIDTH, HEIGHT = 1200, 700

pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("The Solar System")
CX, CY = WIDTH/2, HEIGHT/2

CAMX, CAMY = 0, 0  # m

G = 6.67428e-11
AU = 149.9e9
SOLAR_MASS = 1.989e30
EARTH_MASS = 5.972e24

ZOOM = 8e-10  # pixels for 1 m
TIMESTEP = 2600*24  # 12 hours

ORBIT_TRAIL_LENGTH = 600  # positions of last X frames are stored and shown as trail

class Resources:
    font = pygame.font.SysFont('Consolas', 12)
    space_image = pygame.transform.scale(
        pygame.image.load("space.jpg").convert(),
        (WIDTH, WIDTH)
    )

OBJECTS: list["Object"] = []


class Object:
    def __init__(self, name: str, x, y, mass: int, radious: int, color: tuple,
                 x_vel=0, y_vel=0, star=False, significant=True, track_orbit=False) -> None:
        self.name = name
        self.x = x
        self.y = y
        self.mass = mass
        self.radius = radious
        self.color = color
        
        self.star = star

        self.x_vel = x_vel
        self.y_vel = y_vel
        self.orbit = []

        self.significant = significant
        self.track_orbit = significant or track_orbit
        self._last_zoom = ZOOM  # used for effeciency purposes
        OBJECTS.append(self)

        self.info_distance_to_sun = 0
        self.show_info = False
    
    def get_pos(self):
        return CX + self.x * ZOOM, CY + self.y * ZOOM
    
    def draw(self):
        x = CX + self.x * ZOOM
        y = CY + self.y * ZOOM
        if ZOOM < 1e-11 and not self.significant: return x, y
        r = self.radius * ZOOM

        if self.track_orbit:
            if len(self.orbit) > 1:
                # scaled_points = []
                trail_length = min(ORBIT_TRAIL_LENGTH, len(self.orbit) - 1)
                lx, ly = self.orbit[0]
                for i, (ox, oy) in enumerate(self.orbit[1:]):
                    # scaled_points.append((CX + ox * ZOOM, CY + oy * ZOOM))
                    pygame.draw.line(screen, [n * i / trail_length for n in self.color], (CX+lx*ZOOM, CY+ly*ZOOM), (CX+ox*ZOOM, CY+oy*ZOOM))
                    lx, ly = ox, oy
        
            # pygame.draw.lines(screen, self.color, False, scaled_points)
        
        if r > 1e-6:
            pygame.draw.circle(screen, self.color, (x, y), max(r, 1))

        if (self.significant or ZOOM > 9e-10 or self.show_info) and (not ZOOM < 1e-11 or self.radius >= 696340e3) \
            and (0 < x < WIDTH and 0 < y < HEIGHT):
            text = Resources.font.render(self.name, True, (255, 255, 255))
            rect = text.get_rect()
            rect.center = (x, y + r + 15)
            screen.blit(text, rect)

        if self.show_info:
            if r > 1:
                pygame.draw.line(screen, (200,200,200), (x + r + 15, y), (x + r + 20, y))
                pygame.draw.line(screen, (200,200,200), (x - r - 15, y), (x - r - 20, y))
            else:
                pygame.draw.circle(screen, (200, 200, 200), (x, y), r + 8, 1)

            self.show_info = False

        # TODO: Make it like when the Object takes a decent screen space (zoomed) then
        # Show more info and stop zoom (?)
        return x, y
    
    def kill(self):
        if self in OBJECTS: OBJECTS.remove(self)
       
    def attraction(self, other: "Object"):  # physics and math
        other_x, other_y = other.x, other.y
        distance_x = other_x - self.x
        distance_y = other_y - self.y
        distance = math.sqrt(distance_x ** 2 + distance_y ** 2)

        if distance <= (self.radius + other.radius):  # collision detected
            print("Collision: ", self.name, "into", other.name)  # log
            # new = Object("New", (big.x+small.x)/2, (big.y+small.y)/2, big.mass+small.mass,
            #              big.radius,
            #              [(big.color[i]+small.color[i])/2 for i in range(3)],
            #              big.x_vel, big.y_vel, big.star or small.star,
            #              big.significant or small.significant, big.track_orbit or small.track_orbit
            # )

            self.mass += other.mass
            # big.kill()
            if self.mass > other.mass:  # kills the smaller object by mass in event of collision
                other.kill()
            else:
                self.kill()

        if other.star:
            self.info_distance_to_sun = distance

        force = 0 if distance == 0 else(G * self.mass * other.mass) / distance**2
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

def cords(dist, angle, origin_x=0, origin_y=0):
    # angle goes clockwise, starting from right (+x)
    return origin_x + dist * math.cos(angle), origin_y + dist * math.sin(angle)

def calc_xy_speed(angle, speed, clockwise=False):
    angle += 90 if clockwise else -90
    return speed * math.cos(angle), speed * math.sin(angle)


class Simulation:
    def __init__(self):
        """Units: Meter, Second, KG"""
        self.panel = Panel(self)
        
        self.focus = ""
    
    def _zoom(self, zn: 1 | -1):
        global ZOOM
        if 8e-6 > (ZOOM + (ZOOM / 10) * zn) > 1e-13:  # close limit / far limit
            ZOOM += (ZOOM / 10) * zn
        
    def run(self):
        global ZOOM, CX, CY, CAMX, CAMY
        clock = pygame.time.Clock()
        running = True
        pause = False

        while running:
            for eve in pygame.event.get():
                if eve.type == pygame.QUIT: running = False
                if eve.type == pygame.KEYDOWN and eve.key == pygame.K_SPACE:
                    pause = not pause; print(pause)
            
            setup_perspective()
            mx, my = pygame.mouse.get_pos()  # used later in method
            keys = pygame.key.get_pressed()
            if keys[pygame.K_z]:
                self._zoom(+1)
            elif keys[pygame.K_x]:
                self._zoom(-1)
            if keys[pygame.K_d]:
                CAMX -= 10 / ZOOM  # meters in 10px
                self.focus = ""
            elif keys[pygame.K_a]:
                CAMX += 10 / ZOOM
                self.focus = ""
            if keys[pygame.K_s]:
                CAMY -= 10 / ZOOM  # meters in 10px
                self.focus = ""
            elif keys[pygame.K_w]:
                CAMY += 10 / ZOOM
                self.focus = ""
            
            setup_perspective()
            
            rect = Resources.space_image.get_rect()
            rect.center = WIDTH/2, HEIGHT/2
            # screen.fill((0, 0, 0))
            screen.blit(Resources.space_image, rect)

            focus_obj = None
            if OBJECTS:
                dists = {}
                for obj in OBJECTS:
                    if not pause: obj.update_position()
                    if obj.name == self.focus:
                        track(obj)
                        setup_perspective()
                        focus_obj = obj
                    ox, oy = obj.draw()
                    dist = math.sqrt((mx-ox)**2 + (my-oy)**2)
                    dists[dist] = obj
                
                # show info for the closest obj
                min_dist = min(list(dists))
                if min_dist < 80:
                    dists[min_dist].show_info = True
                    if keys[pygame.K_TAB]:
                        self.focus = dists[min_dist].name
                
            self.panel.draw(focus_obj=focus_obj)
            # show fps
            fps = str(int(clock.get_fps()))
            text = Resources.font.render("FPS: " + fps, True, (255, 255, 255))
            rect = text.get_rect()
            rect.topright = (WIDTH - 10, 10)
            screen.blit(text, rect)

            pygame.display.flip()
            clock.tick(90)  # max fps

        pygame.quit()


class Panel:
    """Handles all text and stuff (other than the simulation) on the screen"""
    def __init__(self, sim) -> None:
        self.sim = sim
    
    def draw(self, focus_obj: Object = None):
        topleft_texts = []
        if focus_obj:
            if focus_obj.star:
                topleft_texts.append("Active")
            else:
                # topleft_texts.append("Inactive")
                pass
            vel = math.sqrt(focus_obj.x_vel ** 2 + focus_obj.y_vel ** 2)
            topleft_texts.append("Speed    "+str(format(round(abs(vel/1e3), 3), ','))+"km/s")
            topleft_texts.append("Mass     "+str(focus_obj.mass)+"kg")
            topleft_texts.append("Diameter "+str(format(focus_obj.radius*2/1e3, ','))+"km")

            screen.blit(Resources.font.render(focus_obj.name, False, focus_obj.color), (20, 20))
            
            text = Resources.font.render("Tracking: " + focus_obj.name, False, (225,225,225))
            rect = text.get_rect(midbottom=(WIDTH/2, HEIGHT - 20))
            screen.blit(text, rect)
        # topleft
        y = 40
        for _text in topleft_texts:
            y += 20
            text = Resources.font.render(_text, False, (255,255,255))
            screen.blit(text, (20, y))
        
        # bottomleft
        text = Resources.font.render("Zoom: " + str('{:.3g}'.format(ZOOM)), False, (225,225,225))
        # '{:.3g}'.format rounds exponential float
        rect = text.get_rect()
        rect.bottomleft = (20, HEIGHT - 20)
        screen.blit(text, rect)



def solarsystem():
    Object("Sun", 0, 0, SOLAR_MASS, 696340e3, (253, 184, 19), star=True)

    Object("Mercury", 57.9e9, 0, 3.285e23, 2439e3, (179, 104, 18), y_vel=-47.4e3)
    Object("Venus", -107.4e9, 0, 4.867e24, 6051e3, (204, 148, 29), y_vel=-35.02e3)
    Object("Earth", AU, 0, EARTH_MASS, 6378e3, (79, 146, 255), y_vel=-29.8e3)
    
    Object("Mars", -228e9, 0, 0.642e24, 6792e3/2, (237, 77, 14), y_vel=24.1e3)
    Object("Jupiter", 778.5e9, 0, 1898e24, 142984e3/2, (216, 202, 157), y_vel=-13.1e3)
    Object("Saturn", -1432e9, 0 , 568e24, 120536e3/2, (206,206,206), y_vel=9.7e3)
    Object("Uranus", 0, -2867e9, 86.8e24, 51118e3/2, (209,231,231), x_vel=6.8e3)
    Object("Neptune", 0, 4515e9, 102e24, 49528e3/2, (91,93,223), x_vel=5.4e3)

    Object("Ceres", 414e9, 0, 9.3839e23, 939.4e3/2, (158,158,150), y_vel=-17.9e3, significant=False, track_orbit=True)
    Object("Pluto", -5900e9, 0, 1.303e22, 1188.3e3, (244,245,223), y_vel=4.743e3, significant=False, track_orbit=True)
    Object("Haumea", 43.116*AU, 0, 4.006e21, 780e3/2, (158,158,150), y_vel=-4.53e3, significant=False, track_orbit=True)

    # for i in range(20):
    #     dist = random.randint(1.9*AU, 3.8*AU)
    #     angle = random.randint(1, 360)
    #     speed = math.sqrt(G * SOLAR_MASS / dist)

    #     x, y = cords(dist, angle)
    #     vx, vy = calc_xy_speed(angle, speed)
        
    #     # signx = 1 if x > 0 else -1
    #     # signy = 1 if y > 0 else -1

    #     # print(x * ZOOM, y * ZOOM)
    #     # print(speed, vx, vy)
    #     Object(f"T{i}", x, y, 2.39e21,
    #             random.randint(1e3, 10e3), (100,100,100), x_vel=vx, y_vel=vy,
    #             significant=False, track_orbit=True)


def systemB():
    Object("B Alpha", 0, 0, 2*SOLAR_MASS, 696340e3, (240, 126, 5), x_vel=3e3, star=True)
    Object("1-B", -2*AU, 0, EARTH_MASS, 6400e3, (200, 200, 10), y_vel=2e4)
    Object("2-B", 1.41*AU, 1.41*AU, EARTH_MASS, 6400e3, (200, 200, 10), y_vel=-2e4)
    Object("3-B", 1.41*AU, 2*AU, EARTH_MASS, 6400e3, (200, 200, 10), y_vel=-2e4)
    Object("4-B", 2*AU, -1.41*AU, EARTH_MASS, 6400e3, (200, 200, 10), y_vel=-2e4)
    # TODO: Refine


def dualstarsystem():
    Object("C41-A", 0, 0, 2*SOLAR_MASS, 696340e3, (240, 126, 5), star=True)
    Object("C41-B", 0, 1.25*AU, SOLAR_MASS, 696340e3, (240, 126, 5), x_vel=55e3, star=True)
    # TODO: Refine


def test():
    # collision on first frame
    Object("C41-A", 0, 0, 2*SOLAR_MASS, 696340e3, (240, 126, 5), star=True)
    Object("C41-B", 0, 10, SOLAR_MASS, 696340e3, (240, 126, 5), star=True)



if __name__ == "__main__": 
    sim = Simulation()
    test()
    sim.run()
