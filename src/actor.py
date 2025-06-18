from util.versionstamp import versionstamp

vm = versionstamp()

class Actor:
    def __init__(self, name: str):
        self.id = vm()
        self.name = name

