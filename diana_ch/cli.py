import threading
import random
from diana import connect
import diana.packet
from diana.tracking import Tracker
import time
import argparse
from . import SHORT_DESCRIPTION
from .joystick_map import JoystickMapping

import sdl2 as SDL
import sdl2.ext as SDLE

def launch_thread(fn):
    target = threading.Thread(target=fn)
    target.daemon = True
    target.start()

YAW = JoystickMapping(min=-32768, centre=-4241, max=28398, dead_zone=0.05)
PITCH = JoystickMapping(min=-32511, centre=-10152, max=29940, dead_zone=0.15)
LEVER = JoystickMapping(min=32767, max=-32768)

LINEAR = JoystickMapping(min=-1, max=1)

class Joystick:
    def __init__(self, raw):
        self.raw = raw
        self._pressed = [False] * SDL.SDL_JoystickNumButtons(raw)

    def update(self):
        pass

    def axis(self, axis, mapping=LINEAR):
        reading = SDL.SDL_JoystickGetAxis(self.raw, axis)
        return mapping.evaluate(reading)

    def hat(self, index=0):
        return SDL.SDL_JoystickGetHat(self.raw, index)

    def button(self, index=0):
        state = SDL.SDL_JoystickGetButton(self.raw, index)
        if state == False:
            self._pressed[index] = False
            return False
        if state == True:
            if self._pressed[index]:
                return False
            else:
                self._pressed[index] = True
                return True

def process_yaw(joystick, tx, get_ship):
    yaw = joystick.axis(0, YAW)
    rudder = (yaw + 1) / 2
    previous_rudder = get_ship().get('rudder')
    if previous_rudder != rudder:
        print('RDR {} -> {}'.format(previous_rudder, rudder))
        tx(diana.packet.HelmSetSteeringPacket(rudder))

def process_pitch(joystick, tx, get_ship):
    previous_pitch = get_ship().get('pitch', 0)
    pitch = joystick.axis(1, PITCH)
    pitch_error = pitch - previous_pitch
    if pitch_error > 0 and random.random() < pitch_error:
        tx(diana.packet.ClimbDivePacket(1))
        print('Pitch UP')
    if pitch_error < 0 and random.random() < -pitch_error:
        tx(diana.packet.ClimbDivePacket(-1))
        print('Pitch DOWN')

def process_thrust(joystick, tx, get_ship):
    thrust = (1 + joystick.axis(2, LEVER)) / 2
    previous_thrust = get_ship().get('impulse', None)
    if thrust != previous_thrust:
        print('IMP {} -> {}'.format(previous_thrust, thrust))
        tx(diana.packet.HelmSetImpulsePacket(thrust))

def process_main_screen(joystick, tx, get_ship):
    MainView = diana.packet.MainView
    view = None
    hat = joystick.hat()
    if hat in (SDL.SDL_HAT_UP, SDL.SDL_HAT_RIGHTUP, SDL.SDL_HAT_LEFTUP):
        view = MainView.forward
    elif hat in (SDL.SDL_HAT_DOWN, SDL.SDL_HAT_RIGHTDOWN, SDL.SDL_HAT_LEFTDOWN):
        view = MainView.aft
    elif hat == SDL.SDL_HAT_LEFT:
        view = MainView.port
    elif hat == SDL.SDL_HAT_RIGHT:
        view = MainView.starboard
    elif joystick.button(1):
        view = MainView.status
    elif joystick.button(2):
        view = MainView.tactical
    elif joystick.button(3):
        view = MainView.lrs
    previous_view = get_ship().get('main-view')
    if view != previous_view and view is not None:
        print('MV {} -> {}'.format(previous_view, view))
        tx(diana.packet.SetMainScreenPacket(view))
    if joystick.button(0):
        tx(diana.packet.TogglePerspectivePacket())

def process_red_alert(joystick, tx, get_ship):
    red_alert = get_ship().get('red-alert', False)
    if joystick.button(4) and not red_alert:
        tx(diana.packet.ToggleRedAlertPacket())
    if joystick.button(5) and red_alert:
        tx(diana.packet.ToggleRedAlertPacket())

def process_shields(joystick, tx, get_ship):
    shields = get_ship().get('shields-state', False)
    if joystick.button(6) and not shields:
        tx(diana.packet.ToggleShieldsPacket())
    if joystick.button(7) and shields:
        tx(diana.packet.ToggleShieldsPacket())

def process_reverse(joystick, tx, get_ship):
    reverse = get_ship().get('reverse', False)
    if joystick.button(11) and not reverse:
        tx(diana.packet.HelmToggleReversePacket())
    if joystick.button(10) and reverse:
        tx(diana.packet.HelmToggleReversePacket())

def process_frame(joystick, tx, get_ship, args):
    for event in SDLE.get_events():
        if event.type == SDL.SDL_QUIT:
            exit(0)
    process_yaw(joystick, tx, get_ship)
    if args.enable_pitch:
        process_pitch(joystick, tx, get_ship)
    process_thrust(joystick, tx, get_ship)
    process_main_screen(joystick, tx, get_ship)
    process_shields(joystick, tx, get_ship)
    process_red_alert(joystick, tx, get_ship)
    process_reverse(joystick, tx, get_ship)
    time.sleep(1 / 15)

def main():
    parser = argparse.ArgumentParser(description=SHORT_DESCRIPTION)
    parser.add_argument('server', help='Server address')
    parser.add_argument('port',
                        help='Server port',
                        type=int,
                        default=2010,
                        nargs='?')
    parser.add_argument('ship',
                        help='Selected ship',
                        type=int,
                        default=0,
                        nargs='?')
    parser.add_argument('--enable-pitch',
                        help='Turn on pitch control',
                        action='store_true')
    args = parser.parse_args()

    SDL.SDL_Init(SDL.SDL_INIT_JOYSTICK)
    for joy in range(SDL.SDL_NumJoysticks()):
        name = SDL.SDL_JoystickNameForIndex(joy)
        if name == b'CH FLIGHT SIM YOKE USB':
            joystick = Joystick(SDL.SDL_JoystickOpen(joy))
            break
    else:
        print('Could not find yoke.')
        exit(1)

    tx, rx = connect(args.server, args.port)
    track = Tracker()

    def handle_input():
        for packet in rx:
            if isinstance(packet, diana.packet.WelcomePacket):
                print("Connected.")
                tx(diana.packet.SetShipPacket(args.ship))
                tx(diana.packet.SetConsolePacket(diana.packet.Console.data,
                                                 True))
                tx(diana.packet.ReadyPacket())
            track.rx(packet)

    launch_thread(handle_input)

    while True:
        process_frame(joystick, tx, lambda: track.player_ship, args)

