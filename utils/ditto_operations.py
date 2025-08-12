"""
Base class for running Eclipse Ditto examples.

This module provides a base class that handles common functionality
for all Ditto example scripts including environment loading, logging,
and HTTP client setup.
"""

import json
import sys
from pathlib import Path
from typing import Dict, Any, Optional

import os
from dotenv import load_dotenv
from .http_client import DittoClient
from .logging_utils import setup_basic_logging


class ExampleRunner:
    """
    Base class for running Ditto examples.
    
    This class provides common functionality for all example scripts
    including environment loading, logging, and HTTP client setup.
    """
    
    def __init__(self, example_name: str):
        """
        Initialize the example runner.
        
        Args:
            example_name: Name of the example for logging
        """
        self.example_name = example_name
        self.logger = setup_basic_logging()
        
        # Load environment variables
        try:
            load_dotenv()
            print("✅ Environment variables loaded from .env")
        except Exception as e:
            self.logger.error(f"Failed to load environment: {e}")
            sys.exit(1)
        
        # Setup HTTP client
        from .config import Config
        config = Config.load()
        self.client = DittoClient(config)
        
        # Get current directory for file operations
        # Handle numbered example directories (e.g., "Device State Sync" -> "1-device-state-sync")
        example_dir = example_name.lower().replace(" ", "-")
        if not example_dir.startswith(("1-", "2-", "3-", "4-", "5-", "6-", "7-")):
            # Try to find the correct numbered directory
            examples_dir = Path(__file__).parent.parent / "examples"
            for i in range(1, 8):
                potential_dir = examples_dir / f"{i}-{example_dir}"
                if potential_dir.exists():
                    example_dir = f"{i}-{example_dir}"
                    break
        
        self.script_dir = Path(__file__).parent.parent / "examples" / example_dir
    
    def log_section(self, message: str):
        """
        Log a section header with consistent formatting.
        
        Args:
            message: Section message
        """
        self.logger.info("")
        self.logger.info("=" * 50)
        self.logger.info(f"[{self.example_name.upper()}] {message}")
        self.logger.info("=" * 50)
    
    def load_json_file(self, filename: str, directory: str = None) -> Dict[str, Any]:
        """
        Load a JSON file from the specified directory or example directory.
        
        Args:
            filename: Name of the JSON file
            directory: Optional directory path (defaults to example directory)
            
        Returns:
            Parsed JSON data
            
        Raises:
            FileNotFoundError: If the file doesn't exist
            json.JSONDecodeError: If the file contains invalid JSON
        """
        if directory:
            file_path = Path(directory) / filename
        else:
            file_path = self.script_dir / filename
            
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        with open(file_path, 'r') as f:
            return json.load(f)
    
    def create_policy(self, policy_id: str, policy_file: str = "policy.json") -> bool:
        """
        Create a policy from a JSON file.
        
        Args:
            policy_id: The policy ID
            policy_file: Name of the policy JSON file
            
        Returns:
            True if successful, False otherwise
        """
        try:
            policy_data = self.load_json_file(policy_file)
            success = self.client.create_policy(policy_id, policy_data)
            if success:
                self.logger.info(f"✅ Policy created: {policy_id}")
            else:
                self.logger.error(f"❌ Failed to create policy: {policy_id}")
            return success
        except Exception as e:
            self.logger.error(f"❌ Error creating policy {policy_id}: {e}")
            return False
    
    def create_thing(self, thing_id: str, thing_file: str = "thing.json") -> bool:
        """
        Create a thing from a JSON file.
        
        Args:
            thing_id: The thing ID
            thing_file: Name of the thing JSON file
            
        Returns:
            True if successful, False otherwise
        """
        try:
            thing_data = self.load_json_file(thing_file)
            success = self.client.create_thing(thing_id, thing_data)
            if success:
                self.logger.info(f"✅ Thing created: {thing_id}")
            else:
                self.logger.error(f"❌ Failed to create thing: {thing_id}")
            return success
        except Exception as e:
            self.logger.error(f"❌ Error creating thing {thing_id}: {e}")
            return False
    
    def update_thing_property(self, thing_id: str, path: str, value: Any) -> bool:
        """
        Update a thing property.
        
        Args:
            thing_id: The thing ID
            path: Property path (e.g., "features/temperature/properties/value")
            value: The value to set
            
        Returns:
            True if successful, False otherwise
        """
        success = self.client.update_thing_property(thing_id, path, value)
        if success:
            self.logger.info(f"✅ Updated {thing_id}/{path} = {value}")
        else:
            self.logger.error(f"❌ Failed to update {thing_id}/{path}")
        return success
    
    def get_thing(self, thing_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a thing by ID.
        
        Args:
            thing_id: The thing ID
            
        Returns:
            Thing data or None if not found
        """
        thing_data = self.client.get_thing(thing_id)
        if thing_data:
            self.logger.info(f"✅ Retrieved thing: {thing_id}")
            print(json.dumps(thing_data, indent=2))
        else:
            self.logger.error(f"❌ Failed to retrieve thing: {thing_id}")
        return thing_data
    
    def run(self):
        """
        Run the example. Override this method in subclasses.
        """
        raise NotImplementedError("Subclasses must implement the run method")
    
    def cleanup(self):
        """
        Clean up resources. Override this method in subclasses if needed.
        """
        self.client.close()
    
    def __enter__(self):
        return self
    
    def run_operations(self, operations):
        """
        Run a list of operations with automatic logging and error handling.
        
        Args:
            operations: List of tuples (description, operation_lambda)
            
        Returns:
            True if all operations succeeded, False otherwise
        """
        for description, operation in operations:
            self.log_section(description)
            if not operation():
                return False
        return True
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cleanup()
