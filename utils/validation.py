"""
Validation utilities for Eclipse Ditto examples.

This module provides validation utilities for schemas, policies, configurations,
and other data structures used in Eclipse Ditto examples. It is used across
multiple example projects in this repository.
"""

import json
from pathlib import Path
from typing import Dict, Any, List, Tuple
from .config import Config


def detect_schema_type(schema: Dict[str, Any]) -> str:
    """
    Detect the type of schema provided.

    Returns one of: "ditto-template", "json-schema", "unknown".
    """
    if isinstance(schema, dict):
        if "attributes" in schema and "features" in schema:
            return "ditto-template"
        if "$schema" in schema or "properties" in schema or "definitions" in schema:
            return "json-schema"
    return "unknown"


def ensure_feature_properties(schema: Dict[str, Any]) -> Dict[str, Any]:
    """
    Ensure every feature in the schema has a properties object.
    If a feature doesn't have properties, wrap all its content in a properties object.
    
    Args:
        schema: The schema dictionary to transform
        
    Returns:
        Modified schema with all features having properties objects
    """
    if not isinstance(schema, dict) or "features" not in schema:
        return schema
    
    # Create a copy to avoid modifying the original
    modified_schema = schema.copy()
    modified_schema["features"] = modified_schema["features"].copy()
    
    for feature_name, feature_data in modified_schema["features"].items():
        if isinstance(feature_data, dict):
            # If the feature doesn't have a properties object, wrap everything in properties
            if "properties" not in feature_data:
                # Create a new feature object with properties containing all existing data
                modified_schema["features"][feature_name] = {
                    "properties": feature_data
                }
    
    return modified_schema


def validate_schema_file(schema_path: Path) -> Tuple[bool, List[str]]:
    """
    Validate that a schema file exists and contains valid JSON of a supported type
    (either a Ditto thing template or a JSON Schema describing an object).
    
    Args:
        schema_path: Path to schema file
        
    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    errors: List[str] = []
    
    # Existence and readability checks
    if not schema_path.exists():
        return False, [f"Schema file does not exist: {schema_path}"]
    if not schema_path.is_file():
        return False, [f"Schema path is not a file: {schema_path}"]
    
    try:
        with open(schema_path, 'r') as f:
            schema_data = json.load(f)
    except json.JSONDecodeError as e:
        return False, [f"Invalid JSON in schema file: {e}"]
    except Exception as e:
        return False, [f"Error reading schema file: {e}"]
    
    if not isinstance(schema_data, dict):
        return False, ["Schema must be a JSON object"]
    
    schema_type = detect_schema_type(schema_data)
    
    if schema_type == "ditto-template":
        # Must include attributes and features top-level keys
        for field in ["attributes", "features"]:
            if field not in schema_data:
                errors.append(f"Schema missing required field: {field}")
        return len(errors) == 0, errors
    
    if schema_type == "json-schema":
        # Basic JSON Schema sanity checks
        if schema_data.get("type") and schema_data.get("type") != "object":
            errors.append("Root JSON Schema 'type' must be 'object' if specified")
        # At least one of properties/definitions should exist for object generation
        if not ("properties" in schema_data or "definitions" in schema_data):
            errors.append("JSON Schema must include 'properties' or 'definitions'")
        return len(errors) == 0, errors
    
    return False, ["Unrecognized schema format. Provide a Ditto thing template or a JSON Schema."]


def validate_policy_file(policy_path: Path) -> Tuple[bool, List[str]]:
    """
    Validate that a policy file exists and contains valid JSON.
    
    Args:
        policy_path: Path to policy file
        
    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    errors = []
    
    # Check if file exists
    if not policy_path.exists():
        errors.append(f"Policy file does not exist: {policy_path}")
        return False, errors
    
    # Check if it's a file
    if not policy_path.is_file():
        errors.append(f"Policy path is not a file: {policy_path}")
        return False, errors
    
    # Try to parse JSON
    try:
        with open(policy_path, 'r') as f:
            policy_data = json.load(f)
    except json.JSONDecodeError as e:
        errors.append(f"Invalid JSON in policy file: {e}")
        return False, errors
    except Exception as e:
        errors.append(f"Error reading policy file: {e}")
        return False, errors
    
    # Validate policy structure
    if not isinstance(policy_data, dict):
        errors.append("Policy must be a JSON object")
        return False, errors
    
    # Check for required fields
    if "policyId" not in policy_data:
        errors.append("Policy missing required field: policyId")
    
    if "entries" not in policy_data:
        errors.append("Policy missing required field: entries")
    
    return len(errors) == 0, errors


