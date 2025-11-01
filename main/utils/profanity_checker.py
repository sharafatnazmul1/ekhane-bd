from better_profanity import profanity

# load default English
profanity.load_censor_words()

# extend Bangla slang + local abusive terms
bangla_words = [
    "choda", "chod", "bokachoda", "randi", "madarchod",
    "harami", "haraami", "gandu", "nicher", "kuttarbaccha",
    "bessha", "gandubaaz", "boka", "tui", "randi",
    "motherchod", "beparoa", "pagol", "pagla", "baperbeta"
]

profanity.add_censor_words(bangla_words)


def has_profanity(text: str) -> bool:
    return profanity.contains_profanity(text)
