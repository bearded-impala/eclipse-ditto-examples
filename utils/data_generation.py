"""
Data generation utilities for Eclipse Ditto examples.

This module provides utilities for generating test data, thing descriptors, and
random configurations for Eclipse Ditto examples and is used across multiple
example projects in this repository.
"""

import json
import uuid
import random
from datetime import datetime, UTC, timedelta
from typing import Any, Dict, Optional, Tuple
from pathlib import Path
from .validation import detect_schema_type, ensure_feature_properties


def generate_short_uuid(length: int = 4) -> str:
    """
    Generate a short UUID string of given length.
    
    Args:
        length: Length of the UUID string
        
    Returns:
        Short UUID string
        
    Note:
        2: up to 1,296 combinations
        3: up to 46,656 combinations
        4: up to 1,679,616 combinations
        6: up to 60,466,176 combinations
    """
    return uuid.uuid4().hex[:length]


def generate_sample_from_schema(schema_node: Any) -> Any:
    """
    Recursively generate a sample from a schema node.
    
    Args:
        schema_node: Schema node to generate sample from
        
    Returns:
        Generated sample data
    """
    if isinstance(schema_node, dict):
        return {k: generate_sample_from_schema(v) for k, v in schema_node.items()}
    elif isinstance(schema_node, list):
        if not schema_node:
            return []
        if all(isinstance(i, list) for i in schema_node):
            return random.choice(schema_node)
        return random.choice(schema_node)
    return schema_node


def generate_random_timestamp(days_back: int = 10) -> str:
    """
    Generate a random timestamp within the last N days.
    
    Args:
        days_back: Number of days back to generate timestamp from
        
    Returns:
        ISO formatted timestamp string
    """
    base_time = datetime.now(UTC) - timedelta(days=days_back)
    random_seconds = random.uniform(0, timedelta(days=days_back).total_seconds())
    random_time = base_time + timedelta(seconds=random_seconds)
    return random_time.isoformat(timespec='milliseconds') + 'Z'


def generate_thing_descriptor(
    schema_path: str, 
    policy_id: str,
    logger: Optional[Any] = None
) -> Tuple[str, Dict[str, Any]]:
    """
    Generate a thing descriptor and return its ID and payload.
    
    Args:
        schema_path: Path to the schema JSON file
        policy_id: Policy ID to assign to the thing
        logger: Optional logger instance for debug output
        
    Returns:
        Tuple of (thing_id, thing_payload)
    """
    with open(schema_path) as f:
        schema = json.load(f)
        # Ensure all features have properties objects
        schema = ensure_feature_properties(schema)
        thing_sample = generate_sample_from_schema(schema)
        
        if logger:
            logger.debug(json.dumps(thing_sample, indent=4))

        # Attributes
        thing_type = thing_sample["attributes"]["type"]
        thing_sample["thingId"] = f"org.eclipse.ditto:{thing_type}-{generate_short_uuid()}-{datetime.now(UTC).strftime('%Y%m%d%f')}"
        thing_sample["policyId"] = policy_id
        thing_sample["attributes"]["timestamp"] = datetime.now(UTC).isoformat(timespec='milliseconds') + 'Z'

        # Features - populate with random values
        _populate_random_values(thing_sample)

        return thing_sample["thingId"], thing_sample


# ------------------------ JSON Schema Support ------------------------ #

def _js_random_string(min_length: int = 5, max_length: int = 20) -> str:
    import random, string
    length = random.randint(min_length, max_length)
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))


def _js_random_number(min_val: float = 0.0, max_val: float = 100.0, integer: bool = False) -> float | int:
    import random
    if integer:
        return random.randint(int(min_val), int(max_val))
    return round(random.uniform(min_val, max_val), 2)


def _generate_from_json_schema(schema: Dict[str, Any], root: Dict[str, Any] | None = None) -> Any:
    """
    Generate a random sample object that conforms to a (simplified) JSON Schema.
    Supports: type, properties, items, enum, const, $ref (root.definitions), anyOf, format.
    """
    import random

    if root is None:
        root = schema

    # Handle direct enum / const first
    if isinstance(schema, dict):
        if "const" in schema:
            return schema["const"]
        if "enum" in schema and isinstance(schema["enum"], list) and schema["enum"]:
            return random.choice(schema["enum"])

    # Handle $ref
    if isinstance(schema, dict) and "$ref" in schema:
        ref = schema["$ref"]
        if ref.startswith("#/definitions/"):
            key = ref.replace("#/definitions/", "")
            defs = root.get("definitions", {})
            if key in defs:
                return _generate_from_json_schema(defs[key], root)

    # Handle anyOf
    if isinstance(schema, dict) and "anyOf" in schema and isinstance(schema["anyOf"], list) and schema["anyOf"]:
        return _generate_from_json_schema(random.choice(schema["anyOf"]), root)

    if isinstance(schema, dict) and "type" in schema:
        t = schema["type"]
        if t == "object":
            result: Dict[str, Any] = {}
            props: Dict[str, Any] = schema.get("properties", {})
            for name, subschema in props.items():
                result[name] = _generate_from_json_schema(subschema, root)
            return result
        if t == "array":
            items_schema = schema.get("items", {})
            min_items = int(schema.get("minItems", 1))
            max_items = int(schema.get("maxItems", max(1, min_items + 2)))
            length = random.randint(min_items, max_items)
            return [_generate_from_json_schema(items_schema, root) for _ in range(length)]
        if t == "string":
            if schema.get("format") == "date-time":
                return datetime.now(UTC).isoformat(timespec='milliseconds') + 'Z'
            if schema.get("format") == "uri":
                return "https://example.com/resource"
            return _js_random_string()
        if t == "integer":
            return _js_random_number(schema.get("minimum", 0), schema.get("maximum", 100), integer=True)
        if t == "number":
            return _js_random_number(schema.get("minimum", 0.0), schema.get("maximum", 100.0), integer=False)
        if t == "boolean":
            return bool(random.choice([True, False]))

    # Fallbacks
    if isinstance(schema, list) and schema:
        return _generate_from_json_schema(random.choice(schema), root)
    if isinstance(schema, dict):
        # Unknown object shape, return empty object
        return {}
    return schema


