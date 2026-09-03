class BaseSNMPProfile:
    def collect(self, transport, target):
        raise NotImplementedError
