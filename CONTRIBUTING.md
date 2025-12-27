# Contributing to GreenChain

Thank you for your interest in contributing to GreenChain! 🌱

## Getting Started

1. **Fork the repository** on GitHub
2. **Clone your fork** locally:
   ```bash
   git clone https://github.com/YOUR_USERNAME/greenchain-agent.git
   cd greenchain-agent
   ```
3. **Install dependencies**:
   ```bash
   pip install -r backend/requirements.txt
   ```
4. **Set up environment**:
   ```bash
   cp .env.example .env.local
   # Add your API keys to .env.local
   ```

## Development Workflow

1. Create a feature branch:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. Make your changes and test locally:
   ```bash
   streamlit run app.py
   ```

3. Commit your changes with clear messages:
   ```bash
   git commit -m "Add: description of your change"
   ```

4. Push to your fork and create a Pull Request

## Code Style

- Follow PEP 8 for Python code
- Use meaningful variable and function names
- Add docstrings to functions and classes
- Keep functions focused and single-purpose

## Project Structure

```
greenchain-agent/
├── app.py                 # Main Streamlit application
├── translations.py        # Multi-language support
├── backend/
│   ├── src/
│   │   ├── agents/        # AI agent implementations
│   │   └── services/      # Backend services (satellite, weather, LLM)
│   └── requirements.txt   # Python dependencies
└── output/                # Generated certificates (gitignored)
```

## Reporting Issues

- Use GitHub Issues for bug reports and feature requests
- Include reproduction steps for bugs
- Provide context about your environment

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

**Thank you for helping make sustainable agriculture more accessible!** 🌍
