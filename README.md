# Order Management System

This is a simple order management system that simulates the process of sending orders to an exchange and handling responses.

## Usage

```python
python scripts/order_management.py
```
Test files can be tested by running the following:
```python
python -m unittest tests/test_unit.py
python -m unittest tests/test_integration.py
```
NOTE: For integration testing, make sure the acceptance time configured is correct for the time it is being tested in. It only checks whether the pipeline works correctly and tests will fail in case we are checking out of the acceptance window.

