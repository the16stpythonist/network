import network.commanding as protocol
import unittest
import socket
import random
import threading
import json
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


class TestForm(unittest.TestCase):

    std_title = "Test"
    std_body = "this is just a short body\nWith two rows\n"
    std_appendix = ["one", "two"]

    def test_init(self):
        """
        Testing the correct assignment of the attributes
        Returns:
        void
        """
        # Building the form
        form = protocol.Form(self.std_title, self.std_body, self.std_appendix)
        self.assertEqual(form.title, self.std_title)
        self.assertEqual(form.body, self.std_body)
        self.assertEqual(form.appendix, self.std_appendix)

    def test_body(self):
        """
        Testing the functionality of passing the Form a list as body and having it correctly transformed into a string
        Testing passing a list of none strings and having them correctly converted to strings
        Testing for the case of a really long list
        Returns:
        void
        """
        # Testing the turning of a list into a line separated string
        body_list = ["first line", "second line", "third line"]
        body_string = "first line\nsecond line\nthird line"
        form = protocol.Form(self.std_title, body_list, self.std_appendix)
        self.assertEqual(form.body, body_string)
        # Testing using other data types in the list to be the body
        body_list = [10, 11, 12]
        body_string = "10\n11\n12"
        form = protocol.Form(self.std_title, body_list, self.std_appendix)
        self.assertEqual(form.body, body_string)
        # Testing for having a really long list
        body_list = list(range(1, 10000, 1))
        body_string = '\n'.join(map(str, body_list))
        form = protocol.Form(self.std_title, body_list, self.std_appendix)
        self.assertEqual(form.body, body_string)

    def test_init_error(self):
        """
        Testing the correct exceptions in case faulty data is passed as parameters
        Returns:
        void
        """
        # Testing if the correct exceptions are risen in case a wrong param is passed
        with self.assertRaises(TypeError):
            protocol.Form(12, self.std_body, self.std_appendix)
        with self.assertRaises(ValueError):
            protocol.Form(self.std_title, 12, self.std_appendix)
        with self.assertRaises(ValueError):
            protocol.Form(self.std_title, self.std_body, b"{hallo")

    def test_appendix_json_basic(self):
        """
        Testing the turning of a dictionary into a json string as appendix
        Testing the loading of data from passing a json string
        Testing for a huge nested data structure
        Returns:
        void
        """
        appendix_dict = {"one": 1, "two": 2}
        # Testing the encoding process of the json encoder
        form = protocol.Form("hallo", ["hallo", "hallo"], appendix_dict,
                             appendix_encoder=protocol.JsonAppendixEncoder)
        appendix_encoded = protocol.JsonAppendixEncoder.encode(appendix_dict)
        self.assertEqual(form.appendix_encoded, appendix_encoded)
        # Testing the decoding process of the json encoder
        form = protocol.Form(self.std_title, self.std_body, appendix_encoded)
        self.assertEqual(form.appendix, appendix_dict)

    def test_appendix_pickle_basic(self):
        """
        Testing the encoding of the appendix using the pickle encoder
        Testing the decoding of the appendix using the pickle encoder
        Returns:
        void
        """
        appendix_dict = {"one": 1, "two": 2}
        # Testing the encoding process of the pickle encoder
        form = protocol.Form("hallo", self.std_body, appendix_dict,
                             appendix_encoder=protocol.PickleAppendixEncoder)
        appendix_encoded = protocol.PickleAppendixEncoder.encode(appendix_dict)
        self.assertEqual(form.appendix_encoded, appendix_encoded)
        # Testing the decoding process of the pickle encoder
        form = protocol.Form(self.std_title, self.std_body, appendix_encoded,
                             appendix_encoder=protocol.PickleAppendixEncoder)
        self.assertEqual(form.appendix, appendix_dict)

    def test_empty(self):
        """
        Testing the empty functionality correctly working
        Returns:
        void
        """
        # Testing in case an empty object is given as appendix
        form = protocol.Form('', '', [])
        self.assertTrue(form.empty)
        # Testing in case an empty string is given as appendix
        form = protocol.Form('', '', '')
        self.assertTrue(form.empty)
        # Testing in case the body is an empty list
        form = protocol.Form('', [], '')
        self.assertTrue(form)

    def test_valid(self):
        """
        Testing if the valid flag works correctly
        Returns:
        void
        """
        # Checking if the valid property is actually false with empty title
        form = protocol.Form('', self.std_body, self.std_appendix)
        self.assertFalse(form.valid)
        # A form should also be unvalid in case it is empty
        form = protocol.Form(self.std_title, '', '')
        self.assertFalse(form.valid)
        self.assertTrue(form.empty)

    def test_eq(self):
        """
        Tests the equal comparison of the form objects
        Returns:
        void
        """
        form1 = protocol.Form(self.std_title, self.std_body, self.std_appendix)
        form2 = protocol.Form(self.std_title, self.std_body, self.std_appendix)
        # Testing if the equal comparison is correctly used by the assert intern function of unittest
        self.assertEqual(form1, form2)
        # Testing if the equals operator works correctly
        self.assertTrue(form1 == form2)


