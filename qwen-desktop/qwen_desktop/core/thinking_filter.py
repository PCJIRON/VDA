import re
import logging

logger = logging.getLogger(__name__)

THINKING_PATTERNS = [
    (r'<thinking>(.*?)</thinking>', re.DOTALL),
    (r'<think>(.*?)</think>', re.DOTALL),
    (r'<Thought>(.*?)</Thought>', re.DOTALL),
    (r'<CoT>(.*?)</CoT>', re.DOTALL),
    (r'\[thinking\](.*?)\[/thinking\]', re.DOTALL),
    (r'\[reasoning\](.*?)\[/reasoning\]', re.DOTALL),
    (r'<reasoning>(.*?)</reasoning>', re.DOTALL),
    (r'reasoning_content:\s*(.*?)(?=\n\S|\Z)', re.DOTALL),
    (r'reasoning_details:\s*(.*?)(?=\n\S|\Z)', re.DOTALL),
    (r'\n\s*Reasoning:.*?(?=\n\s*\S|\Z)', re.DOTALL),
    (r'\n\s*Let me think.*?(?=\n\s*\S|\Z)', re.DOTALL),
    (r'\n\s*Let me analyze.*?(?=\n\s*\S|\Z)', re.DOTALL),
    (r'\n\s*I\'ll approach this.*?(?=\n\s*\S|\Z)', re.DOTALL),
]

LINE_STARTS_TO_REMOVE = [
    "Let me", "Reasoning:", "I'll approach", "I need to",
    "First,", "First let", "Okay,", "Alright,",
    "Thinking:", "Thought:", "Step ", "Stepby", "Step-by-step",
]


def strip_thinking(text: str) -> str:
    for pattern, flags in THINKING_PATTERNS:
        text = re.sub(pattern, '', text, flags=flags)
    lines = text.split('\n')
    filtered = []
    for l in lines:
        stripped = l.strip()
        skip = False
        for prefix in LINE_STARTS_TO_REMOVE:
            if stripped.startswith(prefix):
                skip = True
                break
        if not skip:
            filtered.append(l)
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
        skip = False
        for prefix in LINE_STARTS_TO_REMOVE:
            if stripped.startswith(prefix):
                skip = True
                break
        if skip:
            thinking_parts.append(stripped)
        else:
            visible_lines.append(l)
    visible = '\n'.join(visible_lines).strip()
    thinking = '\n'.join(thinking_parts).strip()
    return visible, thinking