def generate_thing_descriptor_from_json_schema(
    schema_path: str,
    policy_id: str,
    logger: Optional[Any] = None
) -> Tuple[str, Dict[str, Any]]:
    """
    Generate a Ditto-compatible Thing payload by sampling a JSON Schema.
    The generated object is placed under a single feature 'data' as properties.
    """
    with open(schema_path, 'r') as f:
        schema = json.load(f)

    if detect_schema_type(schema) != "json-schema":
        raise ValueError("Provided schema is not recognized as JSON Schema")

    sample = _generate_from_json_schema(schema)

    # Build Ditto thing payload
    device_type = schema.get("title").lower().replace(' ', '-') or "GenericDevice"
    thing_id = f"org.eclipse.ditto:{device_type}-{generate_short_uuid()}-{datetime.now(UTC).strftime('%Y%m%d%f')}"

    # Extract features from the sample and flatten them to Ditto format
    ditto_features = {}
    if 'features' in sample:
        # Transform the features configuration into Ditto features
        for feature_name, feature_data in sample['features'].items():
            ditto_features[feature_name] = {"properties": feature_data}
    
    # Put everything else from sample into attributes
    attributes = {
        "type": device_type,
        "timestamp": datetime.now(UTC).isoformat(timespec='milliseconds') + 'Z',
    }
    
    # Add all other properties from sample to attributes
    for key, value in sample.items():
        if key != 'features':  # Skip features as they go to features section
            attributes[key] = value
    
    payload: Dict[str, Any] = {
        "thingId": thing_id,
        "policyId": policy_id,
        "attributes": attributes,
        "features": ditto_features
    }

    if logger:
        logger.debug(json.dumps(payload, indent=2))

    return thing_id, payload


def _populate_random_values(thing_sample: Dict[str, Any]) -> None:
    """
    Populate random values in a thing sample.
    
    Args:
        thing_sample: Thing sample to populate with random values
    """
    features = thing_sample.get("features", {})
    
    # Video properties
    if "video" in features:
        video_props = features["video"].get("properties", {})
        if "resolution" in video_props and "supportedResolutions" in video_props:
            video_props["resolution"] = random.choice(video_props["supportedResolutions"])
    
    # Storage properties
    if "storage" in features:
        storage_props = features["storage"].get("properties", {})
        if "usedSpaceGB" in storage_props and "capacityGB" in storage_props:
            storage_props["usedSpaceGB"] = random.randint(0, storage_props["capacityGB"])
    
    # Network properties
    if "network" in features:
        network_props = features["network"].get("properties", {})
        if "ip" in network_props:
            network_props["ip"] = f"192.168.{random.randint(0, 255)}.{random.randint(0, 255)}"
        if "signalStrength" in network_props:
            network_props["signalStrength"] = random.randint(0, 100)
    
    # Health properties
    if "health" in features:
        health_props = features["health"].get("properties", {})
        if "uptimeSeconds" in health_props:
            health_props["uptimeSeconds"] = random.randint(1000, 999999)
        if "temperatureC" in health_props:
            health_props["temperatureC"] = round(random.uniform(20.0, 70.0), 1)
        if "cpuLoad" in health_props:
            health_props["cpuLoad"] = round(random.uniform(1, 100), 1)
    
    # Analytics properties
    if "analytics" in features:
        analytics_props = features["analytics"].get("properties", {})
        if "facesDetected" in analytics_props:
            analytics_props["facesDetected"] = round(random.uniform(7, 45), 0)
        
        if "peopleCount" in analytics_props:
            faces_detected = analytics_props.get("facesDetected", 10)
            analytics_props["peopleCount"]["lastHour"] = round(
                random.uniform(1, faces_detected) / random.uniform(3, 7), 0
            )
            analytics_props["peopleCount"]["today"] = round(
                random.uniform(1, faces_detected - analytics_props["peopleCount"]["lastHour"]) / random.uniform(3, 7), 0
            )
        
        if "intrusionEvents" in analytics_props:
            analytics_props["intrusionEvents"] = []
            num_events = random.randint(0, 10)
            for _ in range(num_events):
                analytics_props["intrusionEvents"].append({
                    "timestamp": generate_random_timestamp(),
                    "zone": {"id": f"zone-{random.randint(1, 5)}"}
                })
    
    # Motion detection properties
    if "motionDetection" in features:
        motion_props = features["motionDetection"].get("properties", {})
        if "lastDetection" in motion_props:
            motion_props["lastDetection"]["timestamp"] = generate_random_timestamp()


def load_policy(policy_path: Path) -> Tuple[str, Dict[str, Any]]:
    """
    Load policy from JSON file and extract policy ID.
    
    Args:
        policy_path: Path to policy JSON file
        
    Returns:
        Tuple of (policy_id, policy_data)
    """
    with open(policy_path, 'r') as file:
        policy_data = json.load(file)
        policy_id = policy_data.get('policyId', "ditto:policy:default")
        return policy_id, policy_data 