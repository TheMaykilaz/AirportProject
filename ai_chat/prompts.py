import logging


logger = logging.getLogger(__name__)


class PromptBuilder:
    SYSTEM_PROMPT = (
        "You are AirplaneDJ AI assistant for flight bookings.\n\n"
        "CAPABILITIES:\n"
        "- Help with flight bookings and information\n"
        "- Provide flight details and prices\n"
        "- Answer questions about flights, airlines, and travel\n\n"
        "{context}\n\n"
        "For booking, you need: name, passport, dates, airports, class, number of passengers."
    )

    @classmethod
    def build_system_prompt(cls, context: str) -> str:
        return cls.SYSTEM_PROMPT.format(context=context)

    @classmethod
    def build_prompt(cls, message: str, conversation_history: list[dict], flight_context: str = "") -> str:
        system_prompt = cls.build_system_prompt(flight_context)
        logger.debug(f"Building prompt for message (length: {len(message)})")

        message = (message or "")[:600]

        if not conversation_history:
            return f"<s>[INST] <<SYS>>\n{system_prompt}\n<</SYS>>\n\n{message} [/INST]"

        prompt = f"<s>[INST] <<SYS>>\n{system_prompt}\n<</SYS>>\n\n"
        for msg in conversation_history[-3:]:
            role = msg.get('role', 'user')
            content = (msg.get('content', '') or '')[:400]
            if role == 'user':
                prompt += f"{content} [/INST]"
            else:
                prompt += f" {content} </s><s>[INST] "
        prompt += f"{message} [/INST]"
        return prompt


