"""
Common utility functions for the application.
"""

import hashlib
import secrets
import re
from typing import Optional, List, Dict, Any, Union
from datetime import datetime, timezone
from functools import wraps
import asyncio


def generate_token(length: int = 32) -> str:
    """
    Generate a secure random token.
    
    Args:
        length: Length of the token in bytes
        
    Returns:
        Hex-encoded token string
    """
    return secrets.token_hex(length)


def hash_password(password: str, salt: Optional[str] = None) -> tuple[str, str]:
    """
    Hash a password with salt.
    
    Args:
        password: Password to hash
        salt: Optional salt (generated if not provided)
        
    Returns:
        Tuple of (hashed_password, salt)
    """
    if salt is None:
        salt = secrets.token_hex(16)
    
    # Combine password and salt
    salted_password = f"{password}{salt}"
    
    # Hash with SHA-256
    hashed = hashlib.sha256(salted_password.encode()).hexdigest()
    
    return hashed, salt


def verify_password(password: str, hashed_password: str, salt: str) -> bool:
    """
    Verify a password against its hash.
    
    Args:
        password: Plain text password
        hashed_password: Hashed password
        salt: Salt used in hashing
        
    Returns:
        True if password is correct
    """
    computed_hash, _ = hash_password(password, salt)
    return computed_hash == hashed_password


def normalize_email(email: str) -> str:
    """
    Normalize email address for consistent storage.
    
    Args:
        email: Email address to normalize
        
    Returns:
        Normalized email address (lowercase, stripped)
    """
    return email.strip().lower()


def validate_email_format(email: str) -> bool:
    """
    Validate email format using regex.
    
    Args:
        email: Email address to validate
        
    Returns:
        True if email format is valid
    """
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename by removing/replacing unsafe characters.
    
    Args:
        filename: Original filename
        
    Returns:
        Sanitized filename
    """
    # Remove or replace unsafe characters
    sanitized = re.sub(r'[<>:"/\\|?*]', '_', filename)
    
    # Remove leading/trailing spaces and dots
    sanitized = sanitized.strip(' .')
    
    # Ensure filename is not empty
    if not sanitized:
        sanitized = f"file_{generate_token(8)}"
    
    return sanitized


def truncate_text(text: str, max_length: int, suffix: str = "...") -> str:
    """
    Truncate text to maximum length with optional suffix.
    
    Args:
        text: Text to truncate
        max_length: Maximum length including suffix
        suffix: Suffix to append if truncated
        
    Returns:
        Truncated text
    """
    if len(text) <= max_length:
        return text
    
    truncated_length = max_length - len(suffix)
    return text[:truncated_length] + suffix


def format_currency(amount: float, currency_code: str = "USD") -> str:
    """
    Format currency amount.
    
    Args:
        amount: Amount to format
        currency_code: Currency code (USD, EUR, etc.)
        
    Returns:
        Formatted currency string
    """
    if currency_code == "USD":
        return f"${amount:,.2f}"
    elif currency_code == "EUR":
        return f"€{amount:,.2f}"
    else:
        return f"{amount:,.2f} {currency_code}"


def get_utc_now() -> datetime:
    """
    Get current UTC datetime.
    
    Returns:
        Current UTC datetime with timezone info
    """
    return datetime.now(timezone.utc)


def parse_skills(skills_input: Union[str, List[str]]) -> List[str]:
    """
    Parse skills from string or list input.
    
    Args:
        skills_input: Comma-separated string or list of skills
        
    Returns:
        List of normalized skill strings
    """
    if isinstance(skills_input, str):
        skills = [skill.strip() for skill in skills_input.split(',')]
    else:
        skills = skills_input or []
    
    # Filter out empty strings and normalize
    return [skill.strip().title() for skill in skills if skill.strip()]


def chunk_list(items: List[Any], chunk_size: int) -> List[List[Any]]:
    """
    Split a list into chunks of specified size.
    
    Args:
        items: List to chunk
        chunk_size: Size of each chunk
        
    Returns:
        List of chunks
    """
    return [items[i:i + chunk_size] for i in range(0, len(items), chunk_size)]


def retry_async(max_retries: int = 3, delay: float = 1.0):
    """
    Decorator to retry async functions on failure.
    
    Args:
        max_retries: Maximum number of retry attempts
        delay: Delay between retries in seconds
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_retries:
                        await asyncio.sleep(delay * (2 ** attempt))  # Exponential backoff
                    
            raise last_exception
        return wrapper
    return decorator


def calculate_match_score(
    user_skills: List[str], 
    job_skills: List[str],
    weights: Optional[Dict[str, float]] = None
) -> float:
    """
    Calculate basic skill match score between user and job.
    
    Args:
        user_skills: List of user skills
        job_skills: List of required job skills
        weights: Optional weights for different factors
        
    Returns:
        Match score between 0.0 and 1.0
    """
    if not job_skills:
        return 0.0
    
    # Normalize skills to lowercase for comparison
    user_skills_normalized = [skill.lower() for skill in user_skills]
    job_skills_normalized = [skill.lower() for skill in job_skills]
    
    # Calculate basic overlap
    matching_skills = set(user_skills_normalized) & set(job_skills_normalized)
    basic_score = len(matching_skills) / len(job_skills_normalized)
    
    # Apply weights if provided
    if weights:
        skill_weight = weights.get('skills', 1.0)
        basic_score *= skill_weight
    
    return min(basic_score, 1.0)  # Cap at 1.0
