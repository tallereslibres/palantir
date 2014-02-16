# Código en python para comunicarse con cámaras VC0706 cameras 
# y obtener una foto.
# written by ladyada. MIT license
# Adaptado por Héctor Domínguez
# Para los Talleres Libres de Artes y Tecnologías

# http://www.armhf.com/index.php/posts/

###
# uart3:serial@48024000 (/dev/ttyO2)
#   TX: 0x154 0x01
#   RX: 0x150 0x21
#
# uart4:serial@481a6000 (/dev/ttyO3)
#   TX: 0x164 0x01
#   RX: N/A (not broken out to P8 or P9)
#
# uart5:serial@281a8000 (/dev/ttyO4)
#   TX: 0x074 0x06
#   RX: 0x070 0x26
#
# uart6:serial@481aa000 (/dev/ttyO5)
#   TX: 0x0C0 0x04
#   RX: 0x0C4 0x24
###


import serial

BAUD = 38400
PORT = "/dev/ttyO1"      # se cómunica al puerto serial
TIMEOUT = 0.2

SERIALNUM = 0    # empieza con 0

COMMANDSEND = 0x56
COMMANDREPLY = 0x76
COMMANDEND = 0x00

CMD_GETVERSION = 0x11
CMD_RESET = 0x26
CMD_TAKEPHOTO = 0x36
CMD_READBUFF = 0x32
CMD_GETBUFFLEN = 0x34

FBUF_CURRENTFRAME = 0x00
FBUF_NEXTFRAME = 0x01
FBUF_STOPCURRENTFRAME = 0x00

getversioncommand = [COMMANDSEND, SERIALNUM, CMD_GETVERSION, COMMANDEND]
resetcommand = [COMMANDSEND, SERIALNUM, CMD_RESET, COMMANDEND]
takephotocommand = [COMMANDSEND, SERIALNUM, CMD_TAKEPHOTO, 0x01, FBUF_STOPCURRENTFRAME]
getbufflencommand = [COMMANDSEND, SERIALNUM, CMD_GETBUFFLEN, 0x01, FBUF_CURRENTFRAME]


def checkreply(r, b):
    r = map (ord, r)
    if (r[0] == 0x76 and r[1] == SERIALNUM and r[2] == b and r[3] == 0x00):
        return True
    return False

def reset():
    cmd = ''.join (map (chr, resetcommand))
    s.write(cmd)
    reply = s.read(100)
    r = list(reply)
    if checkreply(r, CMD_RESET):
        return True
    return False
        
def getversion():
    cmd = ''.join (map (chr, getversioncommand))
    s.write(cmd)
    reply =  s.read(16)
    r = list(reply);
    if checkreply(r, CMD_GETVERSION):
        print r
        return True
    return False

def takephoto():
    cmd = ''.join (map (chr, takephotocommand))
    s.write(cmd)
    reply =  s.read(5)
    r = list(reply);
    if (checkreply(r, CMD_TAKEPHOTO) and r[3] == chr(0x0)):
        return True
    return False   

def getbufferlength():
    cmd = ''.join (map (chr, getbufflencommand))
    s.write(cmd)
    reply =  s.read(9)
    r = list(reply);
    if (checkreply(r, CMD_GETBUFFLEN) and r[4] == chr(0x4)):
        l = ord(r[5])
        l <<= 8
        l += ord(r[6])
        l <<= 8
        l += ord(r[7])
        l <<= 8
        l += ord(r[8])
        return l
               
    return 0

readphotocommand = [COMMANDSEND, SERIALNUM, CMD_READBUFF, 0x0c, FBUF_CURRENTFRAME, 0x0a]


def readbuffer(bytes):
    addr = 0
    photo = []
    
    while (addr < bytes + 32):
        command = readphotocommand + [(addr >> 24) & 0xFF, (addr >> 16) & 0xFF,
                                      (addr >> 8) & 0xFF, addr & 0xFF]
        command +=  [0, 0, 0, 32]   # 32 bytes at a time
        command +=  [1,0]         # delay of 10ms
        #print map(hex, command)
        cmd = ''.join(map (chr, command))
        s.write(cmd)
        reply = s.read(32+5)
        r = list(reply)
        if (len(r) != 37):
            continue
        #print r
        if (not checkreply(r, CMD_READBUFF)):
            print "ERROR READING PHOTO"
            return
        photo += r[5:]
        addr += 32
    return photo
    


    
######## main

s = serial.Serial(port=PORT, baudrate=BAUD, timeout=TIMEOUT)

reset()

if (not getversion()):
    print "Cámara encontrada"
    exit
print "Cámara VC0706 encontrada"

if takephoto():
    print "Snap!"
    
bytes = getbufferlength()

print bytes, "Bytes por leer"

photo = readbuffer(bytes)
#photo = readbuffer(5024)

f = open("photo.jpg", 'w')
#print photo
photodata = ''.join(photo)
f.write(photodata)
f.close()
#print length(photo)