"""
Israinsols Pipeline - Inline Keyboards (Phase 4)

Telegram inline buttons banata hai:
1. "🚀 Apply Now" — Direct job URL open kare
2. "✅ Contacted" — Database mein status update
3. "❌ Irrelevant" — Lead reject kare

Har button ka callback_data format: "action:lead_id"
"""
import json


class InlineKeyboardButton:
    """Simple inline keyboard button (compatible with Telegram Bot API)"""

    def __init__(self, text: str, url: str = None, callback_data: str = None):
        self.text = text
        self.url = url
        self.callback_data = callback_data

    def to_dict(self) -> dict:
        data = {'text': self.text}
        if self.url:
            data['url'] = self.url
        if self.callback_data:
            data['callback_data'] = self.callback_data
        return data


class InlineKeyboardMarkup:
    """Simple inline keyboard markup (compatible with Telegram Bot API)"""

    def __init__(self, inline_keyboard: list = None):
        self.inline_keyboard = inline_keyboard or []

    def to_dict(self) -> dict:
        return {
            'inline_keyboard': [
                [btn.to_dict() for btn in row]
                for row in self.inline_keyboard
            ]
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict())

    def to_aiogram_markup(self):
        """Convert to aiogram InlineKeyboardMarkup for use in bot handlers"""
        try:
            from aiogram.types import (
                InlineKeyboardMarkup as AiogramMarkup,
                InlineKeyboardButton as AiogramButton,
            )

            rows = []
            for row in self.inline_keyboard:
                aiogram_row = []
                for btn in row:
                    kwargs = {'text': btn.text}
                    if btn.url:
                        kwargs['url'] = btn.url
                    if btn.callback_data:
                        kwargs['callback_data'] = btn.callback_data
                    aiogram_row.append(AiogramButton(**kwargs))
                rows.append(aiogram_row)

            return AiogramMarkup(inline_keyboard=rows)

        except ImportError:
            # Fallback if aiogram is not installed (for API-only usage)
            return self


def get_lead_keyboard(lead_id: int, job_url: str) -> InlineKeyboardMarkup:
    """
    Lead alert ke liye inline keyboard banao.

    3 Buttons:
    - "🚀 Apply Now"    → Opens the job URL directly
    - "✅ Contacted"    → Updates lead status to 'contacted'
    - "❌ Irrelevant"   → Updates lead status to 'rejected'

    Callback data format: "action:lead_id"
    """
    return InlineKeyboardMarkup(
        inline_keyboard=[
            # Row 1: Apply button (URL button — opens in browser)
            [
                InlineKeyboardButton(
                    text="🚀 Apply Now",
                    url=job_url,
                ),
            ],
            # Row 2: Action buttons (callback buttons — triggers bot handler)
            [
                InlineKeyboardButton(
                    text="✅ Contacted",
                    callback_data=f"contacted:{lead_id}",
                ),
                InlineKeyboardButton(
                    text="❌ Irrelevant",
                    callback_data=f"reject:{lead_id}",
                ),
            ],
            # Row 3: Extra actions
            [
                InlineKeyboardButton(
                    text="🟣 Applied",
                    callback_data=f"applied:{lead_id}",
                ),
                InlineKeyboardButton(
                    text="📝 Add Note",
                    callback_data=f"note:{lead_id}",
                ),
            ],
        ]
    )


def get_status_updated_keyboard(lead_id: int, job_url: str) -> InlineKeyboardMarkup:
    """
    Status update hone ke baad simplified keyboard.
    Sirf Apply aur Undo buttons.
    """
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🚀 Apply Now",
                    url=job_url,
                ),
                InlineKeyboardButton(
                    text="↩️ Undo",
                    callback_data=f"undo:{lead_id}",
                ),
            ],
        ]
    )
