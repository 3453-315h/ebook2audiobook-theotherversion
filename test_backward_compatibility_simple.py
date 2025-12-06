#!/usr/bin/env python3

"""
Simple test script to verify backward compatibility with existing TTS engines
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'lib'))

from lib.models import TTS_ENGINES, default_engine_settings

def test_backward_compatibility_simple():
    """Test that existing TTS engines still work after Supertonic integration"""

    print("Testing backward compatibility...")

    # Test 1: Check that all existing TTS engines are still available
    expected_engines = ['XTTSv2', 'BARK', 'VITS', 'FAIRSEQ', 'TACOTRON2', 'YOURTTS', 'SUPERTONIC']
    for engine in expected_engines:
        assert engine in TTS_ENGINES, f"Missing TTS engine: {engine}"
    print("[+] All expected TTS engines are available")

    # Test 2: Check that existing engines have their settings
    for engine_name, engine_key in TTS_ENGINES.items():
        assert engine_key in default_engine_settings, f"Missing settings for {engine_name}"
        print(f"[+] {engine_name} has settings")

    # Test 3: Check that Supertonic doesn't interfere with existing engine settings
    # Verify that existing engines still have their expected parameters
    xtts_settings = default_engine_settings[TTS_ENGINES['XTTSv2']]
    assert 'temperature' in xtts_settings, "XTTSv2 missing temperature parameter"
    assert 'speed' in xtts_settings, "XTTSv2 missing speed parameter"

    bark_settings = default_engine_settings[TTS_ENGINES['BARK']]
    assert 'text_temp' in bark_settings, "BARK missing text_temp parameter"
    assert 'waveform_temp' in bark_settings, "BARK missing waveform_temp parameter"

    print("[+] Existing engine parameters are intact")

    print("\n[+] Backward compatibility test completed successfully!")
    return True

if __name__ == "__main__":
    success = test_backward_compatibility_simple()
    sys.exit(0 if success else 1)