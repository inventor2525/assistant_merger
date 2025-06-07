import math

class Vector2:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def add(self, other):
        # Optimized addition
        return Vector2(self.x + other.x, self.y + other.y)

    def magnitude(self):
        return math.sqrt(self.x ** 2 + self.y ** 2)

    def scale(self, factor):
        return Vector2(self.x * factor, self.y * factor)

    def normalize(self):
        mag = self.magnitude()
        if mag == 0:
            return Vector2(0, 0)
        return Vector2(self.x / mag, self.y / mag)

    def dot(self, other):
        return self.x * other.x + self.y * other.y

    def subtract(self, other):
        return Vector2(self.x - other.x, self.y - other.y)
###