"""

WHAT TO MAKE THE COMMANDING PROTOCOL BETTER?
- ONe important factor is, that the communication is based on sending a lot of small messages back and forth over the
  connection (This is also a main problem of the form transmission mechanism). It would be WAY better if that could be
  reduced to bigger, but less messages
"""
from network.form import Form
from network.form import FormTransmitterThread
from network.form import FormReceiverThread

from network.polling import GenericPoller

import threading
import random
import queue
import time

# THE COMMANDING PROTOCOL


class CommandContext:
    """
    BASE CLASS
    This is the base class for all specific CommandContext objects. The command context objects are supposed to be
    providing the necessary implementations for the commands used by the CommandingProtocol.

    CREATING COMMAND CONTEXTS
    Commands can be added to the functionality of a specific command set implementation by having a new specialized
    subclass inherit from this CommandContext class and adding new methods, whose names start with 'command' and an
    underscore, followed by the (exact!) name of the command whose functionality is to be implemented:
    Example: def command_print(self, pos_args, kw_args): ...

    EXECUTING COMMANDS:
    The commandContext objects ca be used to directly execute commands, described by a CommandingForm sub class, by
    being passed to the execute method.
    """
    def __init__(self):
        pass

    def execute_form(self, form):
        """
        A CommandingForm subclass can be passed to this method and the action corresponding to the type of form will be
        executed: In case it is a CommandForm, the command will be executed and the return Value will be returned, in
        case it is a ReturnForm the stored return value will be returned
        Args:
            form: The CommandingForm subclass to be executed

        Returns:
        Either the return of the executed command or the return value of a remote executed function
        """
        if isinstance(form, Form):
            if form.title == "COMMAND":
                form = CommandForm(form)
            elif form.title == "RETURN":
                form = ReturnForm(form)
            elif form.title == "ERROR":
                form = ErrorForm(form)
        if isinstance(form, CommandingForm):
            if isinstance(form, CommandForm):
                # Getting the method, that actually executes the behaviour for that command
                command = self.lookup_command(form.command_name)
                # Executing the command with the pos and kw args
                return command(*form.pos_args, **form.key_args)
            elif isinstance(form, ReturnForm):
                # Simply returning the value stored in the form
                return form.return_value
            elif isinstance(form, ErrorForm):
                raise form.exception
        else:
            raise TypeError("The form to execute is supposed to be a CommandingForm subclass")

    def lookup_command(self, command_name):
        """
        This method will use the command name given and first assemble the corresponding method name for that command
        name and then it will attempt to get the attribute of this very command context object. If a method exists,
        that implements the given command name, then the method will return the function object of that method.
        Args:
            command_name: The command name to which the method/ function object is requested

        Returns:
        The function object of the internal command context method with the name specified by the command name
        """
        try:
            command_method_name = self.assemble_command_name(command_name)
            return getattr(self, command_method_name)
        except AttributeError as attribute_error:
            raise attribute_error

    @staticmethod
    def assemble_command_name(command_name):
        """
        Using the name of the command specified by 'command_name' to assemble the name of the method of the context
        object corresponding to that command name. By definition the names of the methods corresponding to specific
        commands have to be named beginning with command, followed by an underscore and the the actual command name
        Notes:
            This method will only assemble the string, as defined by definition, but will not check for the validity
            of that string. The command specified by the command name, might not even be subject to the specific
            command context object, but the possible name will be assembled anyways.
        Args:
            command_name: The string command name of the command for which the method name is requested

        Returns:
        The string name of the CommandContext method corresponding to the command name given
        """
        string_list = ["command_", command_name]
        command_method_name = ''.join(string_list)
        return command_method_name

    def command_time(self,):
        """
        Some sort of dummy command, which just returns the time
        Args:
            pos_args:
            kw_args:

        Returns:
        The int timestamp of the current time
        """
        return time.time()


