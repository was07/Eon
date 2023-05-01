import math

def calc_xy_speed(angle, speed, clockwise=False):
    angle += 90 if clockwise else -90
    return speed * math.cos(angle), speed * math.sin(angle)

print(calc_xy_speed(0, 100))