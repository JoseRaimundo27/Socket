import socket
import threading
import logging

logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(message)s')

class Server:
    PORT_TCP = 8080
    PORT_UDP = 8081
    ADDR = '127.0.0.1'
    CLIENTS = {}  # Mapeia nomes de usuários às informações do cliente (TCP e UDP)
    CREDENTIALS = {}  # Mapeia nomes de usuários às senhas

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
                threading.Thread(target=self.authenticate_client, args=(conn, addr)).start()
        except KeyboardInterrupt:
            logging.info("Servidor encerrando...")
        finally:
            self.TCP.close()
            self.UDP.close()

    def authenticate_client(self, conn, addr):
        try:
            while True:
                data = conn.recv(1024).decode('utf-8').strip()
                if data.startswith("/register"):
                    _, username, password = data.split(' ', 2)
                    if username in self.CREDENTIALS:
                        conn.sendall("Nome de usuário já em uso.".encode('utf-8'))
                    else:
                        self.CREDENTIALS[username] = password
                        self.CLIENTS[username] = {"tcp": conn, "udp": None}
                        conn.sendall("SUCCESS".encode('utf-8'))
                        logging.info(f"Novo cliente registrado: {username} ({addr})")
                        self.handleTCP(conn, username)
                        break

                elif data.startswith("/login"):
                    _, username, password = data.split(' ', 2)
                    if username in self.CREDENTIALS and self.CREDENTIALS[username] == password:
                        self.CLIENTS[username] = {"tcp": conn, "udp": None}
                        conn.sendall("SUCCESS".encode('utf-8'))
                        logging.info(f"Cliente autenticado: {username} ({addr})")
                        self.handleTCP(conn, username)
                        break
                    else:
                        conn.sendall("Credenciais inválidas.".encode('utf-8'))
                else:
                    conn.sendall("Comando inválido.".encode('utf-8'))
        except Exception as e:
            logging.warning(f"Erro ao autenticar cliente {addr}: {e}")

    def handleTCP(self, conn, username):
        try:
            while True:
                data = conn.recv(1024)
                if not data:
                    break

                msg = data.decode('utf-8')
                if msg.startswith("/tcp"):
                    _, recipient, message = msg.split(' ', 2)
                    self.send_direct_message(username, recipient, message)

                elif msg.startswith("/logout"):
                    logging.info(f"{username} se desconectou do servidor.")
                    conn.sendall("Você foi deslogado com sucesso.".encode('utf-8'))
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
                msg = data.decode('utf-8')

                if msg.startswith("/udp"):
                    sender, message = msg[5:].split(':', 1)
                    if sender in self.CLIENTS:
                        self.CLIENTS[sender]["udp"] = addr
                    self.send_message_to_all(sender.strip(), message.strip())
            except Exception as e:
                logging.warning(f"Erro no UDP: {e}")

    def send_direct_message(self, sender, recipient, message):
        if recipient in self.CLIENTS and self.CLIENTS[recipient]["tcp"]:
            conn = self.CLIENTS[recipient]["tcp"]
            conn.sendall(f"[Privado de {sender}]: {message}".encode('utf-8'))
            logging.info(f"Mensagem privada de {sender} para {recipient}: {message}")
        else:
            logging.warning(f"Destinatário {recipient} não encontrado.")
            if sender in self.CLIENTS and self.CLIENTS[sender]["tcp"]:
                self.CLIENTS[sender]["tcp"].sendall("Usuário não encontrado.".encode('utf-8'))

    def send_message_to_all(self, sender, message):
        for username, info in self.CLIENTS.items():
            if info["udp"]:
                try:
                    self.UDP.sendto(f"[{sender}]: {message}".encode('utf-8'), info["udp"])
                    logging.info(f"Mensagem global enviada de {sender} para {username}: {message}")
                except Exception as e:
                    logging.warning(f"Erro ao enviar mensagem UDP para {username}: {e}")

if __name__ == "__main__":
    server = Server()
    server.start()