class CommandungForm:

    def __init__(self, spec_dict):
        self._spec = spec_dict
        # Checking if the actually is a dict
        self._check_spec()

        # Building the form according to the specific implementations
        self.form = self.build_form()

    def build_form(self):
        """
        The CommandingForm sub class already implements the creation of the actual Form object with this method, which
        will be used inside of the constructor of this base class to assign the Form to a instance attribute. But
        because the form is very specific to every certain sub class and their instances, the sub classes have to
        implement the three methods 'procure_title', 'procure_body' and 'procure_appendix' in which they specify, how
        these three parts of a Form are derived from the specific parameters. Those methods are then used in this
        method to actually create the Form

        Returns:
        The Form object created from the specific parameters from the CommandingForm wrapper
        """
        # Creating the title, body and appendix of the form from the methods, that per interface have to be
        # implemented by every sub class of CommandingForm
        title = self.procure_title()
        body = self.procure_body()
        appendix = self.procure_appendix()

        # Creating the actual Form object from those
        form = Form(title, body, appendix)
        return form

    def procure_title(self):
        """
        This method has to be implemented by every sub class of the CommandingForm and has to specify how the title
        of a form data structure can be derived from the data given to the specific instance of the sub class

        Returns:
        The string title of a form data structure
        """
        raise NotImplementedError()

    def procure_body(self):
        """
        This method has to be implemented by every sub class of the CommandingForm and has to specify how the body
        of a form data structure can be derived from the data given to the specific instance of the sub class

        Returns:
        The list of strings, that specify a form body
        """
        raise NotImplementedError()

    def procure_appendix(self):
        """
        This method has to be implemented by every sub class of the CommandingForm and has to specify how the appendix
        of a form data structure can be derived from the data given to the specific instance of the sub class

        Returns:
        Whatever object to be sent as a appendix of the form. The object has to be endcodable by the form
        """
        raise NotImplementedError()

    def __eq__(self, other):
        """
        Generally a CommandingForm object can only be compared to either another CommandingForm object or a Form
        object directly.
        - Comparing with CommandingForm: The comparison basically is a dictionary comparison between the spec
          dicts of the both objects, because they define, what the specific CommandingForms instances look like
        - Comparing with Form: The form is used to build a new instance of a CommandingForm of the type which the
          comparison is called on and then the dictionaries of those are being compared.
        Notes:
            Comparing to a CommandingForm is way more efficient, since no additional CommandingForm has to be
            created, which is the case if compared with a Form
        Args:
            other: The object with which the CommandingForm is being compared with. This has to be some sort
                of CommandingForm or Form object.

        Returns:
        The boolean value of whether or not the two objects are equal
        """
        # Checking if the compared object is also if the type CommandingForm or Form
        if isinstance(other, CommandungForm):

            # Simply checking if the two spec dictionaries are the same
            return dict(self) == dict(other)

        elif isinstance(other, Form):

            # Creating a CommandingForm object of the type on which this method is called from the given form
            other_commanding_form = self.__class__.from_form(other)
            # Now Comparing the spec dicts of those two CommandingForms
            return dict(self) == dict(other_commanding_form)

        else:
            return False

    def __dict__(self):
        """
        The CommandingForm base class dictates, that every subclass has to manage the specific data meant to be
        wrapped into a form for network transmission in a dictionary, mor specifically the _spec dictionary
        as a instance attribute. When calling the dict conversion on a CommandingForm this underlying dictionary
        can be returned directly.

        Returns:
        The dictionary, upon which's entries the CommandingForm is based on
        """
        return self._spec

    def __getitem__(self, item):
        """
        The CommandingForm base class dictates, that every subclass is based on a dictionary, more specifically

        Args:
            item: The string key for the item to get from the internal dictionary

        Returns:
        The dict value of the key, whatever the type may be
        """
        return self._spec[item]

    def __contains__(self, item):
        """
        This method gets called when the "... in <CommandingForm>" gets called and returns whether the given string
        is a key in the internal dictionary of the CommandingForm instance checked
        Args:
            item: The string of the key to be checked if actually a key in the internal dict of the object

        Returns:
        The boolean value of whether or not the string key is part of the object
        """
        return item in self._spec.keys()

    def __str__(self):
        raise NotImplementedError()

    @staticmethod
    def from_form(form):
        """
        Every CommandingForm is supposed to be able to be created from the very specific parameters correlating to the
        function of the specific sub class of CommandingForm and also the CommandingForm is supposed to be
        'derivable' from a given Form object, so that the CommandingForm wrapper can create Forms based on specific
        parameters and also destill those out again, when received on the other end.
        The process of creating the form from specific parameters is assigned to the regular construction and the
        backward construction from the form is supposed to be done with this static class which returns for every
        sub class of CommandingForm a method, that returns a instance of that class with the informations from within
        the Form
        Args:
            form: The Form object to be turned into a CommandingForm wrapper

        Returns:
        The CommandingForm sub class instance, which implements this method explicitly
        """
        raise NotImplementedError()

    def _check_spec(self):
        """
        This method checks the type of the spec dict in the way, that it raises an erro in case the _spec attribute
        is not a dict.
        Raises:
            TypeError: In case the _spec attribute is not a dict
        Returns:
        void
        """
        if not isinstance(self._spec, dict):
            raise TypeError("The spec of CommandingForm has to be dict")


