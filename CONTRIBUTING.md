# Contributing to VDA

First off, thank you for considering contributing to VDA! It's people like you that make open-source projects a great community to learn, inspire, and create.

This project is open-sourced under the **GNU General Public License v3.0**, meaning that any modifications or larger works that distribute this code must also be open-source under the same license.

## How Can I Contribute?

### Reporting Bugs
If you find a bug, please create an issue on GitHub. Make sure to include:
- Your Operating System and Python version.
- The AI provider/model you were using.
- A clear, detailed description of the problem.
- Any error logs from `~/.vda-desktop/app.log`.

### Suggesting Enhancements
Have an idea to make VDA better? We'd love to hear it! Open an issue outlining your proposal. If you have an idea for how to implement it, feel free to describe the technical approach.

### Code Contributions
1. **Fork the repo** and create your branch from `latest`.
2. **Install dependencies** as described in `README.md`.
3. **Make your changes**: 
   - Keep the codebase Python 3.9+ compatible.
   - We use `PyQt6` for UI and do not intend to switch frameworks.
   - Make sure your changes don't break existing agent fallback mechanisms (e.g., SIFT, OCR).
4. **Test your changes**: Run the app locally and test the UI and agent loops.
5. **Issue that pull request!** Ensure your PR description clearly describes the problem and solution.

## Code Style
- Use `black` for code formatting (max line length 100).
- Use `ruff` for linting.
- Ensure all new methods have type hints and docstrings.

We look forward to reviewing your contributions!
