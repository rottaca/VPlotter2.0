


def overrides(interface_class):
    """Checks if a class method is correctly overridden."""
    def overrider(method):
        assert(method.__name__ in dir(interface_class))
        return method
    return overrider
