"""Main entry point for SQUAD refactored version."""

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
