"""
simulation package

This package is the deterministic "world engine":
- It applies Actions to the world state.
- It updates relation values (-100..100).
- It returns only the delta changes for UI/clients.
- It does NOT call LLMs.
- It does NOT own DB sessions (DB layer persists updates).
"""