class CommandingForm:
    """
    INTERFACE
    The CommandingForm is the base class for all the Form wrappers used in the CommandingProtocol.

    The Form wrappers have the overall purpose of creating a form according to their type and the parameters they have
    been given, which the form is supposed to contain.

    This base class has to be passed the finished Form object, which has been created during construction and the
    property methods for accessing the Form attributes like title, body, appendix directly are provided by this super
    class already.
    Furthermore this base class already implements the method, with which the form can be created, but for this
    creation of the form a title, body and appendix are needed, thus this class also enforces sub classes, inheriting
    from it to implement the methods, which assemble the correct title, body and apppendix according to the parameters
    they have been passed.
    At last this base class also provides the functionality of creating the 'spec' dict directly from the Form it has
    been passed. The spec dict is a representation if the body of the Form, where each entry is one line in the body
    string, the key being the string before the ':' separator and the value being the string adter until the new line.

    GENERAL STRUCTURE OF A COMMANDING FORM
    A CommandingForm wrapper creates a Form object, which is then supposed to be sent over the network. This Form has
    the basic structure:
    - Title: The title tells which type CommandingForm has created the Form, by a string in caps
    - Body: The body specifies general information in dictionary like format, separated by newline characters. Each
      each line in the body is separated by a ':' character between the key and the value of the dict like relation.
      This also implicates, that a value in the body cannot possibly contain a ':' character!
    - Appendix: This is a python dictionary object, serialized, and can contain everything possible according to the
      limitations of the encoder and is absolutely up to the specific sub class

    Attributes:
        form: The actual Form object, that has to be created to be sent over the network
        spec: The dictionary, which contains an entry for every line in the body of the Form, with the value being the
            sub string before the separator ':' occurred and the value being the sub string after
    """
    def __init__(self, form):
        self.form = form
        # The spec dict contains all the key value pairs specified in the body 
        self.spec = self.procure_body_dict_raw()

    def build_form(self):
        """
        This method will be used by all the subclasses to create a form object, that represents the information of
        the specialized commanding form, in the case, that the subclasses are not created by passing them a form upon
        which they are based, but rather the more specific parameter set, that describes their behaviour.
        Although for this to work, the sub classes of this class have to implement methods, that create and return the
        body list of strings and the appendix data structure from their individual data set.
        Returns:
        The form object, that was created as a representation of the complex and specialized data set describing an
        individual sub class of this base class form representation
        """
        title = self.procure_form_title()
        body = self.procure_form_body()
        appendix = self.procure_form_appendix()
        form = Form(title, body, appendix)
        return form

    def procure_form_title(self):
        """
        This method creates the title of the form, that is supposed to represent the subclasses of the CommandingForm.
        The title is per protocol defined as the type of the object, which is a upper case noun briefly describing
        the purpose of the class
        Returns:
        The string of the title of the form to be created from the object, which is the type string of the class
        """
        return self.type

    def procure_form_body(self):
        """
        HAS TO BE OVERWRITTEN BY SUB CLASS
        This method will have to create and return a list of strings, that describes the body lines of a form object,
        that represent the subclass.
        Returns:
        The list of strings for the body lines of the form to be created from the data of the sub class object
        """
        raise NotImplementedError("This method has to be overwritten by the sub class!")

    def procure_form_appendix(self):
        """
        HAS TO BE OVERWRITTEN BY SUB CLASS
        This method will have to create and return a data structure, that can be assignes as the appendix of a form and
        that per protocol defines the sub class creating it as that form.
        Returns:
        The appendix data structure
        """
        raise NotImplementedError("This method has to be overwritten by the sub class!")

    def procure_body_dict_raw(self):
        """
        This method will return a dictionary, which has one entry for every line in the body string, whose key is the
        sub string before the split character ':' has occurred and the value being the substring after that character.
        Returns:
        The dictionary which assignes string keys to string values
        """
        body_dict = {}
        # Getting the list of split lists of the body string
        body_list_split = self.procure_body_lines_split()
        for line_list in body_list_split:
            body_dict[line_list[0]] = line_list[1]
        return body_dict

    def procure_body_lines_split(self):
        """
        This method returns a list of lists, with one sub list for each line in the body string. The sub lists are the
        split lists of the lines by the ':' character and each sub list therefore contains two strings.
        Raises:
            ValueError: In case the formatting of the form is wrong and there is either no ':' or more than one in
                a line
        Returns:
        A list of lists, where each sub list has two string items
        """
        body_lines = self.body.split("\n")
        body_lines_split = []
        for line in body_lines:
            split_line = line.split(":")
            # In case the line does not have exactly one ':' character raising error, because invalid format
            if len(split_line) != 2:
                raise ValueError("The CommandingProtocol dictates, that there is exactly one ':' per line in body!")
            body_lines_split.append(split_line)
        return body_lines_split

    def procure_body_lines(self):
        """
        This method will return a list os strings, where each string is one line of the body string. A line is defined
        as the sum if characters until a new line character.
        Returns:
        The list of line strings for the body
        """
        body_lines = self.body.split("\n")
        return body_lines

    def check_spec_key(self, key):
        """
        This method checks if there is a key of the given name in the spec dictionary. In case the key is not part of
        the dict, an error will be risen.
        Raises:
            AttributeError
        Args:
            key: The string name of the key to be in the spec dictionary and therefore in the body of the form

        Returns:
        void
        """
        if key not in self.spec.keys():
            raise AttributeError("The key {} was not specified in the body of the form".format(key))

    def check_type(self):
        """
        This method will check if the type of the object matches the type of the form, upon which it is based on
        Returns:
        void
        """
        if self.title != self.type:
            raise TypeError("The form is not fit for a {} form type wrap object!".format(self.type))

    @property
    def type(self):
        """
        This method will return the type of the command form subclass. The functionality is purely based on the naming
        convention of the CommandingForm subclasses, which has to be the type of the form followed by 'Form'. The
        string of the type will then be returned as all upper case.
        Examples:
            If the type of the object would for example be Apple, then per naming convention the subclass would be
            named 'AppleForm', this class would then return the string 'APPLE', which was extracted from the class name
        Returns:
        The upper case string of the type of the subclass
        """
        # Getting the class name and removing the Form at the end
        class_name = self.__class__.__name__
        type_name = class_name.replace("Form", "")
        # Making it upper case and then returning it
        return type_name.upper()

    @property
    def title(self):
        """
        This method is the property getter for the title of the form. It will return the title of the wrapped form
        Returns:
        the string title of the form
        """
        return self.form.title

    @property
    def body(self):
        """
        This method is the property getter for the body of the form. It will return the body of the wrapped form
        Returns:
        The string of the body of the form
        """
        return self.form.body

    @property
    def appendix(self):
        """
        This is the property getter if the appendix object of the form. It will return the appendix of the wrapped form
        Returns:
        The appendix object of the wrapped form
        """
        return self.form.appendix

    @property
    def appendix_encoder(self):
        """
        This is the property getter method of the encoder object, that is responsible for the encoding and decoding
        of the form object. It will simply return the encoder of the wrappped form
        Returns:
        The AppendixEncoder form, with which the form is being made network transmittable
        """
        return self.form.appendix_encoder

    @staticmethod
    def assemble_body_line(key, value):
        """
        This method assembles the key and value strings for a line in the body of the form, by joining them with a
        ':' used as separator
        Args:
            key:
            value:

        Returns:

        """
        body_line = ':'.join([key, value])
        return body_line


