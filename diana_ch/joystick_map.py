def compute_mapping_coefficients(p, q, r):
    # solve ap^2 + bp + c = -1
    #       aq^2 + bq + c = 0
    #       ar^2 + br + c = -1
    divisor = (q - p)*(r - p)*(q - r)
    a = (p - 2*q + r)/divisor
    b = (p*p - 2*q*q + r*r) / (-divisor)
    c = (p*p*q - p*q*q - q*q*r + q*r*r) / divisor
    return a, b, c

class JoystickMapping:
    def __init__(self, min, max, centre=None, dead_zone=0):
        if centre is None:
            centre = (max + min) / 2
        self.dead_zone = dead_zone
        self.a, self.b, self.c = compute_mapping_coefficients(min, centre, max)

    def evaluate(self, reading):
        output = self.a*reading*reading + self.b*reading + self.c
        if -self.dead_zone <= output <= self.dead_zone:
            return 0
        return output


