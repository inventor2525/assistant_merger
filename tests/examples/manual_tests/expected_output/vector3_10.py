# Vector3 class for 3D vector operations
# Version 1: Basic implementation
# Author: Charlie

class Vector3:
    def __init__(self, x, y, z):
        self.x = x
        self.y = y
        self.z = z

    def add(self, other):
        # Optimized addition
        return Vector3(self.x + other.x, self.y + other.y, self.z + other.z)

    def magnitude(self):
        return (self.x ** 2 + self.y ** 2 + self.z ** 2) ** 0.5

    def scale(self, factor):
        return Vector3(self.x * factor, self.y * factor, self.z * factor)

    def normalize(self):
        mag = self.magnitude()
        if mag == 0:
            return Vector3(0, 0, 0)
        return Vector3(self.x / mag, self.y / mag, self.z / mag)

    def dot(self, other):
        return self.x * other.x + self.y * other.y + self.z * other.z