class CommandForm(CommandingForm):

    def __init__(self, command, pos_args=[], kw_args={}, return_handle="reply", error_handle="reply"):
        # Initializing the attributes for the command form
        if isinstance(command, Form):
            CommandingForm.__init__(self, command)
            self.check_type()
            # Loading the data from the form
            self.command_name = self.procure_command_name()
            self.pos_args = self.procure_positional_args()
            self.key_args = self.procure_keyword_args()
            self.error_handle = self.procure_error_handle()
            self.return_handle = self.procure_return_handle()
        elif isinstance(command, str):
            # The string name of the command to be called in the remote location
            self.command_name = command
            # The positional arguments for the command call
            self.pos_args = pos_args
            # The keyword arguments for the command call
            self.key_args = kw_args
            # The handles are string identifiers about how the return value and the error are suppose to be treated
            self.error_handle = error_handle
            self.return_handle = return_handle
            # Building the form from the information about the command
            form = self.build_form()
            CommandingForm.__init__(self, form)

    def procure_form_appendix(self):
        """
        This method will create the appendix dictionary for the form based on what psoitional and kw arguments have
        been passed to the CommandForm object
        Returns:
        The dictionary, containing the pos and kw args for the command call
        """
        return {"pos_args": self.pos_args, "kw_args": self.key_args}

    def procure_form_body(self):
        """
        This method first creates the spec dictionary from the data about the command stored in the attributes of the
        object, that means about the command name, the return and error mode and the amount of pos args. The it
        assembles this dictionary into the actual body string list
        Returns:
        The list of strings, which are supposed to be the lines of the body string of a form
        """
        string_list = []
        # Getting the spec of the form on which to base the body string
        spec = self.procure_form_spec()
        # Making a new line for each dictionary entry
        for key, value in spec.items():
            line_string = ':'.join([key, value])
            string_list.append(line_string)
        # Appending all the lines to a body, separated by newline characters
        return string_list

    def procure_form_spec(self):
        """
        This method assembled the spec dictionary from the data given for the command form
        Returns:
        the dictionary with the string key value pairs for a command form
        """
        spec = dict()
        spec["error"] = self.error_handle
        spec["return"] = self.return_handle
        spec["command"] = self.command_name
        spec["pos_args"] = str(len(self.pos_args))
        return spec

    def procure_return_handle(self):
        """
        This method will get the return handle string from the spec dict
        Returns:
        the string return handle
        """
        self.check_return_handle()
        return_handle = self.spec["return"]
        return return_handle

    def procure_error_handle(self):
        """
        This method will get the error handle from the spec dict
        Returns:
        The string error handle identifier
        """
        self.check_error_handle()
        error_handle = self.spec["error"]
        return error_handle

    def procure_positional_args(self):
        """
        This method gets the positional arguments list from the appendix dict
        Returns:
        the list of positional arguments for the command call
        """
        self.check_pos_args()
        pos_args = self.appendix["pos_args"]
        if not isinstance(pos_args, list):
            raise TypeError("The positional arguments are supposed to be list!")
        return pos_args

    def procure_keyword_args(self):
        """
        This method gets the key word argument dict from the appendix dict of the form
        Returns:
        The dictionary, that specifies the kewword arguments for the command call
        """
        kw_args = self.appendix["kw_args"]
        if not isinstance(kw_args, dict):
            raise TypeError("The keyword arguments are supposed to be dict!")
        return kw_args

    def procure_command_name(self):
        """
        This method gets the command name for the command to be issued/represented by this form from the spec dict,
        which is based on the information in the body of the form.
        Returns:

        """
        # Checking for the existence of the command name in the spec of the body; raises AttributeError if not
        self.check_command_name()
        # Getting the command name from the dict and returning it
        command_name = self.spec["command"].strip()
        return command_name

    def check_appendix(self):
        """
        This method checks if the appendix object of the form is a dictionary and if that dict has the two entries for
        the pos args and the kw args, as it has to be with a command form
        Returns:
        void
        """
        # Checking if the appendix even is a dictionary
        dict_type = not isinstance(self.appendix, dict)
        if dict_type:
            raise TypeError("The appendix of the command form is supposed ot be a dict!")
        # Checking if the entries of the appendix dict are correct
        keys = self.appendix.keys()
        entries = len(keys) != 2 or 'pos_args' not in keys() or 'kw_args' not in keys()
        if entries:
            raise KeyError("The entries of form appendix do not match command form!")

    def check_command_name(self):
        """
        This method checks if the 'command' field was specified in the body of the form and raises an error if that is
        not the case
        Raises:
            AttributeError: In case the key 'command' is not in the spec dict
        Returns:
        void
        """
        self.check_spec_key("command")

    def check_pos_args(self):
        """
        This method checks if the spec dictionary, which is based on the form body contains an entry, that is named
        'pos_args', which is supposed to be a int number for the amount of pos args to be given to the command call.
        Also checks the conversion.
        Raises:
            AttributeError: in case the entry is not even in the spec dict
            TypeError: In case the value to the entry is not int convertable
        Returns:
        void
        """
        self.check_spec_key("pos_args")
        try:
            int(self.spec["pos_args"].strip())
        except ValueError:
            raise TypeError("The pos_args entry is supposed to be integer type convertable")

    def check_error_handle(self):
        """
        This method checks if the spec dictionary, which is based in the body string of the form, contains an entry
        about the error handle of the command call.
        Returns:
        void
        """
        self.check_spec_key("error")

    def check_return_handle(self):
        """
        This method checks if the spec dictionary, which is based on the body string of the form, contaisn an entry
        about the return handle of the command call.
        Returns:
        void
        """
        self.check_spec_key("return")


