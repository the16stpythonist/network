import threading
import pickle
import time
import json


# THE FORM TRANSMISSION PROTOCOL

class AppendixEncoder:
    """
    INTERFACE
    This is a base class acting as an interface for the different appendix encoder variations.
    The appendix encoder classes are supposed to be static classes implementing the two methods 'encode' and 'decode'
    with which the appendix of a form object can be encoded into a bytestring format, which can be transported over
    a network socket and then be decoded by a form object on the receiving end.

    Notes:
    The different encoder classes are supposed to provide more variance to what kind of objects can be transmitted as
    the appendix of the 'Form' class. Because these encoder classes are mainly used by the Form object to encode and
    decode the appendix objects, theses processes have to be designed for exactly that purpose.
    """
    def __init__(self):
        pass

    @staticmethod
    def encode(obj):
        """
        The encode method is supposed to take any object, that is valid for the specific implementation of the encoding
        and return the byte string representation.
        Args:
            obj: Any type of object, that can be encoded by the chosen method

        Returns:
        a string representation of that object
        """
        raise NotImplementedError("This method has to be overwritten")

    @staticmethod
    def decode(byte_string):
        """
        The decode method is supposed to take a string object and turn it back into the object, that was originally
        encoded using the same method
        Args:
            byte_string: The byte string, which is the encoded format of the received object

        Returns:
        Any kind of object, that was subject to the encoding process
        """
        raise NotImplementedError("This method has to be overwritten!")

    @staticmethod
    def is_serializable(obj):
        """
        This method is supposed to return a boolean value, that indicates whether the passed object can be serialized
        by the method of the specific encoder, which sub classes this base class of appendix encoding.
        Args:
            obj: The object to attempt

        Returns:
        The boolean value if the value can be serialized
        """
        raise NotImplementedError("This method has to be overwritten!")


class JsonAppendixEncoder(AppendixEncoder):

    @staticmethod
    def encode(obj):
        """
        This method will use the json dumps functionality to turn the iterable object given into a json string and
        then return the bytes representation of that string.
        Args:
            obj: Any kind of object, that is naturally json serializable, which is most of the python native iterables

        Returns:
        The byte string representation of the object
        """
        json_string = json.dumps(obj)
        byte_string = json_string.encode()
        return byte_string

    @staticmethod
    def decode(byte_string):
        """
        Thus method will use the json loads functionality to turn the byte string object given back into a string using
        the regular utf 8 decoding and then attempting to json load the original object from that string.
        Notes:
            In case the byte string obe
        Args:
            byte_string: The bytes object, that was originally a object encoded with json

        Returns:
        The object, stored as the byte string
        """
        # Turning the bytes back into the json string first
        json_string = byte_string.decode()
        # Adding the special case for an empty string
        if len(json_string.strip()) == 0:
            return []
        # Loading the json object from the string & returning
        obj = json.loads(json_string)
        return obj

    @staticmethod
    def is_serializable(obj):
        """
        Returns whether the passed object can be json serialized or not
        Args:
            obj: The object in question

        Returns:
        the boolean value
        """
        try:
            JsonAppendixEncoder.encode(obj)
            return True
        except:
            return False


class PickleAppendixEncoder(AppendixEncoder):
    """
    STATIC CLASS
    This is a subclass of the appendix encoder interface, therefore this class specifies the static methods 'encode',
    'decode' and 'is_serializable' to be used to encode the appendix data structures for Form objects.
    This class implements encoding by using the pickle module of python, thus it is able to encode and decode very
    complex data structures, which include all Python built in types and even custom class objects, but that also
    means that the encoding iss limited to a communication between two members operating python.

    Because the class is using pickle, the encoded data is non readable and on default of the bytes data type
    """
    @staticmethod
    def encode(obj):
        """
        This method uses the python native pickle dumps functionality to directly turn the given object into a byte
        string
        Args:
            obj: The object to convert

        Returns:
        The pickled byte string
        """
        byte_string = pickle.dumps(obj)
        return byte_string

    @staticmethod
    def decode(byte_string):
        """
        This method calls the pickle loads on the given byte string to load the encoded object
        Args:
            byte_string: The byte string representation of the encoded object

        Returns:
        The original object
        """
        obj = pickle.loads(byte_string)
        return obj

    @staticmethod
    def is_serializable(obj):
        """
        This method returns whether or not the object passed can be serialized by pickle
        Args:
            obj: The object in question

        Returns:
        boolean value
        """
        try:
            PickleAppendixEncoder.encode(obj)
            return True
        except:
            return False


