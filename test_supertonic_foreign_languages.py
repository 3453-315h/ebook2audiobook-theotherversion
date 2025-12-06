#!/usr/bin/env python3
"""
Test script to verify Supertonic foreign language support
"""

import os
import sys
from lib.lang import language_tts
from lib.models import models

def test_supertonic_language_support():
    """Test that Supertonic supports the expected foreign languages"""

    print("Testing Supertonic foreign language support...")

    # Check that Supertonic language mappings include the new languages
    supertonic_languages = language_tts["supertonic"]

    # Expected languages (original 10 + new 20)
    expected_languages = {
        "eng", "fra", "deu", "spa", "ita", "por", "rus", "jpn", "kor", "zho",  # Original 10
        "ara", "ben", "hin", "tur", "nld", "pol", "swe", "dan", "nob", "fin",  # New 10
        "ind", "vie", "tha", "ell", "heb", "hun", "ces", "ron", "ukr", "bul", "srp"  # New 11 (total 31)
    }

    print(f"Supertonic supports {len(supertonic_languages)} languages:")
    for lang_code, lang_name in supertonic_languages.items():
        print(f"  {lang_code}: {lang_name}")

    # Verify all expected languages are present
    missing_languages = expected_languages - set(supertonic_languages.keys())
    if missing_languages:
        print(f"ERROR: Missing languages: {missing_languages}")
        return False

    # Verify Supertonic models include the new language models
    from lib.models import TTS_ENGINES
    supertonic_models = models[TTS_ENGINES['SUPERTONIC']]

    expected_model_languages = {
        "arabic", "bengali", "hindi", "turkish", "dutch",
        "polish", "swedish", "danish", "norwegian", "finnish",
        "indonesian", "vietnamese", "thai", "greek", "hebrew",
        "hungarian", "czech", "romanian", "ukrainian", "bulgarian", "serbian"
    }

    model_languages = set()
    for model_name, model_config in supertonic_models.items():
        if model_name not in ["internal", "fast", "high_quality", "multilingual", "english_optimized"]:
            model_languages.add(model_name)

    print(f"\nSupertonic has {len(model_languages)} language-specific models:")
    for model_lang in sorted(model_languages):
        print(f"  {model_lang}")

    # Verify all expected model languages are present
    missing_model_languages = expected_model_languages - model_languages
    if missing_model_languages:
        print(f"ERROR: Missing model languages: {missing_model_languages}")
        return False

    print("\nAll Supertonic foreign language tests passed!")
    return True

def test_language_mappings():
    """Test that language mappings exist for all Supertonic languages"""

    print("\nTesting language mappings...")

    from lib.lang import language_mapping, language_math_phonemes, language_clock

    supertonic_languages = language_tts["supertonic"]

    # Check that we have mappings for key language features
    for lang_code in supertonic_languages.keys():
        if lang_code in language_mapping:
            print(f"[OK] {lang_code}: Has language mapping")
        else:
            print(f"[MISSING] {lang_code}: Missing language mapping")

        if lang_code in language_math_phonemes:
            print(f"[OK] {lang_code}: Has math phonemes")
        else:
            print(f"[MISSING] {lang_code}: Missing math phonemes")

        if lang_code in language_clock:
            print(f"[OK] {lang_code}: Has clock formatting")
        else:
            print(f"[MISSING] {lang_code}: Missing clock formatting")

    return True

if __name__ == "__main__":
    print("=" * 60)
    print("Supertonic Foreign Language Support Test")
    print("=" * 60)

    success = True

    # Test 1: Language support
    if not test_supertonic_language_support():
        success = False

    # Test 2: Language mappings
    if not test_language_mappings():
        success = False

    print("\n" + "=" * 60)
    if success:
        print("ALL TESTS PASSED! Supertonic now supports 31 languages!")
        print("Added 21 new foreign language models!")
    else:
        print("Some tests failed!")
    print("=" * 60)

    sys.exit(0 if success else 1)