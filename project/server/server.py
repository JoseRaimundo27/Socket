import socket
import threading
import logging

logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(message)s')

class Server:
    PORT_TCP = 8080
    PORT_UDP = 8081
    ADDR = '127.0.0.1'
    CLIENTS_TCP = {}  # Mapeia nomes de usuários aos sockets
    CLIENTS_UDP = set()

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
                if username in self.CLIENTS_TCP:
                    conn.sendall("Nome de usuário já em uso.".encode('utf-8'))
                    conn.close()
                    return
                self.CLIENTS_TCP[username] = conn
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
            del self.CLIENTS_TCP[username]

    def handleUDP(self):
        while True:
            try:
                data, addr = self.UDP.recvfrom(1024)
                if addr not in self.CLIENTS_UDP:
                    self.CLIENTS_UDP.add(addr)  # Adiciona o cliente à lista de conectados

                msg = data.decode('utf-8')
                if msg.startswith("/udp"):
                    sender, message = msg[5:].split(':', 1)  # Extrai o remetente e a mensagem
                    self.send_message_to_all(sender.strip(), message.strip())  # Retransmite para todos
            except Exception as e:
                logging.warning(f"Erro no UDP: {e}")

    def send_direct_message(self, sender, recipient, message):
        if recipient in self.CLIENTS_TCP:
            conn = self.CLIENTS_TCP[recipient]
            conn.sendall(f"[Privado de {sender}]: {message}".encode('utf-8'))
            logging.info(f"Mensagem privada de {sender} para {recipient}: {message}")
        else:
            logging.warning(f"Destinatário {recipient} não encontrado.")
            if sender in self.CLIENTS_TCP:
                self.CLIENTS_TCP[sender].sendall("Usuário não encontrado.".encode('utf-8'))

    def send_message_to_all(self, sender, message):
        for addr in self.CLIENTS_UDP:
            try:
                self.UDP.sendto(f"[{sender}]: {message}".encode('utf-8'), addr)
                logging.info(f"Mensagem global enviada de {sender} para {addr}: {message}")
            except Exception as e:
                logging.warning(f"Erro ao enviar mensagem UDP para {addr}: {e}")

if __name__ == "__main__":
    server = Server()
    server.start()