class ReturnForm(CommandingForm):

    def __init__(self, return_value):
        if isinstance(return_value, Form):
            CommandingForm.__init__(self, return_value)
            self.check_type()
            self.return_value = self.procure_return_value()
        else:
            self.return_value = return_value
            self.return_type = self.procure_return_type_string()
            form = self.build_form()
            CommandingForm.__init__(self, form)

    def procure_form_body(self):
        """
        This method creates the form body list with one entry and that being the string of the return type
        Returns:
        The list with the body string lines
        """
        body_string = ':'.join(["type", str(self.return_type)])
        return [body_string]

    def procure_form_appendix(self):
        """
        This method creates a dictionary with one entry being the return value of this object
        Returns:
        The assembled dictionary as the appendix of the form
        """
        return {"return": self.return_value}

    def procure_return_value(self):
        """
        This method will extract the return value from the underlying form. The return value object is supposed to be
        stored in the entry with the key 'return'
        Returns:
        The object which is supposed to be the return
        """
        self.check_appendix()
        return_value = self.appendix["return"]
        return return_value

    def procure_return_type_string(self):
        """
        This method will get the string format of the type of the return value
        Returns:
        The string of the type of the return value object
        """
        return_type = self.procure_return_type()
        return str(return_type)

    def procure_return_type(self):
        """
        This method will get the type of the return value of the return form object
        Returns:
        The type object for the type of the return form object
        """
        return_type = type(self.return_value)
        return return_type

    def check_appendix(self):
        """
        This method checks if the appendix of the given form is actually a dictionary object and if that dictionary
        contains an entry with the key "return" as it should do
        Raises:
            TypeError: In case the dictionary is not how it should be
        Returns:
        void
        """
        if not isinstance(self.appendix, dict) or 'return' not in self.appendix.keys():
            raise TypeError("The appendix has to be a dict!")


class ErrorForm(CommandingForm):

    def __init__(self, exception):
        if isinstance(exception, Exception):
            self.exception = exception
            form = self.build_form()
            CommandingForm.__init__(self, form)
        elif isinstance(exception, Form):
            CommandingForm.__init__(self, exception)
            self.check_type()
            self.exception = self.procure_exception()
        else:
            raise TypeError("The Error form has to be passed either form or exception object!")

    def procure_form_appendix(self):
        #TODO: CHANGE THE WHOLE ERROR FORM CONCEPT
        """
        This method will create the appendix of the form, which is supposed to represent this object. If the
        appendix encoder used for the form is able to encode the exception object itself a dictionary will be sent,
        that only has ine item with the key 'error' and tge value being the exception object. If the encoder is not
        able to serialize the exception, an empty dict will be used as appendix
        Returns:
        dict
        """
        if False:
            return {"error": self.exception}
        else:
            return {}

    def procure_form_body(self):
        """
        This method will create the body of a form, which is supposed to represent this object, from the exception
        name of the exception, that was passed to the object for construction.
        Returns:
        The list containing
        """
        # Getting the name of the exception
        exception_name = self.procure_exception_name()
        exception_message = self.procure_exception_message().replace("\n", "")
        exception_message = exception_message.replace(":", ";")
        name_line = self.assemble_body_line("name", exception_name)
        message_line = self.assemble_body_line("message", exception_message)
        return [name_line, message_line]

    def procure_exception_name(self):
        """
        This method extracts the exception name from the exception attribute of this class and then returns the string
        name of the exception class
        Returns:
        The string name of the exception
        """
        exception_class = self.exception.__class__
        exception_name = exception_class.__name__
        return exception_name

    def procure_exception_message(self):
        """
        This method will get the exception message from the exception object, that is the attribute of this object
        Returns:
        The string exception message
        """
        exception_message = str(self.exception)
        return exception_message

    def procure_exception(self):
        """
        This method will create an exception object from the data given by the underlying form object. In case there is
        only an empty appendix (which means that the appendix encoder cannot encode exception objects) a new exception
        object will be created by dynamically interpreting the error name and message in the body of the form. In case
        there is an appendix using the exception object stored in the appendix to return
        Returns:
        An exception object, as specified by the form
        """
        if len(self.appendix) == 0:
            # Creating the python expression of creating a new exception object as a string expression from the name
            # and message of the exception from the body
            eval_string = self.procure_exception_eval_string()
            # Dynamically interpreting that string and retunring the new exception object
            return eval(eval_string)
        else:
            return self.appendix["error"]

    def procure_exception_eval_string(self):
        """
        This method will create a string expression, that represents a python source code statement of creating a new
        exception object with using the excepetion name, specified by the body as the class to create and the message
        given in the body as the string parameter for the exception object creation.
        Returns:
        A string, that is a python statement
        """
        exception_name = self.spec["name"]
        exception_message = self.spec["message"]
        return ''.join([exception_name, '("', exception_message, '")'])


