# Agent Instructions

This repository is an AI training gym & arena to train agents playing generalized variants of chess.

It exposes a central GUI in `./app.py` allowing players to play against the AI in their chosen Chess variant or organize tournaments opposing the AIs of their choice.

## Repository layout

- `./app.py`: central GUI, built with `gradio`,
- `./jedrezito/`: packaged & reusable code.
- `./docs/`: user-facing documentation.

## Language

- **Code, docstrings & filenames**: English.
- **User conversation**: English.
- **User-facing doc**: French.
- **GUI text**: French.
- **Git operations**: English.

## Test suite

Test suite is run with `pytest`, and contains one script for each class/method tested. The name of the script should reveal the object tested (e.g. `test_xxx.py` for method `xxx` method).

Test scripts should consist in **unitary** tests. This means that each test of the class should test *one, and one only** functionality. In particular, **no unit test should contain multiple assertions**.

## CI

The CI runs scripts with GitHub Actions. They should all be executed in the following cases:

- when pushing on `main`,
- when a PR is proposed on `main`,
- via a manual execution in GitHub platform.

Current scripts:

- `docs`: build & deploy user-facing doc,
- `tests`: runs test suite.