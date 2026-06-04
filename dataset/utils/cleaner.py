import re
from collections import Counter
from typing import Tuple, Optional, Dict, Any
from dataclasses import dataclass
from functools import lru_cache
import numpy as np 
@dataclass
class LanguageProfile:
    """Statistical language profile for Malagasy text"""
    malagasy_markers: set = None  # Common Malagasy function words
    french_markers: set = None    # French words that appear in natural Malagasy
    noise_patterns: list = None   # Regex patterns for obvious garbage
    
    def __post_init__(self):
        # Malagasy common words (preserved from web text)
        self.malagasy_markers = {
            "ny", "amin", "ho", "dia", "fa", "ao", "izany", "reo", "isa", 
            "noho", "tamin", "mba", "etsy", "araka", "mbola", "avy", "manao",
            "misy", "tao", "tsy", "efa", "tena", "mbola", "satria", "kosa",
            "ary", "sady", "kanefa", "raha", "ka", "fa", "nefa", "faingana",
            "ankehitriny", "raha", "satria", "mba", "indray", "fotsiny",
        }
        
        # French words that naturally appear in Malagasy (not contamination)
        self.french_markers = {
            "mais", "donc", "puis", "avec", "pour", "chez", "sans", "par",
            "dans", "sur", "sous", "très", "bien", "oui", "non", "merci",
            "bonjour", "aujourd", "demain", "soir", "matin", "petit", "grand",
            "fois", "peu", "beaucoup", "depuis", "pendant", "encore", "toujours",
        }
        
        # Garbage patterns (metadata, code, formatting artifacts)
        self.noise_patterns = [
            (r"^(ISBN|doi|http|https|ftp|www\.|@\w+|#\w+|\d+\.\d+\.\d+\.\d+)", 0.9),  # High confidence garbage
            (r"^\s*[\({\[]?\d+[\)}\]]?\s+[A-Z]", 0.7),  # Numbered list without context
            (r"(?:copyright|©|®|™|all rights reserved)", 0.8),  # Legal boilerplate
            (r"(?:click|tap|swipe|scroll|menu|button|keyboard)", 0.6),  # UI instructions (low confidence)
            (r"(?:xml|json|html|css|javascript|api|endpoint)", 0.9),  # Code references
            (r"^\s*[-=*_]{10,}\s*$", 1.0),  # Visual separators
            (r"(?:fig\.|table|figure|section|chapter|page|pp\.)\s+\d+", 0.7),  # Academic references
            (r"(?:e\.g\.|i\.e\.|et al\.|cf\.|viz\.|ibid\.)", 0.8),  # Latin abbreviations
            (r"[\u0000-\u0008\u000B\u000C\u000E-\u001F]", 1.0),  # Control characters
        ]

