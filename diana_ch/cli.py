import threading
from diana import connect
import argparse
from . import SHORT_DESCRIPTION

def launch_thread(fn):
    target = threading.Thread(target=fn)
    target.daemon = True
    target.start()

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
    print(args)

