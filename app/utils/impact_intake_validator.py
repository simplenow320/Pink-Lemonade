"""
Impact Intake Payload Validation Utility
"""
import re
from typing import Dict, List, Any


def validate_and_merge_intake_payload(existing_payload: dict, incoming: dict) -> dict:
    """
    Validate and merge intake payload with participant demographics and stories.
    
    Supported fields in payload:
    - age: integer >= 0 and <= 120
    - zip: string, 5-10 characters (alphanumeric + dash)
    - ethnicity: string, 1-80 characters
    - stories: array of max 4 strings, each max 2000 chars
    
    Args:
        existing_payload: Current payload dict (preserved for backward compatibility)
        incoming: New data to validate and merge
    
    Returns:
        Merged payload dict with validated values
        
    Raises:
        ValueError: If validation fails
    """
    # Start with existing payload for backward compatibility
    result = existing_payload.copy() if existing_payload else {}
    
    # Validate and merge age
    if 'age' in incoming:
        age = incoming['age']
        if age is not None:
            try:
                age_int = int(age)
                if age_int < 0:
                    raise ValueError("age: must be >= 0")
                if age_int > 120:
                    raise ValueError("age: must be <= 120")
                result['age'] = age_int
            except (TypeError, ValueError) as e:
                if "must be" not in str(e):
                    raise ValueError(f"age: must be a valid integer")
                raise
    
    # Validate and merge zip
    if 'zip' in incoming:
        zip_code = incoming['zip']
        if zip_code is not None:
            # Strip non-alphanumeric except dash
            zip_str = str(zip_code)
            zip_cleaned = re.sub(r'[^a-zA-Z0-9\-]', '', zip_str).strip()
            
            if len(zip_cleaned) < 5:
                raise ValueError("zip: must be at least 5 characters")
            if len(zip_cleaned) > 10:
                raise ValueError("zip: must be at most 10 characters")
            
            result['zip'] = zip_cleaned
    
    # Validate and merge ethnicity
    if 'ethnicity' in incoming:
        ethnicity = incoming['ethnicity']
        if ethnicity is not None:
            ethnicity_str = str(ethnicity).strip()
            
            if len(ethnicity_str) < 1:
                raise ValueError("ethnicity: must be at least 1 character")
            if len(ethnicity_str) > 80:
                raise ValueError("ethnicity: must be at most 80 characters")
            
            result['ethnicity'] = ethnicity_str
    
    # Validate and merge stories
    if 'stories' in incoming:
        stories = incoming['stories']
        if stories is not None:
            if not isinstance(stories, list):
                raise ValueError("stories: must be a list")
            
            # Truncate to first 4 items
            stories_list = stories[:4]
            
            # Validate each story
            validated_stories = []
            for i, story in enumerate(stories_list):
                if story is not None:
                    story_str = str(story).strip()
                    if len(story_str) > 2000:
                        raise ValueError(f"stories[{i}]: must be at most 2000 characters")
                    validated_stories.append(story_str)
                else:
                    validated_stories.append("")
            
            result['stories'] = validated_stories
    
    return result