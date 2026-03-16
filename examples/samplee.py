def get_first_element(arr):
    """Returns the first element of the array."""
    return arr[0]

def find_max(arr):
    """Find max function.

    Args:
        arr: Description.

    Returns:
        Description.
    """
    mx = arr[0]
    for x in arr:
        if x > mx:
            mx = x
    return mx

def print_pairs(arr):
    """Print pairs function.

    Args:
        arr: Description.
    """
    n = len(arr)
    for i in range(n):
        for j in range(n):
            print(arr[i], arr[j])

def count_steps(n):
    """Count steps function.

    Args:
        n: Description.

    Returns:
        Description.
    """
    count = 0
    while n > 1:
        n //= 2
        count += 1
    return count

def log_inside_loop(n):
    """Log inside loop function.

    Args:
        n: Description.
    """
    for _ in range(n):
        x = n
        while x > 1:
            x //= 2

def sum_array(arr, n):
    """Sum array function.

    Args:
        arr: Description.
        n: Description.

    Returns:
        Description.
    """
    if n == 0:
        return 0
    return arr[n - 1] + sum_array(arr, n - 1)

def binary_search(arr, l, r, x):
    """Binary search function.

    Args:
        arr: Description.
        l: Description.
        r: Description.
        x: Description.

    Returns:
        Description.
    """
    if l > r:
        return -1
    mid = (l + r) // 2
    if arr[mid] == x:
        return mid
    elif arr[mid] < x:
        return binary_search(arr, mid + 1, r, x)
    else:
        return binary_search(arr, l, mid - 1, x)