def calculate_average(numbers):
    """
    Calculates the average of a list of numbers.

    Args:
    numbers (list): A list of numbers to calculate the average from.

    Returns:
    float: The average of the input numbers.
    """
    total = 0
    for n in numbers:
        total += n
    if len(numbers) == 0:
        return 0
    return total / len(numbers)

def add(a: int, b: int) -> int:
    """
    --- 
    Parameters
    ----------
    a : int
        The first integer to add.
    b : int
        The second integer to add.
    Returns
    ----------
    int
        The sum of a and b.
    """
    return a + b

class Processor:

    def process(self, data):
        """This function processes the given data by printing each item.

        :param data: The data to be processed, expected to be an iterable.
        :type data: iterable
        :rtype: None."""
        for item in data:
            if item is None:
                continue
            print(item)