# Quaternion class for 3D rotations
# Version 1: Basic implementation

class Quaternion:
    def __init__(self, w, x, y, z):
        self.w = w
        self.x = x
        self.y = y
        self.z = z

    def conjugate(self):
        return Quaternion(self.w, -self.x, -self.y, -self.z)

    def norm(self):
        return (self.w ** 2 + self.x ** 2 + self.y ** 2 + self.z ** 2) ** 0.5

    def multiply(self, other):
        return Quaternion(
            self.w * other.w - self.x * other.x - self.y * other.y - self.z * other.z,
            self.w * other.x + self.x * other.w + self.y * other.z - self.z * other.y,
            self.w * other.y - self.x * other.z + self.y * other.w + self.z * other.x,
            self.w * other.z + self.x * other.y - self.y * other.x + self.z * other.w
        )

    def inverse(self):
        norm_sq = self.norm() ** 2
        if norm_sq == 0:
            raise ValueError("Cannot invert zero quaternion")
        conj = self.conjugate()
        return Quaternion(conj.w / norm_sq, conj.x / norm_sq, conj.y / norm_sq, conj.z / norm_sq)

# End of Quaternion