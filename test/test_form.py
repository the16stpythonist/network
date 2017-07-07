"""
This is the test module for testing the functionality, that is contained within the "test" module of the network
project.
"""
from network.form import AppendixEncoder
from network.form import PickleAppendixEncoder
from network.form import JsonAppendixEncoder

from network.form import Form

import unittest


class TestEncoder(unittest.TestCase):

    def _test(self, encoder, obj):
        # test if the encoder is actually an encoder
        #self._test_is_appendix_encoder(encoder)
        # Test if the object returns True for being able to be encoded
        self._test_is_serializable(encoder, obj)
        # Test if the encoding and decoding is correct
        self._test_encode(encoder, obj)

    def _test_is_appendix_encoder(self, encoder):
        """
        This method will run the test of the given object being a subclass if the appendix encoder
        Args:
            encoder: The AppendixEncoder subclass to be checked

        Returns:
        void
        """
        self.assertIsInstance(encoder, AppendixEncoder)

    def _test_is_serializable(self, encoder, obj):
        """
        This method runs the method if the obj can be encoded with the given encoder and checks if the bool return is
        True for the assert
        Args:
            encoder: The AppendixEncoder subclass to check
            obj: The object to be tested

        Returns:
        void
        """
        is_able = encoder.is_serializable(obj)
        self.assertTrue(is_able)

    def _test_encode(self, encoder, obj):
        """
        This method encodes the given object, tests if this encoded version is really a bytes type and then test if
        the decoded version is the same as the original
        Args:
            encoder: The AppendixEncoder subclass to use
            obj: The object to encode

        Returns:
        void
        """
        encoded = encoder.encode(obj)
        self.assertIsInstance(encoded, bytes)
        decoded = encoder.decode(encoded)
        if isinstance(obj, list):
            self.assertListEqual(obj, decoded)
        elif isinstance(obj, dict):
            self.assertDictEqual(obj, decoded)
        else:
            self.assertEqual(obj, decoded)


class TestJsonAppendixEncoder(TestEncoder):

    encoder = JsonAppendixEncoder

    def test_encode_string(self):
        test_string = "Hallo"
        self._test(self.encoder, test_string)

    def test_encode_long_string(self):
        test_string = "hallo this is a rather long string to begin with... " * 1000
        self._test(self.encoder, test_string)

    def test_encode_int(self):
        test_int = 1234 * 9833
        self._test(self.encoder, test_int)

    def test_encode_float(self):
        test_float = 123.4859 * 2348.982
        self._test(self.encoder, test_float)

    def test_encode_list(self):
        test_list = ["hallo", 1748, 87.927]
        self._test(self.encoder, test_list)

    def test_encode_long_list(self):
        test_list = []
        for i in range(9000):
            test_list.append("This is a very long string already and there will be a int a a sublist also")
            test_list.append(["hallo"])
            test_list.append(98707 * 12345)
        self._test(self.encoder, test_list)

    def test_encode_dict(self):
        test_dict = {"hallo": ["hallo, 12"], "Wort": {"hallo": []}}
        self._test(self.encoder, test_dict)


class TestPickleAppendixEncoder(TestEncoder):

    encoder = PickleAppendixEncoder

    def test_encode_string(self):
        test_string = "Hallo"
        self._test(self.encoder, test_string)

    def test_encode_long_string(self):
        test_string = "hallo this is a rather long string to begin with... " * 1000
        self._test(self.encoder, test_string)

    def test_encode_int(self):
        test_int = 1234 * 9833
        self._test(self.encoder, test_int)

    def test_encode_float(self):
        test_float = 123.4859 * 2348.982
        self._test(self.encoder, test_float)

    def test_encode_list(self):
        test_list = ["hallo", 1748, 87.927]
        self._test(self.encoder, test_list)

    def test_encode_long_list(self):
        test_list = []
        for i in range(9000):
            test_list.append("This is a very long string already and there will be a int a a sublist also")
            test_list.append(["hallo"])
            test_list.append(98707 * 12345)
        self._test(self.encoder, test_list)

    def test_encode_dict(self):
        test_dict = {"hallo": ["hallo, 12"], "Wort": {"hallo": []}}
        self._test(self.encoder, test_dict)

    def test_encode_complex(self):
        test_complex = complex(1, 2)
        self._test(self.encoder, test_complex)