def validate_config(config: Config) -> Tuple[bool, List[str]]:
    """
    Validate configuration settings.
    
    Args:
        config: Config instance to validate
        
    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    errors = []
    
    # Validate Ditto URL
    if not config.ditto_url:
        errors.append("DITTO_URL is not set")
    elif not config.ditto_url.startswith(('http://', 'https://')):
        errors.append("DITTO_URL must start with http:// or https://")
    
    # Validate authentication
    if not config.auth_user:
        errors.append("AUTH_USER is not set")
    
    if not config.auth_pass:
        errors.append("AUTH_PASS is not set")
    
    # Validate count
    if config.count <= 0:
        errors.append("COUNT must be greater than 0")
    
    return len(errors) == 0, errors


def validate_thing_data(thing_data: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validate thing data structure.
    
    Args:
        thing_data: Thing data dictionary
        
    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    errors = []
    
    # Check required fields
    required_fields = ["thingId", "policyId", "attributes", "features"]
    for field in required_fields:
        if field not in thing_data:
            errors.append(f"Thing data missing required field: {field}")
    
    # Validate thingId format
    if "thingId" in thing_data:
        thing_id = thing_data["thingId"]
        if not isinstance(thing_id, str):
            errors.append("thingId must be a string")
        elif not thing_id.startswith("org.eclipse.ditto:"):
            errors.append("thingId must start with 'org.eclipse.ditto:'")
    
    # Validate attributes
    if "attributes" in thing_data:
        attributes = thing_data["attributes"]
        if not isinstance(attributes, dict):
            errors.append("attributes must be an object")
        elif "type" not in attributes:
            errors.append("attributes must contain 'type' field")
    
    # Validate features
    if "features" in thing_data:
        features = thing_data["features"]
        if not isinstance(features, dict):
            errors.append("features must be an object")
        else:
            for feature_name, feature_data in features.items():
                if not isinstance(feature_data, dict):
                    errors.append(f"Feature '{feature_name}' must be an object")
                elif "properties" not in feature_data:
                    errors.append(f"Feature '{feature_name}' missing 'properties' field")
    
    return len(errors) == 0, errors


def validate_query_expression(query: str) -> Tuple[bool, List[str]]:
    """
    Basic validation of Ditto query expressions.
    
    Args:
        query: Query expression string
        
    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    errors = []
    
    if not query:
        errors.append("Query expression cannot be empty")
        return False, errors
    
    # Check for balanced parentheses
    open_parens = query.count('(')
    close_parens = query.count(')')
    if open_parens != close_parens:
        errors.append("Unbalanced parentheses in query expression")
    
    # Check for basic function names
    valid_functions = ['eq', 'ne', 'gt', 'gte', 'lt', 'lte', 'like', 'ilike', 'in', 'exists', 'and', 'or', 'not']
    words = query.replace('(', ' ').replace(')', ' ').replace(',', ' ').split()
    
    for word in words:
        if word in valid_functions:
            continue
        # Skip quoted strings and numbers
        if (word.startswith("'") and word.endswith("'")) or word.replace('.', '').replace('-', '').isdigit():
            continue
        # Skip property paths (contain slashes)
        if '/' in word:
            continue
        # Skip boolean values
        if word.lower() in ['true', 'false']:
            continue
    
    return len(errors) == 0, errors


def print_validation_errors(errors: List[str], title: str = "Validation Errors") -> None:
    """
    Print validation errors in a formatted way.
    
    Args:
        errors: List of error messages
        title: Title for the error section
    """
    if not errors:
        return
    
    print(f"\n{title}:")
    print("-" * len(title))
    for i, error in enumerate(errors, 1):
        print(f"{i}. {error}")
    print() 