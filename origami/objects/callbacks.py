# Standard library imports
from inspect import signature


class PropertyCallbackManager:
    """A mixin class to provide an interface for registering and triggering callbacks"""

    def __init__(self, *args, **kw):
        super(PropertyCallbackManager, self).__init__(*args, **kw)
        self._callbacks = dict()
        self._block_trigger = False

    def on_change(self, event, *callbacks):
        """Add a callback on this object to trigger when ``attr`` changes.

        Parameters
        ----------
        event : str
            an attribute name on this object
        callbacks : List[callable]
            a callback function to register
        """
        if len(callbacks) == 0:
            raise ValueError("on_change takes an attribute name and one or more callbacks, got only one parameter")

        _callbacks = self._callbacks.setdefault(event, [])
        for callback in callbacks:
            if callback in _callbacks:
                continue

            _check_callback(callback, ["event", "metadata"])
            _callbacks.append(callback)

    def remove_on_change(self, event, *callbacks):
        """ Remove a callback from this object """
        if len(callbacks) == 0:
            raise ValueError(
                "remove_on_change takes an attribute name and one or more callbacks, got only one parameter"
            )
        _callbacks = self._callbacks.setdefault(event, [])
        for callback in callbacks:
            _callbacks.remove(callback)

    def clear_on_change(self, event):
        """Removes all callbacks from this object"""
        if event not in self._callbacks:
            raise ValueError(f"Event `{event}` not in callbacks")

        self._callbacks[event].clear()

    def trigger(self, event, metadata):
        """Trigger callbacks for ``attr`` on this object.

        Parameters
        ----------
        event : str
            name of the event being triggered
        metadata : Any
            any valid Python object
        """

        def invoke():
            callbacks = self._callbacks.get(event)
            if callbacks:
                for callback in callbacks:
                    callback(event, metadata)

        # prevent invocation of the trigger function
        if self._block_trigger:
            return
        invoke()


def format_signature(sig):
    return str(sig)


def get_param_info(sig):
    defaults = []
    for param in sig.parameters.values():
        if param.default is not param.empty:
            defaults.append(param.default)
    return list(sig.parameters), defaults


def _nargs(fn):
    sig = signature(fn)
    all_names, default_values = get_param_info(sig)
    return len(all_names) - len(default_values)


def _check_callback(callback, fargs, what="Callback functions"):
    """Check callback signature"""
    sig = signature(callback)
    formatted_args = format_signature(sig)
    error_msg = what + " must have signature func(%s), got func%s"

    all_names, default_values = get_param_info(sig)
    nargs = len(list(all_names)) - len(default_values)
    if nargs != len(fargs):
        raise ValueError(error_msg % (", ".join(fargs), formatted_args))
