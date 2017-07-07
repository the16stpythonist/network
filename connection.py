import socket
import time



class SocketWrapper:
    """
    GENERAL
    This object wraps a socket connection and adds some additional functionality. A wrapped socket will be able to
    receive data until a certain character is received, only receive a certain length
    """
    def __init__(self, sock, connected):
        # Assigning the socket object to the variable
        self.sock = sock
        # The variable, which stores the state of the connection
        self.connected = connected
        # The properties, that describe the type of the socket
        self.family = None
        self.appoint_family()
        self.type = None
        self.appoint_type()

    def connect(self, ip, port, attempts, delay):
        """
        This method capsules the connect functionality of the wrapped socket. The method will try to connect to the
        specified address, trying that the specified amount of attempts.
        In case an already connected socket is already stored in the wrapper, this method will close and connect to the
        new address (in case that is possible obviously).
        In case the connection could not be established after the specified amount of attempts, the method will raise
        an ConnectionRefusedError!
        Args:
            ip: The string ip address of the target to connect to
            port: The integer port of the target to connect to
            attempts: The integer amount of attempts of trying to connect
            delay: The float amount of seconds delayed to the next attempt

        Returns:
        void
        """
        # Checking the data types for the inputs
        assert isinstance(ip, str), "ip is not a string"
        assert isinstance(port, int) and (0 <= port <= 65536), "The port is wrong type or value range"
        assert isinstance(attempts, int) and (0 <= attempts), "The attempts parameter is not the same value"
        # Assembling the port and the ip to the address tuple
        address = (ip, port)
        # Calling the connect of the socket as many times as specified
        while not self.connected:
            try:
                # Delaying the try possibly
                time.sleep(delay)
                # Attempting to build the connection
                self.sock.connect(address)
                # Updating the connected status to True
                self.connected = True
            except Exception as exception:
                # Closing the socket and creating a new one, which is gonna be used in the next try
                self.sock.close()
                self.sock = socket.socket(self.family, self.type)
                self.connected = False
                # Decrementing the counter for the attempts
                attempts -= 1

        # In case the loop exits without the connection being established
        if self.attempts == 0:
            raise ConnectionRefusedError("The socket could not connect to {}".format(address))

    def receive_until_character(self, character, limit, timeout=None, include=False):
        """
        This method receives data from the wrapped socket until the special 'character' has been received. The limit
        specifies after how many bytes without the termination character a Error should be raised. The timeout
        is the amount of seconds every individual byte is allowed to take to receive before raising an error. The
        include flag tells whether the termination character should be included in the returned data.
        Args:
            character: can either be an integer in the range between 0 and 255, that is being converted into a
                character or can be a bytes object/ bytes string of the length 1. After receiving this byte the data
                up to that point is returned.
            limit: The integer amount of bytes, that can be received without terminating, without raising an error.
            timeout: The float amount of seconds each individual byte is allowed to take to receive before a
                Timeout is raised.
            include: The boolean flag of whether to include the termination character in the return or not

        Returns:
        The data bytes, that were received up to the point, when the termination character was received
        """
        # Checking for the data type fo
        is_bytes = isinstance(character, bytes)
        is_int = isinstance(character, int)
        assert (is_bytes and len(character) == 1) or (is_int and 0 <= character <= 255)
        # In case the input is an integer converting it into a bytes object
        if is_int:
            character = int.to_bytes(character, "1", "big")

        counter = 0
        # Calling the receive length function with one byte at a time until the character in question appears
        data = b""
        while True:
            # Checking if the limit of bytes has been reched
            if counter > limit:
                raise OverflowError("The limit of bytes to receive until character has been reached")
            current = self.receive_length(1, timeout)
            if current == character:
                if include is True:
                    data += character
                # After the character has been found and eventually was added to the data, breaking the infinite loop
                break
            else:
                # In case the character is not there adding the byte to the counter and incrementing the counter
                data += current
                counter += 1
        return data

    def receive_line(self, limit, timeout=None):
        """
        This method simply calls the method for receiving until a character with the newline character to receive one
        line of data
        Args:
            limit:
            timeout:

        Returns:

        """
        return self.receive_until_character(b"\n", limit, timeout=timeout)

    def receive_length(self, length, timeout=None):
        """
        This method receives a certain amount of bytes from the socket object, that is being wrapped. It is also
        possible to specify the amount of time the method is supposed to wait for the next character to be received
        before issuing a timeout.
        Raises:
            EOFError: In case the data stream terminated before the specified amount of bytes was received
            ConnectionError: In case the socket object in question is not connected yet.
            TimeoutError: In case it took to long to receive the next byte
        Args:
            length: The integer amount of bytes to be received from the socket
            timeout: The float amount of time, that is tolerated for a byte to be received

        Returns:
        The bytes string of the data with the specified length, received from the socket
        """
        # First checking whether or not there actually is a callable socket within the 'connection' attribute, by
        # checking the 'connected' flag. In case there is not, will raise an exception
        if not self.connected:
            raise ConnectionError("There is no open connection to receive from yet!")

        start_time = time.time()
        data = b''
        while len(data) < length:
            # receiving more data, while being careful not accidentally receiving too much
            more = self.sock.recv(length - len(data))

            # In case there can be no more data received, but the amount of data already received does not match the
            # amount of data that was specified for the method, raising End of file error
            if not more:
                raise EOFError("Only received ({}/{}) bytes".format(len(data), length))

            # Checking for overall timeout
            time_delta = time.time() - start_time
            if (timeout is not None) and time_delta >= timeout:
                raise TimeoutError("{} Bytes could not be received in {} seconds".format(length, timeout))

            # Adding the newly received data to the stream of already received data
            data += more
        return data

    def sendall(self, data):
        """
        Simply wraps the 'sendall' method of the actual socket object.
        Raises:
            ConnectionError: In case the socket is not connected yet.
        Args:
            data: The data to be sent over the socket, best case would be bytes already, does not have to be though

        Returns:
        void
        """
        # Checking if the socket is already connected
        if not self.connected:
            raise ConnectionError("There is no open connection to send to yet!")
        # Actually calling the method of the socket
        if isinstance(data, bytes):
            self.sock.sendall(data)
        elif isinstance(data, str):
            self.sock.sendall(data.encode())
        else:
            raise TypeError("The data to send via socket has to be either string or bytes")

    def release_socket(self):
        """
        This method releases the socket from the wrapper, by setting the internal property to the socket to None and
        returning the wrapper
        Returns:
        The socket, that was used by the wrapper
        """
        # Removing the pointer to the socket from the object property and returning the socket
        sock = self.sock
        self.sock = None
        return sock

    def appoint_family(self):
        """
        This method simply sets the family attribute of the object to the same value as the family property of the
        socket, that is being wrapped
        Returns:
        void
        """
        self.family = self.sock.family

    def appoint_type(self):
        """
        this method simply sets the type property of the object to the same value as the type property of the
        socket, that is being wrapped.
        Returns:
        void
        """
        self.type = self.sock.type


