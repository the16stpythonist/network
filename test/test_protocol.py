import network.protocol as protocol
import unittest
import json

class TestForm(unittest.TestCase):

    std_title = "Test"
    std_body = "this is just a short body\nWith two rows\n"
    std_appendix = ["one", "two"]

    def test_init(self):
        # Building the form
        form = protocol.Form(self.std_title, self.std_body, self.std_appendix)
        self.assertEqual(form.title, self.std_title)
        self.assertEqual(form.body, self.std_body)
        self.assertEqual(form.appendix, self.std_appendix)

    def test_body(self):
        # Testing the turing of a list into a line separated string
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
        # Testing if the correct exceptions are risen in case a wrong param is passed
        with self.assertRaises(TypeError):
            protocol.Form(12, self.std_body, self.std_appendix)
        with self.assertRaises(ValueError):
            protocol.Form(self.std_title, 12, self.std_appendix)
        with self.assertRaises(ValueError):
            protocol.Form(self.std_title, self.std_body, "{hallo")

    def test_appendix(self):
        # Testing the turning of a list into a json string by the form
        appendix_dict = {"a": ["first", 129], "b": list(map(str, [1, 2, 3]))}
        appendix_json = json.dumps(appendix_dict)
        form = protocol.Form(self.std_title, self.std_body, appendix_dict)
        self.assertEqual(form.appendix_json, appendix_json)
        # Testing if the json string gets detected as such and loaded from the json format
        form = protocol.Form(self.std_title, self.std_body, appendix_json)
        self.assertDictEqual(form.appendix, appendix_dict)
        # Testing in case of a very long data structure
        # Creating a very long dictionary structure
        long_dict = {}
        for i in range(1, 1000, 1):
            sub_dict = {}
            for k in range(1, 100, 1):
                sub_dict[str(k)] = ["random", "random", "random"]
            long_dict[str(i)] = sub_dict
        long_json = json.dumps(long_dict)
        # Testing the internal conversion from dict to json
        form = protocol.Form(self.std_title, self.std_body, long_dict)
        self.assertEqual(form.appendix_json, long_json)
        # Testing the internal conversion from json string to object
        form = protocol.Form(self.std_title, self.std_body, long_json)
        self.assertDictEqual(form.appendix, long_dict)

    def test_empty(self):
        # Testing in case an empty object is given as appendix
        form = protocol.Form('', '', [])
        self.assertTrue(form.empty)
        # Testing in case an empty string is given as appendix
        form = protocol.Form('', '', '')
        self.assertTrue(form.empty)
        # Testing in case the body is an empty list
        form = protocol.Form('', [], '')
        self.assertTrue(form)

