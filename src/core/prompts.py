"""
FlowNote - Prompt templates for different note styles
"""

class NoteStyles:
    PROMPTS = {
        "concise": """Convert to brief bullet notes (3-5 bullets max).

Content:
{content}

Output format:
## Title
• Point 1
• Point 2
• Point 3""",

        "elaborate": """Convert to detailed notes with explanations.

Content:
{content}

Output format:
## Title

**Overview:**
[2-3 sentence summary]

**Key Points:**
• Point 1: [brief explanation]
• Point 2: [brief explanation]
• Point 3: [brief explanation]

**Takeaway:**
[1 sentence conclusion]""",

        "bullets": """Extract all key information as bullet points.

Content:
{content}

Output format:
## Title

• [Bullet 1]
• [Bullet 2]
• [Bullet 3]
• [Bullet 4]
• [Bullet 5]
• [Bullet 6 if relevant]""",

        "summary": """Create a concise summary.

Content:
{content}

Output format:
## Title

[2-3 sentence summary]""",

        "technical": """Convert to technical documentation format.

Content:
{content}

Output format:
## Title

**Definition:**
[What this is]

**Key Components:**
• Component 1
• Component 2
• Component 3

**Usage:**
[How to use/apply]

**Notes:**
[Any important details]""",
    }

    DEFAULT_STYLE = "concise"

    @classmethod
    def get_prompt(cls, style: str = None, content: str = "") -> str:
        if not style:
            style = cls.DEFAULT_STYLE
        prompt_template = cls.PROMPTS.get(style, cls.PROMPTS[cls.DEFAULT_STYLE])
        return prompt_template.format(content=content)

    @classmethod
    def get_available_styles(cls) -> list:
        return list(cls.PROMPTS.keys())
