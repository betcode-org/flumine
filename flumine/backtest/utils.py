class PendingPackages(list):
    """List which only returns packages
    which haven't been processed.
    """

    def __iter__(self):
        return (x for x in list.__iter__(self) if not x.processed)
