from network.connection import SocketConnection

import threading
import random
import socket
import time


def open_port():
    """
    This function will return an open network port
    Returns:
    the integer port number of the open port
    """
    # Choosing the port random in the upper port range
    port = random.randint(30000, 60000)
    result = 0
    while result == 0:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        address = ('127.0.0.1', port)
        # attempting to connect to the server, in case not possible, there is no socket on the port -> port is free
        result = sock.connect_ex(address)
        port = random.randint(30000, 60000)
    # Returning the found free port
    return port


def sockets(port=None):
    """
    This function wraps the functionality of the SockGrab class, by returning a pair of connected sockets
    Args:
        port:

    Returns:
    a tuple of connected sockets, where the first one is the one that was returned by the accepted server connection
    and the second one the actively requesting a connection
    """
    # Setting the port to any open port in case no special one specified
    if port is None:
        port = open_port()

    sock_grab = SockGrab(port)
    sock_grab.start()
    return sock_grab.sockets()


def connections(port=None):
    sock1, sock2 = sockets(port)
    # Creating SocketConnection objects from these sockets
    return SocketConnection(sock1), SocketConnection(sock2)


class SockGrab(threading.Thread):
    """
    This is a utility class, which will open a server socket at the given port and then simply wait for the first
    incoming connection and then assign the bound socket, which is the result of this first established connection to
    the internal 'connection' attribute, where it can be grabbed for further use.
    """
    def __init__(self, port):
        threading.Thread.__init__(self)
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.address = ('127.0.0.1', port)
        self.connector = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.connection = None

    def run(self):
        """
        The main method of the Thread, which will be called after the Thread was started. This will simply define the
        internal socket object as a server and wait for a connection, which it then assigns to the connection attribute
        Returns:
        void
        """
        self.sock.bind(self.address)
        self.sock.listen(2)
        self.connection, address = self.sock.accept()

    def sockets(self):
        """
        This method returns the pair of connected sockets.
        Returns:
        The
        """
        # Connecting the connector
        self.connect()
        # Waiting for the corresponding socket was accepted in the server socket
        self.get_connection()
        return self.connection, self.connector

    def get_connection(self):
        """
        This method is used to get the connected server socket from the Thread. The method will be blocking until the
        connection attribute is assigned the connected socket from the server accepting or the timeout of waiting one
        second has been exceeded
        Raises:
            TimeoutError: In case, that even one second after the method was called, the socket was sill not assigned
                to the connection attribute of this object
        Returns:
        The socket object, that was given by the server for the established connection
        """
        start_time = time.time()
        while self.connection is None:
            delta = time.time() - start_time
            if delta > 1:
                raise TimeoutError("Connection problems in testing")
        return self.connection

    def connect(self):
        """
        This method will simply connect the internal connector socket to the server. Thus it has to be called only
        after the Thread has been started
        Returns:
        void
        """
        self.connector.connect(self.address)