class Connection:
    """
    ABSTRACT BASE CLASS

    GENERAL:
    One problem one might encounter with networking code is that while sockets are the most basic construct to be used
    and therefore also to be preferred as the basic building block of network code such as the form transmission
    protocol, the sockets might also not always works with other frameworks or even the platform the code is running on.
    A good example would be using Python with kivy on android, sockets themselves behave very problematic and as a
    developer your best choice is to use the twisted framework for network com. And if one wishes to use the protocol
    framework even then, all of the classes would have to be rewritten, but if a abstract encapsulation of the network
    such as the Connection objects would be used as the basic building block for the networking, the twisted
    functionality could simply be implemented and hidden behind a new type of Connection instance and the whole
    frameworks would still work.

    This abstract implementation also allows the protocol framework to be used in other fields as well, for example a
    Connection object could be build as a shared state between two Threads, or a Pipe between two processes. Even
    a really slow running communication based on emails could be capsuled to be managed by the protocol framework.

    The Connection object is build as something like a bidirectional socket, that implements behaviour for sending
    string data as well as receiving string and bytes data.
    """
    def __init__(self):
        pass

    def sendall_string(self, string):
        """
        A Connection object obviously has to implement the functionality of sending a string over the connection
        Args:
            string: The string to be sent to the the other side of the connection

        Returns:
        void
        """
        raise NotImplementedError()

    def sendall_bytes(self, bytes_string):
        """
        A Connection object also has to be able to send raw bytes data over the connection
        Args:
            bytes_string: The bytes string object to be sent

        Returns:
        void
        """
        raise NotImplementedError()

    def receive_length_string(self, length, timeout):
        """
        A Connection object has to be able to receive only a certain length of string from the communication
        Args:
            length: The amount of characters or the int length of the string supposed to be receuved from the
            connection.
            timeout: The float amount of time the reception of the string is allowed to take until a Timeout Error
                is being raised

        Returns:
        The received string
        """
        raise NotImplementedError()

    def receive_length_bytes(self, length, timeout):
        """
        A Connection object has to be able to receive bytes data of a certain (character-) length correctly
        Args:
            length: The amount of characters or the int length of the string supposed to be receuved from the
            connection.
            timeout: The float amount of time the reception of the string is allowed to take until a Timeout Error
                is being raised

        Returns:
        The received bytes string object
        """
        raise NotImplementedError()

    def wait_length_string(self, length):
        """
        The wait method is equal to the equally named receive method except for the fact, that it does not implement a
        timeout on purpose for situations where one wants to infinitely wait to receive from a connection.
        Args:
            length: The amount of characters or the int length of the string supposed to be receuved from the
            connection.

        Returns:
        The received string
        """
        raise NotImplementedError()

    def wait_length_bytes(self, length):
        """
        This method will be used to wait an indefinte amount of time for the reception of a byte string from the
        connection
        Args:
            length: The amount of characters or the int length of the string supposed to be receuved from the
            connection.

        Returns:
        the received byte string
        """
        raise NotImplementedError()

    def receive_line(self, timeout):
        """
        A Connection object has to be able to receive a line from the stream
        Args:
            timeout: The float amount of time the reception of the string is allowed to take until a Timeout Error
                is being raised
        Returns:
        A string up until a new_line character has been received from the connection
        """
        raise NotImplementedError()

    def receive_string_until_character(self, character, timeout):
        """
        A Connection object has to be able to receive a string until a special break character has been received
        Args:
            character: The string character with the length one, which is supposed to be received
            timeout: The float amount of time the reception of the string is allowed to take until a Timeout Error
                is being raised
        Raises:
            TimeoutError: In case the process of receiving exceeds the amount of time specified
        Returns:
        A string up until a special line character has been received
        """
        raise NotImplementedError()

    def receive_bytes_until_byte(self, byte, timeout):
        """
        This method will be used to receive a byte string until a special break character (also byte string) occurred
        in the stream
        Args:
            byte: The byte string character after which to return the received sub byte string
            timeout: The float amount of time the reception of the string is allowed to take until a Timeout Error
                is being raised

        Returns:
        The received byte string
        """
        raise NotImplementedError()

    def wait_string_until_character(self, character):
        """
        The wait method is equal to the equally named receive method except for the fact, that it does not implement a
        timeout on purpose for situations where one wants to infinitely wait to receive from a connection.
        Args:
            character: The character after which to return the substring up to that point

        Returns:
        The string received
        """
        raise NotImplementedError()

    def wait_bytes_until_byte(self, byte):
        """
        This method will be used to wait an indefinite amount of time until a special break byte string will be read
        from the stream and then return the byte string received up until then.
        Args:
            byte: The byte string object of length one after which the received is to be returned

        Returns:
        The received bytes string
        """
        raise NotImplementedError()

    @staticmethod
    def _check_timeout(timeout):
        """
        This is a utility method, that checks if a passed value for a timeout is actually a int or a float
        Raises:
            TypeError: If the specified timeout value is not a proper value of float or int type
        Args:
            timeout: The timeout value to check

        Returns:
        void
        """
        if not (isinstance(timeout, int) or isinstance(timeout, float)):
            raise TypeError("The timeout has to be a int value")

    @staticmethod
    def _check_character(character):
        """
        This is a utility method, that checks if a passed value for a character param is actually a string and also if
        that string actually has the length one
        Raises:
            TypeError: In case the passed value is not even a string
            ValueError: In case the passed string is not of the length one
        Args:
            character: The value to check

        Returns:
        void
        """
        if not isinstance(character, str):
            raise TypeError("The character has to be a string")
        if not len(character) == 1:
            raise ValueError("The character string has to be length one")

    @staticmethod
    def _check_byte(byte):
        """
        This is a utility function for checking if a passed byte parameter value actually is of the bytes type and has
        the required length one.
        Args:
            byte: The value to check

        Returns:
        void
        """
        if not isinstance(byte, bytes):
            raise TypeError("The byte param has to be a bytes string object")
        if not len(byte) == 1:
            raise ValueError("the byte param object has to be a byte string of the length one")

    @staticmethod
    def _check_length(length):
        """
        This is a utility function for checking if a passed value for the length of a string is actually a int value
        and if that value is positive.
        Args:
            length: The value in question

        Returns:
        void
        """
        if not isinstance(length, int):
            raise TypeError("The length parameter has to be int")
        if not length > 0:
            raise ValueError("The length has to be a positive value")


