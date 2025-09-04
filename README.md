# chatroom

A Python-based socket programming project focused on messaging and file transfer, exploring the application of TCP and UDP network protocols and multi-threading. It consists of two main programs:

- **Server**: Authenticates users, manages active sessions, logs activity, and handles communication.  
- **Client**: Connects to the server via TCP, authenticates users, and provides a command-line interface to interact.  

---

## Supported Features

- **Authentication** with username/password from `credentials.txt` (with account blocking after failed attempts).  
- **Private messaging** (`/msgto`) between users.  
- **Active user list** (`/activeuser`) showing logged-in users. 
- **Group chat support**:  
  - Create group: `/creategroup`  
  - Join group: `/joingroup`  
  - Send group message: `/groupmsg`  
- **Logout** (`/logout`) with proper session clean-up.  
- **Logging** of users and messages in automatically generated files.  
- **File transfer** (`/p2pvideo`) to send binary files directly between clients.

## How to Run

### Server
Run the server **before any clients**.
```
python server.py [server_port] [num]
```

Arguments:
- `server_port` → the port the server will listen on.  
- `num` → max login retries before blocking (integer 1–5).  

Example:  
```bash
python server.py 12345 3
```

### Client

Run each client in a separate terminal.
```
python client.py [server_IP] [server_port] [udp_port]
```

Arguments:
- `server_IP` → the server’s IP address
- `server_port` → the TCP port the server is listening on
- `udp_port` → the client’s own UDP port used for peer-to-peer video transfer

Example:  
```bash
python client.py 127.0.0.1 12345 6000
```
