def calculate_average(numbers):

    total = 0
    for n in numbers:
        total += n
    if len(numbers) == 0:
        return 0
    return total / len(numbers)

def add(a: int, b: int) -> int:
    """
    This function adds two integers.

    Parameters
    ----------
    a : int
    The first integer to add.
    b : int
    The second integer to add.

    Returns
    -------
    int
    The sum of a and b.
    """
    return a + b

class Processor:

    def process(self, data):
        """
        Process the given data by printing each non-None item.

        Parameters
        ----------
        data : iterable
        The input data to be processed.

        Returns
        ----------
        None
        This function does not return any value.
        """
        for item in data:
            if item is None:
                continue
            print(item)
