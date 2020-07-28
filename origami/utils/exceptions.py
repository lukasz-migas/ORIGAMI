# Third-party imports
from pubsub import pub

# Local imports
from origami.gui_elements.misc_dialogs import DialogBox


class IncorrectValueError(Exception):
    pass


class NoIonMobilityDatasetError(Exception):
    pass


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
        self.message = message

        DialogBox(title, message, kind="Error")


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
