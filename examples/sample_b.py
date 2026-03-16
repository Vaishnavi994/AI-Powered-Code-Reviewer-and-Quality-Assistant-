def generator_example(n):
    """Generator example function.

    Args:
        n: Description.
    """
    for i in range(n):
        yield i

def raises_example(x):
    
    if x < 0:
        raise ValueError('negative')
    return x * 2