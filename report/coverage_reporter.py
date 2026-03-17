from parser.analyzer import analyze_directory


# def generate_coverage_report(directory):
#     """
#     Generate documentation coverage statistics for a directory.
#     """

#     # Analyze all functions
#     results = analyze_directory(directory)

#     total_functions = len(results)

#     # Handle empty directories
#     if total_functions == 0:
#         return {
#             "coverage_percent": 0,
#             "total_functions": 0,
#             "documented_functions": 0
#         }

#     documented_functions = 0

#     for fn in results:
#         # If a function has parameters or returns value, count it as documented
#         if fn.get("params") or fn.get("returns_value"):
#             documented_functions += 1

#     coverage_percent = (documented_functions / total_functions) * 100

#     return {
#         "coverage_percent": round(coverage_percent, 2),
#         "total_functions": total_functions,
#         "documented_functions": documented_functions
#     }



def generate_coverage_report(directory):

    results = analyze_directory(directory)

    total_functions = len(results)

    if total_functions == 0:
        return {
            "coverage_percent": 0,
            "total_functions": 0,
            "documented_functions": 0
        }

    documented_functions = 0

    for fn in results:
        if fn.get("has_docstring"):
            documented_functions += 1

    coverage_percent = (documented_functions / total_functions) * 100

    return {
        "coverage_percent": round(coverage_percent, 2),
        "total_functions": total_functions,
        "documented_functions": documented_functions
    }