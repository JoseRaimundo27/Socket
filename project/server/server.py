import socket
import threading
import logging

logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(message)s')

class Server:
    PORT_TCP = 8080
    PORT_UDP = 8081
    ADDR = '127.0.0.1'
    CLIENTS = {}  # Mapeia nomes de usuários às informações do cliente (TCP e UDP)

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
                threading.Thread(target=self.register_client, args=(conn, addr)).start()
        except KeyboardInterrupt:
            logging.info("Servidor encerrando...")
        finally:
            self.TCP.close()
            self.UDP.close()

    def register_client(self, conn, addr):
        try:
            data = conn.recv(1024).decode('utf-8').strip()
            if data.startswith("/register"):
                _, username = data.split(' ', 1)
                if username in self.CLIENTS:
                    conn.sendall("Nome de usuário já em uso.".encode('utf-8'))
                    conn.close()
                    return
                self.CLIENTS[username] = {"tcp": conn, "udp": None}
                logging.info(f"Novo cliente registrado: {username} ({addr})")
                self.handleTCP(conn, username)
            else:
                conn.sendall("Registro inválido.".encode('utf-8'))
                conn.close()
        except Exception as e:
            logging.warning(f"Erro ao registrar cliente {addr}: {e}")

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
                    sender, message = msg[5:].split(':', 1)  # Extrai o remetente e a mensagem
                    if sender in self.CLIENTS:
                        self.CLIENTS[sender]["udp"] = addr  # Atualiza o endereço UDP do cliente
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
