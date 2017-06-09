import threading
import socket
import time
import json

# UNIVERSAL


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
                data += character
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
        self.sock.sedall(data)

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


# THE FORM TRANSMISSION PROTOCOL


class Form:
    """
    GENERAL
    A form represents a special kind of data type, which imposes some restrictions as to what kind of data can be
    represented, but works directly with network protocols and can be transmitted more easily. A Form consists of the
    3 parts:
    - TITLE: The title is a single line string, that specifies the rough function of the form
    - BODY: The Body can be any kind of string block. It should be organized in new lines, as that is how it is being
      transmitted later on
    - APPENDIX: The appendix is supposed to represent the part of a message, which cannot be easily turned into a
      string, organized by newlines. This can be almost any data structure with the only limitation of being able to
      be turned into a json.
    The form is sort aof a base structure for communication, as the three parts of data can be used and assigned
    meaning by special protocols later on. The form objects just provide the blank skeleton of a message

    CONSTRUCTION
    A form object has to be passed the three arguments: title, body and appendix.
    The title has to be a single line string (which means, there cannot be a newline character in there). The body can
    either be a string all together or a list of items (which one has to be able to convert to strings) which are then
    internally being turned into the expected string structure.
    The appendix is special, if it is a string it is being interpreted as already being a json string and it is
    attempted to load the data, any other data type will be attempted to be converted into a json string!

    Attributes:
        title: The string title of the Form
        body: The string block, organized by new line characters
        appendix_json: The Json string of the data to be represented by the appendix
        appendix: The actual data object, described by the json string
    """
    def __init__(self, title, body, appendix):
        self.title = title
        self.body = body
        self.appendix = appendix
        self.appendix_json = None

        # Checking if the title is a string without a new line, as needed
        self.check_title()
        # Assuring, that the body is one single string, as it has to be
        self.evaluate_body()
        # Json the appendix in case it is raw data, attempting to load in case it is a string
        self.evaluate_appendix()

    def evaluate_body(self):
        """
        The body parameter can either be a string or a list of items (which have to be able to be turned into strings),
        but the objects needs the body property to be a string. Thus this method checks for the requirements of type
        etc. to match and turns the list into a string with newline seperation of the characters.
        Raises:
            TypeError: In case the body attribute is neither string nor list
            ValueError: In case the items of the list cannot be turned into a string
        Returns:
        None
        """
        # Checking the body attribute for the requirements
        self.check_body()
        if isinstance(self.body, list):
            # Since the body attribute has been checked, it is safe to assume every item can be converted into string
            body_string_map = map(str, self.body)
            body_string_list = list(body_string_map)
            # Producing a string, that separates the strings in this list by a newline character
            body_string = '\n'.join(body_string_list)
            # Setting the body to be the assembled
            self.body = body_string

    def evaluate_appendix(self):
        """
        The appendix can be anything, with the limitation, that it can be turned into a json string. In case that is
        possible this method will do that and assign the string to the appendix attribute.
        Raises:
            ValueError: In case the object cannot be turned into a json
        Returns:

        """
        # In case the appendix is a string it is being interpreted as already in json format and thus trying to unjson
        if isinstance(self.appendix, str):
            try:
                self.appendix_json = self.appendix
                self.appendix = json.loads(self.appendix_json)
            except ValueError as e:
                raise e
        # All other data types are interpreted as raw data and are being jsoned
        else:
            try:
                self.appendix_json = json.dumps(self.appendix)
            except ValueError as e:
                raise e

    @property
    def empty(self):
        """
        This property tells whether the form is empty, meaning both the appendix and the body being a empty string
        Returns:
        the boolean value of whether or not the body and the appendix are empty
        """
        return len(self.body) == 0 and len(self.appendix) == 0

    @property
    def valid(self):
        """
        This property tells whether or not the form qualifies as being valid. A form is invalid if either the title is
        a empty string or only whitespaces or the body and the appendix being completely empty (here a single whitespace
        would be valid)
        Returns:
        The boolean value of whether or not the form is valid
        """
        # stripped refers to as being stripped of all its whitespaces
        stripped_title = self.title.replace(" ", "")
        if len(stripped_title) == 0:
            return False
        elif self.empty:
            return False
        else:
            return True

    def check_attributes(self):
        """
        This function checks the attributes for correct data types.
        The body attribute has to be either one big string or a list of objects, that can be turned into strings. The
        title has to be a string without a newline character.
        Raises:
            TypeError
            ValueError
        Returns:
        void
        """
        # Checking the body and the title to be the correct data type
        self.check_body()
        self.check_title()

    def check_title(self):
        """
        This method will simply check the title attribute of the object for the correct type, which is supposed to be
        a string.
        Raises:
            TypeError: In case the title attribute is not a string
        Returns:
        void
        """
        if not isinstance(self.title, str):
            raise TypeError("The title has to be a string object")
        # Checking if the given string is one lined string
        else:
            if "\n" in self.title:
                raise ValueError("The title string has to be single line!")

    def check_body(self):
        """
        This method will simply check the attribute of the objects body property.
        The body can be one of the following data types:
        - A string
        - A list with strings or objects, that can be converted to strings
        Raises:
            TypeError: In case the objects in the list cannot be turned into strings, or are neither string nor list
        Returns:
        void
        """
        # The body being a string would be the most common case
        if not isinstance(self.body, str):
            if isinstance(self.body, list):
                # In case one item cannot be turned into a string, will be deleted
                for item in self.body:
                    try:
                        str(item)
                    except ValueError:
                        raise TypeError("The list for the body must only contain items, that can be strings")
            else:
                raise ValueError("The body attribute must either be a string or a list os strings")


