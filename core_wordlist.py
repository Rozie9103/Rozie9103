from datetime import datetime
from utils_config import COMMON_PASSWORDS, KEYBOARD_WALKS, LEET_SPEAK_MAP, SPECIAL_COMBINATIONS

class WordlistGenerator:
    def __init__(self, custom_words=None, use_api=False, min_length=6, max_length=32):
        self.current_year = str(datetime.now().year)
        self.custom_words = custom_words or []
        self.use_api = use_api
        self.min_length = min_length
        self.max_length = max_length
    
    def generate(self):
        """Generator function that yields passwords one at a time"""
        # Use custom wordlist if provided
        if self.custom_words:
            for word in self.custom_words:
                if self._valid_length(word):
                    yield word
        
        # Basic patterns from default lists
        for pattern in COMMON_PASSWORDS + KEYBOARD_WALKS:
            for variation in self._get_variations(pattern):
                if self._valid_length(variation):
                    yield variation
        
        # Year combinations
        for pattern in COMMON_PASSWORDS + KEYBOARD_WALKS:
            for variation in self._get_variations(pattern):
                year_variations = [
                    variation + self.current_year,
                    self.current_year + variation
                ]
                for year_var in year_variations:
                    if self._valid_length(year_var):
                        yield year_var
        
        # Special combinations
        for pattern in COMMON_PASSWORDS + KEYBOARD_WALKS:
            for variation in self._get_variations(pattern):
                for suffix in SPECIAL_COMBINATIONS:
                    special_variations = [
                        variation + suffix,
                        suffix + variation
                    ]
                    for special_var in special_variations:
                        if self._valid_length(special_var):
                            yield special_var
        
        # Leet speak variations
        for pattern in COMMON_PASSWORDS + KEYBOARD_WALKS:
            for variation in self._get_variations(pattern):
                leet_variation = self._apply_leet_speak(variation)
                if leet_variation != variation and self._valid_length(leet_variation):
                    yield leet_variation
        
        # API integration
        if self.use_api:
            for word in self._fetch_api_wordlist():
                if self._valid_length(word):
                    yield word
    
    def _valid_length(self, word):
        """Check if word meets length requirements"""
        return self.min_length <= len(word) <= self.max_length
    
    def _get_variations(self, pattern):
        """Generate variations of a pattern"""
        variations = [
            pattern,
            pattern.lower(),
            pattern.upper(),
            pattern.capitalize(),
            pattern[::-1]  # Reverse
        ]
        return variations
    
    def _apply_leet_speak(self, term):
        for char, replacements in LEET_SPEAK_MAP.items():
            for rep in replacements:
                term = term.replace(char, rep)
        return term
        
    def _fetch_api_wordlist(self):
        # Placeholder: Integration with external API (e.g., CrackStation)
        # Can be filled with requests to public APIs if available
        return []
