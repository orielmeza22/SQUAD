import sys
import io

# Force UTF-8 encoding for standard output/error to prevent UnicodeEncodeError with emojis on Windows
if sys.platform.startswith('win'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except AttributeError:
        # Fallback if reconfigure is not available
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

import uvicorn
from src.api import create_app
from src.utils.helpers import setup_logging, load_config


def main():

    """Run the SQUAD application."""
    # Setup logging
    logger = setup_logging()
    logger.info("Starting SQUAD...")
    
    # Load configuration
    config = load_config()
    logger.info(f"Loaded configuration: {config}")
    
    # Create and run application
    app = create_app()
    uvicorn.run(app, host="0.0.0.0", port=8000)


if __name__ == "__main__":
    main()
