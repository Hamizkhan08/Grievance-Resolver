"""
Utility functions for agent JSON parsing.
Handles LLM responses that may contain extra text before/after JSON.
"""
import json
import re
import structlog

logger = structlog.get_logger()


def extract_json_from_string(response: str) -> dict:
    """
    Extract and parse JSON from LLM response string.
    Handles cases with extra text before/after JSON.
    
    Args:
        response: Raw LLM response string
        
    Returns:
        Parsed JSON dictionary
        
    Raises:
        ValueError: If no valid JSON can be found
        json.JSONDecodeError: If JSON is malformed
    """
    if not response:
        raise ValueError("Empty response from LLM")
    
    # First, try to find a JSON object using regex
    json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', response)
    if not json_match:
        # Fallback: try to find any JSON-like structure
        json_match = re.search(r'\{.*?\}', response, re.DOTALL)
    
    if json_match:
        json_str = json_match.group()
        try:
            return json.loads(json_str)
        except json.JSONDecodeError:
            # Continue to manual parsing
            pass
    
    # Manual parsing: find first { and matching }
    start_idx = response.find('{')
    if start_idx == -1:
        raise ValueError(f"No JSON object found in response: {response[:500]}")
    
    # Find matching closing brace by counting braces
    brace_count = 0
    end_idx = start_idx
    for i in range(start_idx, len(response)):
        if response[i] == '{':
            brace_count += 1
        elif response[i] == '}':
            brace_count -= 1
            if brace_count == 0:
                end_idx = i
                break
    
    if brace_count != 0:
        raise ValueError(f"Incomplete JSON in response: {response[:500]}")
    
    json_str = response[start_idx:end_idx + 1]
    try:
        return json.loads(json_str)
    except json.JSONDecodeError as e:
        logger.error("Failed to parse JSON", json_str=json_str[:200], error=str(e))
        raise ValueError(f"Invalid JSON in response: {str(e)}. Response: {response[:500]}") from e


def parse_json_from_response(response: str) -> dict:
    """
    Parse JSON from LLM response, handling cases with extra text.
    Alias for extract_json_from_string for backward compatibility.
    
    Args:
        response: Raw LLM response string
        
    Returns:
        Parsed JSON dictionary
        
    Raises:
        ValueError: If no valid JSON can be found
        json.JSONDecodeError: If JSON is malformed
    """
    return extract_json_from_string(response)
