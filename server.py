# python3

from socket import *
import sys
from datetime import datetime
from threading import Thread
import os
import time

# MAIN
# wipe previous logs
if os.path.exists('userlog.txt'):
  os.remove('userlog.txt')

if os.path.exists('messagelog.txt'):
  os.remove('messagelog.txt')

# check for valid cmd line argument
if len(sys.argv) != 3:
    print('Usage: python3 server.py [server_port] [num_attempts]')
    exit(1)
try:
    maxAttempts = int(sys.argv[2])
except ValueError:
    print('Please input an integer')
    exit(1)

if maxAttempts < 1 or maxAttempts > 5:
    print('Please input a number between 1 and 5')
    exit(1)

# one thread for each new client
class ClientThread(Thread):
    def __init__(self, clientAddress, clientSocket):
        Thread.__init__(self)
        self.clientAddress = clientAddress
        self.clientSocket = clientSocket
        self.clientAlive = False
        # username of client
        self.user = ''
        self.clientAlive = True
        # groups client has joined
        self.groups = []
        # temporary username used when trying to log in
        self.tempUser = ''
        
    def run(self):
        message = ''
        
        # listen for instructions from client
        while self.clientAlive:
            message = self.recMessage().split()
            if message:
                if message[0] == '[login]':
                    self.process_login(message[1], message[2], message[3])
                elif message[0] == '[logout]':
                    self.process_logout()
                    break
                elif message[0] == '[msgto]':
                    self.process_msgto(message[1], ' '.join(message[2:]))
                elif message[0] == '[activeuser]':
                    self.process_activeuser()
                elif message[0] == '[crgroup]':
                    self.process_creategroup(message[1], message[2:])
                elif message[0] == '[joingroup]':
                    self.process_joingroup(message[1])
                elif message[0] == '[groupmsg]':
                    self.process_groupmsg(message[1], ' '.join(message[2:]))
                elif message[0] == '[getport]':
                    self.process_getport(message[1])
                else:
                    print('[error] you shouldnt be seeing this')

    # HELPER FUNCTIONS
    
    def recMessage(self):
        return self.clientSocket.recv(1024).decode('utf-8')
    
    # send message to client
    def sendMessage(self, message):
        self.clientSocket.sendall(bytes(str(message), 'utf-8'))

    # send message to other client
    def sendTo(self, to, message):
        to.sendall(bytes(str(message), 'utf-8'))

    # creates file if it doesn't exist
    def checkFile(self, file):
        f = open(file,'a+')
        f.close()

    # checks global dictionary to determine if a user is online
    def userOnline(self, user):
        if (user in clients.keys()):
            return True
        else:
            return False

    # gets and formats current time
    def getTime(self):
        return datetime.now().strftime("%d %b %Y %H:%M:%S")

    # adds new online user to userlog.txt
    def log(self, login):
        self.checkFile('userlog.txt')
        with open('userlog.txt', 'r') as file:
            data = file.readlines()
        
        seqNum = len(data) + 1
        now = self.getTime()
        log = f'{seqNum}; {now}; {login[0]}; {login[1]}; {login[2]}\n'
        # update own username
        self.user = login[0]
        # reset login attempts
        loginAtt[self.user] = 0
        # add to online users
        clients[self.user] = self.clientSocket
        data.append(log)
        print(f'{self.user} online')
        
        with open('userlog.txt', 'w') as file:
            file.writelines(data)

    # checks if group exists and if user is invited
    def checkGroup(self, name):
        if name in inviteGroups.keys():
            if self.user in inviteGroups[name]:
                return True
            else:
                self.sendMessage(f'{self.user} not invited to group chat {name}')
        else:
            self.sendMessage(f'group chat {name} does not exist')
        return False

    # verify username and password
    def credentials(self, now, udpPort, ip):
        userFound = -1
        index = 0
        # check user exists and get expected pwd
        while userFound == -1:
            rec = self.recMessage().split()
            username = rec[0]
            self.checkFile('credentials.txt')
            with open('credentials.txt', 'r') as f:
                for i in f:
                    line = i.split()
                    if username == line[0]:
                        password = line[1]
                        userFound = index
                    index += 1
            if userFound == -1:
                self.sendMessage('user not found. please try again')
                return 'continue'
        
        username = rec[0]
        self.tempUser = username
        # check if user blocked
        if float(now) < timeout.get(username, 0):
            self.sendMessage('your account has been blocked, try again later')
            return 'blocked'
        if username not in loginAtt.keys():
            loginAtt[username] = 0

        inputPassword = rec[1]
        # check if password correct
        if password != inputPassword:
            loginAtt[username] += 1
            # if wrong, check again if user is now blocked
            if loginAtt[username] == maxAttempts:
                self.sendMessage('your account has been blocked, try again later')
                return 'blocked'
            self.sendMessage('incorrect credentials')
            return 'continue'
        else:
            # correct credentials, login
            ret = f'{username}, {ip}, {udpPort}'
            return ret
        
    # receives and processes login request
    def process_login(self, now, udp, ip):
        numAttempts = 0
        login = 'continue'
        while numAttempts < maxAttempts and login == 'continue':
            login = self.credentials(now, udp, ip)
            numAttempts = loginAtt.get(self.tempUser, 0)
        if login != 'blocked' and login != 'continue':
            self.sendMessage('successfully logged in')
            self.log(login.split(', '))
        else:
            # blocked
            if numAttempts == maxAttempts:
                # reset login attempts
                loginAtt[self.tempUser] = 0
                # sets time until unblocked
                timeout[self.tempUser] = time.time() + 10
            print(f'{self.tempUser} blocked :(')
            self.process_logout()

    # receives and processes logout request
    def process_logout(self):
        # checks if user is logged in
        if (self.user in clients.keys()):
            clients.pop(self.user)
            # removes user from all groups
            for group in self.groups:
                activeGroups[group].remove(self.user)

            prev = 0
            with open('userlog.txt', 'r') as f:
                lines = f.readlines()
            with open('userlog.txt', 'w') as f:
                for line in lines:
                    info = line.split('; ')
                    if info[2] != self.user:
                        f.write(f'{prev + 1}; {line[3:]}')
                        prev += 1

            print(f'{self.user} offline')
            self.sendMessage(f'goodbye, {self.user}!')
        self.clientAlive = False
        self.clientSocket.close()

    # receives messages and forwards messages to others + updates log
    def process_msgto(self, user, msg):
        self.checkFile('messagelog.txt')
        now = self.getTime()
        if (self.userOnline(user)):
            # sends msg
            self.sendTo(clients[user], f'{now}, {self.user}: {msg}')
            # updates log
            with open('messagelog.txt', 'r') as file:
                data = file.readlines()
            seqNum = len(data) + 1
            now = self.getTime()
            log = f'{seqNum}; {now}; {user}; {msg}\n'
            data.append(log)
            with open('messagelog.txt', 'w') as file:
                file.writelines(data)
            self.sendMessage(f'message sent at {now}')
            print(f'{self.user} message to {user}: \'{msg}\' at {now}')
        else:
            self.sendMessage(f'{user} not online')

    # receives request and builds list of active users (excluding client)
    def process_activeuser(self):
        ret = []
        with open('userlog.txt', 'r') as f:
            for line in f:
                info = line.split('; ')
                if info[2] != self.user:
                    # use -1 to splice off newline char
                    ret.append(f'{info[2]}, {info[3]}, {info[4][:-1]}, active since {info[1]}')
        ret = '\n  '.join(ret)
        if len(ret) == 0:
            ret = 'no other active user'
        self.sendMessage(ret)

    # receives and processes request to join group
    def process_joingroup(self, name):
        if self.checkGroup(name):
            # check if user has not already joined
            if self.user not in activeGroups[name]:
                activeGroups[name].append(self.user)
                self.groups.append(name)
                self.sendMessage(f'{self.user} joined the group chat {name} successfully')
                print(f'{self.user} joined group {name}')
            else:
                self.sendMessage(f'{self.user} already joined group chat {name}')

    # creates new group
    def process_creategroup(self, name, member):
        if name in inviteGroups.keys():
            self.sendMessage(f'group chat {name} already exists')
        else:
            inviteGroups[name] = [self.user]
            activeGroups[name] = [self.user]
            i = 0
            online = True
            # invites each member listed into group, checks if members are online
            while i < len(member) and online:
                person = member[i]
                if person in clients.keys():
                    if person not in inviteGroups[name]:
                        inviteGroups[name].append(person)
                    else:
                        self.sendMessage(f'{person} cannot be added more than once')
                        online = False
                else:
                    self.sendMessage(f'{person} is not online')
                    online = False
                i += 1
            if online:
                self.groups.append(name)
                # formats response text
                open(f'{name}_messagelog.txt', 'w').close()
                ret = f'group chat {name} created, users: '
                users = []
                for person in inviteGroups[name]:
                    users.append(person)
                ret += ', '.join(users)
                self.sendMessage(ret)
                print(f'{users[0]} created group {name}')
            else:
                inviteGroups.pop(name)
                activeGroups.pop(name)

    # relays group message to all active group members
    def process_groupmsg(self, name, msg):
        if self.checkGroup(name):
            # checks if user is in group
            if name in self.groups:
                now = self.getTime()
                # sends message to all online users in group
                for client in activeGroups[name]:
                    if client != self.user:
                        self.sendTo(clients[client], f'{now}, {name}, {self.user}: {msg}')
                # updates log for group
                with open(f'{name}_messagelog.txt', 'r') as file:
                    data = file.readlines()
                seqNum = len(data) + 1
                log = f'{seqNum}; {now}; {self.user}; {msg}\n'
                data.append(log)
                with open(f'{name}_messagelog.txt', 'w') as file:
                    file.writelines(data)

                self.sendMessage(f'{name} group chat message sent at {now}')
                print(f'{self.user} message to group {name}: \'{msg}\' at {now}')
            else:
                self.sendMessage(f'{self.user} has not joined group chat {name}')
    
    # returns UDP port of specified user
    def process_getport(self, user):
        # checks for online user
        port = False
        self.checkFile('userlog.txt')
        with open('userlog.txt', 'r') as f:
            for i in f:
                line = i.split('; ')
                if user == line[2]:
                    port = int(line[4])
        if not port:
            self.sendMessage(f'{user} is not online')
        else:
            self.sendMessage(f'[noprint] {user} {port}')

# names of active members in groups, group names as keys
activeGroups = {}
# tcp sockets of online users, usernames as keys
clients = {}
# names of invited members of groups, group names as keys
inviteGroups = {}
# number of failed login attempts
loginAtt = {}
# time blocked
timeout = {}

port = int(sys.argv[1])
tcp = socket(AF_INET, SOCK_STREAM)
tcp.bind(('localhost', port))
tcp.listen(1)

print('Server is running')
print('Waiting for connection requests...')

while 1:
    tcp.listen()
    tcpClient, tcpAddr = tcp.accept()
    clientThread = ClientThread(tcpAddr, tcpClient)
    clientThread.start()