class CommandingBase(threading.Thread):

    def __init__(self, connection, command_context, separation="$separation$"):
        threading.Thread.__init__(self)
        self.connection = connection
        self.separation = separation
        self.command_context = command_context

    def send_request(self):
        """
        This method sends a 'request' string over the connection and then waits an indefinite amount of time until a
        line string has been received. If the received string is the 'ack' string, the methods exists, in case not, an
        exception is being raised.
        Raises:
            ValueError: In case the received string is not the ack string
        Returns:
        void
        """
        # Sending a request to the other side of the connection
        self.connection.sendall_string("request\n")
        # Waiting for the ack
        line_string = self.wait_line()
        if line_string != "ack":
            raise ValueError("The ack was not replied")

    def wait_request(self):
        """
        This method waits an indefinite amount of time for a new line to be received over the connection, then checks
        if the received string is a 'request' string. In case it is, an 'ack' string will be sent back to the client,
        which signals, that the actual form can now be transmitted.
        Raises:
            ValueError: In case the received string was not the request string
        Returns:
        void
        """
        # Waiting for a line to be received by the connection
        line_string = self.wait_line()
        if line_string != "request":
            raise ValueError("The client has sent wrong request identifier")
        # Sending the ack in response
        self.send_ack()

    def send_ack(self):
        """
        This method will send the string 'ack' over the connection object followed by a new line character. An ack is
        being sent as the response to a request by the client of the connection and thus also signals the client to
        begin sending the actual form.
        Returns:
        void
        """
        self.connection.sendall_string("ack\n")

    def wait_line(self):
        """
        This method will wait an indefinite amount of time until a string is being sent over a the connection and will
        then eventually return the substring until a new line character has occurred in the stream
        Returns:
        The received string
        """
        return self.connection.wait_string_until_character("\n")

    def send_command_context_type(self):
        """
        This method will send the string representation of the command context class, so that on the remote side of the
        communication it can be compared, if the server and client are on the same page
        Returns:

        """
        command_context_type_string = str(self.command_context_class) + "\n"
        self.connection.sendall_string(command_context_type_string)

    def validate(self):
        """
        This function shall be used by the handler as well as the client as the method with which they compare the type
        of command context on which they are based, to validate if a successful communication is possible
        Returns:
        void
        """
        raise NotImplementedError()

    def _send_form(self, form):
        """
        This method will send the specified form over the connection and will block the call until the transmission is
        finished
        Args:
            form: The form object to be transmitted

        Returns:
        void
        """
        transmitter = FormTransmitterThread(self.connection, form, self.separation)
        transmitter.start()
        while not transmitter.finished:
            time.sleep(0.001)

    @property
    def command_context_class(self):
        """
        Both the client and the server are supposed to implement a property for getting the type of the command context
        object, which they are based on. This function is supposed to return the class specification of the command
        context object
        Returns:
        The class object of the respective command contect, on which the object is based on
        """
        return self.command_context.__class__

    @staticmethod
    def evaluate_commanding_form(form):
        """
        This is a utility function, which evaluates a form object, as it was received by the form transmission
        protocol and returns the commanding form wrapper object according to what the original form is meant to
        resemble.
        Raises:
            TypeError: In case the passed value is not Form object
            ValueError: In case the type of the form is none of the commanding forms command, return or error
        Args:
            form: The form to be wrapped in a commanding form

        Returns:
        The commanding form, the given form is meant to resemble
        """
        if not isinstance(form, Form):
            raise TypeError("Only Form objects can be evaluated to CommandingForm objects")
        if form.title == "COMMAND":
            return CommandForm(form)
        elif form.title == "RETURN":
            return ReturnForm(form)
        elif form.title == "ERROR":
            return ErrorForm(form)
        else:
            raise ValueError("The received form '{}' is not a commanding form")


class CommandingHandler(CommandingBase):

    def __init__(self, connection, command_context):
        # Initializing the super class
        CommandingBase.__init__(self, connection, command_context)

        # Setting the running state variable to True
        self.running = True

    def run(self):
        """
        When the CommandingHandler Thread os being started it will first validate  with the connected client (For a
        explanation read the validate method). Then the main loop will be entered. In the main loop the handler will
        call a blocking receive call on the connection, waiting for a communication request coming from the client.
        After a request has been received and responded with an ack, A FormReceiverThread will be started to
        receive the CommandForm, which specifies the command to be executed, The command form will be executed by the
        CommandContext and depending on the case a ReturnForm or a ErrorForm will be created and then sent back via
        the FormTransmitterThread.
        Notes:
            It is important, that the receive call in the main loop is blocking and thus the Thread can not be
            terminated by simply inverting the running flag, but the socket has to be closed forcefully. This method
            will buffer the exception in such a case.
        Returns:
        void
        """
        try:
            # Checking if the connection client is compatible
            self.validate()
            while self.running:
                self.wait_request()

                # Receiving the form
                receiver = FormReceiverThread(self.connection, self.separation)
                receiver.start()
                form = receiver.receive_form()
                # Creating the commanding form wrapper from the plain form
                commanding_form = self.evaluate_commanding_form(form)
                # Executing the commanding form
                try:
                    return_value = self.execute_form(commanding_form)
                    response = ReturnForm(return_value)
                except Exception as exception:
                    response = ErrorForm(exception)
                # Sending the response form over a form transmitter Thread
                self._send_form(response.form)
        except ConnectionAbortedError:
            pass

    def execute_form(self, commanding_form):
        """
        This method will execute the form with the command context object on which it is based on
        Args:
            commanding_form: The received Form object

        Returns:
        The return value of the command execution
        """
        return self.command_context.execute_form(commanding_form)

    def validate(self):
        """
        This method checks, if the server and the client have the same command context to work with
        Returns:
        void
        """
        # Sending the type of command context in which the server is based on to the client
        self.send_command_context_type()
        # Receiving the type of command context on which the client is based on from the client
        line_string = self.connection.receive_line(10)
        if str(self.command_context_class) != line_string:
            raise ConnectionAbortedError("The client and server do not have the same command context")

    def stop(self):
        self.running = False
        self.connection.sock.close()

    def _check_command_context(self):
        """
        This method checks if the object passed to specify the command context is actually a CommandContext object
        Returns:
        void
        """
        if not isinstance(self.command_context, CommandContext):
            raise TypeError("The command context parameter of the Commanding server has to be CommandContext")


