# Chat com Sockets TCP e UDP

Este projeto implementa um sistema de chat com suporte a comunicações privadas (via TCP) e comunicações globais (via UDP). O servidor gerencia conexões simultâneas e registra usuários, enquanto os clientes podem trocar mensagens privadas ou enviar mensagens globais para todos os usuários conectados.

## Funcionalidades

- **Comunicação Privada (TCP):** Envio de mensagens privadas de um cliente para outro, utilizando conexões seguras por TCP.
- **Comunicação Global (UDP):** Envio de mensagens que são retransmitidas para todos os clientes conectados ao servidor, utilizando o protocolo UDP.
- **Registro de Usuários:** Cada cliente registra um nome de usuário único ao se conectar ao servidor.
- **Gerenciamento Centralizado:** O servidor mantém uma única estrutura para rastrear clientes e suas conexões TCP e UDP.

## Estrutura do Projeto

### Diretórios principais:

- `server/`
  - `server.py`: Código do servidor que gerencia conexões TCP e UDP.
- `client/`
  - `client.py`: Código do cliente que permite enviar e receber mensagens.
- `utils/`: Diretório reservado para futuras implementações utilitárias.

### Tecnologias utilizadas:

- Python
- Sockets (TCP/UDP)
- Multithreading para suportar múltiplas conexões simultâneas.
- Criptografia (AES)

## Como Usar

### Requisitos

- Python 3.x instalado.
- Uma máquina local ou rede onde clientes e servidor possam se comunicar.

### Instruções para Executar

1. **Inicie o Servidor:**
   Navegue até o diretório `server/` e execute o arquivo `server.py` para iniciar o servidor.

   ```bash
   cd server
   python server.py
   ```

2. **Inicie os Clientes:**
   Em outro terminal (ou máquina), navegue até o diretório `client/` e execute o arquivo `client.py` para iniciar um cliente. Ao iniciar, o cliente pediraá um nome de usuário para registro.

   ```bash
   cd client
   python client.py
   ```

3. **Envie Mensagens:**
   No prompt do cliente, você pode:

   - Enviar mensagens globais:
     Use o comando `/udp` seguido da mensagem para enviá-la a todos os usuários conectados.

     ```
     /udp Esta mensagem será enviada a todos os usuários conectados.
     ```

   - Enviar mensagens privadas:
     Use o comando `/tcp` seguido do nome do destinatário e da mensagem.

     ```
     /tcp <nome_destinatario> Esta mensagem é privada.
     ```

| **Protocolo** | **Aplicação**           | **Vantagens**                                                                                      |
|---------------|-------------------------|----------------------------------------------------------------------------------------------------|
| **TCP**       | Mensagens privadas      | Conexão confiável, entrega garantida, ordem preservada, ideal para conversas entre dois usuários.  |
| **UDP**       | Mensagens globais       | Comunicação rápida e eficiente para vários clientes, adequado para mensagens não críticas.         |

### Exemplos de Uso

#### Comunicação Global (UDP):

Cliente A:
```
Digite sua mensagem (/udp para chat em grupo, /tcp <destinatário> para mensagem direta):
/udp Olá, todos!
```

Todos os clientes conectados recebem:
```
[UDP] A: Olá, todos!
```

#### Comunicação Privada (TCP):

Cliente A:
```
Digite sua mensagem (/udp para chat em grupo, /tcp <destinatário> para mensagem direta):
/tcp B Olá, B!
```

Apenas o Cliente B recebe:
```
[TCP] Privado de A: Olá, B!
```

## TO DO

- Transferência de arquivos entre clientes.
- Colocar 0.0.0.0 no servidor ( para escutar) e o ip do servidor no cliente!
