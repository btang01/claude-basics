# Create virtual environment
python3 -m venv claude-env

# Activate it
source claude-env/bin/activate  # On macOS/Linux
# or
claude-env\Scripts\activate     # On Windows

# Install fastmcp
pip install fastmcp

# Also install anthropic if you haven't
pip install anthropic

pip install aiohttp

# every new terminal, go into the same venv
source claude-env/bin/activate
