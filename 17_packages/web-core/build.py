"""Reproducible Web Core CSS bundle from v3.3 canonical generated CSS and component layer."""
from pathlib import Path
import argparse
here=Path(__file__).resolve().parent
root=here.parents[1]
source=(root/'04_tokens/taktera.tokens.css').read_text(encoding='utf-8')
component=(here/'component.css').read_text(encoding='utf-8')
target=here/'taktera-ui.css'
content='/* Self-contained Taktera UI alpha.3 CSS (generated); no external dependencies. */\n'+source+'\n'+component
parser=argparse.ArgumentParser();parser.add_argument('--check',action='store_true');args=parser.parse_args()
if args.check:
    assert target.read_text(encoding='utf-8')==content, 'CSS bundle is out of sync'
    print('Web Core CSS matches tokens and component source')
else:
    target.write_text(content,encoding='utf-8');print('Wrote',target)
