"""numpy stand-in - main.py only uses np.array() as a list wrapper."""


def array(x, *a, **k):
    return list(x)


def asarray(x, *a, **k):
    return list(x)
