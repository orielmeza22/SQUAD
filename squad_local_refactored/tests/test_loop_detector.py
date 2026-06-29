import pytest
from squad_local_refactored.src.tools.loop_detector import LoopDetector


def test_loop_detector_no_loop():
    detector = LoopDetector(trigger_threshold=3)

    # Different traceback errors
    assert detector.register_error("NameError: name 'app' is not defined") is False
    assert detector.register_error("SyntaxError: invalid syntax") is False
    assert detector.register_error("TypeError: 'int' object is not callable") is False


def test_loop_detector_with_loop():
    detector = LoopDetector(trigger_threshold=3)

    # Register same error consecutively
    assert detector.register_error("NameError: name 'app' is not defined") is False
    assert detector.register_error("NameError: name 'app' is not defined") is False
    
    # 3rd consecutive identical error triggers loop detection
    assert detector.register_error("NameError: name 'app' is not defined") is True


def test_loop_detector_parser_extraction():
    detector = LoopDetector()
    
    traceback_sample = """
Traceback (most recent call last):
  File "<stdin>", line 2, in <module>
NameError: name 'conn' is not defined
"""
    parsed = detector._parse_error(traceback_sample)
    assert parsed is not None
    assert parsed[0] == "NameError"
    assert parsed[1] == "name 'conn' is not defined"
    assert parsed[2] == "line 2"
