# Contributing to NorwinMouseAssist

Thank you for your interest in contributing to NorwinMouseAssist! This project aims to help people with Parkinson's disease and other conditions that affect hand steadiness.

## How to Contribute

### Reporting Bugs

If you find a bug, please open an issue with:
- A clear description of the problem
- Steps to reproduce
- Expected vs actual behavior
- Your operating system and Python version
- Any error messages or logs

### Suggesting Features

We welcome feature suggestions! Please open an issue describing:
- The feature you'd like to see
- Why it would be helpful
- How you envision it working

### Code Contributions

1. **Fork the repository**
2. **Create a branch** for your feature or fix
   ```bash
   git checkout -b feature/your-feature-name
   ```
3. **Make your changes**
   - Follow the existing code style
   - Add comments for complex logic
   - Test your changes thoroughly
4. **Commit your changes**
   ```bash
   git commit -m "Add feature: description"
   ```
5. **Push to your fork**
   ```bash
   git push origin feature/your-feature-name
   ```
6. **Open a Pull Request**

## Development Setup

```bash
# Clone the repository
git clone https://github.com/NorwinLabs/NorwinMouseAssist.git
cd NorwinMouseAssist

# Install dependencies
pip install -r requirements.txt

# Run the application
python main.py
```

## Code Style Guidelines

- Follow PEP 8 style guide for Python code
- Use descriptive variable and function names
- Add docstrings to classes and functions
- Keep functions focused and concise
- Comment complex algorithms or non-obvious logic

## Testing

- Test your changes on your platform
- If possible, test on multiple operating systems
- Ensure the application starts without errors
- Verify that smoothing works as expected with your changes

## Areas for Contribution

Here are some areas where contributions would be especially valuable:

### Features
- Additional smoothing algorithms
- Preset profiles for different conditions
- Keyboard shortcut to toggle smoothing
- System tray integration
- Multiple monitor support improvements
- Logging and diagnostics

### Platform Support
- Testing and fixes for macOS
- Testing and fixes for different Linux distributions
- Wayland support improvements

### UI/UX
- Accessibility improvements
- Alternative UI frameworks
- Better visual feedback
- Help system or tutorial

### Documentation
- More detailed usage guides
- Video tutorials
- Translations to other languages
- Better screenshots and examples

## Questions?

Feel free to open an issue with the "question" label if you need clarification or help getting started.

## Code of Conduct

Please be respectful and constructive in all interactions. This project is dedicated to helping people, and we want the community to reflect that mission.
