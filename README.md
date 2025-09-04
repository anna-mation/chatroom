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
