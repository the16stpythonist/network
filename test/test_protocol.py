import network.protocol as protocol
import unittest

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