def is_conversational_malagasy(text: str) -> Tuple[bool, Dict[str, float]]:
    """
    Determine if text is suitable conversational Malagasy with confidence scores.
    Returns (keep, scores) where scores contains diagnostic information.
    """
    if not text or len(text.strip()) < 10:
        return False, {"reason": "too_short", "confidence": 0.0}
    
    text = text.strip()
    scores = {
        "length_score": 0.0,
        "letter_density": 0.0,
        "malagasy_density": 0.0,
        "noise_score": 0.0,
        "contamination_score": 0.0,
        "repetition_penalty": 0.0
    }
    
    # 1. Length-based scoring (not just binary cutoff)
    words = text.split()
    scores["length_score"] = min(1.0, len(words) / 30)  # Prefer 10-30 words
    
    # 2. Letter density (allow more flexibility)
    letter_count = len(re.findall(r"[A-Za-zÀ-ÿ]", text))
    total_chars = max(1, len(text))
    letter_density = letter_count / total_chars
    scores["letter_density"] = letter_density
    if letter_density < 0.35:  # Lower threshold than before
        return False, scores
    
    # 3. Statistical language detection (not just lookup)
    words_lower = re.findall(r"\b[a-zà-ÿ]{2,}\b", text.lower())
    if not words_lower:
        return False, scores
    
    word_counts = Counter(words_lower)
    total_words = len(words_lower)
    
    profile = LanguageProfile()
    
    # Calculate densities with smoothing
    malagasy_count = sum(1 for w in words_lower if w in profile.malagasy_markers)
    french_count = sum(1 for w in words_lower if w in profile.french_markers)
    
    malagasy_density = malagasy_count / total_words if total_words else 0
    french_density = french_count / total_words if total_words else 0
    
    scores["malagasy_density"] = malagasy_density
    
    # Contamination score: English words are bad, French is expected
    # But we need to detect actual code-mixing vs natural borrowing
    contamination_score = 0.0
    
    # Check for English grammatical patterns (more reliable than word lists)
    english_patterns = [
        r"\b(?:the|and|for|with|from|by|to|of|in|at)\s+\w+",  # English function words
        r"\b(?:is|are|was|were|be|been|being)\s+\w+",  # English copula
        r"\b(?:I|you|he|she|it|we|they)\s+\w+",  # English pronouns
        r"\b(?:have|has|had|do|does|did)\s+\w+",  # English auxiliaries
    ]
    
    for pattern in english_patterns:
        if re.search(pattern, text, re.I):
            contamination_score += 0.2
    
    # Specific code-mixed garbage patterns
    garbage_patterns = [
        r"lol|omg|wtf|fyi|btw|imo|smh",  # Internet slang
        r"\b[a-z]{1,2}\b(?![\'à-ÿ])",  # Single/double letters (no diacritics) - often noise
        r"\b(?:etc|vs|ie|eg|al)\b",  # Latin abbreviations
        r"(?:\d{1,2}:\d{2}\s*(?:am|pm))",  # Timestamps
        r"(?:https?://|www\.)[^\s]+",  # URLs
        r"[@#]\w+",  # Mentions/hashtags
    ]
    
    for pattern in garbage_patterns:
        if re.search(pattern, text, re.I):
            contamination_score += 0.15
    
    scores["contamination_score"] = min(1.0, contamination_score)
    
    # 4. Noise pattern scoring with confidence weighting
    noise_score = 0.0
    for pattern, confidence in profile.noise_patterns:
        if re.search(pattern, text, re.I):
            noise_score += confidence * 0.3  # Each pattern contributes up to 0.3
    
    scores["noise_score"] = min(1.0, noise_score)
    
    # 5. Repetition detection (stuttering artifacts)
    repetition_penalty = 0.0
    
    # Check for repeated character sequences
    if re.search(r"(.)\1{4,}", text):  # 5+ same chars in a row
        repetition_penalty += 0.3
    
    # Check for repeated word patterns
    if re.search(r"\b(\w+)(?:\s+\1){3,}\b", text, re.I):  # Same word 4+ times
        repetition_penalty += 0.4
    
    # Check for n-gram repetition (common in scraped artifacts)
    words_small = text.lower().split()
    if len(words_small) > 10:
        trigrams = Counter(zip(words_small, words_small[1:], words_small[2:]))
        if max(trigrams.values() if trigrams else [0]) > 2:
            repetition_penalty += 0.2
    
    scores["repetition_penalty"] = min(0.8, repetition_penalty)
    
    # 6. Decision logic with adaptive thresholds
    keep = True
    reasons = []
    
    # Rule 1: Must have some Malagasy content
    if malagasy_density < 0.05 and len(text) > 20:
        keep = False
        reasons.append("no_malagasy_content")
    
    # Rule 2: High contamination (>50%) from English/garbage
    if contamination_score > 0.5:
        keep = False
        reasons.append(f"high_contamination_{contamination_score:.2f}")
    
    # Rule 3: High noise score (>60%)
    if noise_score > 0.6:
        keep = False
        reasons.append(f"high_noise_{noise_score:.2f}")
    
    # Rule 4: Severe repetition
    if repetition_penalty > 0.5:
        keep = False
        reasons.append("excessive_repetition")
    
    # Rule 5: Special case - allow short utterances if they're clearly conversational
    if len(words) <= 5 and contamination_score < 0.2 and malagasy_density > 0:
        keep = True  # Short phrases like "Misaotra" or "Eny" are valid
    
    # Rule 6: Allow some French if mostly Malagasy
    if french_density > 0.3 and malagasy_density < 0.1:
        keep = False
        reasons.append("too_much_french_no_malagasy")
    
    scores["keep_reason"] = reasons if not keep else None
    
    return keep, scores


def clean_conversational_sample(text: str, min_confidence: float = 0.6) -> Optional[str]:
    """
    Clean a single text sample with diagnostic confidence scoring.
    Returns cleaned text or None if should be discarded.
    """
    if not text:
        return None
    
    original = text.strip()
    
    # Statistical filtering
    keep, scores = is_conversational_malagasy(original)
    
    if not keep:
        return None
    
    # Apply cleaning operations
    cleaned = original
    
    # Fix hyphenation (preserve intentional hyphens)
    cleaned = re.sub(r"(\w)-\s+(\w)", r"\1\2", cleaned)
    
    # Remove control characters
    cleaned = re.sub(r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]", "", cleaned)
    
    # Normalize whitespace
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    
    # Fix partial sentence artifacts (e.g., hanging punctuation)
    cleaned = re.sub(r'([.!?])\s*["\']?\s*$', r'\1', cleaned)
    
    # Remove common metadata suffixes
    cleaned = re.sub(r'\s*[-–—]\s*(?:Wikipedia|Wiktionary|Source|Retrieved from).*$', '', cleaned, re.I)
    
    # Remove trailing incomplete fragments (after 3+ periods)
    cleaned = re.sub(r'\.{3,}.*$', '', cleaned)
    
    # Balance quotes if possible (simple case)
    if cleaned.count('"') % 2 != 0:
        # Remove trailing unmatched quote
        cleaned = re.sub(r'"\s*$', '', cleaned)
    
    # Final length validation
    if len(cleaned) < 8:
        return None
    
    return cleaned


