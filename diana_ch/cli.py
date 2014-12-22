import threading
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

def process_yaw(joystick, tx, get_ship):
    yaw_reading = SDL.SDL_JoystickGetAxis(joystick, 0)
    yaw = YAW.evaluate(yaw_reading)
    if yaw < -1:
        print("Out-of-bounds low mark, reading={}".format(yaw_reading))
    if yaw > 1:
        print("Out-of-bounds high mark, reading={}".format(yaw_reading))
    rudder = (yaw + 1) / 2
    previous_rudder = get_ship().get('rudder')
    if previous_rudder != rudder:
        print('RDR {} -> {}'.format(previous_rudder, rudder))
        tx(diana.packet.HelmSetSteeringPacket(rudder))

def process_frame(joystick, tx, get_ship):
    for event in SDLE.get_events():
        if event.type == SDL.SDL_QUIT:
            exit(0)
    process_yaw(joystick, tx, get_ship)
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
    args = parser.parse_args()

    SDL.SDL_Init(SDL.SDL_INIT_JOYSTICK)
    for joy in range(SDL.SDL_NumJoysticks()):
        name = SDL.SDL_JoystickNameForIndex(joy)
        if name == b'CH FLIGHT SIM YOKE USB':
            joystick = SDL.SDL_JoystickOpen(joy)
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
        process_frame(joystick, tx, lambda: track.player_ship)

