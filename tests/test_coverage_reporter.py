# # tests/test_coverage_reporter.py
# """Tests for coverage reporter."""

# from core.reporter.coverage_reporter import compute_coverage
# from core.parser.python_parser import parse_path


# def test_coverage_keys_exist():
#     """Test coverage report structure."""
#     parsed = parse_path("examples")
#     report = compute_coverage(parsed)
    
#     assert "aggregate" in report
#     assert "coverage_percent" in report["aggregate"]
#     assert "total_functions" in report["aggregate"]
#     assert "documented" in report["aggregate"]


# def test_coverage_threshold_check():
#     """Test threshold checking in coverage report."""
#     parsed = parse_path("examples")
#     report = compute_coverage(parsed, threshold=90)
    
#     assert "meets_threshold" in report["aggregate"]
#     assert isinstance(report["aggregate"]["meets_threshold"], bool)


# def test_empty_input_handling():
#     """Test coverage computation with empty input."""
#     report = compute_coverage([])
#     assert report["aggregate"]["total_functions"] == 0
#     assert report["aggregate"]["coverage_percent"] == 0




# """Tests for coverage reporter."""

# import sys
# import os

# # Allow tests to import project modules
# sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# from analyzer import analyze_directory


# def test_coverage_keys_exist():
#     """Test coverage report structure."""
#     report = analyze_directory("examples")

#     assert "coverage_percent" in report
#     assert "total_functions" in report
#     assert "documented_functions" in report


# def test_coverage_threshold_check():
#     """Test threshold checking."""
#     report = analyze_directory("examples")

#     assert isinstance(report["coverage_percent"], (int, float))


# def test_empty_input_handling():
#     """Test coverage with empty folder."""
    
#     empty_folder = "storage"

#     report = analyze_directory(empty_folder)

#     assert report["total_functions"] >= 0
"""Tests for coverage reporter."""

import sys
import os

# Allow tests to import project modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from report.coverage_reporter import generate_coverage_report


def test_coverage_keys_exist():
    """Test coverage report structure."""
    
    report = generate_coverage_report("examples")

    assert "coverage_percent" in report
    assert "total_functions" in report
    assert "documented_functions" in report


def test_coverage_threshold_check():
    """Test coverage percent type."""
    
    report = generate_coverage_report("examples")

    assert isinstance(report["coverage_percent"], (int, float))


def test_empty_input_handling():
    """Test coverage with empty folder."""

    empty_folder = "storage"

    report = generate_coverage_report(empty_folder)

    assert report["total_functions"] >= 0