class FormFrame:

    def __init__(self, title, body, appendix):
        self._title = title
        self._body = body
        self._appendix = appendix

    @property
    def valid(self):
        raise NotImplementedError()

    @property
    def empty(self):
        raise NotImplementedError()

    @property
    def title(self):
        raise NotImplementedError()

    @property
    def body(self):
        raise NotImplementedError()

    @property
    def appendix(self):
        raise NotImplementedError()

    def __eq__(self, other):
        raise NotImplementedError()

    def __str__(self):
        raise NotImplementedError()


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
    def __init__(self, title, body, appendix, appendix_encoder=JsonAppendixEncoder):
        self.title = title
        self.body = body
        self.appendix = appendix
        self.appendix_encoded = None
        self.appendix_encoder = appendix_encoder

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
        void
        """
        # In case the appendix is a string it is being interpreted as already in json format and thus trying to unjson
        if isinstance(self.appendix, bytes):
            try:
                # Attempting to use the encoder to encoder to decode the bytes string
                self.appendix_encoded = self.appendix
                appendix_decoded = self.appendix_encoder.decode(self.appendix_encoded)
                self.appendix = appendix_decoded
            except ValueError as value_error:
                raise value_error
            except TypeError as type_error:
                raise type_error
        # All other data types are interpreted as raw data and are being jsoned
        else:
            try:
                self.appendix_encoded = self.appendix_encoder.encode(self.appendix)
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

    @property
    def body_string(self):
        """
        This method will return the body in string format, as it would be written in the message itself.
        The method simply returns the value of the body attribute, as that already is the string
        Returns:
        The body string
        """
        return self.body

    @property
    def body_list(self):
        """
        This method will return the list rep of the body of the form, where this representation is basically just the
        body string split by the newline characters, which makes the list a list of individual lines of the body string
        EXAMPLE:
            The body:
            "hello:1
            test:2
            back:3"
            >>
            ["hello:1", "test:2", "back:3"]
        Returns:
        The line list of the body string
        """
        return self.body.split("\n")

    @property
    def title_string(self):
        """
        This method will return the title as a string format, by just returning the value of the title attribute, as
        that is already string by default
        Returns:
        The string title
        """
        return self.title

    @property
    def appendix_string(self):
        """
        This method will return the appendix of the form in a rather fancy string format (Which means, this is not how
        the dict would have been converted to string, but it is formatted to be human readable).
        EXAMPLE:
            A dict of {"hello2": 12.01, "test":complex(1, 2)} would look like:
            "{
            hello2: 12.01
            test: (1+2j)
            }"

        Returns:
        The formatted string of the appendix
        """
        string_list = ["{"]

        # Creating a line string for each item in the dictionary, by calling the string conversion on both the value
        # and the key and putting them as one string separated by one ":"
        for key, value in self.appendix.items():
            line_string = " {}: {}".format(str(key), str(value))
            string_list.append(line_string)

        # Assembling the list of the line strings into an actually line separated string all together
        string_list.append("}")
        appendix_string = '\n'.join(string_list)
        return appendix_string

    def __eq__(self, other):
        """
        The magic method for comparing two form objects. Two form objects are equal if the title, the body and the
        appendix are equal
        Args:
            other: The other Form object to test

        Returns:
        boolean value of whether or not they are equal
        """
        if isinstance(other, Form):
            same_title = other.title == self.title
            # List comprehension, where the order is irrelevant
            same_body = sorted(other.body_list) == sorted(self.body_list)
            same_appendix = other.appendix == self.appendix
            if same_title and same_body and same_appendix:
                return True
        return False

    def __str__(self):
        """
        This method will return a string representation of the form, which will be remotely human readable. The
        string will be structured as following:
        - The first line will be the title of the form
        - The following lines will be the lines of the body, just like they will actually be in the form
        - The appendix will be starting with the dict bracket "{" and the lines in between the closing brackets will
          be the items of the dict, on which the string conversion was called
        Returns:
        The string rep. of the form object
        """
        string_list = [self.title_string, self.body_string, self.appendix_string]
        return '\n'.join(string_list)


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
    ocurrances of the separation string and then adjusted, so that they would not be recognised, by adding a whitespace
    at the front of the line. In case the adjust is False, the body will be searched for the separation string and
    an exception risen in case one was found
    """
    def __init__(self, connection, form, separation, timeout=10, adjust=True):
        threading.Thread.__init__(self)
        # The form object to be transmitted over the socket connection
        self.form = form
        self.check_form()
        # The socket and the wrapped socket
        self.connection = connection
        # A string to be separating the body from the appendix
        self.separation = separation
        self.check_separation()

        if adjust:
            self.adjust_body_string()
        else:
            self.check_body_string()

        # The timeout of receiving the ack after a sending
        self.timeout = timeout
        self.exception = None
        # The state variables of the Thread and the transmission
        self.running = False
        self.finished = False

    def run(self):
        try:
            self.running = True
            self.send_title()
            self.wait_ack()
            self.send_body()
            self.wait_ack()
            self.send_appendix()
            self.wait_ack()

            # Updating the state variables
            self.running = False
            self.finished = True
        except Exception as exception:
            self.exception = exception

    def send_body(self):
        """
        This method simply pushes the complete body string into the socket connection
        Returns:
        void
        """
        # Sending the individual lines of the body of the form over the socket
        body_string_lines = self.form.body.split("\n")
        for line in body_string_lines:
            self.connection.sendall_string(line+"\n")
            self.wait_ack()
        # Sending the separation at last
        separator = self.assemble_separator()
        self.connection.sendall_string(separator+"\n")

    def send_title(self):
        title = self.form.title + "\n"
        self.connection.sendall_string(title)

    def send_appendix(self):
        """
        This method will send the appendix in form of the json string
        Returns:
        void
        """
        appendix_encoded = self.form.appendix_encoded
        self.connection.sendall_bytes(appendix_encoded)

    def wait_ack(self):
        """
        This method will wait and receive an ACK.
        Raises:
            TimeoutError: If the specified timeout error is exceeded while waiting for the ACK
        Returns:
        void
        """
        response = self.connection.receive_length_bytes(3, self.timeout)
        if not response == b'ack':
            raise ValueError("Incorrect ACK sent")

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
            if form_body_lines[i][:len(self.separation)] == self.separation:
                raise ValueError("There is a collision of the separation string in the form body")

    def assemble_separator(self):
        """
        This method will assemble the string to send as separation from the
        Returns:
        The string consisting of the separation string and the length of the appendix
        """
        appendix = self.form.appendix_encoded
        appendix_length = len(appendix)
        return ''.join([self.separation, str(appendix_length)])

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
            if form_body_lines[i][:len(self.separation)] == self.separation:
                form_body_lines[i] = " " + form_body_lines[i]
        form_body_string = "\n".join(form_body_lines)
        self.form.body = form_body_string

    def raise_exception(self):
        """
        In case the Thread has raised an exception, this exception will be saved in the designated 'exception'
        attribute of the Thread object. If there was an exception this method will simply raise it in the context
        where the method is being called. If there is no exception, this method will do simply nothing
        Returns:
        void
        """
        if self.exception is not None:
            raise self.exception


