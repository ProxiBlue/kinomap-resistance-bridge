# Contributing

Thanks for your interest in contributing! Every non-smart bike is different, so community contributions are particularly valuable.

## Ways to Contribute

### Share Your Bike Configuration
If you've adapted this for a different bike model:
1. Document your bike's button circuit (voltage, current, switch type)
2. Share your `config/local.yaml` settings
3. Note any hardware modifications needed
4. Submit a PR adding your bike to a `configs/` directory

### Report Issues
- Include your RPi model, OS version, and Python version
- Attach relevant log output
- Describe your bike model and button type

### Code Contributions
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/my-improvement`)
3. Test your changes on actual hardware if possible
4. Submit a pull request with a clear description

## Code Style

- Python: Follow PEP 8, use type hints where practical
- Keep functions focused and well-named
- Add docstrings to public functions
- Update documentation if you change behavior

## Testing

```bash
# Run unit tests (no hardware needed)
python -m pytest tests/

# Run hardware tests (RPi with relay wired)
python scripts/test_buttons.py
```
