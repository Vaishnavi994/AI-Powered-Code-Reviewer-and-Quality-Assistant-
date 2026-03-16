def constant_time(n):
    """
    --- 
    Function to return a constant value.
    ---
    Parameters
    ----------
    n : int
        Input number (not used in the function).
    Returns
    ----------
    int
        The sum of two constants (10 and 20).
    """
    x = 10
    y = 20
    return x + y





def print():
    """
    --- 
    Parameters
    ----------
    None

    Returns
    -------
    None
    """


def linear_time(n):
    """
    --- 
    Parameters
    ----------
    n : int
        The number of iterations to print.

    Returns
    -------
    None
        This function does not return any value, it prints numbers from 0 to n-1.
    """
    for i in range(n):
        print(i)


def quadratic_time(n):
    """
    --- 
    Quadratic Time Function
    ---
    Parameters
    ----------
    n : int
        The number of iterations for both loops.

    Returns
    -------
    None
        This function does not return any value, it prints the iteration indices instead.
    """
    for i in range(n):
        for j in range(n):
            print(i, j)






def cubic_time(n):
    """
    --- 
    Parameters
    ----------
    n : int
        The number of iterations for each loop.

    Returns
    ----------
    None
        This function does not return any value, it prints the indices of the nested loops.
    """
    for i in range(n):
        for j in range(n):
            for k in range(n):
                print(i, j, k)


def log_time(n):
    """
    --- 
    Parameters
    ----------
    n : int
        The input number to be reduced by half until it is less than or equal to 1.

    Returns
    ----------
    None
        This function does not return any value, it only performs the operation in-place.
    """
    while n > 1:
        n //= 2


def n_log_n_time(n):
    """
    --- 
    Parameters
    ----------
    n : int
        The input number.

    Returns
    ----------
    None
        This function does not return any value, it is used to demonstrate a time complexity of O(n log n).
    """
    for i in range(n):
        m = n
        while m > 1:
            m //= 2


def n2_log_n_time(n):
    """
    --- 
    Function to demonstrate n^2 log n time complexity.

    Parameters
    ----------
    n : int
        The input number that determines the number of iterations.

    Returns
    ----------
    None
    """
    for i in range(n):
        for j in range(n):
            m = n
            while m > 1:
                m //= 2


def early_break(n):
    """
    --- 
    Parameters
    ----------
    n : int
        The number of iterations.

    Returns
    ----------
    None
        The function does not return any value, it breaks the loop when i equals 5.
    """
    for i in range(n):
        if i == 5:
            break


def conditional_loop(n):
    """
    --- 
    Parameters
    ----------
    n : int
        The number of iterations for the outer loop.

    Returns
    ----------
    None
        This function does not return any value, it prints the results directly to the console.
    """
    for i in range(n):
        if i % 2 == 0:
            for j in range(n):
                print(i, j)


def recursive_linear(n):
    """
    --- 
    Parameters
    ----------
    n : int
        The input number for the recursive linear function.

    Returns
    ----------
    None
        The function does not return any value.
    """
    if n == 0:
        return


def recursive_log(n):
    """
    --- 
    Parameters
    ----------
    n : int
        The input number for the recursive logarithm calculation.

    Returns
    ----------
    None
        This function does not return any value, it is used for recursive calculation purposes.
    """
    if n <= 1:
        return
    recursive_log(n // 2)
