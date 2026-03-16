def get_first_element(arr):
    '''Returns the first element of the array.'''
    return arr[0]
def find_max(arr):
    mx = arr[0]
    for x in arr:
        if x > mx:
            mx = x
    return mx

def print_pairs(arr):
    '''Prints all pairs of elements in the array.'''
    n = len(arr)
    for i in range(n):
        for j in range(n):
            print(arr[i], arr[j])

def count_steps(n):
    count = 0
    while n > 1:
        n //= 2
        count += 1
    return count

def log_inside_loop(n):
    '''Example of a function with a logarithmic loop inside a linear loop.'''
    for _ in range(n):
        x = n
        while x > 1:
            x //= 2


def sum_array(arr, n):
    if n == 0:
        return 0
    return arr[n-1] + sum_array(arr, n-1)


def binary_search(arr, l, r, x):
    if l > r:
        return -1

    mid = (l + r) // 2

    if arr[mid] == x:
        return mid
    elif arr[mid] < x:
        return binary_search(arr, mid + 1, r, x)
    else:
        return binary_search(arr, l, mid - 1, x)
    


# def merge_sort(arr):
#     if len(arr) <= 1:
#         return arr

#     mid = len(arr) // 2
#     left = merge_sort(arr[:mid])
#     right = merge_sort(arr[mid:])

#     return merge(left, right)   # merging takes O(n)