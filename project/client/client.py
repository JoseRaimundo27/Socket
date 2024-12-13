import socket
import threading
import logging

logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(message)s')

class Client:
    SERVER_ADDR = '127.0.0.1'
    PORT_TCP = 8080
    PORT_UDP= 8081
    
    def __init__(self):
        self.TCP = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.UDP = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        
    def start(self):
        try:
            self.TCP.connect((self.SERVER_ADDR,self.PORT_TCP))
            logging.info(f"Conectando ao servidor TCP em {self.SERVER_ADDR}:{self.PORT_TCP}")
            
            udpThread = threading.Thread(target=self.receiveUDP)
            udpThread.start()
            
            tcpThread = threading.Thread(target=self.receiveTCP)
            tcpThread.start()
            
            while True:
                message = input("Digite sua mensagem (use /udp para chat em grupo) \n")
                
                if message.startswith("/udp"):
                    udpMessage = message[5:] # Remove o prefixo /udp
                    self.UDP.sendto(udpMessage.encode('utf-8') , (self.SERVER_ADDR,self.PORT_UDP))
                    
                else:
                    #Envia via tcp
                    self.TCP.sendall(message.encode('utf-8'))
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
                    logging.info(f"[TCP] Mensagem recebida: {data.decode('utf-8')}")
            except ConnectionResetError:
                logging.warning("Conexão TCP perdida.")
                break
            
            
    def receiveUDP(self):
        self.UDP.bind(("",self.PORT_UDP)) #vincula a um porto local aleatorio
        while True:
            try:
                data = self.UDP.recvfrom(1024)
                logging.info(f"[UDP] Mensagem recebida: {data.decode('utf-8')}")
            
            except Exception as e:
                logging.warning(f"Erro ao receber mensagem UDP: {e}")
                break

if __name__ == "__main__":
    client = Client()
    client.start()