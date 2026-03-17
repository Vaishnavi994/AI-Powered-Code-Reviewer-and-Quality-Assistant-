import ast

def analyze_function(function_node):

    params = [arg.arg for arg in function_node.args.args]

    returns_value = False
    nested_loops = 0
    is_recursive = False

    for node in ast.walk(function_node):

        if isinstance(node, ast.Return):
            if node.value is not None:
                returns_value = True

        if isinstance(node, (ast.For, ast.While)):
            nested_loops += 1

        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                if node.func.id == function_node.name:
                    is_recursive = True

    return {
        "params": params,
        "returns_value": returns_value,
        "loops": nested_loops,
        "recursive": is_recursive
    }

import os
from parser.file_parser import parse_path
import ast


def analyze_directory(directory):
    """Analyze all functions in a directory."""

    parsed_files = parse_path(directory)

    results = []

    for file in parsed_files:

        file_path = file["file_path"]

        with open(file_path, "r", encoding="utf-8") as f:
            source = f.read()

        tree = ast.parse(source)

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):

                analysis = analyze_function(node)

                results.append({
                    "file": file_path,
                    "function": node.name,
                    **analysis
                })

    return results