class TestFormTransmission(unittest.TestCase):

    std_separation = "$separation$"
    std_port = 56777
    std_form = protocol.Form("Title", ["first", "second"], {"a": 1, "b": 2})
    dummy_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def test_adjust(self):
        """
        Testing the adjust option for the creation of the FormTransmissionThread. For adjust True the body is supposed
        to be changed, so that there is no collision of the body and the separation, if it is False a exception will
        be risen in case there is a collision
        Returns:
        void
        """
        separation = "hallo"
        title = "TITLE"
        body = ["first", "hallo", "second"]
        form = protocol.Form(title, body, '')
        # Double checking the validity function of the Form class
        self.assertTrue(form.valid)
        # Testing in case adjust is True if the body string gets modified correctly
        expected_body = "first\n hallo\nsecond"
        transmitter = protocol.FormTransmitterThread(self.dummy_socket, form, separation, adjust=True)
        self.assertEqual(transmitter.form.body, expected_body)
        # Testing for the exception in case the adjust was turned of
        with self.assertRaises(ValueError):
            form = protocol.Form(title, body, '')
            protocol.FormTransmitterThread(self.dummy_socket, form, separation, adjust=False)

    def test_basic(self):
        """
        Testing the basic functionality of the form transmission process and if the sockets used for the transmission
        can be recycled for another transmission
        Returns:
        void
        """
        socks = sockets()
        # Testing the basic functionality of the form transmission
        transmitter = protocol.FormTransmitterThread(socks[0], self.std_form, self.std_separation)
        receiver = protocol.FormReceiverThread(socks[1], self.std_separation)
        transmitter.start()
        receiver.start()
        # Waiting for the transmission to finish
        receiver.receive_form()
        self.assertEqual(receiver.form, self.std_form)
        # Testing if the sockets can be reused after the sending of one form
        transmitter = protocol.FormTransmitterThread(socks[1], self.std_form, self.std_separation)
        receiver = protocol.FormReceiverThread(socks[0], self.std_separation)
        transmitter.start()
        receiver.start()
        # Waiting for the transmission to finish
        receiver.receive_form()
        self.assertEqual(receiver.form, self.std_form)

    def test_empty_appendix(self):
        """
        Testing whether the transmission works correctly with an empty appendix
        Returns:
        void
        """
        socks = sockets()
        # Testing for the case that the appendix of the form is empty
        form = protocol.Form("title", ["first", "second"], '')
        transmitter = protocol.FormTransmitterThread(socks[0], form, self.std_separation)
        receiver = protocol.FormReceiverThread(socks[1], self.std_separation)
        transmitter.start()
        receiver.start()
        received_form = receiver.receive_form()
        self.assertEqual(form.appendix, received_form.appendix)

    def test_empty_body(self):
        """
        Testing whether the transmission works correctly with an empty body
        Returns:
        void
        """
        socks = sockets()
        form = protocol.Form("title", "", ["hallo"])
        transmitter = protocol.FormTransmitterThread(socks[0], form, self.std_separation)
        receiver = protocol.FormReceiverThread(socks[1], self.std_separation)
        transmitter.start()
        receiver.start()
        received_form = receiver.receive_form()
        self.assertEqual(form.body, received_form.body)
        self.assertEqual(form.appendix, received_form.appendix)

    def test_valid(self):
        """
        Testing whether the transmitter actually raises a error if it is about to send a invalid form
        Returns:
        void
        """
        with self.assertRaises(ValueError):
            # Creating an invalid form of the missing title kind
            form = protocol.Form('', "hallo", '')
            protocol.FormTransmitterThread(self.dummy_socket, form, self.std_separation)

    def test_long_body(self):
        """
        Testing if a long body string can be received correctly
        Returns:
        void
        """
        # Creating the long body
        body = []
        for i in range(1, 1000, 1):
            body.append("this is just some random text 123")
        # Creating the form with the long body and empty appendix
        form = protocol.Form("title", body, '')
        # Creating the sockets and the transmission objects
        socks = sockets()
        transmitter = protocol.FormTransmitterThread(socks[0], form, self.std_separation)
        receiver = protocol.FormReceiverThread(socks[1], self.std_separation)
        transmitter.start()
        receiver.start()
        # Waiting for the form to be received
        received_form = receiver.receive_form()
        self.assertEqual(form.body, received_form.body)

    def test_long_appendix(self):
        """
        Testing if a long appendix can be received correctly
        Returns:

        """
        # Creating the long appendix
        appendix = {}
        for i in range(1, 1000, 1):
            appendix["random key string" + str(i)] = "random text to be used as value"
        # Creating the form object with the long appendix
        form = protocol.Form("title", ["first", "second"], appendix)
        # Creating the sockets and the transmission objects
        socks = sockets()
        transmitter = protocol.FormTransmitterThread(socks[0], form, self.std_separation)
        receiver = protocol.FormReceiverThread(socks[1], self.std_separation)
        transmitter.start()
        receiver.start()
        # Waiting for the form to be received
        received_form = receiver.receive_form()
        self.assertEqual(form.appendix, received_form.appendix)


