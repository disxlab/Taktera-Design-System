#!/usr/bin/env python3
"""Generate legacy Tk* brush keys from canonical Tkn* brushes for Avalonia Controls.
Do not alter the canonical generated token dictionaries.
"""
from pathlib import Path
import xml.etree.ElementTree as ET
root=Path(__file__).resolve().parents[1]
source=root/'25_internal_completion/generated/avalonia'
output=root/'27_beta_readiness_3/avalonia_compat'
output.mkdir(exist_ok=True)
ns='{http://schemas.microsoft.com/winfx/2006/xaml}Key'
mapping={
'TkMarkBrush':'TknFoundationMarkBrush',
'TkCanvasBrush':'TknFoundationCanvasBrush',
'TkSurfaceBrush':'TknFoundationSurfaceBrush',
'TkTextBrush':'TknFoundationTextBrush',
'TkMutedBrush':'TknFoundationMutedBrush',
'TkBorderBrush':'TknFoundationBorderBrush',
'TkControlBorderBrush':'TknFoundationControlBorderBrush',
'TkDisabledBgBrush':'TknFoundationDisabledBgBrush',
'TkDisabledTextBrush':'TknFoundationDisabledTextBrush',
'TkAccentBrush':'TknBrandAccentBrush',
'TkOnAccentBrush':'TknBrandOnAccentBrush',
'TkAccentTextBrush':'TknBrandAccentTextBrush',
'TkAccentTextCanvasBrush':'TknBrandAccentTextCanvasBrush',
'TkAccentHoverBrush':'TknBrandAccentHoverBrush',
'TkAccentPressedBrush':'TknBrandAccentPressedBrush',
'TkFocusRingBrush':'TknBrandFocusRingBrush',
'TkStatusSuccessTextBrush':'TknSemanticSuccessForegroundBrush',
'TkStatusSuccessBgBrush':'TknSemanticSuccessBackgroundBrush',
'TkStatusInfoTextBrush':'TknSemanticInfoForegroundBrush',
'TkStatusInfoBgBrush':'TknSemanticInfoBackgroundBrush',
'TkStatusWarningTextBrush':'TknSemanticWarningForegroundBrush',
'TkStatusWarningBgBrush':'TknSemanticWarningBackgroundBrush',
'TkStatusErrorTextBrush':'TknSemanticErrorForegroundBrush',
'TkStatusErrorBgBrush':'TknSemanticErrorBackgroundBrush',
}
for f in sorted(source.glob('Taktera.*.axaml')):
    tree=ET.parse(f)
    colors={e.attrib[ns]:e.attrib.get('Color') for e in tree.getroot().iter() if ns in e.attrib and e.tag.endswith('SolidColorBrush')}
    missing=set(mapping.values())-colors.keys()
    if missing:raise ValueError(f'{f.name}: {sorted(missing)}')
    content=['<?xml version="1.0" encoding="utf-8"?>',f'<!-- GENERATED compatibility adapter from {f.name}; Tk* API -->',
       '<ResourceDictionary xmlns="https://github.com/avaloniaui" xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml">']
    for dest,src in mapping.items():content.append(f'  <SolidColorBrush x:Key="{dest}" Color="{colors[src]}"/>')
    content.append('</ResourceDictionary>')
    (output/f.name).write_text('\n'.join(content)+'\n',encoding='utf-8')
print(f'Avalonia compatibility dictionaries: {len(list(output.glob("Taktera.*.axaml")))}')
