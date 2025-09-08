"""
Unit tests for utility helper functions.
"""

import pytest
from unittest.mock import patch
from datetime import datetime, timezone
import asyncio

from app.utils.helpers import (
    generate_token,
    hash_password,
    verify_password,
    normalize_email,
    validate_email_format,
    sanitize_filename,
    truncate_text,
    format_currency,
    get_utc_now,
    parse_skills,
    chunk_list,
    calculate_match_score,
    retry_async
)


class TestTokenGeneration:
    """Test token generation utilities."""
    
    def test_generate_token_default_length(self):
        """Test token generation with default length."""
        token = generate_token()
        assert len(token) == 64  # 32 bytes = 64 hex chars
        assert all(c in '0123456789abcdef' for c in token)
    
    def test_generate_token_custom_length(self):
        """Test token generation with custom length."""
        token = generate_token(16)
        assert len(token) == 32  # 16 bytes = 32 hex chars
    
    def test_generate_token_uniqueness(self):
        """Test that generated tokens are unique."""
        tokens = [generate_token() for _ in range(100)]
        assert len(set(tokens)) == 100


class TestPasswordHashing:
    """Test password hashing and verification."""
    
    def test_hash_password_without_salt(self):
        """Test password hashing without providing salt."""
        password = "test_password_123"
        hashed, salt = hash_password(password)
        
        assert len(hashed) == 64  # SHA-256 hex digest
        assert len(salt) == 32    # 16 bytes = 32 hex chars
        assert hashed != password
    
    def test_hash_password_with_salt(self):
        """Test password hashing with provided salt."""
        password = "test_password_123"
        salt = "fixed_salt_for_testing"
        hashed, returned_salt = hash_password(password, salt)
        
        assert returned_salt == salt
        assert hashed != password
    
    def test_verify_password_correct(self):
        """Test password verification with correct password."""
        password = "test_password_123"
        hashed, salt = hash_password(password)
        
        assert verify_password(password, hashed, salt) is True
    
    def test_verify_password_incorrect(self):
        """Test password verification with incorrect password."""
        password = "test_password_123"
        wrong_password = "wrong_password"
        hashed, salt = hash_password(password)
        
        assert verify_password(wrong_password, hashed, salt) is False


class TestEmailUtilities:
    """Test email-related utility functions."""
    
    def test_normalize_email(self):
        """Test email normalization."""
        assert normalize_email("Test@Example.COM  ") == "test@example.com"
        assert normalize_email("  USER@DOMAIN.org") == "user@domain.org"
    
    @pytest.mark.parametrize("email,expected", [
        ("user@example.com", True),
        ("test.email+tag@domain.co.uk", True),
        ("user123@test-domain.com", True),
        ("invalid.email", False),
        ("@domain.com", False),
        ("user@", False),
        ("user @domain.com", False),
        ("", False)
    ])
    def test_validate_email_format(self, email, expected):
        """Test email format validation."""
        assert validate_email_format(email) == expected


class TestStringUtilities:
    """Test string manipulation utilities."""
    
    @pytest.mark.parametrize("filename,expected", [
        ("normal_file.txt", "normal_file.txt"),
        ("file<with>bad:chars.pdf", "file_with_bad_chars.pdf"),
        ("file/with\\slashes.doc", "file_with_slashes.doc"),
        ("   file with spaces   ", "file with spaces"),
        ("", "file_"),  # Should generate something for empty string
    ])
    def test_sanitize_filename(self, filename, expected):
        """Test filename sanitization."""
        result = sanitize_filename(filename)
        if expected.endswith("_"):
            assert result.startswith("file_")
        else:
            assert result == expected
    
    def test_truncate_text_short(self):
        """Test text truncation with short text."""
        text = "Short text"
        result = truncate_text(text, 20)
        assert result == text
    
    def test_truncate_text_long(self):
        """Test text truncation with long text."""
        text = "This is a very long text that needs truncation"
        result = truncate_text(text, 20)
        assert len(result) == 20
        assert result.endswith("...")
        assert result == "This is a very lo..."
    
    def test_truncate_text_custom_suffix(self):
        """Test text truncation with custom suffix."""
        text = "Long text for testing"
        result = truncate_text(text, 15, " [more]")
        assert len(result) == 15
        assert result.endswith(" [more]")


class TestCurrencyFormatting:
    """Test currency formatting utilities."""
    
    def test_format_currency_usd(self):
        """Test USD currency formatting."""
        assert format_currency(1234.56) == "$1,234.56"
        assert format_currency(1234.56, "USD") == "$1,234.56"
    
    def test_format_currency_eur(self):
        """Test EUR currency formatting."""
        assert format_currency(1234.56, "EUR") == "€1,234.56"
    
    def test_format_currency_other(self):
        """Test other currency formatting."""
        assert format_currency(1234.56, "GBP") == "1,234.56 GBP"


