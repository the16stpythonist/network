"""
The Poller classes:
The Poller classes are supposed to implement the behaviour of polling a connection for its availability. The problem
could be the following: A program has to know if a connection is still available at (almost) all the time and not
only once an important message is being sent be the service operating in that connection only to realize far too late,
that there is no reply.
This kind of polling service can be build in two main ways:
- As plain objects: Where the idle time or the interval in which no poll has been performed is being maintained by the
  service that is also maintaining the poller object itself. In such a situation the Poller objects do not offer a great
  advantage as they are simply a way of managing the various functions that are used for the polling, but the actual
  poll tracking sill has to be implemented higher level.
- As Threads: obviously a more elegant approach is to run the Poller parallel and just let it do its thing in the
  background, while the service itself is not using the connection.
  With this approach though there is the need for a more advanced implementation for the Connection interface, which
  also features the possibility to put a threading Lock on the connection. And also if there is a big number of
  connections to contain a polling service it would be problematic for the performance to maintain a big number of
  mostly idle Threads, that just count the time till the next poll...
"""
import time


class Poller:
    """
    ABSTRACT BASE CLASS / INTERFACE

    This class is supposed to act as a sort of interface and base class to a construct of a Poller.
    On the abstract base level a Poller is supposed to be a object, which manages the polling communication over a
    Connection. The Poller is in charge of checking if the connection is still valid, by constantly asking the remote
    participant of the communication "whether it is still there".
    The basic thought is: This general idea of polling is supposed to be used in cases where the state of a
    Connection has to be known (almost) all the time (as good as the time resolution is set) and not just as late as
    a message being sent by the "normal service" of that connection just does not reply.
    """
    def __init__(self, connection, interval, poll_instruction):
        self._interval = interval
        self.connection = connection
        self._poll_instruction = poll_instruction

    def is_interval_match(self, interval, update=False):
        """
        This function is supposed to take a float interval value in seconds as a parameter internally check if the
        interval time has been exceeded or not. The function is supposed to return a tuple with the boolean value of
        whether or not the interval has been exceeded and the second element being the int value (positive or negative)
        of how long the interval has been exceeded or how long it still is until the interval will be exceeded by the
        time value passed to the function
        Args:
            interval: The int value for the interval in seconds
            update: Whether or not the interval is supposed to be updated after it was checked

        Returns:
        A tuple (bool, int) where the boolean value states whether or not the interval value given is already bigger
        than the interval value specified by the Poller and the int value the time difference of given interval time
        minus specified time by Poller.
        """
        raise NotImplementedError()

    def poll(self):
        """
        This function is supposed to do whatever the specific implementation of the Poller does for performing the
        actual polling process. This function is supposed to contain the whole process from sending the poll to waiting
        for the response. Therefore this function has to be the one to raise a TimeoutError Exception in case the poll
        was unsuccessful.
        Raises:
            TimeoutError: In case the poll was unsuccessful

        Returns:
        void
        """
        raise NotImplementedError()

    @property
    def interval(self):
        """
        This is the property getter function for the interval attribute.

        Returns:
        Should be a integer for the time in seconds
        """
        raise NotImplementedError()

    @property
    def poll_instruction(self):
        """
        This is the property getter function for the poll instruction attribute of the Poller.

        Returns:
        The type of what the instruction is is based on the specific implementation
        """
        raise NotImplementedError()


