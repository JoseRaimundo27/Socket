import socket
import threading
import logging
from crypto import AES

logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(message)s')

class Client:
    SERVER_ADDR = '192.168.1.5'
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

            print("COMANDOS: '/global <mensagem>', '/privado <destinatário> <mensagem>', '/sendfile <destinatário> <filename>', '/logout' \n")
            while True:
                message = input()

                if message.startswith("/global"):
                    udp_message = message[5:]
                    full_message = f"/global {self.username}: {udp_message}"
                    encrypted_message = self.aes.encrypt(full_message)
                    self.UDP.sendto(encrypted_message.encode('utf-8'), (self.SERVER_ADDR, self.PORT_UDP))

                elif message.startswith("/privado"):
                    if message.count(' ') < 2:
                        print("Sua mensagem precisa seguir este padrão: /privado <destinatário> <mensagem> \n")  # Conta o número de espaços
                        continue
                    else:
                        _, recipient, tcp_message = message.split(' ', 2)
                        full_message = f"/privado {recipient} {self.username}: {tcp_message}"
                        encrypted_message = self.aes.encrypt(full_message)
                        self.TCP.sendall(encrypted_message.encode('utf-8'))
                        
                elif message.startswith("/sendfile"):
                    if message.count(' ') < 2:
                        print("Sua mensagem precisa seguir este padrão: /sendfile <destinatário> <filename> \n")  # Conta o número de espaços
                        continue
                    else:
                        _, recipient, filename = message.split(' ', 2)
                        try:
                            if not filename.endswith('.txt'):
                                print("Apenas arquivos .txt são permitidos.\n")
                                continue
                            
                            with open(filename, "r") as f: content = f.read() # Ler conteudo do arquivo txt.
                            
                            # Acrescenta o conteúdo do arquivo ao comando.
                            full_message = f"/sendfile {recipient} {filename} {content}"
                            encrypted_message = self.aes.encrypt(full_message)
                            self.TCP.sendall(encrypted_message.encode('utf-8'))
                            
                        except FileNotFoundError:
                            print("Arquivo não encontrado. Verifique o caminho e tente novamente.\n")
                        except Exception as e:
                            print(f"Erro ao enviar arquivo: {e}\n")
                    
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
                    if decrypted_message.startswith("/file"):
                        _, sender, filename, content = decrypted_message.split(' ', 3)
                        
                        # Salvar conteúdo em um novo arquivo local
                        with open(f"received_{filename}", "w") as f:
                            f.write(content)
                        print(f"Arquivo '{filename}' recebido de {sender} e salvo como 'received_{filename}'.")
                    else:
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

if __name__ == "__main__":
    client = Client()
    client.start()
