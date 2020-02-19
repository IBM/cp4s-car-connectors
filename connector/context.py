from car_service import CarService

class Context(object):
    def __init__(self, args, source):
        self.args = args
        self.source = source
        self.car_service = CarService(self)
        