class TestCommandForm(unittest.TestCase):

    std_title = "COMMAND"
    std_body = ["command:print", "return:reply", "error:reply", "pos_arg:0"]
    std_appendix = {"pos_args": [], "kw_args": {}}

    def test_init(self):
        """
        Generally testing if the CommandForm object gets instanced correctly and if it correctly inherits from the base
        class CommandingForm
        Returns:
        void
        """
        command = protocol.CommandForm("print")
        self.assertIsInstance(command, protocol.CommandForm)
        self.assertEqual(command.title, "COMMAND")
        self.assertIsInstance(command, protocol.CommandingForm)

    def test_command_init(self):
        """
        This method tests if the command gets initialized correctly if it is based in the command specifications, which
        means passing the command name and the pos & kw args to the constructor
        Returns:
        void
        """
        pos_args = [12, "hallo"]
        kw_args = {"one": 2}
        command_name = "print"
        command_form = protocol.CommandForm(command_name, pos_args, kw_args)
        # Testing the attributes of the command form object itself
        self.assertEqual(command_form.command_name, command_name)
        self.assertEqual(command_form.pos_args, pos_args)
        self.assertEqual(command_form.key_args, kw_args)
        # Testing the form attributes created from the command data
        self.assertEqual(command_form.title, "COMMAND")
        # Testing for correct appendix
        appendix = {"pos_args": pos_args, "kw_args": kw_args}
        self.assertDictEqual(command_form.appendix, appendix)
        # Testing for correct body
        body = sorted(["command:print", "pos_args:2", "return:reply", "error:reply"])
        actual_body = sorted(command_form.body.split("\n"))
        self.assertListEqual(actual_body, body)

    def test_form_init(self):
        """
        This method tests for correct init if the CommandForm is created by passing Form
        Returns:

        """
        title = "COMMAND"
        body = ["command:print", "return:reply", "error:reply", "pos_args:2"]
        appendix = {"pos_args": ["hallo", "hallo"], "kw_args":{}}
        form = protocol.Form(title, body, appendix)
        # Creating the CommandForm from the Form object
        command_form = protocol.CommandForm(form)
        # Testing the parameters
        self.assertEqual(command_form.command_name, "print")
        self.assertEqual(command_form.return_handle, "reply")
        self.assertEqual(command_form.error_handle, "reply")
        self.assertListEqual(command_form.pos_args, ["hallo", "hallo"])

    def test_wrong_form_title(self):
        """
        Testing for TypeError in case of wrong form title
        Returns:
        void
        """
        # Testing fo a just slightly different title with lower case
        title = "Command"
        form = protocol.Form(title, self.std_body, self.std_appendix)
        with self.assertRaises(TypeError):
            protocol.CommandForm(form)
        # Testing for a different form title
        title = "RETURN"
        form = protocol.Form(title, self.std_body, self.std_appendix)
        with self.assertRaises(TypeError):
            protocol.CommandForm(form)

    def test_missing_param_body(self):
        """
        Testing if exceptions raised in case a parameter is missing in the body of the form
        Returns:
        void
        """
        # Creating the faulty form with the command name missing
        body = ["return:reply", "error:reply", "pos_args:0"]
        form = protocol.Form(self.std_title, body, self.std_appendix)
        with self.assertRaises(AttributeError):
            protocol.CommandForm(form)
        # Creating form with error spec missing
        body = ["return:reply", "command:print", "pos_args:0"]
        form = protocol.Form(self.std_title, body, self.std_appendix)
        with self.assertRaises(AttributeError):
            protocol.CommandForm(form)
        # Creating form with return spec missing
        body = ["error:reply", "command:print", "pos_args:0"]
        form = protocol.Form(self.std_title, body, self.std_appendix)
        with self.assertRaises(AttributeError):
            protocol.CommandForm(form)
        # Creating form with pos_args spec missing
        body = ["return:reply", "command:print", "error:reply"]
        form = protocol.Form(self.std_title, body, self.std_appendix)
        with self.assertRaises(AttributeError):
            protocol.CommandForm(form)
        # Testing for empty form
        form = protocol.Form(self.std_title, [], self.std_appendix)
        with self.assertRaises(AttributeError):
            protocol.CommandForm(form)