class GenericPoller(Poller):
    """
    This is a specific implementation of the abstract Poller class. In general objects of this class will perform the
    basic polling mechanism if passed a generator function without parameters, which returns a numeric value in the
    series of interval values, the connection object on which to perform the polling, and the function with the single
    parameter being the connection object, which specifies the actual process of the polling itself.
    Attributes:
        interval_generator: The generator function without parameters, which forms the series of interval
            specifications for the polling process
        keep_interval: The boolean flag of whether or not the current interval value is supposed to be kept or if the
            value is supposed to be replaced with the next value from the interval generator function
        connection: The Connection object on which the polling is supposed to be performed
        _poll_instruction: The function which actually implements the whole polling process, by using the connection
            object as the parameter. This function then raises a TimeoutError in case the poll was unsuccessful, which
            is then being risen from within the 'poll' call of the Poller object
        _interval: The actual numeric interval value, which holds the current interval to check for
    """
    def __init__(self, connection, interval_generator, polling_function):
        self.interval_generator = interval_generator
        interval = self._next_interval()
        self.keep_interval = True
        Poller.__init__(self, connection, interval, polling_function)

    def poll(self):
        """
        This method will call the function, that was specified as the poll instruction with the connection object as
        the parameter.
        Returns:
        void
        """
        self.poll_function(self.connection)

    def is_interval_match(self, interval, update=False):
        """
        This function checks if the interval passed as parameter is already bigger than the interval specified by the
        Poller object. This function will return a tuple of a boolean and an int value, where the boolean value states
        whether the passed interval was indeed bigger then the value specified by the Poller, in which case that is
        called an interval match, and the int value that tells how much the passed value has exceeded the one of the
        poller. In case the passed value has not exceeded the Poller value, the integer value will be negative.
        The update flag can be set to signal, that the interval value is supposed to be updated to the next value,
        returned by the generator.
        Args:
            interval: The numeric value for the interval, which is supposed to be compared to the value of the Poller
            update: The boolean flag to tell whether the interval value is supposed to be updated to the next
                generator value after the call or not

        Returns:
        A tuple (bool, int/float), where bool is whether the interval is exceeded, and int is how much exceeded
        """
        difference = interval - self.interval
        if difference < 0:
            return False, difference
        else:
            # Updating the interval value in case by setting the flag
            if update:
                self.keep_interval = False
            return True, difference

    @property
    def interval(self):
        """
        This is the getter method of the interval. The interval is a numeric value, that states the amount of seconds
        supposed to be between the individual poll calls.
        The function checks if the keep_interval flag is still set and returns the ild value in case it is, but
        updates the internal attribute with the new value of the generator function in case it is not.
        Notes:
            Since this is the generic Implementation of a poller there are a lot of possibilities by defining a
            generator for the series of new interval values, which means, that the interval values will most likely
            not be the same.

        Returns:
        The int/float value of the interval
        """
        if self.keep_interval:
            return self._interval
        else:
            # Updating the interval and then returning the new value
            self._update_interval()
            # Setting the flag to keep the new interval until it is exceeded the next time
            self.keep_interval = True
            return self._interval

    @property
    def poll_instruction(self):
        """
        This function will simply return the value of the attribute 'polling_instruction', which is supposed to be
        a function with a single parameter, that is the Connection of the poller, and a void return.
        Returns:
        The one parameter function passed as polling instruction
        """
        return self._poll_instruction

    @property
    def poll_function(self):
        """
        This function will simply return the value of the attribute if the 'polling_instruction', and is thus exactly
        the same as the property method for the 'polling_instruction' itself.
        Notes:
            The 'polling_instruction' property is enforced by the interface, but does not really specify what the
            instruction is by a clear property name, therefore this property should be used when using the
            GenericPoller consciously and the other when handling Poller's generically.
        Returns:
        The one parameter function passed as the polling instruction
        """
        return self.poll_instruction

    def _update_interval(self):
        """
        This function will update the private interval attribute of the object, by getting the next interval value from
        the generator function and then assigning that new value to the interval attribute.
        Will return the current value of the interval attribute, which means the value before the update
        Returns:
        The current value of the interval
        """
        current_value = self._interval
        next_interval = self._next_interval()
        self._assign_interval(next_interval)
        return current_value

    def _next_interval(self):
        """
        This function will simply call the interval generator of the Poller and therefore get the next interval, that
        is supposed to be used as the specified interval after which the poller should be sending a poll.
        Returns:
        The float/int value for the interval
        """
        return self.interval_generator()

    def _assign_interval(self, interval):
        """
        This function will assign the passed float/int value to the interval.
        Notes:
            This function does not type check, as it is supposed to be the correct type because the private function
            is only being handled by class internal implementation
        Args:
            interval: The int/float amount for the new value of the interval attribute

        Returns:
        void
        """
        # Assigning the new value to the interval attribute of the object
        self._interval = interval