# Testing the form class

class TestForm(unittest.TestCase):

    std_title = "STANDARD"
    std_body = ["line one", "line two", "line three"]
    std_appendix = {"Hallo": 12.1, "Nein": 11.2}

    def test_init(self):
        form = self._create_std_form()
        self._test_std_form(form)

    def test_long_title(self):
        title = "HEAD" * 1000
        form = Form(title, self.std_body, self.std_appendix)
        self._test_title(form, title)

    def test_long_body(self):
        body = ("This is a line in a body string \n" * 1000).split("\n")
        form = Form(self.std_title, body, self.std_appendix)
        self._test_body(form, body)

    def test_long_appendix(self):
        appendix = {}
        for i in range(1000):
            appendix[i] = ["This is a long string to make matters worse and then the square", i**2]
        form = Form(self.std_title, self.std_body, appendix)
        self._test_appendix(form, appendix)

    def test_empty_standard(self):
        # Checking for the correct behaviour in the standard case
        form = Form(self.std_title, [], {})
        self.assertTrue(form.empty)
        # Checking for not being co related
        form = Form("", [], {})
        self.assertTrue(form.empty)

    def test_not_empty(self):
        # Checking with only the empty body
        form = Form(self.std_title, [], self.std_appendix)
        self.assertFalse(form.empty)
        # Checking with only the empty appendix
        form = Form(self.std_title, self.std_body, {})
        self.assertFalse(form.empty)

    def test_valid(self):
        # Checking for validity standard
        form = self._create_std_form()
        self.assertTrue(form.valid)
        # Checking for validity not given, when title empty
        form = Form("", self.std_body, self.std_appendix)
        self.assertFalse(form.valid)
        # Checking for whitespace title
        form = Form("     ", self.std_body, self.std_appendix)
        self.assertFalse(form.valid)
        # Checking for empty
        form = Form(self.std_title, [], {})
        self.assertFalse(form.valid)

    def test_equals(self):
        # Checking if they are equal
        form1 = self._create_std_form()
        form2 = self._create_std_form()
        self.assertEqual(form1, form2)
        # Checking if they are not equal in the title
        form1 = Form(self.std_title, self.std_body, self.std_appendix)
        form2 = Form("Hallo", self.std_body, self.std_appendix)
        self.assertNotEqual(form1, form2)
        # Checking for different bodys
        form1 = Form(self.std_title, ["hallo"], self.std_appendix)
        form2 = Form(self.std_title, ["allo"], self.std_appendix)
        self.assertNotEqual(form1, form2)

    def _create_std_form(self):
        """
        This method creates a new form object from the standard values of the test class and retunrs that form
        Returns:
        the Form object created
        """
        form = Form(self.std_title, self.std_body, self.std_appendix)
        return form

    def _test_body(self, form, body):
        """
        This method test for the body is equal
        Args:
            form: The form whose body to test
            body: The body either as string or as list of strings

        Returns:
        void
        """
        if isinstance(body, list):
            body = "\n".join(body)
        self.assertEqual(form.body, body)

    def _test_appendix(self, form, appendix):
        """
        This method test for the appendix is the same
        Args:
            form: The form object whose appendix to test
            appendix: The appendix dict to compare to

        Returns:
        void
        """
        self.assertDictEqual(form.appendix, appendix)

    def _test_title(self, form, title):
        """
        This method tests for the head the same
        Args:
            form: The form object whose head to be tested
            title: The head string to comapre to

        Returns:
        void
        """
        self.assertEqual(form.title, title)

    def _test_std_form(self, form):
        """
        This method tests if the given form correctly resembles a std form
        Args:
            form: The form object to test

        Returns:
        void
        """
        self.assertIsInstance(form, Form)
        self._test_title(form, self.std_title)
        self._test_body(form, self.std_body)
        self._test_appendix(form, self.std_appendix)


class TestFormTransmission(unittest.TestCase):

    pass