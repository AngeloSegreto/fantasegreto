"""Archive the user-supplied league screenshots and transcribe visible settings."""
from pathlib import Path
import argparse
import hashlib
import json
import shutil

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'evidence/league_2026_10_18'


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--source-directory', type=Path, required=True)
    source = parser.parse_args().source_directory
    OUT.mkdir(parents=True, exist_ok=True)
    names = ['IMG_9122(1).png'] + [f'IMG_{n}.png' for n in range(9123, 9128)]
    refs = {}
    for name in names:
        dest = OUT / name.replace('(1)', '')
        shutil.copyfile(source / name, dest)
        refs[name] = {'path': str(dest.relative_to(ROOT)),
                      'sha256': hashlib.sha256(dest.read_bytes()).hexdigest(),
                      'received_at': '2026-10-18T23:03:06+02:00',
                      'source_type': 'USER_SUPPLIED_LEAGUE_APP_SCREENSHOT',
                      'url': None, 'scope': 'Visible settings only; no retroactive pre-lock evidence'}
    config = {
        'version': 'FS_LEAGUE_SCREENSHOTS_V3_3_1_20261018',
        'league_id': 'NATIONAL_LEAGUE_2026_27',
        'league_identity_basis': 'User conversation; league name not visible in settings crops',
        'status': 'PARTIALLY_VERIFIED', 'sources': refs,
        'rules': {
            'fantasy_goals': {'status': 'SCREENSHOT_VERIFIED', 'first_goal': '66',
                'band_width': '4', 'fixed': True, 'unbounded': True,
                'unbounded_basis': 'Ratified V3.3.1; screenshot displays through 94',
                'source': 'IMG_9122(1).png'},
            'substitutions': {'status': 'VISIBLE_SETTINGS_VERIFIED', 'maximum': 5,
                'type_label': 'Traditional', 'office_reserve_enabled': False,
                'source': 'IMG_9123.png', 'detailed_sv_policy': None},
            'defense_modifier': {'status': 'VISIBLE_SETTINGS_VERIFIED', 'enabled': True,
                'minimum_effective_defenders': 4, 'top_defenders': 3,
                'include_keeper': True, 'apply_to': 'OWN_TEAM', 'basis': 'PURE_VOTE',
                'after_substitutions': True, 'office_reserve_eligible': False,
                'political_six_vote': '6', 'sv_yellow_vote_if_validated': '6',
                'sv_yellow_validation_enabled': None,
                'bands': [{'minimum': None, 'bonus': '0'},
                    {'minimum': '6', 'bonus': '0'}, {'minimum': '6.25', 'bonus': '0.5'},
                    {'minimum': '6.5', 'bonus': '1'}, {'minimum': '6.75', 'bonus': '1.5'},
                    {'minimum': '7', 'bonus': '2'}],
                'sources': ['IMG_9125.png', 'IMG_9127.png']},
            'captain_factor': {'status': 'VISIBLE_SETTINGS_VERIFIED', 'enabled': True,
                'vice_when_captain_without_vote': True, 'designate_each_match': True,
                'double_bonuses': False, 'double_penalties': False,
                'at_or_below': {'vote': '4.5', 'bonus': '-1.5'},
                'exact_votes': {'5': '-1', '5.5': '0', '6': '0', '6.5': '0', '7': '1'},
                'at_or_above': {'vote': '7.5', 'bonus': '1.5'},
                'unlisted_vote_policy': None, 'both_without_vote_policy': None,
                'source': 'IMG_9126.png'},
            'bonus_malus': {'status': 'VISIBLE_SETTINGS_VERIFIED',
                'values': {'conceded_goal': '-1', 'penalty_scored': '3',
                    'penalty_missed': '-2', 'penalty_saved': '3', 'yellow': '-0.5',
                    'red': '-1', 'assist_standard': '1', 'assist_soft': '0.5',
                    'assist_gold': '1.5', 'own_goal': '-2', 'equalizing_goal': '0',
                    'winning_goal': '0', 'clean_sheet': '1', 'player_of_match': '0'},
                'ordinary_goal': None, 'source': 'IMG_9124.png',
                'note': 'Upper page is not shown; ordinary goal bonus not certified by this crop'}},
        'release': {'gold_lock': False, 'stat_validated': False, 'tech_pass': False}}
    # JSON syntax is a valid YAML 1.2 document; no loader dependency is required.
    (ROOT / 'league_config.yaml').write_text(json.dumps(config, indent=2, ensure_ascii=False) + '\n')
    (OUT / 'transcription.json').write_text(json.dumps(config, indent=2, ensure_ascii=False) + '\n')
    print('Archived six source screenshots and visible settings; GOLD remains blocked.')


if __name__ == '__main__':
    main()
