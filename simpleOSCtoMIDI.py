from pythonosc.dispatcher import Dispatcher
from pythonosc.osc_server import BlockingOSCUDPServer
import rtmidi

midiout = rtmidi.MidiOut()
available_ports = midiout.get_ports()

DEBUG = True
ip = "127.0.0.1"
port = 4888

if available_ports:
    midiout.open_port(1) # if on windows install loopMIDI https://www.tobias-erichsen.de/software/loopmidi.html
    print("midi device: ", midiout)
else:
    midiout.open_virtual_port("OSC_to_MIDI") #dosent work on windows

def parseValue(value):
    try:
        f = float(value)
        return int((f) * 127)
    except ValueError:
        if(value == "True"):
            return 127
    return 0

def print_handler(address, *args):
    print(f"{address}: {args}")

# expected addres structure .../raw/<chanel>/<button>
def midi_handler_note(address, *args):
    global midiout
    addresSplit = address.split("/")
    channel = 0
    button = 0
    try:
        channel = int(addresSplit[-2])
    except:
        print("invaliud channel name", addresSplit[-2])
    try:
        button = int(addresSplit[-1])
    except:
        print("invaliud button name", addresSplit[-1])

    for arg in args:
        midiout.send_message([0x90 + channel, button, parseValue(arg)])

# expected addres structure .../cc/<cc>
def midi_handler_CC(address, *args):
    global midiout
    addresSplit = address.split("/")
    cc = 0
    try:
        cc = int(addresSplit[-1])
    except:
        print("invaliud cc name", addresSplit[-1])
    for arg in args:
        midiout.send_message([0xB0, cc, parseValue(arg)])

def update_midi_CCTap(cc):
    global midiout
    midiout.send_message([0xB0, cc, 0])
    midiout.send_message([0xB0, cc, 127])

print("OSC server running on ", f'osc://{ip}:{port}')


dispatcher = Dispatcher()
if DEBUG:
    dispatcher.map("/*", print_handler) #print

dispatcher.map("/cc/*", midi_handler_CC)
dispatcher.map("/raw/*", midi_handler_note)

server = BlockingOSCUDPServer((ip, port), dispatcher)
server.serve_forever()  # Blocks forever