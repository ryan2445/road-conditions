import base64
import json
import os
import re
from io import BytesIO

import anthropic
import openai
import PIL.Image
from google import genai

from models import ANALYSIS_PROMPT, AnalysisResult


def _parse_response(text: str | None) -> AnalysisResult:
    """Extract JSON from a VLM response, handling markdown code fences."""
    if text is None:
        raise ValueError("Response text is None")
    # Strip markdown code fences if present
    match = re.search(r"```(?:json)?\s*(.*?)```", text, re.DOTALL)
    json_str = match.group(1) if match else text
    data = json.loads(json_str)
    score = float(data["clearness_score"])
    if not 0.0 <= score <= 1.0:
        raise ValueError(f"clearness_score {score} out of range [0, 1]")
    return AnalysisResult(clearness_score=score, summary=str(data["summary"]))


class ClaudeProvider:
    def __init__(self) -> None:
        self.client = anthropic.Anthropic(
            api_key=os.environ.get("ANTHROPIC_API_KEY"),
        )
        self.model = os.environ.get("ANTHROPIC_MODEL", "")

    def analyze_image(self, image_bytes: bytes) -> AnalysisResult:
        response = self.client.messages.create(
            model=self.model,
            max_tokens=256,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/jpeg",
                                "data": base64.standard_b64encode(image_bytes).decode(),
                            },
                        },
                        {"type": "text", "text": ANALYSIS_PROMPT},
                    ],
                }
            ],
        )
        return _parse_response(response.content[0].text)  # type: ignore[union-attr]


class OpenAIProvider:
    def __init__(self) -> None:
        self.client = openai.OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
        self.model = os.environ.get("OPENAI_MODEL", "gpt-4o")

    def analyze_image(self, image_bytes: bytes) -> AnalysisResult:
        b64 = base64.standard_b64encode(image_bytes).decode()
        response = self.client.chat.completions.create(
            model=self.model,
            max_tokens=256,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{b64}",
                            },
                        },
                        {"type": "text", "text": ANALYSIS_PROMPT},
                    ],
                }
            ],
        )
        return _parse_response(response.choices[0].message.content)


class GeminiProvider:
    def __init__(self) -> None:
        self.client = genai.Client(api_key=os.environ.get("GOOGLE_API_KEY"))
        self.model = os.environ.get("GOOGLE_MODEL", "gemini-3-flash-preview")

    def analyze_image(self, image_bytes: bytes) -> AnalysisResult:
        image = PIL.Image.open(BytesIO(image_bytes))
        response = self.client.models.generate_content(
            model=self.model, contents=[image, ANALYSIS_PROMPT]
        )
        return _parse_response(response.text)