class FormTransmitterThread(threading.Thread):
    """
    GENERAL
    This is a Thread. The Thread is supposed to be passed a socket, which has an already open connection to a Thread
    on the other side, which receives the Form data as a counterpart to this one. This Thread is used to transmit a
    Form object. The title of the form is being sent first and after that the individual lines of the forms string
    body are being transmitted before the separation (a special string, that can also be specified) is being sent with
    the length of the string of the forms appendix.
    In between each sending the receiving end is supposed to be sending an ACK message. In case the ACK is not sent in
    the specified amount of time for the timeout the communication is stopped.

    SEPARATION COLLISIONS:
    The separation string is supposed to be a definite sign, that the body of the form is now finished and that the
    appendix starts now. In case the separation string is already the front part of a line in the body of the form
    that would lead to an error. Through the 'adjust' parameter it can be set, that the body is being searched for
    occurances of the separation string and then adjusted, so that they would not be recognised, by adding a whitespace
    at the front of the line. In case the adjust is False, the body will be searched for the separation string and
    an exception risen in case one was found
    """
    def __init__(self, sock, form, separation, timeout=10, adjust=True):
        threading.Thread.__init__()
        # The form object to be transmitted over the socket connection
        self.form = form
        self.check_form()
        # The socket and the wrapped socket
        self.sock = sock
        self.sock_wrap = SocketWrapper(self.sock, True)
        # A string to be separating the body from the appendix
        self.separation = separation
        self.check_separation()

        if adjust:
            self.adjust_body_string()
        else:
            self.check_body_string()

        # The timeout of receiving the ack after a sending
        self.timeout = timeout
        # The state variables of the Thread and the transmission
        self.running = False
        self.finished = False

    def run(self):
        self.running = True
        self.send_title()
        self.send_body()
        self.send_appendix()

        # Updating the state variables
        self.running = False
        self.finished = True

    def send_body(self):
        """
        This method simply pushes the complete body string into the socket connection
        Returns:
        void
        """
        # Sending the individual lines of the body of the form over the socket
        body_string_lines = self.form.body.split("\n")
        for line in body_string_lines:
            self.sock_wrap.sendall(line+"\n")
            self.wait_ack()
        # Sending the separation at last
        separator = self.assemble_separator()
        self.sock_wrap.sendall(separator+"\n")
        self.wait_ack()

    def send_title(self):
        title = self.form.title
        self.sock_wrap.sendall(title)

    def send_appendix(self):
        """
        This method will send the appendix in form of the json string
        Returns:
        void
        """
        appendix_json = self.form.appendix_json
        self.sock_wrap.sendall(appendix_json)
        self.wait_ack()

    def wait_ack(self):
        """
        This method will wait and receive an ACK.
        Raises:
            TimeoutError: If the specified timeout error is exceeded while waiting for the ACK
        Returns:
        void
        """
        response = []
        start_time = time.time()
        time_delta = 0
        while response != ["a", "c", "k"]:
            if time_delta >= self.timeout:
                raise TimeoutError("Timeout exceeded, while waiting for ack")
            # Adding a character at the time to the response list
            response_character = self.sock_wrap.receive_length(1)
            response.append(response_character)
            # Calculating the time delta
            time_delta = time.time() - start_time

    def check_form(self):
        """
        This method checks the form attribute of the object. The form attribute has to be a Form object (whose class
        can be found in the very same module), additionally the Form object has to be valid, which is the case if it
        has a none empty body and appendix and a title none empty and not only whitespaces.
        Raises:
            TypeError: In case the form attribute is not a Form object
            ValueError: In case the Form object is not 'valid'
        Returns:
        void
        """
        if isinstance(self.form, Form):
            # In case it actually is a form, the form also has to be valid
            if not self.form.valid:
                raise ValueError("The passed Form object has to be valid")
        else:
            raise TypeError("The form attribute has to be a Form object")

    def check_separation(self):
        """
        Checks the separation attribute. The separation attribute has to be a string, which is None empty and a single
        line.
        Raises:
            TypeError: In case the separation attribute is not a string
            ValueError: In case the string is empty or the string has more than one line
        Returns:
        void
        """
        if isinstance(self.separation, str):
            # Checking for the possibility of a multi line separation string
            if "\n" in self.separation:
                raise ValueError("The separation has to be a one line string")
            # Checking for the possibility of a empty separation string
            stripped_separation = self.separation.replace(" ", "")
            if len(stripped_separation) == 0:
                raise ValueError("The separation has to be a None empty string")
        else:
            raise TypeError("The separation has to be a string")

    def check_body_string(self):
        """
        Checking the body string for a occurance of the separation string and raising an error in case the is a
        collision of the separation string in the body of the form
        Returns:
        void
        """
        form_body_string = self.form.body
        form_body_lines = form_body_string.split("\n")
        for i in range(len(form_body_lines)):
            if form_body_lines[i][:len(self.separation)] is self.separation:
                raise ValueError("There is a collision of the separation string in the form body")

    def assemble_separator(self):
        """
        This method will assemble the string to send as separation from the
        Returns:
        The string consisting of the separation string and the length of the appendix
        """
        appendix = self.form.appendix_json
        appendix_length = len(appendix.encode('utf-8'))
        return ''.join([self.separation, appendix_length])

    def adjust_body_string(self):
        """
        This method adjusts the body string of the form to transmit by appending a whitespace character to the front
        of all the lines, that match the separation string. If lines from the form body, this would cause an error
        in the loading of the appendix.
        Notes:
            This method assumes, that the separation and the form attribute of the object is correctly set, so this
            method is not to be called in before initializing those parameters
        Returns:
        void
        """
        form_body_string = self.form.body
        form_body_lines = form_body_string.split("\n")
        for i in range(len(form_body_lines)):
            if form_body_lines[i] is self.separation:
                form_body_lines[i] = " " + form_body_lines[i]
        form_body_string = "\n".join(form_body_lines)
        self.form.body = form_body_string