class SocketConnection(Connection):
    """
    This is a subclass of the Connection object and therefore a direct implementation of its abstract methods. This
    class uses the network communication via socket objects to ensure the receive/send functionlity guaranteed for
    a Connection object.
    """
    def __init__(self, sock):
        Connection.__init__(self)
        self.sock = sock

    def sendall_bytes(self, bytes_string):
        """
        This method is used to send a bytes string over the connection
        Args:
            bytes_string: The bytes string to send

        Returns:
        void
        """
        self.sock.sendall(bytes_string)

    def sendall_string(self, string):
        """
        This method is used to send a string over the connection
        Args:
            string: The string to be sent

        Returns:
        void
        """
        self.sendall_bytes(string.encode())

    def receive_line(self, timeout):
        """
        This method will receive one line from the connection, which means, the string until a new line character
        occurred.
        Args:
            timeout: The max amount of time for the reception

        Returns:
        The received string
        """
        return self.receive_string_until_character("\n", timeout)

    def receive_length_string(self, length, timeout):
        """
        This method will receive a specified length of string
        Args:
            length: The int length of the string to receive
            timeout: The max amount of time for the reception

        Returns:
        The received string
        """
        byte_string = self.receive_length_bytes(length, timeout)
        return byte_string.decode()

    def receive_length_bytes(self, length, timeout):
        """
        This method will receive a specified length of byte string
        Args:
            length: The length of the byte string to receive
            timeout: The max amount of time for the reception

        Returns:
        The received byte string
        """
        self._check_timeout(timeout)
        self._check_length(length)
        # Setting up the list wich will contain the data already received
        data = b''
        # Setting up the time for the timeout detection
        start_time = time.time()
        while len(data) < length:
            received = self.sock.recv(length - len(data))

            # Checking if there is nothing to receive anymore, before the specified amount was reached
            if not received:
                raise EOFError("Only received ({}|{}) bytes from the socket".format(len(bytes), bytes))

            # Checking for overall timeout
            time_delta = time.time() - start_time
            if time_delta > timeout:
                raise TimeoutError("{} Bytes could not be received in {} seconds".format(length, timeout))

            data += received

        return data

    def wait_length_string(self, length):
        """
        This method will wait an indefinite amount of time to receive a string of the specified length
        Args:
            length: The int length of the string to receive

        Returns:
        The received string
        """
        bytes_string = self.wait_length_bytes(length)
        return bytes_string.decode()

    def wait_length_bytes(self, length):
        """
        This method will wait an indefinite amount of time to receive a bytes string of the specified length
        Args:
            length: The length of the byte string to receive

        Returns:
        The received byte string
        """
        self._check_length(length)
        # Setting up the list which will contain the data already received
        data = b''
        while len(data) < length:
            received = self.sock.recv(length - len(data))

            # Checking if there is nothing to receive anymore, before the specified amount was reached
            if not received:
                raise EOFError("Only received ({}|{}) bytes from the socket".format(len(bytes), bytes))

            data += received

        return data

    def receive_string_until_character(self, character, timeout):
        """
        This function will receive from the socket until the specified break character has been read in the stream.
        After that the substring, that has been received up until that point will be returned
        Args:
            character: the string break character
            timeout: The max amount of time for the reception

        Returns:
        The received string
        """
        self._check_character(character)
        byte_character = character.encode()
        bytes_string = self.receive_bytes_until_byte(byte_character, timeout)
        return bytes_string.decode()

    def receive_bytes_until_byte(self, byte, timeout):
        """
        This function will receive the bytes string and return the sub string until a special break byte character
        has occurred in the stream
        Args:
            byte: The byte string character after which to return the sub string before
            timeout: The max time for the reception

        Returns:
        The received bytes string
        """
        # Raising error in case wrong values have been passed as parameters
        self._check_byte(byte)
        self._check_timeout(timeout)
        # Setting up for the timeout watch
        start_time = time.time()
        # The list of byte string data, which is later going to contain the string to return
        data = []
        # The temporary string received
        received = b''
        while byte != received:
            received = self.sock.recv(1)

            # Checking if there is nothing to receive anymore, before the specified amount was reached
            if not received:
                raise EOFError("Only received ({}|{}) bytes from the socket".format(len(bytes), bytes))

            # Checking for overall timeout
            time_delta = time.time() - start_time
            if time_delta > timeout:
                raise TimeoutError("Bytes could not be received in {} seconds".format(timeout))

            data.append(received)
        # Removing the break character from the data list
        data.pop(-1)
        # Returning the assembled bytes string
        return b''.join(data)

    def wait_string_until_character(self, character):
        """
        This method will wait an indefinite amount of time until the break character has been received and then
        return the sub strung received up to that point
        Args:
            character: The string character to act as breaking point in the reception

        Returns:
        The received string
        """
        self._check_character(character)
        byte_character = character.encode()
        bytes_string = self.wait_bytes_until_byte(byte_character)
        return bytes_string.decode()

    def wait_bytes_until_byte(self, byte):
        """
        This method will wait an indefinite amount of time until the break byte character has been received and then
        return the sub string received up to that point.
        Args:
            byte: The byte string character

        Returns:
        The received byte string
        """
        # Raising error in case wrong values have been passed as parameters
        self._check_byte(byte)
        # The list of byte string data, which is later going to contain the string to return
        data = []
        # The temporary string received
        received = b''
        while byte != received:
            received = self.sock.recv(1)

            # Checking if there is nothing to receive anymore, before the specified amount was reached
            if not received:
                raise EOFError("Only received ({}|{}) bytes from the socket".format(len(bytes), bytes))

            data.append(received)
        # Removing the break character from the data list
        data.pop(-1)
        # Returning the assembled bytes string
        return b''.join(data)