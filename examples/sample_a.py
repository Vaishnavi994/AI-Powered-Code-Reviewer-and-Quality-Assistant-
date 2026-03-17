def calculate_average(numbers):
    """
    Calculate the average of a list of numbers.

    :param numbers: A list of numbers.
    :type numbers: list
    :return: The average of the numbers.
    :rtype: float
    """
    total = 0
    for n in numbers:
        total += n
    if len(numbers) == 0:
        return 0
    return total / len(numbers)

def add(a: int, b: int) -> int:
    """
    This function adds two integers.

    :param a: The first integer to add.
    :type a: int
    :param b: The second integer to add.
    :type b: int
    :return: The sum of a and b.
    :rtype: int
    """
    return a + b

class Processor:

    def process(self, data):
        """
        Process the given data.

        :param data: The data to be processed
        :type data: iterable
        :return: None
        :rtype: None
        """
        for item in data:
            if item is None:
                continue
            print(item)
