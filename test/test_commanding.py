from network.protocol.commanding import CommandForm
from network.protocol.commanding import ReturnForm

from network.form import Form

import unittest


class TestCommandForm(unittest.TestCase):

    basic_command_name = "command"
    basic_pos_args = ["hallo", 30]
    basic_kw_args = {"pos1": 123.0, "pos2": [1, 2, 3]}

    def test_creation_command_basic(self):
        """
        Testing the creation of a CommandForm from command spec
        Returns:
        void
        """
        command_form = self.basic_command_form
        # Testing if the parameters are correct transitioned to the attributes
        self.assertEqual(command_form.command_name, self.basic_command_name)
        self.assertListEqual(command_form.pos_args, self.basic_pos_args)
        self.assertDictEqual(command_form.key_args, self.basic_kw_args)
        # Testing if the Form was created correctly
        form = self.basic_form
        self.assertEqual(command_form.form, form)

    def test_creation_form_basic(self):
        """
        Testing the creation of a CommandForm form a Form object
        Returns:
        void
        """
        # Getting the basic form, on which the CommandForm is to be based
        form = self.basic_form

        # Creating the command form from the form
        command_form = CommandForm(form)

        # Testing if the form attribute was correctly assigned
        self.assertEqual(command_form.form, form)
        # Testing the actual command attributes
        self.assertEqual(command_form.command_name, self.basic_command_name)
        self.assertEqual(command_form.pos_args, self.basic_pos_args)
        self.assertEqual(command_form.key_args, self.basic_kw_args)

    @property
    def basic_command_form(self):
        """
        This method takes the parameters for a basic command, defined by the class attributes of this TestCase and
        builds a CommandForm from them
        Returns:
        The built CommandForm object
        """
        command_form = CommandForm(self.basic_command_name, self.basic_pos_args, self.basic_kw_args)
        return command_form

    @property
    def basic_form(self):
        """
        This method returns the form object, which is how a form object has to look like, when assembled by the
        CommandForm wrapper.
        Returns:
        The form object
        """
        # Creating the body and appendix from the class variables specifying the basic command
        name = self.basic_command_name
        pos_count = len(self.basic_pos_args)
        body = ["error:reply", "return:reply", "command:{}".format(name), "pos_args:{}".format(str(pos_count))]
        appendix = {"pos_args": self.basic_pos_args, "kw_args": self.basic_kw_args}

        # Creating the form object from the title, body and appendix & returning that
        form = Form("COMMAND", body, appendix)
        return form


class TestReturnForm(unittest.TestCase):

    basic_return_value = ["A list of strings", "with strings"]

    def test_basic_value_creation(self):
        """
        Testing the creation of a ReturnForm with a list as return value
        Returns:
        void
        """
        # Creating the basic form
        return_form = self.basic_return_form

        # Testing if the ReturnForm object still has the correct value saved as attribute
        self.assertListEqual(return_form.return_value, self.basic_return_value)
        # Testing if the Form created by the ReturnForm wrapper matches the desired result
        form = self.basic_form
        self.assertEqual(return_form.form, form)

    def test_basic_form_creation(self):
        """
        Testing the creation of a ReturnForm from a Form object
        Returns:
        void
        """
        # Creating the ReturnForm from the Form object
        form = self.basic_form
        return_form = ReturnForm(form)

        # Testing if the form is still the same as attribute
        self.assertEqual(return_form.form, form)
        # Testing if the return value has been extracted correctly
        self.assertListEqual(return_form.return_value, self.basic_return_value)

    @property
    def basic_return_form(self):
        """
        This method simply creates a ReturnForm object from the basic return value, which is class variable of this
        TestCase
        Returns:
        The ReturnForm object
        """
        return_form = ReturnForm(self.basic_return_value)
        return return_form

    @property
    def basic_form(self):
        """
        This method returns the Form object, which was built manually and resembles the form, that is SUPPOSED to be
        created by the ReturnForm wrapper, when passed the basic return value set as class attribute of this TestCase
        Returns:
        The Form object
        """
        type_string = str(type(self.basic_return_value))
        body = ["type:{}".format(type_string)]
        appendix = {"return": self.basic_return_value}

        # Creating the form from the desired appendix & body
        form = Form("RETURN", body, appendix)
        return form