class TestDateTimeUtilities:
    """Test datetime utilities."""
    
    def test_get_utc_now(self):
        """Test UTC datetime generation."""
        now = get_utc_now()
        assert isinstance(now, datetime)
        assert now.tzinfo == timezone.utc


class TestSkillsParsing:
    """Test skills parsing utilities."""
    
    def test_parse_skills_string(self):
        """Test parsing skills from comma-separated string."""
        skills_str = "python, javascript, react, node.js"
        result = parse_skills(skills_str)
        expected = ["Python", "Javascript", "React", "Node.Js"]
        assert result == expected
    
    def test_parse_skills_list(self):
        """Test parsing skills from list."""
        skills_list = ["python", "javascript", "react"]
        result = parse_skills(skills_list)
        expected = ["Python", "Javascript", "React"]
        assert result == expected
    
    def test_parse_skills_empty(self):
        """Test parsing empty skills."""
        assert parse_skills("") == []
        assert parse_skills([]) == []
        assert parse_skills(None) == []
    
    def test_parse_skills_whitespace(self):
        """Test parsing skills with extra whitespace."""
        skills_str = " python ,  javascript  , react "
        result = parse_skills(skills_str)
        expected = ["Python", "Javascript", "React"]
        assert result == expected


class TestListUtilities:
    """Test list manipulation utilities."""
    
    def test_chunk_list_even(self):
        """Test chunking list with even division."""
        items = list(range(10))
        chunks = chunk_list(items, 3)
        expected = [[0, 1, 2], [3, 4, 5], [6, 7, 8], [9]]
        assert chunks == expected
    
    def test_chunk_list_exact(self):
        """Test chunking list with exact division."""
        items = list(range(9))
        chunks = chunk_list(items, 3)
        expected = [[0, 1, 2], [3, 4, 5], [6, 7, 8]]
        assert chunks == expected
    
    def test_chunk_list_empty(self):
        """Test chunking empty list."""
        chunks = chunk_list([], 3)
        assert chunks == []


class TestMatchScoring:
    """Test match scoring utilities."""
    
    def test_calculate_match_score_perfect(self):
        """Test perfect skill match."""
        user_skills = ["Python", "JavaScript", "React"]
        job_skills = ["python", "javascript", "react"]
        score = calculate_match_score(user_skills, job_skills)
        assert score == 1.0
    
    def test_calculate_match_score_partial(self):
        """Test partial skill match."""
        user_skills = ["Python", "JavaScript"]
        job_skills = ["python", "javascript", "react", "node.js"]
        score = calculate_match_score(user_skills, job_skills)
        assert score == 0.5  # 2 out of 4 skills match
    
    def test_calculate_match_score_no_match(self):
        """Test no skill match."""
        user_skills = ["Python", "JavaScript"]
        job_skills = ["java", "c++"]
        score = calculate_match_score(user_skills, job_skills)
        assert score == 0.0
    
    def test_calculate_match_score_empty_job_skills(self):
        """Test match score with empty job skills."""
        user_skills = ["Python", "JavaScript"]
        job_skills = []
        score = calculate_match_score(user_skills, job_skills)
        assert score == 0.0
    
    def test_calculate_match_score_with_weights(self):
        """Test match score with weights."""
        user_skills = ["Python", "JavaScript"]
        job_skills = ["python", "javascript", "react", "node.js"]
        weights = {"skills": 0.8}
        score = calculate_match_score(user_skills, job_skills, weights)
        assert score == 0.4  # 0.5 * 0.8


class TestRetryDecorator:
    """Test retry decorator."""
    
    @pytest.mark.asyncio
    async def test_retry_success_first_attempt(self):
        """Test retry decorator with success on first attempt."""
        call_count = 0
        
        @retry_async(max_retries=3, delay=0.1)
        async def success_function():
            nonlocal call_count
            call_count += 1
            return "success"
        
        result = await success_function()
        assert result == "success"
        assert call_count == 1
    
    @pytest.mark.asyncio
    async def test_retry_success_after_failures(self):
        """Test retry decorator with success after failures."""
        call_count = 0
        
        @retry_async(max_retries=3, delay=0.01)
        async def flaky_function():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError("Temporary failure")
            return "success"
        
        result = await flaky_function()
        assert result == "success"
        assert call_count == 3
    
    @pytest.mark.asyncio
    async def test_retry_max_retries_exceeded(self):
        """Test retry decorator when max retries exceeded."""
        call_count = 0
        
        @retry_async(max_retries=2, delay=0.01)
        async def always_fail_function():
            nonlocal call_count
            call_count += 1
            raise ValueError("Always fails")
        
        with pytest.raises(ValueError, match="Always fails"):
            await always_fail_function()
        
        assert call_count == 3  # Initial attempt + 2 retries
