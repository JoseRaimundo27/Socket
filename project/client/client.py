import socket
import threading
import logging

logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(message)s')

class Client:
    SERVER_ADDR = '127.0.0.1'
    PORT_TCP = 8080
    PORT_UDP = 8081

    def __init__(self):
        self.username = None
        self.TCP = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.UDP = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.UDP.bind(("", 0))  # Porta local aleatória para mensagens UDP

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
                    self.TCP.sendall(f"/register {username} {password}".encode('utf-8'))
                elif option == "2":
                    username = input("Digite seu nome de usuário: ")
                    password = input("Digite sua senha: ")
                    self.TCP.sendall(f"/login {username} {password}".encode('utf-8'))
                else:
                    print("Opção inválida. Tente novamente.")
                    continue

                response = self.TCP.recv(1024).decode('utf-8')
                if response == "SUCCESS":
                    self.username = username
                    print(f"Autenticação bem-sucedida! Bem-vindo, {self.username}.")
                    break
                else:
                    print(response)
            except Exception as e:
                logging.error(f"Erro na autenticação: {e}")
                break

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
                    self.TCP.sendall(f"/register {username} {password}".encode('utf-8'))
                elif option == "2":
                    username = input("Digite seu nome de usuário: ")
                    password = input("Digite sua senha: ")
                    self.TCP.sendall(f"/login {username} {password}".encode('utf-8'))
                else:
                    print("Opção inválida. Tente novamente.")
                    continue

                response = self.TCP.recv(1024).decode('utf-8')
                if response == "SUCCESS":
                    self.username = username
                    print(f"Autenticação bem-sucedida! Bem-vindo, {self.username}.")
                    break
                else:
                    print(response)
            except Exception as e:
                logging.error(f"Erro na autenticação: {e}")
                break

    def start(self):
        try:
            self.TCP.connect((self.SERVER_ADDR, self.PORT_TCP))
            logging.info(f"Conectado ao servidor TCP em {self.SERVER_ADDR}:{self.PORT_TCP}")

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
                    self.UDP.sendto(full_message.encode('utf-8'), (self.SERVER_ADDR, self.PORT_UDP))

                elif message.startswith("/tcp"):
                    _, recipient, tcp_message = message.split(' ', 2)
                    full_message = f"/tcp {recipient} {self.username}: {tcp_message}"
                    self.TCP.sendall(full_message.encode('utf-8'))

                elif message.startswith("/logout"):
                    self.TCP.sendall("/logout".encode('utf-8'))
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
                    print(f"[TCP] {data.decode('utf-8')}")
            except:
                break

    def receiveUDP(self):
        while True:
            try:
                data, _ = self.UDP.recvfrom(1024)
                if data:
                    print(f"[UDP] {data.decode('utf-8')}")
            except:
                break

if __name__ == "__main__":
    client = Client()
    client.start()
