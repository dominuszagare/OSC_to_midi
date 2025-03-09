from pythonosc.dispatcher import Dispatcher
from pythonosc.osc_server import BlockingOSCUDPServer
import rtmidi

midiout = rtmidi.MidiOut()
midiin = rtmidi.MidiIn()
available_ports = midiout.get_ports()

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

def parseValueLSB_MSB(value):
    lsb = 0
    msb = 0
    try:
        f = float(value)
        val = int((f) * 16383)
        lsb = val & 127
        msb = val >> 7
        return lsb, msb
        
    except ValueError:
        if(value == "True"):
            return 16383
    return lsb, msb

def print_handler(address, *args):
    print(f"{address}: {args}")

# expected addres structure .../note/<chanel>/<button>
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
        midiout.send_message([0x90 + channel, button, parseValue(arg)]) #sends midi message bytes in oreder [byte1,byte2,byte3]

# expected addres structure .../cc/<chanel>/<cc>
def midi_handler_CC(address, *args):
    global midiout
    addresSplit = address.split("/")
    cc = 0
    channel = 0
    try:
        channel = int(addresSplit[-2])
    except:
        print("invaliud channel name", addresSplit[-2])
    try:
        cc = int(addresSplit[-1])
    except:
        print("invaliud cc name", addresSplit[-1])
    for arg in args:
        midiout.send_message([0xB0 + channel, cc, parseValue(arg)])

# expected addres structure /hex/status/ or /hex/status/data1/ or /hex/status/data1/data2
def midi_handler_hex(address, *args):
    global midiout
    addresSplit = address.split("/")
    status = 0
    data1 = 0
    data2 = 0
    try:
        status = int(addresSplit[2],16)
    except:
        print("invalid status", addresSplit[1])
    if len(addresSplit) > 3:
        try:
            data1 = int(addresSplit[3],16)
        except:
            print("invalid data1", addresSplit[2])
    if len(addresSplit) > 4:
        try:
            data2 = int(addresSplit[4],16)
        except:
            print("invalid data2", addresSplit[4])

    
    for arg in args:
        print(address, status, data1, data2, parseValue(arg), parseValueLSB_MSB(arg))
        if(status > 128 and status < 144):
            #OFF velocity
            midiout.send_message([status, data1, parseValue(arg)])
        if(status > 159 and status < 176):
            #ON velocity
            midiout.send_message([status, data1, parseValue(arg)])
        if(status > 143 and status < 160):
            #ploy key presure
            midiout.send_message([status, data1, parseValue(arg)])
        if(status > 175 and status < 192):
            #control change
            midiout.send_message([status, data1, parseValue(arg)])
        if(status > 191 and status < 208):
            #program chnage
            midiout.send_message([status, data1])
        if(status > 207 and status < 224):
            #chanel presure
            midiout.send_message([status, parseValue(arg)])
        if(status > 223 and status < 240):
            #pitch bend
            lsb, msb = parseValueLSB_MSB(arg)
            midiout.send_message([status,lsb,msb]) 

def update_midi_CCTap(cc):
    global midiout
    midiout.send_message([0xB0, cc, 0])
    midiout.send_message([0xB0, cc, 127])

print("OSC server running on ", f'osc://{ip}:{port}')


dispatcher = Dispatcher()

dispatcher.map("/cc/*", midi_handler_CC)
dispatcher.map("/note/*", midi_handler_note)
dispatcher.map("/hex/*", midi_handler_hex)

server = BlockingOSCUDPServer((ip, port), dispatcher)
server.serve_forever()  # Blocks forever