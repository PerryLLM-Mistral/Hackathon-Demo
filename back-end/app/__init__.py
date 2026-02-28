"""
multi_llm package

This package is responsible for *decision making* only:
- It takes a WorldState snapshot and outputs a list of Actions.
- It does NOT read/write the database.
- It does NOT apply consequences (simulation does that).
"""