class FormReceiverThread(threading.Thread):

    def __init__(self, connection, separation, timeout=10):
        threading.Thread.__init__(self)
        # The socket and the wrapped socket
        self.connection = connection
        # A string to be separating the body from the appendix
        self.separation = separation

        # The timeout of receiving the ack after a sending
        self.timeout = timeout
        self.start_time = None
        self.exception = None
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
        # Catching every exception and in case there is one putting it into the attribute variable
        try:
            self.running = True
            self.receive_title()
            self.send_ack()
            self.receive_body()
            self.send_ack()
            self.receive_appendix()
            self.send_ack()
            self.assemble_form()
            self.running = False
            self.finished = True
        except Exception as exception:
            self.exception = exception

    def receive_form(self):
        """
        This method will be blocking until the finished flag of the object was set to True and then return the
        received form object
        Returns:
        The Form object received through the socket
        """
        while not self.finished:
            if self.exception is None:
                time.sleep(0.0005)
            else:
                self.raise_exception()
        return self.form

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
                # Sending the ack
                self.send_ack()
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
        appendix_bytes = self.connection.receive_length_bytes(self.appendix_length, timeout=self.timeout)
        appendix_string = appendix_bytes
        self.appendix = appendix_string

    def receive_line(self):
        """
        This method will receive a line from the socket as a bytes string object and then turn the byte string back
        into a regular string, assuming the standard encoding
        Returns:
        The string line, received from the socket
        """
        return self.connection.receive_line(self.timeout)

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

    def assemble_form(self):
        """
        This method will use all the data received through the socket and saved in the objects attributes to build a
        new form object.
        Raises:
            ValueError: In case the form has not been completely received yet
        Returns:
        void
        """
        # Checking if all the data has been received and if it is save to assemble a Form object from that data
        self.check_form()
        # Building the Form object from the received data
        form = Form(self.title, self.body, self.appendix)
        self.form = form

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

    def check_form(self):
        """
        This method checks if all the attribute of this object, that were supposed to contain the form data actually
        contain data other than None and thus checking if it is save to assemble a form object.
        Raises:
            ValueError
        Returns:
        void
        """
        if self.title is None or self.body is None or self.appendix is None:
            raise ValueError("The form data has not been completely received")

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
        if len(line) > len(self.separation):
            separation_length = len(self.separation)
            if line[:separation_length] == self.separation:
                return True
        # In case one of the conditions was not given, False is returned
        return False

    def send_ack(self):
        """
        This method simply sends a string with the ack to the transmitting end, wo signal, that the connection is still
        active
        Returns:
        void
        """
        self.connection.sendall_bytes(b"ack")

    def raise_exception(self):
        """
        In case the Thread has raised an exception, this exception will be saved in the designated 'exception'
        attribute of the Thread object. If there was an exception this method will simply raise it in the context
        where the method is being called. If there is no exception, this method will do simply nothing
        Returns:
        void
        """
        if self.exception is not None:
            raise self.exception
