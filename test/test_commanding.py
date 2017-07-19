from network.protocol.commanding import CommandForm

from network.form import Form

import unittest


class TestCommandForm(unittest.TestCase):

    def test_creation_command_basic(self):
        command_name = "time"
        pos_args = ["pos1", "pos2"]
        kw_args = {"kw1": 1, "kw2": 2}
        command_form = CommandForm(command_name, pos_args, kw_args)
        # Testing if the parameters are correct transitioned to the attributes
        self.assertEqual(command_form.command_name, command_name)
        self.assertListEqual(command_form.pos_args, pos_args)
        self.assertDictEqual(command_form.key_args, kw_args)
        # Testing if the Form was created correctly
        body = ["error:reply", "return:reply", "command:time", "pos_args:2"]
        appendix = {"pos_args": pos_args, "kw_args": kw_args}
        form = Form("COMMAND", body, appendix)
        print(str(command_form.form))
        print(str(form))
        self.assertEqual(command_form.form, form)