class FormReceiverThread(threading.Thread):

    def __init__(self, sock, separation, timeout=10):
        threading.Thread.__init__()
        # The socket and the wrapped socket
        self.sock = sock
        self.sock_wrap = SocketWrapper(self.sock, True)
        # A string to be separating the body from the appendix
        self.separation = separation

        # The timeout of receiving the ack after a sending
        self.timeout = timeout
        # The state variables of the Thread and the transmission
        self.running = False
        self.finished = False
        # The variable for the length of the appendix to receive
        self.appendix_length = None
        # All the variables holding the relevant values for the form object
        self.title = None
        self.body = None
        self.appendix = None
        self.form = None

    def run(self):
        pass

    def receive_title(self):
        """
        This method receives a single line and assigns that line as the title of the form. Because it does so, this
        method has to be called as the first method when beginning a form transmission.
        Returns:
        void
        """
        line = self.receive_line()
        self.title = line

    def receive_body(self):
        """
        This method will receive the body of the form, by receiving line for line until the separation line has been
        received. The separation line will then be processed into the length of the appendix and the received lines
        will be processed into the body string
        Returns:
        void
        """
        is_separation = False
        line_list = []
        line = None
        # Receiving new lines from the socket, until the separation line has been received
        while not is_separation:
            line = self.receive_line()
            is_separation = self.checkup_separation(line)
            if not is_separation:
                line_list.append(line)
        # If the while loop exits, that means the separation has been sent and is now the last line that was received
        # which means the string is still inside the line variable
        self.process_separation(line)

        # Assembling the line list into the body string and assigning it to the body
        body_string = '\n'.join(line_list)
        self.body = body_string

    def receive_appendix(self):
        """
        This method will receive the appendix data from the socket, by receiving exactly as many bytes as the length
        extracted from the separation string
        Returns:
        void
        """
        # Receiving as many bytes as the length was dictated by the separation string
        appendix_bytes = self.sock_wrap.receive_length(self.appendix_length, timeout=self.timeout)
        appendix_string = appendix_bytes.decode()
        self.appendix = appendix_string

    def receive_line(self):
        """
        This method will receive a line from the socket as a bytes string object and then turn the byte string back
        into a regular string, assuming the standard encoding
        Returns:
        The string line, received from the socket
        """
        line_bytes = self.receive_line_bytes()
        # Turning the bytes string back into a string, assuming the standard encoding
        line_string = line_bytes.decode()
        return line_string

    def receive_line_bytes(self):
        """
        This method will receive a line from the socket, it manages, by using the receive until character method from
        the socket wrapper object. The timeout of that method is set to be the timeout specified in the attribute of
        this object, although it has to be noted, that this timeout is used for the reception of every character
        Returns:
        The byte string of the line, that was received
        """
        line_bytes = self.sock_wrap.receive_until_character(b'\n', 1024, timeout=self.timeout)
        return line_bytes

    def process_separation(self, line):
        """
        This method will take the separation line, check it for its validity and in case it is correct extract the
        appendix length from the string and then assign this length to the length attribute of this object
        Args:
            line: the string line to be processed for the length of the appendix

        Returns:
        void
        """
        # Checking if this actaully is the separation string line
        self.check_separation(line)
        # Removing the actual separation string from the line
        length_string = line.replace(self.separation, "")
        length_string.strip()
        # Turning the string into a number
        length = int(length_string)
        # Assigning that length value to the designated attribute of this object
        self.appendix_length = length

    def check_separation(self, line):
        """
        This method checks, whether the passed object is a string and then also checks if that string is actually the
        separation string by calling the checkup method for the separation string. An exception will be risen in case
        either one of the conditions is not met.
        This method is used to assure, that the correct object is being used for further processing
        Raises:
            ValueError
            TypeError
        Args:
            line: The string line, which is supposed to be the separation string

        Returns:
        void
        """
        # Raising an error, in case the passed object is not a string or not the separation string
        if not isinstance(line, str):
            raise TypeError("The passed line is not even a string")
        if not self.checkup_separation(line):
            raise ValueError("The passed line is not the separation string")

    def checkup_separation(self, line):
        """
        This method checks whether the the passed line string is the separation line, that is meant to separate the
        body from the appendix and returns the boolean value of that being the case ot not
        Args:
            line: The string of the receuved line to check

        Returns:
        The boolean value of the line being the separation line or not
        """
        # The first condition of the line being the separation is it being longer than the sep string alone
        if len(line) > self.separation:
            separation_length = len(self.separation)
            if line[:separation_length] is self.separation:
                return True
        # In case one of the condifitions was not given, False is returned
        return False

    def send_ack(self):
        """
        This method simply sends a string with the ack to the transmitting end, wo signal, that the connection is still
        active
        Returns:
        void
        """
        self.sock_wrap.sendall("ack")

