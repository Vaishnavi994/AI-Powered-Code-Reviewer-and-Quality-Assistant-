# import ast
# import json
# import os

# def extract_functions(file_path):
#     with open(file_path, "r", encoding="utf-8") as f:
#         source = f.read()

#     tree = ast.parse(source)
#     results = []

#     for node in ast.walk(tree):
#         if isinstance(node, ast.FunctionDef):
#             start_line = node.lineno
#             end_line = max(
#                 [n.lineno for n in ast.walk(node) if hasattr(n, "lineno")],
#                 default=start_line
#             )

#             cyclomatic = 1
#             for child in ast.walk(node):
#                 if isinstance(child, (ast.If, ast.For, ast.While, ast.And, ast.Or)):
#                     cyclomatic += 1

#             docstring = ast.get_docstring(node)
#             has_docstring = docstring is not None

#             results.append({
#                 "file_name": os.path.basename(file_path),  # Added file name
#                 "function_name": node.name,
#                 "start_line": start_line,
#                 "end_line": end_line,
#                 "cyclomatic_complexity": cyclomatic,
#                 "has_docstring": has_docstring
#             })

#     return results


# def save_json(results, output_file="functions.json"):
#     with open(output_file, "w", encoding="utf-8") as f:
#         json.dump(results, f, indent=4)





import ast
import json
import os
import re


def is_snake_case(name):
    return re.match(r'^[a-z_][a-z0-9_]*$', name) is not None


def extract_functions(file_path, original_name=None):
    with open(file_path, "r", encoding="utf-8") as f:
        source = f.read()
        lines = source.splitlines()

    tree = ast.parse(source)
    results = []

    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):

            start_line = node.lineno
            end_line = max(
                [n.lineno for n in ast.walk(node) if hasattr(n, "lineno")],
                default=start_line
            )

            # Cyclomatic Complexity
            cyclomatic = 1
            for child in ast.walk(node):
                if isinstance(child, (ast.If, ast.For, ast.While, ast.And, ast.Or)):
                    cyclomatic += 1

            # Missing Docstring
            docstring = ast.get_docstring(node)
            has_docstring = docstring is not None
            missing_docstring = not has_docstring

            # Excess Empty Lines
            function_lines = lines[start_line - 1:end_line]
            empty_lines = sum(1 for line in function_lines if line.strip() == "")
            excess_empty_lines = empty_lines > 2

            # Improper Variable Naming
            bad_variable_names = []
            for child in ast.walk(node):
                if isinstance(child, ast.Name) and isinstance(child.ctx, ast.Store):
                    if not is_snake_case(child.id):
                        bad_variable_names.append(child.id)

            improper_variable_naming = len(bad_variable_names) > 0

            # High Complexity
            high_complexity = cyclomatic > 5

            # Collect Errors
            errors = []

            if missing_docstring:
                errors.append("Missing Docstring")

            if excess_empty_lines:
                errors.append("Excess Empty Lines")

            if improper_variable_naming:
                errors.append("Improper Variable Naming")

            if high_complexity:
                errors.append("High Cyclomatic Complexity")

            results.append({
                "file_name": original_name if original_name else os.path.basename(file_path),
                "function_name": node.name,
                "start_line": start_line,
                "end_line": end_line,
                "cyclomatic_complexity": cyclomatic,
                "has_docstring": has_docstring,
                "missing_docstring": missing_docstring,
                "excess_empty_lines": excess_empty_lines,
                "improper_variable_naming": improper_variable_naming,
                "high_complexity": high_complexity,
                "errors": errors
            })

    return results


def save_json(results, output_file="functions.json"):
    # Remove error flags from exported JSON
    clean_results = []
    for r in results:
        clean_results.append({
            "file_name": r["file_name"],
            "function_name": r["function_name"],
            "start_line": r["start_line"],
            "end_line": r["end_line"],
            "cyclomatic_complexity": r["cyclomatic_complexity"],
            "has_docstring": r["has_docstring"]
        })

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(clean_results, f, indent=4)