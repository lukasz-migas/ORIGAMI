# Third-party imports
from pubsub import pub

# Local imports
from origami.gui_elements.misc_dialogs import DialogBox


class IncorrectValueError(Exception):
    """Exception raised if incorrect value was specified"""


class NoIonMobilityDatasetError(Exception):
    """Exception raised if dataset has no ion mobility"""


class IncorrectPlotTypeError(Exception):
    """Exception raised if incorrect plot type is being plotted"""

    def __init__(self, message):
        self.message = message
        pub.sendMessage("notify.message.error", message=message)


class PlotTypeNotPlottedWarning(Warning):
    """Exception raised if plot of the requested type has not been plotted yet"""

    def __init__(self, message):
        self.message = message
        pub.sendMessage("notify.message.warning", message=message)


class MessageError(Exception):
    """Exception raised for errors in the input.

    Attributes:
        expression -- input expression in which the error occurred
        message -- explanation of the error

    Usage:
        raise MessageError("Title", "Message")
    """

    def __init__(self, title, message):
        self.title = title
        self.message = str(message)

        DialogBox(self.title, self.message, kind="Error")


class NotificationError(Exception):
    """Exception raised for errors in the input.

    Attributes:
        expression -- input expression in which the error occurred
        message -- explanation of the error

    Usage:
        raise MessageError("Title", "Message")
    """

    def __init__(self, message):
        self.message = message

        pub.sendMessage("notify.message.warning", message=message)
