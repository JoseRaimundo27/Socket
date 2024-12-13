import logging
import socket
import threading

logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(message)s')

class Server:
    PORT_TCP = 8080;
    PORT_UDP = 8081
    ADDR = '127.0.0.1'
    CLIENTS_TCP = []
    CLIENTS_UDP = []
       
    def start(self):
        TCP = socket.socket(socket.AF_INET, socket.SOCK_STREAM) #ipv4 e tcp
        UDP = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) #ipv4 e udp
        
        TCP.bind((self.ADDR,self.PORT_TCP))
        TCP.listen()
        logging.info(f"Servidor TCP iniciado em {self.ADDR}:{self.PORT_TCP}")
        
        UDP.bind((self.ADDR, self.PORT_UDP))
        logging.info(f"Servidor UDP inciado em {self.ADDR}:{self.PORT_UDP}")
        
        udp_thread = threading.Thread(target=self.handleUDP, args=(UDP,)) # thread para gerenciar multichat
        udp_thread.start()
        
        try:
            while True:
                conn, addr = TCP.accept()
                self.CLIENTS_TCP.append(conn)
                
                clientThread = threading.Thread(target=self.handleTCP, args=(conn,addr))
                clientThread.start()
                logging.info(f"Clientes ativos: {len(self.CLIENTS_TCP)}")
                
        except KeyboardInterrupt:
            logging.info("Servidor encerrando...")
        
        finally:
            for client in self.CLIENTS_TCP:
                client.close()
            TCP.close()
            
    
    def handleTCP(self, conn, addr):
        logging.info(f"Nova conexão de {self.ADDR}")
        
        try:
            while True:
                data = conn.recv(1024)
                if not data:
                    break
                
                logging.info(f"Recebido de {addr}: {data.decode('utf-8')}")
                conn.sendall(f"Server recebeu: {data.decode('utf-8')}".encode('utf-8'))
        except ConnectionResetError:
            logging.warning(f"Conexão perdida com {addr}")
        
        finally:
            conn.close()
            self.CLIENTS_TCP.remove(conn)
            logging.info(f"Conexão encerrada com {addr}")
            
    def handleUDP(self, UDP):
        logging.info("Thread UDP inciada")
        
        while True:
            data,addr = UDP.recvfrom(1024)
            if addr not in self.CLIENTS_UDP:
                self.CLIENTS_UDP.append(addr)
            
            logging.info(f"Mensagem UDP de {addr}:{data.decode('utf-8')}")
            
            for client_addr in self.CLIENTS_UDP:
                if (client_addr != addr):
                    UDP.sendto(data, client_addr) 
        
        
    
if __name__ == "__main__": 
    server = Server()
    server.start()
        