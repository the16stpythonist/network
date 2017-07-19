from network.protocol.commanding import CommandForm

from network.form import Form

import unittest


class TestCommandForm(unittest.TestCase):

    basic_command_name = "command"
    basic_pos_args = ["hallo", 30]
    basic_kw_args = {"pos1": 123.0, "pos2": [1, 2, 3]}

    def test_creation_command_basic(self):
        command_form = self.basic_command_form
        # Testing if the parameters are correct transitioned to the attributes
        self.assertEqual(command_form.command_name, self.basic_command_name)
        self.assertListEqual(command_form.pos_args, self.basic_pos_args)
        self.assertDictEqual(command_form.key_args, self.basic_kw_args)
        # Testing if the Form was created correctly
        form = self.basic_form
        self.assertEqual(command_form.form, form)

    def test_creation_form_basic(self):
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
