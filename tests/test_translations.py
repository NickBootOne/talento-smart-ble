import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1] / 'custom_components/talento_smart_ble'


def leaf_paths(value, prefix=()):
    paths = set()
    for key, child in value.items():
        if isinstance(child, dict):
            paths.update(leaf_paths(child, prefix + (key,)))
        else:
            paths.add(prefix + (key,))
    return paths


class TranslationTests(unittest.TestCase):
    def test_english_is_the_source_and_dutch_has_same_keys(self):
        source = json.loads((ROOT / 'strings.json').read_text(encoding='utf-8'))
        english = json.loads((ROOT / 'translations/en.json').read_text(encoding='utf-8'))
        dutch = json.loads((ROOT / 'translations/nl.json').read_text(encoding='utf-8'))
        self.assertEqual(source, english)
        self.assertEqual(leaf_paths(english), leaf_paths(dutch))
        self.assertEqual(english['entity']['switch']['relay_fix']['name'], 'Relay (FIX control)')
        self.assertEqual(dutch['entity']['switch']['relay_fix']['name'], 'Relais (FIX-bediening)')

    def test_existing_relay_state_values_have_both_display_translations(self):
        for language in ['en', 'nl']:
            data = json.loads((ROOT / f'translations/{language}.json').read_text(encoding='utf-8'))
            self.assertEqual(set(data['entity']['sensor']['relay']['state']), {'aan', 'uit'})
