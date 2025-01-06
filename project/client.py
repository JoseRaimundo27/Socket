import socket
import threading
import logging
import os
from crypto import AES  # Importar o módulo de criptografia

logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(message)s')

class Client:
    SERVER_ADDR = '192.168.0.108'
    PORT_TCP = 8080
    PORT_UDP = 8081

    def __init__(self):
        self.username = None
        self.TCP = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.UDP = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.UDP.bind(("", 0))  # Porta local aleatória para mensagens UDP
        self.aes = AES()  # Inicializa o AES com uma chave aleatória

    def authenticate(self):
        while True:
            try:
                print("Escolha uma opção:")
                print("1 - Registrar")
                print("2 - Login")
                option = input("Opção: ")

                if option == "1":
                    username = input("Escolha um nome de usuário: ")
                    password = input("Escolha uma senha: ")
                    encrypted_message = self.aes.encrypt(f"/register {username} {password}")
                    self.TCP.sendall(encrypted_message.encode('utf-8'))
                elif option == "2":
                    username = input("Digite seu nome de usuário: ")
                    password = input("Digite sua senha: ")
                    encrypted_message = self.aes.encrypt(f"/login {username} {password}")
                    self.TCP.sendall(encrypted_message.encode('utf-8'))
                else:
                    print("Opção inválida. Tente novamente.")
                    continue

                response = self.TCP.recv(1024).decode('utf-8')
                decrypted_response = self.aes.decrypt(response)
                if decrypted_response == "SUCCESS":
                    self.username = username
                    print(f"Autenticação bem-sucedida! Bem-vindo, {self.username}.")
                    break
                else:
                    print(decrypted_response)
            except Exception as e:
                logging.error(f"Erro na autenticação: {e}")
                break

    def start(self):
        try:
            self.TCP.connect((self.SERVER_ADDR, self.PORT_TCP))
            logging.info(f"Conectado ao servidor TCP em {self.SERVER_ADDR}:{self.PORT_TCP}")

            # Envia a chave AES ao servidor para criptografia
            self.TCP.sendall(self.aes.key)

            self.authenticate()

            udp_thread = threading.Thread(target=self.receiveUDP, daemon=True)
            udp_thread.start()

            tcp_thread = threading.Thread(target=self.receiveTCP, daemon=True)
            tcp_thread.start()

            while True:
                message = input("Digite sua mensagem (/udp, /tcp <destinatário>, /logout): ")

                if message.startswith("/udp"):
                    udp_message = message[5:]
                    full_message = f"/udp {self.username}: {udp_message}"
                    encrypted_message = self.aes.encrypt(full_message)
                    self.UDP.sendto(encrypted_message.encode('utf-8'), (self.SERVER_ADDR, self.PORT_UDP))

                elif message.startswith("/tcp"):
                    _, recipient, tcp_message = message.split(' ', 2)
                    full_message = f"/tcp {recipient} {self.username}: {tcp_message}"
                    encrypted_message = self.aes.encrypt(full_message)
                    self.TCP.sendall(encrypted_message.encode('utf-8'))

                elif message.startswith("/logout"):
                    encrypted_message = self.aes.encrypt("/logout")
                    self.TCP.sendall(encrypted_message.encode('utf-8'))
                    print("Você foi desconectado.")
                    break
        except KeyboardInterrupt:
            logging.info("Cliente encerrando...")
        finally:
            self.TCP.close()
            self.UDP.close()

    def receiveTCP(self):
        while True:
            try:
                data = self.TCP.recv(1024)
                if data:
                    decrypted_message = self.aes.decrypt(data.decode('utf-8'))
                    print(f"[TCP] {decrypted_message}")
            except:
                break

    def receiveUDP(self):
        while True:
            try:
                data, _ = self.UDP.recvfrom(1024)
                if data:
                    decrypted_message = self.aes.decrypt(data.decode('utf-8'))
                    print(f"[UDP] {decrypted_message}")
            except:
                break

    def send_file(self, recipient, file_path):
        if not os.path.exists(file_path):
            print("Arquivo não encontrado!")
            return

        with open(file_path, "rb") as f:
            data = f.read()

        # Envia o comando inicial com o nome do arquivo
        filename = os.path.basename(file_path)
        self.tcp_socket.sendall(self.aes.encrypt(f"/file {recipient} {filename}").encode('utf-8'))

        # Divide o arquivo em chunks e envia cada parte
        chunk_size = 1024  # Tamanho do chunk (1 KB)
        for i in range(0, len(data), chunk_size):
            chunk = data[i:i+chunk_size]
            encrypted_chunk = self.aes.encrypt(chunk.decode('latin1'))
            self.tcp_socket.sendall(encrypted_chunk.encode('utf-8'))

        # Finaliza o envio com um comando especial
        self.tcp_socket.sendall(self.aes.encrypt("/file_end").encode('utf-8'))
        print(f"Arquivo '{filename}' enviado para {recipient}.")

    def handle_incoming_messages(self):
        while True:
            try:
                encrypted_data = self.tcp_socket.recv(1024)
                if not encrypted_data:
                    break

                msg = self.aes.decrypt(encrypted_data.decode('utf-8'))
                
                if msg.startswith("/file"):
                    _, filename = msg.split(' ', 1)
                    with open(filename, "wb") as f:
                        print(f"Recebendo arquivo: {filename}")

                elif msg.startswith("/file_end"):
                    print("Arquivo recebido com sucesso.")

                else:
                    with open(filename, "ab") as f:
                        f.write(msg.encode('latin1'))
                        
            except Exception as e:
                print(f"Erro ao receber mensagem: {e}")


if __name__ == "__main__":
    client = Client()
    client.start()
