import diana_ch.joystick_map as jm
from fractions import Fraction as F
from nose.tools import eq_

def test_passthrough():
    straightforward_mapping = jm.JoystickMapping(min=F(-1), max=F(1))
    eq_(straightforward_mapping.a, 0)
    eq_(straightforward_mapping.b, 1)
    eq_(straightforward_mapping.c, 0)

def test_offset():
    straightforward_mapping = jm.JoystickMapping(min=F(0), max=F(1))
    eq_(straightforward_mapping.a, 0)
    eq_(straightforward_mapping.b, 2)
    eq_(straightforward_mapping.c, -1)

