class Undefined:
    singlton = None

    def __init__(self):
        if self.singlton is not None:
            raise Exception("Undefined is singleton.")
        self.__class__.singlton = self

    def __str__(self):
        return "undefined"

    def __eq__(self, o: object) -> bool:
        if self is o:
            return True
        else:
            return False


undefined = Undefined()
