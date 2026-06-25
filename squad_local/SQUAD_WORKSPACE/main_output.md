# archivo test.py
import pytest

def mi_funcion():
    return True

def test_mi_funcion():
    assert mi_funcion() == True
