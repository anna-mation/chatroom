# coding: utf-8
# python3
from socket import *
import sys
import time
import threading

# HELPER FUNCTIONS
def recMessage(sock):
    return sock.recv(1024).decode('utf-8')

def sendMessage(sock, message):
    sock.sendall(bytes(str(message), 'utf-8'))

# listens for incoming messages from the server. run in a separate thread
def listen(sock):
    while continueListen:
        data = recMessage(sock)
        if data:
            portInfo = data.split()
            if portInfo[0] != '[noprint]':
                print('> ' + data)
                if data.endswith('is not online') and portInfo[0] in peers.keys():
                    peers.pop(portInfo[0])
                if continueListen:
                    print('========= Please enter a command: =========')
            else:
                peers[portInfo[1]] = int(portInfo[2])

# listens for incoming files from the other peers. run in a separate thread
def listenFile(sock):
    while continueListen:
        # whether file has been received
        fileRec = False
        # assume file has finished downloading after idle 1 sec
        sock.settimeout(1)
        try:
            chunks = {}
            rec = sock.recvfrom(8192)[0].decode('utf-8')
            t0 = time.time()
            data = rec.split('<SEP>')
            while 1:
                peer = data[0]
                filename = data[1]
                # ignore if file has been downloaded before
                # intended to stop late chunks arriving after file has been generated
                if filename in downloaded:
                    break
                num = int(data[2])
                bits = data[3]
                chunks[num] = bits
                fileRec = True

                rec = sock.recvfrom(8192)[0].decode('utf-8')
                data = rec.split('<SEP>')
        except timeout:
            pass
        if fileRec:
            # sort chunks into order
            file = [chunks[i] for i in sorted(chunks)]
            
            newFile = f'{peer}_{filename}'
            checkFile(newFile)

            # generare new file
            with open(newFile, 'wb') as f:
                for b in file:
                    f.write(eval(b))
            t1 = time.time()
            total = round(t1 - t0, 2)
            print(f'> file {filename} received from {peer}')
            print(f'> time taken: {total} secs, packets received: {len(file)}')
            downloaded.append(filename)
            print('========= Please enter a command: =========')

            fileRec = False

# creates file if it doesn't exist
def checkFile(file):
    f = open(file,'a+')
    f.close()

# command functions
# relays commands to server
def msgto(tcp, username, msg):
    sendMessage(tcp, f'[msgto] {username} {msg}')

# relays login details to server
def login(tcp, udpPort, ip):
    blocked = 'your account has been blocked, try again later'
    success = 'successfully logged in'

    sendMessage(tcp, f'[login] {time.time()} {udpPort} {ip}')
    rec = ''
    while rec != success and rec != blocked:
        user = input('username: ')
        pas = input('password: ')
        sendMessage(tcp, f'{user} {pas}')
        rec = recMessage(tcp)
        print(f'> {rec}')
    if rec == success:
        return user
    else:
        return False

# activates logout sequence
def logout(tcp):
    sendMessage(tcp, '[logout]')

# activates activeuser sequence
def activeuser(tcp):
    sendMessage(tcp, f'[activeuser]')

# checks for valid input then creates group
def creategroup(tcp, name, people):
    cont = True

    # check for valid group name
    if not name.isalnum():
        print(f'group name {name} must be alphanumeric')
        cont = False
    if cont:
        members = ' '.join(people)
        sendMessage(tcp, f'[crgroup] {name} {members}')

# activates joingroup sequence
def joingroup(tcp, name):
    sendMessage(tcp, f'[joingroup] {name}')

# activates groupmsg sequence
def groupmsg(tcp, name, msg):
    sendMessage(tcp, f'[groupmsg] {name} {msg}')

# activates p2p transfer
def p2p(tcp, udp, name, file):
    # checks for existing/online user
    sendMessage(tcp, f'[getport] {name}')

    time.sleep(0.1)
    if name in peers.keys():
        port = peers[name]
        sendFile(udp, port, file)

# sends file in packets
def sendFile(udp, port, file):
    # sequence number
    num = 0
    # header included in every chunk
    header = f'{username}<SEP>{file}'
    checkFile(file)

    with open(file, 'rb') as f:
        print('> uploading...')
        # timer start
        t0 = time.time()
        while True:
            num += 1
            data = f.read(2048 - len(f'{header}<SEP>{num}<SEP>'.encode('utf-8')))
            # no more data to send
            if not data:
                break
            send = f'{header}<SEP>{num}<SEP>{data}'
            udp.sendto(send.encode('utf-8'), (ip, port))
            time.sleep(0.00001)
    t1 = time.time()
    total = round(t1 - t0, 2)
    print(f'> {file} has been uploaded')
    print(f'> time taken: {total} secs, packets sent: {num - 1}')
    print('========= Please enter a command: =========')

# MAIN
if len(sys.argv) != 4:
    print('> Usage: python3 client.py [server_IP] [server_port] [client_udp_server_port]')
    exit(1)

tcp = socket(AF_INET, SOCK_STREAM)
udp = socket(AF_INET, SOCK_DGRAM)
ip = sys.argv[1]
udpPort = int(sys.argv[3])

tcp.connect((ip, int(sys.argv[2])))
udp.bind(('', udpPort))

ip = gethostbyname(gethostname())
# files downloaded by client before
downloaded = []

print('Welcome! Please login :)')

username = login(tcp, udpPort, ip)

if username == False:
    tcp.close()
    udp.close()
    exit(1)

# ports of all other online peers
peers = {}
continueListen = True
listening = threading.Thread(target=listen, args=(tcp,))
listening.start()

listeningFile = threading.Thread(target=listenFile, args=(udp,))
listeningFile.start()
print(f'Welcome to TESSENGER, {username}!')
print('Commands: /msgto, /activeuser, /creategroup, /joingroup, /groupmsg, /p2pvideo, /logout')
print('========= Please enter a command: =========')

cmd = ''
while ' '.join(cmd) != '/logout':
    cmd = input('').split()
    if cmd[0] == '/msgto':
        if len(cmd) >= 3:
            msgto(tcp, cmd[1], ' '.join(cmd[2:]))
        else:
            print('> Usage: /msgto [username] [message]')
    elif cmd[0] == '/logout':
        if len(cmd) == 1:
            logout(tcp)
        else:
            print('> Usage: /logout')
    elif cmd[0] == '/activeuser':
        if len(cmd) == 1:
            activeuser(tcp)
        else:
            print('> Usage: /activeuser')
    elif cmd[0] == '/creategroup':
        if len(cmd) >= 3:
            creategroup(tcp, cmd[1], cmd[2:])
        else:
            print('> Usage: /creategroup [groupname] [username1] [username2]...')
    elif cmd[0] == '/joingroup':
        if len(cmd) == 2:
            joingroup(tcp, cmd[1])
        else:
            print('> Usage: /joingroup [groupname]')
    elif cmd[0] == '/groupmsg':
        if len(cmd) >= 3:
            groupmsg(tcp, cmd[1], ' '.join(cmd[2:]))
        else:
            print('> Usage: /groupmsg [groupname] [message]')
    elif cmd[0] == '/p2pvideo':
        if len(cmd) == 3:
            p2p(tcp, udp, cmd[1], cmd[2])
        else:
            print('> Usage: /p2pvideo [username] [filename]')
    else:
        print('> Invalid command')
# stop listening to tcp socket
continueListen = False
listening.join()
listeningFile.join()
tcp.close()
udp.close()
