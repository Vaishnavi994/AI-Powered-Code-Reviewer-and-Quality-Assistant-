# import ast

# def get_function_node(tree, function_name):

#     for node in ast.walk(tree):

#         if isinstance(node, ast.FunctionDef) and node.name == function_name:
#             return node

#     return None
import ast
import os


def get_function_node(tree, function_name):
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == function_name:
            return node
    return None


def parse_file(file_path):
    """Parse a Python file and extract function metadata."""

    with open(file_path, "r", encoding="utf-8") as f:
        source = f.read()

    tree = ast.parse(source)

    functions = []

    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):

            args = []
            for arg in node.args.args:
                args.append({
                    "name": arg.arg
                })

            functions.append({
                "name": node.name,
                "args": args,
                "has_docstring": ast.get_docstring(node) is not None
            })

    return {
        "file_path": file_path,
        "functions": functions
    }


def parse_path(path):
    """Parse all Python files in a folder."""

    results = []

    if not os.path.exists(path):
        return results

    for root, _, files in os.walk(path):
        for file in files:
            if file.endswith(".py"):
                full_path = os.path.join(root, file)
                results.append(parse_file(full_path))

    return results