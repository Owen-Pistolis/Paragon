from automation_runner import AutomationRunner
import logging
import os
import sys

def setup_logging():
    """Setup logging configuration"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('automation.log')
        ]
    )

def ensure_directories():
    """Ensure required directories exist"""
    os.makedirs('C:\\temp', exist_ok=True)

def main():
    try:
        # Setup logging
        setup_logging()
        logger = logging.getLogger(__name__)
        
        # Ensure required directories exist
        ensure_directories()
        
        # Get absolute path to workflow file
        current_dir = os.path.dirname(os.path.abspath(__file__))
        workflow_path = os.path.join(current_dir, "test_workflow.json")
        
        if not os.path.exists(workflow_path):
            logger.error(f"Workflow file not found: {workflow_path}")
            return
        
        # Create and run automation
        logger.info("Starting automation runner")
        runner = AutomationRunner()
        runner.last_mouse_positions = []
        runner.run(workflow_path)
        
    except Exception as e:
        logger.error(f"Error running automation: {str(e)}", exc_info=True)

if __name__ == "__main__":
    main()