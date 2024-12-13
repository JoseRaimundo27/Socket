import socket
import threading
import logging

logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(message)s')

class Client:
    SERVER_ADDR = '127.0.0.1'
    PORT_TCP = 8080
    PORT_UDP = 8081

    def __init__(self):
        self.username = input("Digite seu nome de usuário: ")
        self.TCP = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.UDP = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.UDP.bind(("", 0))  # Porta local aleatória para receber mensagens UDP

    def start(self):
        try:
            self.TCP.connect((self.SERVER_ADDR, self.PORT_TCP))
            logging.info(f"Conectado ao servidor TCP em {self.SERVER_ADDR}:{self.PORT_TCP}")

            # Enviar nome de usuário para o servidor
            self.TCP.sendall(f"/register {self.username}".encode('utf-8'))

            udp_thread = threading.Thread(target=self.receiveUDP, daemon=True)
            udp_thread.start()

            tcp_thread = threading.Thread(target=self.receiveTCP, daemon=True)
            tcp_thread.start()

            while True:
                message = input("Digite sua mensagem (/udp para chat em grupo, /tcp <destinatário> para mensagem direta):\n")

                if message.startswith("/udp"):
                    udp_message = message[5:]  # Remove o prefixo /udp
                    full_message = f"/udp {self.username}: {udp_message}"
                    self.UDP.sendto(full_message.encode('utf-8'), (self.SERVER_ADDR, self.PORT_UDP))

                elif message.startswith("/tcp"):
                    try:
                        _, recipient, tcp_message = message.split(' ', 2)  # Formato: /tcp <destinatário> <mensagem>
                        full_message = f"/tcp {recipient} {self.username}: {tcp_message}"
                        self.TCP.sendall(full_message.encode('utf-8'))
                    except ValueError:
                        logging.warning("Formato de mensagem inválido. Use: /tcp <destinatário> <mensagem>")
                    except Exception as e:
                        logging.warning(f"Erro ao enviar mensagem TCP: {e}")

                else:
                    logging.warning("Comando não reconhecido. Use /udp ou /tcp.")

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
                    logging.info(f"[TCP] {data.decode('utf-8')}\n")
            except ConnectionResetError:
                logging.warning("Conexão TCP perdida.")
                break

    def receiveUDP(self):
        while True:
            try:
                data, addr = self.UDP.recvfrom(1024)
                if data:
                    logging.info(f"[UDP] {data.decode('utf-8')}")
            except Exception as e:
                logging.warning(f"Erro ao receber mensagem UDP: {e}")
                break

if __name__ == "__main__":
    client = Client()
    client.start()
