"""
Path utilities for consistent path resolution across the codebase.
"""

from pathlib import Path
from typing import Optional, Union


def get_project_root() -> Path:
    """
    Get the project root directory.
    
    Returns:
        Path to the project root
    """
    # Start from utils directory and go up to project root
    return Path(__file__).resolve().parent.parent


def get_script_dir() -> Path:
    """
    Get the directory of the calling script.
    
    Returns:
        Path to the directory containing the calling script
    """
    import inspect
    caller_frame = inspect.currentframe().f_back
    if caller_frame:
        caller_file = Path(caller_frame.f_globals.get('__file__', ''))
        if caller_file.exists():
            return caller_file.parent
    
    # Fallback to current working directory
    return Path.cwd()


def find_file_in_paths(filename: str, search_paths: list[Path]) -> Optional[Path]:
    """
    Find a file in a list of search paths.
    
    Args:
        filename: Name of the file to find
        search_paths: List of paths to search in
        
    Returns:
        Path to the file if found, None otherwise
    """
    for search_path in search_paths:
        file_path = search_path / filename
        if file_path.exists():
            return file_path
    return None


def find_schema_file(schema_name: str, script_dir: Optional[Path] = None) -> Path:
    """
    Find a schema file using consistent search logic.
    
    Args:
        schema_name: Name of the schema file (e.g., "camera.json")
        script_dir: Directory to start search from (defaults to calling script dir)
        
    Returns:
        Path to the schema file
        
    Raises:
        FileNotFoundError: If schema file cannot be found
    """
    if script_dir is None:
        script_dir = get_script_dir()
    
    # Search paths in order of preference
    search_paths = [
        script_dir / "schema",           # Local schema directory
        script_dir.parent / "schema",    # Parent schema directory  
        get_project_root() / "examples" / "9-spawn-fleet" / "schema",  # Default schema location
    ]
    
    schema_path = find_file_in_paths(schema_name, search_paths)
    if schema_path is None:
        raise FileNotFoundError(f"Schema file '{schema_name}' not found in: {search_paths}")
    
    return schema_path


def find_policy_file(script_dir: Optional[Path] = None) -> Path:
    """
    Find a policy.json file using consistent search logic.
    
    Args:
        script_dir: Directory to start search from (defaults to calling script dir)
        
    Returns:
        Path to the policy.json file
        
    Raises:
        FileNotFoundError: If policy.json cannot be found
    """
    if script_dir is None:
        script_dir = get_script_dir()
    
    # Search paths in order of preference
    search_paths = [
        script_dir,                      # Same directory as script
        script_dir.parent,               # Parent directory
        get_project_root() / "examples" / "9-spawn-fleet",  # Default location
    ]
    
    policy_path = find_file_in_paths("policy.json", search_paths)
    if policy_path is None:
        raise FileNotFoundError(f"policy.json not found in: {search_paths}")
    
    return policy_path


def ensure_directory(path: Union[str, Path]) -> Path:
    """
    Ensure a directory exists, creating it if necessary.
    
    Args:
        path: Directory path
        
    Returns:
        Path to the directory
    """
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_safe_filename(name: str, max_length: int = 60) -> str:
    """
    Convert a string to a safe filename.
    
    Args:
        name: Original name
        max_length: Maximum length of filename
        
    Returns:
        Safe filename string
    """
    # Replace non-alphanumeric characters with underscores
    safe_name = "".join(c if c.isalnum() else "_" for c in name[:max_length])
    return safe_name


def resolve_relative_path(path: Union[str, Path], base_dir: Optional[Path] = None) -> Path:
    """
    Resolve a relative path against a base directory.
    
    Args:
        path: Path to resolve (can be relative or absolute)
        base_dir: Base directory (defaults to calling script directory)
        
    Returns:
        Resolved absolute path
    """
    path = Path(path)
    if path.is_absolute():
        return path
    
    if base_dir is None:
        base_dir = get_script_dir()
    
    return (base_dir / path).resolve()
