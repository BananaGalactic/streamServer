import socket, threading
import logging
import os, sys

CHUNK = 1024
logPath = os.path.join(os.getcwd(),"Log")
fileName = "server"

logFormatter = logging.Formatter("%(asctime)s [%(threadName)-12.12s] [%(levelname)-5.5s]  %(message)s",datefmt='%m/%d/%Y %I:%M:%S %p')
rootLogger = logging.getLogger()
rootLogger.setLevel(logging.DEBUG)

fileHandler = logging.FileHandler("{0}/{1}.log".format(logPath, fileName))
fileHandler.setFormatter(logFormatter)
rootLogger.addHandler(fileHandler)

consoleHandler = logging.StreamHandler(sys.stdout)
consoleHandler.setFormatter(logFormatter)
rootLogger.addHandler(consoleHandler)

class ClientThread(threading.Thread):
    def __init__(self,clientAddress,dict_of_clients, clientData,running):
        threading.Thread.__init__(self)
        
        self.clientAddress = clientAddress
        self.clients_dict = dict_of_clients
        self.csocket = self.clients_dict[self.clientAddress]
        self.csocket.settimeout(5)
        self.receivedBytes = 0
        self.running = running
        self.clientData = clientData

    def run(self):
        self.client_thread = threading.current_thread().name
        logging.info("{} started for {}".format(self.client_thread,self.clientAddress))
        #print ("Connection from : ", clientAddress)
        #self.csocket.send(bytes("Hi, This is from Server..",'utf-8'))
        data = b''
        while self.running:
            try:
                while len(data) != CHUNK:
                    data += self.csocket.recv(CHUNK)
                
            except socket.timeout:
                    pass
            except ConnectionResetError:
                break
            else:
                dataSize = len(data)
                #print("broadcastin {} bytes from {}".format(dataSize,self.clientAddress))
                serverThread.broadcastWithoutMe(data,self.csocket,enc=False)
                #serverThread.broadcastToAll(data,enc=False)
                self.receivedBytes += dataSize
                self.clientData[self.clientAddress] = self.receivedBytes
                   

        logging.info("Client at {} disconnected...".format(self.clientAddress))
        #serverThread.onDisconnect(self.csocket,self.clientAddress)
        del(self.clients_dict[self.clientAddress])
        self.csocket.close()


class ThreadedServer(threading.Thread):
    def __init__(self, address="127.0.0.1", port=8080, queueClient = 2, blocking = 1):
        threading.Thread.__init__(self)
        self.address = address
        self.port = port
        self.queueClient = queueClient
        self.blocking = blocking
        self.clients_dict = {}
        self.clients_data = {}
        
        self.server_socket = self.init_socket((self.address,self.port),self.queueClient)
        self.running = True
        #logging.info("Listening at {}:{}".format(self.address, self.port))

    def init_socket(self, address, queueClient):
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.settimeout(5)
        server.setblocking(self.blocking)
        server.bind(address)
        server.listen(queueClient)
        return server

    def run(self):
        self.server_thread = threading.current_thread().name
        logging.info("Init socket on {} OK".format(self.server_thread))

        while self.running:
            logging.info('Waiting for client')
            try:
                
                clientsock, clientAddress = self.server_socket.accept()
                #self.onConnect(clientsock, clientAddress)
            except OSError:
                logging.info("Server socket closed")
            else:
                logging.info("New client connected")
                self.clients_dict[clientAddress] = clientsock
                self.clients_data[clientAddress] = 0
                
                newthread = ClientThread(clientAddress, self.clients_dict, self.clients_data, self.running)
                newthread.daemon = True
                newthread.start()

    def onConnect(self,sock, addr):
        logging.info("Broadcasting incomer {}".format(addr))
        self.broadcastWithoutMe("{} join the room".format(addr),sock)

    def onDisconnect(self,sock,addr):
        logging.info("Broadcasting leaver {}".format(addr))
        self.broadcastWithoutMe("{} left the room".format(addr),sock)

    def broadcastWithoutMe(self,msg,sock,enc=True):
        dico = self.clients_dict.copy()
        for add, soc in dico.items():
            #print(add, soc)
            if soc is not sock:
                if enc == True:
                    soc.send(msg.encode())
                else:
                    try:
                        soc.send(msg)
                    except socket.timeout:
                        print("timeout on broadcast to {}".format(add))
                    
                    except ConnectionResetError:
                        print("error on broadcast to {}".format(add))
        

    def broadcastToAll(self,msg,enc=True):
        dico = self.clients_dict.copy()
        for add, soc in dico.items():
            if enc == True:
                soc.send(msg.encode())
            else:
                try:
                    soc.send(msg)
                except socket.timeout:
                    print("timeout on broadcast to {}".format(add))
                  
                except ConnectionResetError:
                    print("error on broadcast to {}".format(add))

    def print_clients_infos(self):
        print("")
        print("Client infos | Total connected client : {}".format(len(self.clients_data)))
        print("********************************************")
        print("Connected client")
        for client in self.clients_dict:
                    print("{}".format(client))
        print("--------------------------------------------")
        print("Clients data received")
        for client, dataSize in self.clients_data.items():
                    print("{} sent {} bytes.".format(client, dataSize))
        print("")
            

    def close(self):
        self.running = False
        #print(self.clients_dict)
        for address, client_sock in self.clients_dict:
            try:
                client_sock.close()
            except Exception as e:
                pass
                #print(e)
        self.server_socket.close()
        logging.info("Bye")


if __name__ == "__main__":
    

    logging.info("Starting server Thread")
    serverThread = ThreadedServer(address='192.168.1.10', port=10000, blocking=1)
    serverThread.daemon = True
    serverThread.start()
    logging.info("Starting console on {}".format(threading.current_thread().name))
    while True:
        cmd = input()
        if cmd == "stop":
            serverThread.close()
            break
        elif cmd == "info":
            serverThread.print_clients_infos()
        elif cmd == "restart":
            serverThread.close()
            serverThread = ThreadedServer(address='192.168.1.10', port=10000, blocking=1)
            serverThread.daemon = True
            serverThread.start()
        elif "say" in cmd:
            msg = cmd.split(" ")[1]
            serverThread.broadcastToAll("SERVER : {}".format(msg))