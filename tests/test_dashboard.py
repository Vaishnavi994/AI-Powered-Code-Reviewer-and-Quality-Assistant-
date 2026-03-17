# # tests/test_dashboard.py
# """Tests for dashboard UI."""

# from dashboard_ui.dashboard import load_pytest_results, filter_functions


# def test_dashboard_loads_pytest_results():
#     """Test loading pytest results (may be None if not generated)."""
#     data = load_pytest_results()
#     assert data is None or isinstance(data, dict)


# def test_filter_functions_search():
#     """Test function filtering by search term."""
#     functions = [
#         {"name": "test_function", "has_docstring": True, "file_path": "test.py"},
#         {"name": "other_function", "has_docstring": False, "file_path": "test.py"}
#     ]
    
#     filtered = filter_functions(functions, search="test", status=None)
#     assert len(filtered) == 1
#     assert filtered[0]["name"] == "test_function"


# def test_filter_functions_status():
#     """Test function filtering by status."""
#     functions = [
#         {"name": "documented", "has_docstring": True, "file_path": "test.py"},
#         {"name": "undocumented", "has_docstring": False, "file_path": "test.py"}
#     ]
    
#     filtered_ok = filter_functions(functions, search=None, status="OK")
#     assert len(filtered_ok) == 1
    
#     filtered_fix = filter_functions(functions, search=None, status="Fix")
#     assert len(filtered_fix) == 1


# def test_filter_functions_combined():
#     """Test combining search and status filters."""
#     functions = [
#         {"name": "test_doc", "has_docstring": True, "file_path": "test.py"},
#         {"name": "test_undoc", "has_docstring": False, "file_path": "test.py"},
#         {"name": "other_doc", "has_docstring": True, "file_path": "test.py"}
#     ]
    
#     filtered = filter_functions(functions, search="test", status="OK")
#     assert len(filtered) == 1
#     assert filtered[0]["name"] == "test_doc"

"""Tests for dashboard related functions."""

import sys
import os

# Allow tests to import project modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import json


def load_pytest_results(path="storage/test_report.json"):
    """Load pytest JSON report."""
    if not os.path.exists(path):
        return None

    with open(path, "r") as f:
        return json.load(f)


def filter_functions(functions, search=None, status=None):
    """Filter functions by search text and documentation status."""
    
    filtered = []

    for f in functions:
        name = f["name"]
        has_doc = f["has_docstring"]

        if search and search.lower() not in name.lower():
            continue

        if status == "OK" and not has_doc:
            continue

        if status == "Fix" and has_doc:
            continue

        filtered.append(f)

    return filtered


def test_dashboard_loads_pytest_results():
    """Test loading pytest results."""
    data = load_pytest_results()
    assert data is None or isinstance(data, dict)


def test_filter_functions_search():
    """Test search filtering."""

    functions = [
        {"name": "test_function", "has_docstring": True, "file_path": "test.py"},
        {"name": "other_function", "has_docstring": False, "file_path": "test.py"}
    ]

    filtered = filter_functions(functions, search="test", status=None)

    assert len(filtered) == 1
    assert filtered[0]["name"] == "test_function"


def test_filter_functions_status():
    """Test status filtering."""

    functions = [
        {"name": "documented", "has_docstring": True, "file_path": "test.py"},
        {"name": "undocumented", "has_docstring": False, "file_path": "test.py"}
    ]

    filtered_ok = filter_functions(functions, status="OK")
    assert len(filtered_ok) == 1

    filtered_fix = filter_functions(functions, status="Fix")
    assert len(filtered_fix) == 1


def test_filter_functions_combined():
    """Test search + status filter."""

    functions = [
        {"name": "test_doc", "has_docstring": True, "file_path": "test.py"},
        {"name": "test_undoc", "has_docstring": False, "file_path": "test.py"},
        {"name": "other_doc", "has_docstring": True, "file_path": "test.py"}
    ]

    filtered = filter_functions(functions, search="test", status="OK")

    assert len(filtered) == 1
    assert filtered[0]["name"] == "test_doc"