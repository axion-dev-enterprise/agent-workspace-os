from pathlib import Path
import json, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

p1 = Path(r"C:\workspace\memory\telegram\chats\5511988045139@s.whatsapp.net.jsonl")
p2 = Path(r"C:\workspace\memory\telegram\chats\36735559962762@lid.jsonl")

print("=== 5511988045139@s.whatsapp.net.jsonl ===")
if p1.exists():
    for l in p1.read_text(encoding='utf-8').splitlines():
        d = json.loads(l)
        print(d.get('timestamp')[:19], "|", d.get('direction'), "|", d.get('text')[:100].replace('\n', ' '))

print("\n=== 36735559962762@lid.jsonl ===")
if p2.exists():
    for l in p2.read_text(encoding='utf-8').splitlines():
        d = json.loads(l)
        print(d.get('timestamp')[:19], "|", d.get('direction'), "|", d.get('text')[:100].replace('\n', ' '))
