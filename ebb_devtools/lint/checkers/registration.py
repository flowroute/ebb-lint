import venusian


def register_checker(pattern, **extra):
    def deco(func):
        def callback(scanner, name, obj):
            scanner.register(pattern, obj, extra)
        venusian.attach(func, callback)
        return func
    return deco
