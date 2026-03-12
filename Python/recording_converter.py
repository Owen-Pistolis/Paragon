import json
import time
from datetime import datetime
import logging
import os

def convert_recording_to_workflow(recording_data):
    """
    Convert raw recording data to workflow format.
    
    Args:
        recording_data (list): Raw recording data from system_recording.py
        
    Returns:
        dict: Workflow data in the format workflow_system.py can handle
    """
    try:
        workflow = {
            "name": f"Recorded_Workflow_{int(time.time())}",
            "actions": []
        }
        
        # Track state for combining actions
        current_typing_sequence = []
        last_action_time = None
        typing_timeout = 1.0  # Seconds between keystrokes to consider a new sequence
        
        for action in recording_data:
            action_type = action.get('type')
            timestamp = action.get('timestamp', 0)
            
            # Skip actions without proper type or details
            if not action_type or 'details' not in action:
                continue
                
            details = action.get('details', {})
            
            # Handle different action types
            if action_type in ['keystroke', 'special_key_press']:
                # Combine keystrokes into typing sequences
                if last_action_time and (timestamp - last_action_time) > typing_timeout:
                    # Add the completed typing sequence
                    if current_typing_sequence:
                        workflow["actions"].append(create_typing_sequence_action(current_typing_sequence))
                        current_typing_sequence = []
                
                current_typing_sequence.append(details)
                last_action_time = timestamp
                
            elif action_type in ['left_click', 'right_click']:
                # First, add any pending typing sequence
                if current_typing_sequence:
                    workflow["actions"].append(create_typing_sequence_action(current_typing_sequence))
                    current_typing_sequence = []
                
                # Add mouse click action
                workflow["actions"].append(create_mouse_action(action_type, details))
                
            elif action_type == 'window_focus':
                # Add window focus change
                if current_typing_sequence:
                    workflow["actions"].append(create_typing_sequence_action(current_typing_sequence))
                    current_typing_sequence = []
                    
                workflow["actions"].append(create_window_action(details))
        
        # Add any remaining typing sequence
        if current_typing_sequence:
            workflow["actions"].append(create_typing_sequence_action(current_typing_sequence))
        
        # Add metadata to the workflow
        workflow["metadata"] = {
            "created_at": datetime.now().isoformat(),
            "source": "system_recording",
            "total_actions": len(workflow["actions"]),
            "duration": recording_data[-1].get('timestamp', 0) - recording_data[0].get('timestamp', 0)
            if recording_data else 0
        }
        
        return workflow
        
    except Exception as e:
        logging.error(f"Error converting recording to workflow: {e}")
        return None

def create_typing_sequence_action(keystrokes):
    """Create a typing sequence action from collected keystrokes."""
    text = ""
    for keystroke in keystrokes:
        if keystroke.get('key_type') == 'character':
            text += keystroke.get('key', '')
        elif keystroke.get('key_type') == 'special':
            # Handle special keys (enter, tab, etc.)
            special_key = keystroke.get('key', '').strip('Key.')
            if special_key.lower() == 'space':
                text += ' '
            elif special_key.lower() == 'enter':
                text += '\n'
            elif special_key.lower() == 'tab':
                text += '\t'
    
    return {
        "type": "typing_sequence",
        "text": text,
        "typing_speed": 0.1,  # Default typing speed
        "meta_information": {
            "sequence_order": len(text),
            "description": f"Type text: {text[:50]}{'...' if len(text) > 50 else ''}"
        }
    }

def create_mouse_action(action_type, details):
    """Create a mouse action from recorded details."""
    position = details.get('position', {})
    
    return {
        "type": action_type,
        "x": position.get('x', 0),
        "y": position.get('y', 0),
        "meta_information": {
            "description": f"{action_type} at ({position.get('x', 0)}, {position.get('y', 0)})"
        }
    }

def create_window_action(details):
    """Create a window focus action."""
    window_info = details.get('window_transition', {})
    
    return {
        "type": "window_focus",
        "window_title": window_info.get('to'),
        "meta_information": {
            "description": f"Focus window: {window_info.get('to', 'Unknown')}"
        }
    }

def process_raw_recording_file(file_path):
    """
    Process a raw recording file and convert it to a workflow.
    
    Args:
        file_path (str): Path to the raw recording JSON file
        
    Returns:
        tuple: (workflow_data, output_path) or (None, None) on error
    """
    try:
        # Read raw recording data
        with open(file_path, 'r') as f:
            raw_data = json.load(f)
        
        # Convert to workflow format
        workflow = convert_recording_to_workflow(raw_data.get('recording_data', []))
        
        if workflow:
            # Create output filename
            output_dir = 'converted_workflows'
            os.makedirs(output_dir, exist_ok=True)
            output_path = os.path.join(
                output_dir,
                f"workflow_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            )
            
            # Save converted workflow
            with open(output_path, 'w') as f:
                json.dump(workflow, f, indent=4)
                
            logging.info(f"Workflow converted and saved to: {output_path}")
            return workflow, output_path
            
        return None, None
        
    except Exception as e:
        logging.error(f"Error processing raw recording file: {e}")
        return None, None

def batch_convert_recordings(directory_path):
    """
    Convert all raw recordings in a directory to workflows.
    
    Args:
        directory_path (str): Path to directory containing raw recordings
        
    Returns:
        list: List of (workflow, output_path) tuples for successful conversions
    """
    results = []
    
    try:
        for filename in os.listdir(directory_path):
            if filename.endswith('_raw_recording.json'):
                file_path = os.path.join(directory_path, filename)
                workflow, output_path = process_raw_recording_file(file_path)
                
                if workflow and output_path:
                    results.append((workflow, output_path))
                    
        return results
        
    except Exception as e:
        logging.error(f"Error in batch conversion: {e}")
        return results

if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # Example usage
    raw_recordings_dir = 'raw_recordings'
    if os.path.exists(raw_recordings_dir):
        results = batch_convert_recordings(raw_recordings_dir)
        logging.info(f"Converted {len(results)} recordings to workflows")