def filter_dataset_batch(samples: list, verbose: bool = False) -> list:
    """
    Filter a batch of samples with detailed statistics.
    Returns filtered samples with metadata.
    """
    filtered = []
    stats = {
        "total": len(samples),
        "kept": 0,
        "reasons": Counter(),
        "score_distribution": []
    }
    
    for sample in samples:
        text = sample.get("Malagasy", "") if isinstance(sample, dict) else sample
        
        keep, scores = is_conversational_malagasy(text)
        
        if keep:
            cleaned = clean_conversational_sample(text)
            if cleaned:
                if isinstance(sample, dict):
                    sample["Malagasy_clean"] = cleaned
                    filtered.append(sample)
                else:
                    filtered.append(cleaned)
                stats["kept"] += 1
        else:
            reason = scores.get("keep_reason", ["unknown"])[0] if scores.get("keep_reason") else "unknown"
            stats["reasons"][reason] += 1
        
        if verbose and not keep:
            print(f"REJECTED: {text[:80]}... | Reason: {scores.get('keep_reason')} | Scores: {scores}")
    
    if verbose:
        print(f"\nFiltering stats: {stats['kept']}/{stats['total']} kept ({stats['kept']/stats['total']*100:.1f}%)")
        print(f"Top rejection reasons: {stats['reasons'].most_common(5)}")
    
    return filtered


# Example usage with your data
def prepare_training_data(samples: list, output_format: str = "qwen") -> list:
    """
    Convert cleaned samples to Qwen2.5 instruction format.
    """
    formatted = []
    
    for sample in samples:
        text = sample.get("Malagasy_clean", sample.get("Malagasy", ""))
        emotion = sample.get("emotion", "neutral")
        
        if not text:
            continue
        
        if output_format == "qwen":
            # Qwen2.5 chat format
            formatted.append({
                "messages": [
                    {"role": "system", "content": "You are a helpful assistant that speaks Malagasy naturally."},
                    {"role": "user", "content": text},
                    {"role": "assistant", "content": f"Eny, azoko. {text[:100]}..."}  # Placeholder response
                ],
                "emotion": emotion
            })
        elif output_format == "conversation":
            # Simple conversation format for fine-tuning
            formatted.append({
                "input": f"Malagasy: {text}",
                "output": f"Malagasy response here",  # You'll need to generate these
                "emotion": emotion
            })
    
    return formatted


# Adaptive threshold based on dataset statistics
class AdaptiveDataFilter:
    """Learns optimal thresholds from your dataset"""
    
    def __init__(self, target_keep_rate: float = 0.4):
        self.target_keep_rate = target_keep_rate
        self.thresholds = {
            "min_malagasy_density": 0.05,
            "max_contamination": 0.50,
            "max_noise": 0.60,
            "min_length": 10,
            "max_repetition": 0.50,
        }
    
    def analyze_sample_batch(self, samples: list) -> Dict[str, Any]:
        """Analyze a batch to determine optimal thresholds"""
        scores_list = []
        
        for sample in samples:
            text = sample.get("Malagasy", "") if isinstance(sample, dict) else sample
            _, scores = is_conversational_malagasy(text)
            scores_list.append(scores)
        
        # Compute statistics
        analysis = {
            "avg_length_score": np.mean([s["length_score"] for s in scores_list]),
            "avg_letter_density": np.mean([s["letter_density"] for s in scores_list]),
            "avg_malagasy_density": np.mean([s["malagasy_density"] for s in scores_list]),
            "contamination_percentiles": np.percentile([s["contamination_score"] for s in scores_list], [25, 50, 75]),
            "noise_percentiles": np.percentile([s["noise_score"] for s in scores_list], [25, 50, 75]),
        }
        
        # Suggest thresholds based on data distribution
        if analysis["avg_malagasy_density"] < 0.03:
            # Dataset is very noisy, relax constraints
            self.thresholds["min_malagasy_density"] = 0.02
            self.thresholds["max_contamination"] = 0.60
        
        return analysis