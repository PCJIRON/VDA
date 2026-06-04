import re
import logging

logger = logging.getLogger(__name__)

THINKING_PATTERNS = [
    (r'<thinking>(.*?)</thinking>', re.DOTALL),
    (r'<Thought>(.*?)</Thought>', re.DOTALL),
    (r'<CoT>(.*?)</CoT>', re.DOTALL),
    (r'\[thinking\](.*?)\[/thinking\]', re.DOTALL),
    (r'\n\s*Reasoning:.*?(?=\n|$)', 0),
    (r'\n\s*Let me think.*?(?=\n|$)', 0),
]


def strip_thinking(text: str) -> str:
    for pattern, flags in THINKING_PATTERNS:
        text = re.sub(pattern, '', text, flags=flags)
    lines = text.split('\n')
    filtered = [l for l in lines if not l.strip().startswith('Let me') and not l.strip().startswith('Reasoning:')]
    return '\n'.join(filtered).strip()


def extract_thinking(text: str) -> tuple[str, str]:
    visible = str(text)
    thinking_parts = []
    for pattern, flags in THINKING_PATTERNS:
        matches = re.findall(pattern, visible, flags=flags)
        for m in matches:
            thinking_parts.append(m)
        visible = re.sub(pattern, '', visible, flags=flags)
    visible_lines = []
    for l in visible.split('\n'):
        stripped = l.strip()
        if stripped.startswith('Let me') or stripped.startswith('Reasoning:'):
            thinking_parts.append(stripped)
        else:
            visible_lines.append(l)
    visible = '\n'.join(visible_lines).strip()
    thinking = '\n'.join(thinking_parts).strip()
    return visible, thinking
