

class BaseStrategy:

    name = 'BASE_STRATEGY'

    def __init__(self):
        pass

    def __call__(self, *args, **kwargs):
        pass

    def __str__(self):
        return '<%s>' % self.name
