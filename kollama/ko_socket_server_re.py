import socket
import struct
import os

#from final_app import Assistant -> englisht ver
from ko_final_app import Assistant 

class ServerSocket:
    def __init__(self):
        self.HOST = '192.168.0.55'
        self.PORT = 5678
        self.BUFFER_SIZE = 1024

        self.response_is_ready_in_server = 0 # response.wav 생성 완료 신호
        self.response_send_complete = 0 # response.wav 송신 완료 신호

        self.output_wav_filename = 'output.wav'
        self.response_wav_filename = 'response.wav'

        self.client_dir = '/home/ubuntu/Desktop/mines_lab/mines_robot/CHAT/' 
        self.server_dir = '/home/mines/Desktop/chat/' 

        self.socket = None
        self.conn = None

        self.start_server()

    def start_server(self):
        '''
        server socket 초기화 및 client 대기
        '''
        self.close_socket_with_client() # socket 초기화

        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            
            self.socket.bind((self.HOST, self.PORT))
            self.socket.listen(1)
            print('\nWaiting for connection with client...')

        except Exception as e:
            print(f"Error starting server : {e}")
            

    def accept_client(self):
        '''
        client 연결 수락
        '''
        try:
            if not self.socket:
                self.start_server()
            self.conn, addr = self.socket.accept()
            print(f"Connected with client : {addr}") #addr client와 연결
        except Exception as e:
            print(f"Error accepting client : {e}")

    def close_socket_with_client(self):
        '''
        socket 연결 닫기
        '''
        if self.conn:
            try:
                self.conn.close()
                print('\nClosed connection with client')
            except Exception as e:
                print(f"Error closing client connection : {e}")

            finally:
                self.conn = None
        if self.socket:
            try :
                self.socket.close()
                print('\nClosed server socket')
            except Exception as e:
                print(f"Error closing server socket : {e}")

            finally:
                self.socket = None
                
    def receive_sign_from_client(self):
        '''
        client에게서 'output.wav 가져가' 신호 수신
        '''
        try:
            print('\nWaiting for signal from client...')
            self.accept_client() #client 연결 수락

            data = self.conn.recv(1)
            print(data)

            if data.decode() == '1':
                print('\nReceived signal from client')
                self.receive_from_client() #output.wav 수신

            else:
                print('\nNo sign Received')
                self.close_socket_with_client()
        except Exception as e:
            print(f"Error receving signal from client : {e}")
            self.close_socket_with_client()

    def receive_from_client(self):
        '''
        client에게서 output.wav 수신
        '''
        try:
            sign = self.conn.recv(4)
            if sign != b'UPLD':
                print('Invaild upload signal received')
                return
            
            self.conn.send(b'READY') #client에게 준비 완료 신호 전송

            #파일 이름 길이 수신
            print("\n Receiving file name size...") 
            file_name_size = struct.unpack('h',self.conn.recv(2))[0]

            #파일 이름 수신
            print(f"\n File name size received: {file_name_size}")
            file_name = self.conn.recv(file_name_size).decode()

            #client에게 파일 이름을 수신받았다는 신호 보내기
            self.conn.send(b'GOT NAME')

            #파일 크기 수신
            print("\n Receiving file size...")
            file_size = struct.unpack('i', self.conn.recv(4))[0]
            print(file_size)

            output_file_path = os.path.join(self.server_dir, file_name)
            
            count=0
	    
            with open(output_file_path, 'wb') as output_file:
                bytes_received = 0
                print('\nReceiving..')
                while bytes_received < file_size:
                    chunk = self.conn.recv(self.BUFFER_SIZE)
                    if not chunk:
                        print('Connection closed unexpectedly.')
                        break
                    count+=1
                    print(f'Received chunk {count}')
                
                    output_file.write(chunk)
                    bytes_received += len(chunk)

            if bytes_received < file_size:
                print(f"Warning: Only {bytes_received} bytes received out of {file_size} bytes")
            else:
                print(f"\nReceived file {file_name} complete")
        
        except Exception as e:
            print(f"Error receiving file from client:{e}")
            
        finally:
            output_file.close()
            # self.close_socket_with_client()

    def llama_response(self):
        '''
        response.wav 생성
        '''
        try:
            assistant = Assistant()
            assistant.run()
            print('Save response.wav in server')
            self.response_is_ready_in_server = 1

        except Exception as e:
            print(f"Error generating response : {e}")

    def send_ready_sign_to_client(self):
        '''
        client에게 'response.wav 가져가' 신호 송신
        '''
        try:
            self.socket.listen(1)
            print('\nWaiting for connection with client...')

            self.conn, _ = self.socket.accept()
            print('connected to client!')

            if self.conn:
                self.conn.send(str(self.response_is_ready_in_server).encode())
                print('Sent ready sign to client')
            else:
                print('No client connection available')

        except Exception as e:
            print(f"Error sending ready sign to client: {e}")

    def send_to_client(self):
        '''
        client에게 response.wav 송신
        '''
        if self.response_is_ready_in_server != 1:
            print('Response file is not ready.')
            return
        
        print(f"\nUploading file:{self.response_wav_filename}...")
        try:
            with open(os.path.join(self.server_dir,self.response_wav_filename),'rb') as content:
                
                #UPLD 신호 전송
                self.conn.send(b'UPLD')

                #client로부터 응답 대기
                self.conn.recv(self.BUFFER_SIZE)

                #파일명 길이 전송
                self.conn.send(struct.pack('h',len(self.response_wav_filename)))
                #파일명 전송
                self.conn.send(self.response_wav_filename.encode())

                #파일 크기 계산 및 전송
                file_size=os.path.getsize(os.path.join(self.server_dir, self.response_wav_filename))
                self.conn.recv(self.BUFFER_SIZE) 
                self.conn.send(struct.pack('i',file_size))

                print("\nSending file to robot")
                while True:
                    chunk = content.read(self.BUFFER_SIZE)
                    if not chunk:
                        break
                    self.conn.sendall(chunk)

                print(f"Sent file {self.response_wav_filename} to robot")
                self.response_send_complete = 1

        except Exception as e:
            print(f"Error sending file to client : {e}")
        finally:
            self.close_socket_with_client()

'''if __name__ == '__main__':
    server = ServerSocket()

    server.receive_sign_from_client()
    server.llama_response()
    server.send_ready_sign_to_client()
    server.send_to_client()'''

if __name__ == '__main__':
    server = ServerSocket()

    try :
        while True :
            server.receive_sign_from_client()
            server.llama_response()
            server.send_ready_sign_to_client()
            server.send_to_client()

            print('Waiting Next interaction....')

    except KeyboardInterrupt:
        print('Server interrupted by user.')



'''if __name__ == '__main__':
    server = ServerSocket()

    try :
        while True :
            server.receive_sign_from_client()
            server.llama_response()
            server.send_ready_sign_to_client()
            server.send_to_client()

            print('Waiting Next interaction....')

    except KeyboardInterrupt:
        print('Server interrupted by user.')

    finally:
        server.close_socket_with_client()
'''