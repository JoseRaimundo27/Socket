import socket
import threading
import logging
from crypto import AES
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(message)s')

class Server:
    PORT_TCP = 8080
    PORT_UDP = 8081
    ADDR = '0.0.0.0'
    CLIENTS = {}  # Mapeia nomes de usuários às informações do cliente (TCP, endereço UDP e chave AES)
    CREDENTIALS = {}  # Mapeia nomes de usuários às senhas
    MAX_CONNECTIONS = 10  # Limite de conexões simultâneas

    def start(self):
        self.TCP = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.UDP = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        self.TCP.bind((self.ADDR, self.PORT_TCP))
        self.TCP.listen()
        logging.info(f"Servidor TCP iniciado em {self.ADDR}:{self.PORT_TCP}")

        self.UDP.bind((self.ADDR, self.PORT_UDP))
        logging.info(f"Servidor UDP iniciado em {self.ADDR}:{self.PORT_UDP}")

        threading.Thread(target=self.handleUDP, daemon=True).start()

        try:
            while True:
                conn, addr = self.TCP.accept()

                if len(self.CLIENTS) >= self.MAX_CONNECTIONS:
                    logging.warning("Número máximo de conexões atingido.")
                    conn.sendall("Número máximo de conexões atingido. Tente novamente mais tarde.\n".encode('utf-8'))
                    conn.close()
                    continue

                threading.Thread(target=self.authenticate_client, args=(conn, addr)).start()
        except KeyboardInterrupt:
            logging.info("Servidor encerrando...")
        finally:
            self.TCP.close()
            self.UDP.close()

    def authenticate_client(self, conn, addr):
        try:
            aes_key = conn.recv(32)
            aes = AES(key=aes_key)

            while True:
                encrypted_data = conn.recv(1024).decode('utf-8')
                data = aes.decrypt(encrypted_data).strip()

                if data.startswith("/register"):
                    _, username, password = data.split(' ', 2)
                    if username in self.CREDENTIALS:
                        conn.sendall(aes.encrypt("Nome de usuário já em uso.\n").encode('utf-8'))
                    else:
                        self.CREDENTIALS[username] = password
                        self.CLIENTS[username] = {"tcp": conn, "addr": None, "aes": aes}
                        conn.sendall(aes.encrypt("SUCCESS").encode('utf-8'))
                        logging.info(f"Novo cliente registrado: {username} ({addr})")
                        self.handleTCP(conn, username)
                        break

                elif data.startswith("/login"):
                    _, username, password = data.split(' ', 2)
                    if username in self.CREDENTIALS and self.CREDENTIALS[username] == password:
                        self.CLIENTS[username] = {"tcp": conn, "addr": None, "aes": aes}
                        conn.sendall(aes.encrypt("SUCCESS").encode('utf-8'))
                        logging.info(f"Cliente autenticado: {username} ({addr})")
                        self.handleTCP(conn, username)
                        break
                    else:
                        conn.sendall(aes.encrypt("Credenciais inválidas.\n").encode('utf-8'))
                else:
                    conn.sendall(aes.encrypt("Comando inválido.").encode('utf-8'))
        except Exception as e:
            logging.warning(f"Erro ao autenticar cliente {addr}: {e}")

    def handleTCP(self, conn, username):
        aes = self.CLIENTS[username]["aes"]
        try:
            while True:
                encrypted_data = conn.recv(1024)
                if not encrypted_data: break

                msg = aes.decrypt(encrypted_data.decode('utf-8'))
                if msg.startswith("/privado"):
                    _, recipient, message = msg.split(' ', 2)
                    self.send_direct_message(username, recipient, message)
                    
                elif msg.startswith("/sendfile"):
                    _, recipient, filename, content = msg.split(' ', 3)
                    self.sendFile(username, recipient, filename, content) # Enviar arquivo ao destinatário

                elif msg.startswith("/logout"):
                    logging.info(f"{username} se desconectou do servidor.")
                    conn.sendall(aes.encrypt("Você foi deslogado com sucesso. \n").encode('utf-8'))
                    break

        except ConnectionResetError:
            logging.warning(f"Conexão perdida com {username}")
        finally:
            conn.close()
            if username in self.CLIENTS:
                del self.CLIENTS[username]

    def handleUDP(self):
        while True:
            try:
                data, addr = self.UDP.recvfrom(1024)
                encrypted_msg = data.decode('utf-8')

                for username, info in self.CLIENTS.items():
                    aes = info["aes"]
                    try:
                        msg = aes.decrypt(encrypted_msg)
                        if msg.startswith("/global"):
                            sender, message = msg[8:].split(':', 1)

                            if info["addr"] is None:
                                info["addr"] = addr
                                join_message = f"{sender} joined the global chat."
                                self.send_message_to_all("Server", join_message)

                            self.send_message_to_all(sender.strip(), message.strip())
                            break
                    except Exception:
                        continue
            except Exception as e:
                logging.warning(f"Erro no UDP: {e}")

    def send_direct_message(self, sender, recipient, message):
        if recipient in self.CLIENTS and self.CLIENTS[recipient]["tcp"]:
            conn = self.CLIENTS[recipient]["tcp"]
            aes = self.CLIENTS[recipient]["aes"]
            encrypted_message = aes.encrypt(f"[Privado de {sender}]: {message}")
            conn.sendall(encrypted_message.encode('utf-8'))
            logging.info(f"Mensagem privada de {sender} para {recipient}: {message}")
        else:
            logging.warning(f"Destinatário {recipient} não encontrado.")
            if sender in self.CLIENTS and self.CLIENTS[sender]["tcp"]:
                sender_aes = self.CLIENTS[sender]["aes"]
                self.CLIENTS[sender]["tcp"].sendall(sender_aes.encrypt("Usuário não encontrado. \n").encode('utf-8'))

    def send_message_to_all(self, sender, message):
        for username, info in self.CLIENTS.items():
            if info["addr"]:
                try:
                    aes = info["aes"]
                    encrypted_message = aes.encrypt(f"[{sender}]: {message}")
                    self.UDP.sendto(encrypted_message.encode('utf-8'), info["addr"])
                    logging.info(f"Mensagem global enviada de {sender} para {username}: {message}")
                except Exception as e:
                    logging.warning(f"Erro ao enviar mensagem UDP para {username}: {e}\n")
                    
    def sendFile(self, sender, recipient, filename, content):
        if recipient in self.CLIENTS and self.CLIENTS[recipient]["tcp"]:
            conn = self.CLIENTS[recipient]["tcp"]
            aes = self.CLIENTS[recipient]["aes"]

            # Formatar mensagem para o destinatário
            encrypted_message = aes.encrypt(f"/file {sender} {filename} {content}")
            conn.sendall(encrypted_message.encode('utf-8'))
            logging.info(f"Arquivo '{filename}' enviado de {sender} para {recipient}.")
        else:
            logging.warning(f"Destinatário {recipient} não encontrado.")
            if sender in self.CLIENTS and self.CLIENTS[sender]["tcp"]:
                sender_aes = self.CLIENTS[sender]["aes"]
                self.CLIENTS[sender]["tcp"].sendall(sender_aes.encrypt("Usuário não encontrado. \n").encode('utf-8'))

if __name__ == "__main__":
    server = Server()
    server.start()
