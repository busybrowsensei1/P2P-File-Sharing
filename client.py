import socket
import threading
import platform
import mimetypes
import os
import sys
import time
from pathlib import Path


class MyException(Exception):
    pass


class Client(object):
    def __init__(self, serverhost='localhost', V='P2P-CI/1.0', DIR='rfc'):
        self.SERVER_HOST = serverhost
        self.SERVER_PORT = 7734
        self.V = V
        self.DIR = 'rfc'  # file directory
        Path(self.DIR).mkdir(exist_ok=True)

        self.UPLOAD_PORT = None
        self.shareable = True

    def start(self):
        # connect to server
        print('Connecting to the server %s:%s' %
              (self.SERVER_HOST, self.SERVER_PORT))
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.server.connect((self.SERVER_HOST, self.SERVER_PORT))
        except Exception:
            print('Server Not Available.')
            return

        print('Connected')
        # upload
        uploader_process = threading.Thread(target=self.init_upload)
        uploader_process.start()
        while self.UPLOAD_PORT is None:
            # wait until upload port is initialized
            pass
        print('Listening on the upload port %s' % self.UPLOAD_PORT)

        # interactive shell
        self.cli()

    def cli(self):
        command_dict = {'1': self.add,
                        '2': self.lookup,
                        '3': self.listall,
                        '4': self.pre_download,
                        '5': self.shutdown}
        while True:
            try:
                req = input('\n1: Add, 2: Look Up, 3: List All, 4: Download, 5: Shut Down\nEnter your request: ')
                command_dict.setdefault(req, self.invalid_input)()
            except MyException as e:
                print(e)
            except Exception:
                print('System Error.')
            except BaseException:
                self.shutdown()

    def init_upload(self):
        # listen upload port
        self.uploader = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.uploader.bind(('', 0))
        self.UPLOAD_PORT = self.uploader.getsockname()[1]
        self.uploader.listen(5)

        while self.shareable:
            requester, addr = self.uploader.accept()
            handler = threading.Thread(
                target=self.handle_upload, args=(requester, addr))
            handler.start()
        self.uploader.close()

    def handle_upload(self, soc, addr):
        header = soc.recv(1024).decode().splitlines()
        try:
            version = header[0].split()[-1]
            num = header[0].split()[-2]
            method = header[0].split()[0]
            path = '%s/rfc%s.txt' % (self.DIR, num)
            if version != self.V:
                soc.sendall(str.encode(
                    self.V + ' 505 P2P-CI Version Not Supported\n'))
            elif not Path(path).is_file():
                soc.sendall(str.encode(self.V + ' 404 Not Found\n'))
            elif method == 'GET':
                header = self.V + ' 200 OK\n'
                header += 'Data: %s\n' % (time.strftime(
                    "%a, %d %b %Y %H:%M:%S GMT", time.gmtime()))
                header += 'OS: %s\n' % (platform.platform())
                header += 'Last-Modified: %s\n' % (time.strftime(
                    "%a, %d %b %Y %H:%M:%S GMT", time.gmtime(os.path.getmtime(path))))
                header += 'Content-Length: %s\n' % (os.path.getsize(path))
                header += 'Content-Type: %s\n' % (
                    mimetypes.MimeTypes().guess_type(path)[0])
                soc.sendall(header.encode())
                # Uploading
                try:
                    print('\nUploading...')

                    send_length = 0
                    with open(path, 'r') as file:
                        to_send = file.read(1024)
                        while to_send:
                            send_length += len(to_send.encode())
                            soc.sendall(to_send.encode())
                            to_send = file.read(1024)
                except Exception:
                    raise MyException('Uploading Failed')
                # total_length = int(os.path.getsize(path))
                # print('send: %s | total: %s' % (send_length, total_length))
                # if send_length < total_length:
                #     raise MyException('Uploading Failed')
                print('Uploading Completed.')
                # Restore CLI
                print(
                    '\n1: Add, 2: Look Up, 3: List All, 4: Download\nEnter your request: ')
            else:
                raise MyException('Bad Request.')
        except Exception:
            soc.sendall(str.encode(self.V + '  400 Bad Request\n'))
        finally:
            soc.close()

    def add(self, num=None, title=None):
        if not num:
            raise MyException('RFC number must be provided.')
        if not num.isdigit():
            raise MyException('Invalid Input.')
        if not title:
            raise MyException('RFC title must be provided.')

        file = Path(f'{self.DIR}/rfc{num}.txt')
        if not file.is_file():
            raise MyException('File Does Not Exist!')

        msg = f'ADD RFC {num} {self.V}\n'
        msg += f'Host: {socket.gethostname()}\n'
        msg += f'Post: {self.UPLOAD_PORT}\n'
        msg += f'Title: {title}\n'
        self.server.sendall(msg.encode())
        res = self.server.recv(1024).decode()
        return f'Received response: \n{res}'

    def lookup(self, num=None, title=None):
        if not num:
            raise MyException('RFC number must be provided.')

        msg = f'LOOKUP RFC {num} {self.V}\n'
        msg += f'Host: {socket.gethostname()}\n'
        msg += f'Post: {self.UPLOAD_PORT}\n'
        msg += f'Title: {title}\n' if title else ''
        self.server.sendall(msg.encode())
        res = self.server.recv(1024).decode()
        return f'Received response: \n{res}'

    def listall(self):
        msg = f'LIST ALL {self.V}\n'
        msg += f'Host: {socket.gethostname()}\n'
        msg += f'Post: {self.UPLOAD_PORT}\n'
        self.server.sendall(msg.encode())
        res = self.server.recv(1024).decode()
        return f'Received response: \n{res}'

    def pre_download(self, num):
        if not num:
            raise MyException('RFC number must be provided.')

        msg = f'LOOKUP RFC {num} {self.V}\n'
        msg += f'Host: {socket.gethostname()}\n'
        msg += f'Post: {self.UPLOAD_PORT}\n'
        self.server.sendall(msg.encode())
        
        lines = self.server.recv(1024).decode().splitlines()
        
        # Process response
        response = {}
        if lines[0].split()[1] == '200':
            # Successfully looked up, process the peer info
            peers = []
            for line in lines[1:]:
                parts = line.split()
                if len(parts) >= 3:  # Ensure there are enough parts
                    peer_info = {
                        'title': ' '.join(parts[:-2]),  # Title is everything except the last two parts
                        'host': parts[-2],
                        'port': int(parts[-1])
                    }
                    peers.append(peer_info)
            response['peers'] = peers
            response['message'] = 'Successfully retrieved peer info.'
            response['status'] = 200
        else:
            # Handle error responses
            response['message'] = f"Error: {lines[0]}"
            response['status'] = 400

        return response  # Return structured response


    def shutdown(self):
        print('\nShutting Down...')
        self.server.close()
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)

    def download(self, num, title, peer_host, peer_port):
        try:
            # Establish connection with the peer
            soc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            if soc.connect_ex((peer_host, peer_port)):
                raise MyException('Peer Not Available')

            # Send GET request to the peer
            msg = f'GET RFC {num} {self.V}\n'
            msg += f'Host: {socket.gethostname()}\n'
            msg += f'OS: {platform.platform()}\n'
            soc.sendall(msg.encode())

            # Handle the downloading
            header = soc.recv(1024).decode()
            print('Received response header:\n%s' % header)
            header_lines = header.splitlines()

            if header_lines[0].split()[-2] == '200':
                path = f'{self.DIR}/rfc{num}.txt'
                print('Downloading...')
                try:
                    with open(path, 'w') as file:
                        content = soc.recv(1024)
                        while content:
                            file.write(content.decode())
                            content = soc.recv(1024)

                    print('Download completed.')
                    # Optionally add the RFC to the server after downloading
                    if self.shareable:
                        self.add(num, title)
                except Exception:
                    raise MyException('Downloading Failed')

                total_length = int(header_lines[4].split()[1])
                if os.path.getsize(path) < total_length:
                    raise MyException('Incomplete Download.')

                print('Downloading completed and file saved.')
            elif header_lines[0].split()[1] == '400':
                raise MyException('Invalid Input.')
            elif header_lines[0].split()[1] == '404':
                raise MyException('File Not Available.')
            elif header_lines[0].split()[1] == '500':
                raise MyException('Version Not Supported.')
        finally:
            soc.close()

    def invalid_input(self):
        raise MyException('Invalid Input.')

    


if __name__ == '__main__':
    if len(sys.argv) == 2:
        client = Client(sys.argv[1])
    else:
        client = Client()
    client.start()
