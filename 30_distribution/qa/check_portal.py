from html.parser import HTMLParser
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
class Links(HTMLParser):
    def __init__(self):super().__init__();self.links=[];self.cards=0
    def handle_starttag(self,tag,attrs):
        attrs=dict(attrs)
        if 'data-doc' in attrs:self.cards+=1
        for key in ('href','src'):
            if key in attrs:self.links.append(attrs[key])
page=ROOT/'30_distribution/portal/index.html';doc=Links();doc.feed(page.read_text(encoding='utf-8'))
assert doc.cards>=6
for link in doc.links:
    assert not link.startswith(('http:','https:','//','javascript:')),link
    target=(page.parent/link.split('#')[0]).resolve()
    assert target.is_relative_to(ROOT) and target.is_file(),link
print(f'Developer portal: {doc.cards} sections, {len(doc.links)} local links PASS')