class CommandingClient(CommandingBase):

    def __init__(self, connection, command_context, separation="$separation$", timeout=10, polling_interval=None,
                 queue_size=10):
        CommandingBase.__init__(self, connection, command_context, separation)
        self.timeout = timeout

        self.last_activity_timestamp = None
        self.idle_time = 0
        self._polling_interval = polling_interval
        interval_generator = self.build_interval_generator()
        polling_function = self.build_polling_function()
        self.poller = GenericPoller(self.connection, interval_generator, polling_function)

        # The attribute to store the size of the queue
        self.queue_size = queue_size
        self.response_dict = {}
        self.call_queue = queue.PriorityQueue(10)
        self.running = False

    def run(self):
        self.running = True
        try:
            self.validate()
            while self.running:
                # Check the Que not to be empty
                if self.call_queue.empty():
                    # Updating the idle time
                    self.idle_time = time.time() - self.last_activity_timestamp
                    # First checking if the object actually has polling enabled and then if the poller tells that the
                    # interval for activity has been exceeded
                    """
                    if self.is_polling and self.poller.is_interval_match(self.idle_time, True):
                        # Sending a request first
                        self.send_request()
                        # Polling and then updating the last activity time
                        self.poller.poll()
                        self.update_last_activity_time()
                    """
                else:
                    call = self.call_queue.get()

                    # Sending a request
                    self.send_request()

                    # Sending the actual command form
                    call_id, command_name, pos_args, kw_args = self.unpack_call(call)
                    self._send_command(command_name, pos_args, kw_args)
                    # Receiving the return form and putting it into the list
                    receiver = FormReceiverThread(self.connection, self.separation)
                    receiver.start()
                    response = receiver.receive_form()

                    # Adding the response to the response dict with the call id as the key
                    self.response_dict[call_id] = response

                    # Updating the last activity
                    self.update_last_activity_time()
        except:
            pass

    def execute_command(self, command_name, pos_args, kw_args, priority=1, blocking=True):
        """
        This method will send the command as a form over the connection and therefore issue the command on the remote
        Handler. Depending on whether the method is executed as blocking or not, the method will either exit as void
        after the command has been issued or wait for the response to be received and then execute the action specified
        in the response form, thus either raising an error or returning the return value of the command
        Args:
            command_name: The string name of the command to execute
            pos_args: The pos args list
            kw_args: The kw args dict
            blocking: The boolean value of whether the method should wait for the response to be returned and then
                execute the the response or exit straight after issuing the command

        Returns:
        -
        """
        call_id = self.put_call(command_name, pos_args, kw_args, priority)
        if blocking:
            while not self.has_response(call_id):
                time.sleep(0.001)
            # Getting the Commanding form, that was sent as a response for the command from the buffer and then
            # executing it via the command context object
            response = self.get_response(call_id)
            return self.command_context.execute_form(response)
        else:
            return call_id

    def validate(self):
        """
        This method checks if the handler and the client have the same command context to work with. If that is not
        the case an error will be raised, because the handler and client are incompatible.
        Raises:
            ConnectionAbortedError: In case the handler and the client are based on different command contexts
        Returns:
        void
        """
        # Receiving the command context type string from the handler
        line_string = self.connection.receive_line(10)
        # Sending the own command context type over the connection
        self.send_command_context_type()
        if not line_string == str(self.command_context_class):
            raise ConnectionAbortedError("The client and server do not have the same command context")

    def get_response(self, call_id):
        """
        If given a request tuple, which consists of the three elements in order: The command name, the commands
        positional arguments as a list and the commands keyword arguments as a dict, this method will search the
        response list and return the response object, that has been received as an answer to that request. In case
        there is no response to the request yet, an error will be raised.
        Raises:
            KeyError: In case there is no response to the given request yet
        Args:
            call_id: The int id for the call for which to return the response object

        Returns:
        The response is a CommandingForm, usually of the type ReturnForm or ErrorForm
        """
        # Getting the response and then deleting it from the dict
        response = self.response_dict[call_id]
        del self.response_dict[call_id]

        return response

    def has_response(self, call_id):
        """
        If given the call id of a issued command to the client, this function will return whether or not the response
        to that command call has already been received and therefore added to the response dict
        Args:
            call_id: The int id for the call for which to check if the response has already arrived

        Returns:
        The bool value of whether or not the response to the call correlating to the call id has already been received
        """
        return call_id in self.response_dict.keys()

    def unpack_call(self, call_tuple):
        """
        This method will take a call tuple, as it gets popped from the call queue, as the parameter and it will return
        a tuple of the 4 values: call_id,  command_name, pos_args, kw_args
        Args:
            call_tuple: The tuple in the way it was popped from the call queue

        Returns:
        The tuple (call_id,  command_name, pos_args, kw_args) according to the call tuple passed to the method
        """
        call_id = call_tuple[1][0]
        command_name = call_tuple[1][1]
        pos_args = call_tuple[1][2]
        kw_args = call_tuple[1][3]
        return call_id, command_name, pos_args, kw_args

    def put_call(self, command_name, pos_args, kw_args, priority):
        """
        This method will put a request tuple into the request queue of the object, which consists of the command
        specification passed to this method as parameters.
        Therefore a call id is created, which will be used to add the response to the response dict once the
        response has been received.
        Args:
            command_name: The name of the command to execute
            pos_args: The positional arguments of that command
            kw_args: The keyword arguments of that command
            priority: The priority of that command execution

        Returns:
        The int call id, which will later be the id for the response object in the dict
        """
        # Getting a id for the request
        call_id = self._generate_id(command_name)
        # Generating the request tuple
        call = (priority, (call_id, command_name, pos_args, kw_args))
        # Putting the request into the priority queue
        self.call_queue.put(call)

        # Returning the request id, so that the response can be easily fetched from the dictionary
        return call_id

    @property
    def is_polling(self):
        """
        The is_polling property is a boolean flag, which states whether or not the client object performs a polling
        activity on the connection.
        Returns:
        The boolean property of whether or not polling is enabled
        """
        return self._polling_interval is None

    def build_interval_generator(self):
        """
        This function builds a new function internally, which has no parameters and acts as a generator, that
        always yields the same value, which is the one specified by the polling interval attribute.
        Notes:
            The function will, as a generator, always yield the value with which it was set up. Changing the polling
            interval attribute will not change the generator function.
        Returns:
        the function object, which is the generator for the interval value
        """
        polling_interval = self._polling_interval
        # Creates an internal function, that always yields the same value, which is the one in the interval attribute

        def gen():
            yield polling_interval

        return gen

    def build_polling_function(self):
        """
        This function creates a new function object, by using the already implemented poll procedure of the static
        method '_poll_function' wrapped in a lambda expression, that hides the excess parameters which are based on
        the attributes of the individual CommandClient instance
        Returns:
        The function object to be used as the polling function for the GenericPoller object, bing used for the polling##
        """
        return lambda conn: self._polling_function(conn, self.separation, self.timeout)

    def update_last_activity_time(self):
        """
        This method simply assignes the current timestamp of the time module to the attribute that monitors the
        last activity. Also resets the idle time counter
        Returns:
        void
        """
        self.last_activity_timestamp = time.time()
        self.idle_time = 0

    def procure_random_int_list(self, length, a=100, b=10000):
        """
        This method creates a list with the passed length of random integers in the range between a and b.
        This list will then be used as the stack for managing the id's for retrieving response objects from the
        dictionary, that stores them.
        Args:
            length: The length wanted for the list of random integers
            a: The start of the range in which to pick the random ints
            b: The end of the range in which to pick the random ints

        Returns:
        A list of integers with the length passed to the method call
        """
        random_list = []
        for i in range(length):
            random_int = self.procure_random_int(a, b)
            random_list.append(random_int)
        return random_list

    @staticmethod
    def procure_random_int(a=100, b=10000):
        """
        This method will simply return a random integer number in the range from a to b.
        This functionality is needed for creating the list of random numbers to be used as id's for the dictionary,
        that stores the responses the requests, after they have been received
        Args:
            a: The start of the range in which to pick a random int number. Defaults to 100
            b: The end of the range in which to pick a random int number. Defaults 10000

        Returns:
        A random integer number
        """
        return random.randint(a, b)

    @staticmethod
    def _polling_function(connection, separation, timeout):
        """
        This method provides the basic function object for the polling function for the GenericPoller to perform the
        polling operation. The function sends a CommandForm to the remote participant calling the time dummy function
        to fetch the local time and send it back as a response.
        Although this function has 3 parameters, where as the polling function is expected to implement the connection
        parameter as the only one. This means this method has to be wrapped by a lambda function to preset the
        attributes of the calling CommandClient as fix parameters.
        Args:
            connection: The connection object to perform the poll on
            separation: The separation used by the CommandingClient
            timeout: The timout specified by the CommandingClient

        Returns:
        void
        """
        form = CommandForm("time")
        transmitter = FormTransmitterThread(connection, form, separation=separation, timeout=timeout)
        transmitter.start()
        receiver = FormReceiverThread(connection, separation=separation, timeout=timeout)
        receiver.start()
        receiver.receive_form()

    def _send_command(self, command_name, pos_args, kw_args):
        """
        This method will actually create a CommandForm with the given specification of the command name, positional
        and keyword agruments and then send this form over the connection, using a FormTransmitterThread. The method
        will exit, when the form has been transmitted completely
        Args:
            command_name: The string name of the command to execute
            pos_args: The pos args list
            kw_args: The kw args dict

        Returns:
        void
        """
        command_form = CommandForm(command_name, pos_args, kw_args)
        self._send_form(command_form.form)

    @staticmethod
    def _generate_id(command_name):
        """
        This function creates an id based on random modulo hashing
        Args:
            command_name: The name of the command, for which to generate an id

        Returns:
        A string containing a hey number, which is the id for the given command name, randomized
        """
        command_name_bytes = command_name.encode()
        command_name_int = int.from_bytes(command_name_bytes, "big")
        random_hash_key = random.randint(1, command_name_int)
        call_id_int = command_name_int % random_hash_key
        call_id_hex = hex(call_id_int)
        return call_id_hex

