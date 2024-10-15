## Introduction

This project implements a decentralized system where peers can share and retrieve files directly from each other. A central dictionary keeps track of which peer holds each file, acting as a directory to help locate files across the network. Peers can add, search, list, and retrieve files using this directory for efficient file sharing and management.

## Architecture

## Implementation
### Components
- **Centralized Index Server**: Handles client connections, registers shared files, and helps locate file-hosting peers. 
- **Clients (Peers)**: Users of the system who can share and request files. Each client communicates with the server and directly with other clients for downloading files. 

### Interactions
- **Client Registration**: Peers register their available files with the server. 
- **File Request**: A peer queries the server for the location of a file. The server returns a list of peers hosting  the file. 
- **File Transfer**: The requesting client connects to the file-hosting peer and downloads the file directly

## Setup

1. **Clone the project**:
   ```bash
   git clone git@github.com:busybrowsensei1/P2P-File-Sharing.git

2. **Run Server Process**:
   ```bash
   python server.py

3. **Get into the client directory and run the client process:**
   ```bash
  cd client1
  python app.py
   ```
Do the same for other clients as well. If you want more clients, copy the client code into another directory and change the port number in app.py.

## Team:

- Darshan Birhade
- Himanshu Raheja
- Ojjas Madare
- Pulkit Jain
- Sudharma Teredesai
