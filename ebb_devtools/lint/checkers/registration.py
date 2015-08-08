import venusian


def register_checker(pattern):
    def deco(func):
        def callback(scanner, name, obj):
            scanner.register(pattern, obj)
        venusian.attach(func, callback)
        return func
    return deco
