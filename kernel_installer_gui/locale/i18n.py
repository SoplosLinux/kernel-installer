"""
Internationalization (i18n) support using gettext.
Provides _() function for translatable strings.
"""

import gettext
import locale
import os
from pathlib import Path

# Application domain
DOMAIN = "kernel-installer"

# Locale directory (relative to package)
LOCALE_DIR = Path(__file__).parent.parent / "locale"

# System locale directories to search
SYSTEM_LOCALE_DIRS = [
    Path("/usr/share/locale"),
    Path("/usr/local/share/locale"),
    Path.home() / ".local/share/locale",
]

# Current translation instance
_translation = None


def init_i18n(language: str = None) -> None:
    """
    Initialize internationalization.
    
    Args:
        language: Force a specific language (e.g. 'es', 'en'), or None for system default
    """
    global _translation
    
    # Get locale directories to search
    locale_dirs = [LOCALE_DIR] + SYSTEM_LOCALE_DIRS
    locale_dirs = [d for d in locale_dirs if d.exists()]
    
    # Determine languages to try
    if language:
        languages = [language]
    else:
        # Use system locale
        try:
            system_lang = locale.getdefaultlocale()[0]
            if system_lang:
                languages = [system_lang.split('_')[0], system_lang]
            else:
                languages = ['en']
        except Exception:
            languages = ['en']
    
    # Try to load translation
    for locale_dir in locale_dirs:
        try:
            _translation = gettext.translation(
                DOMAIN,
                localedir=str(locale_dir),
                languages=languages,
                fallback=False
            )
            return
        except FileNotFoundError:
            continue
    
    # Fallback to NullTranslations (returns original strings)
    _translation = gettext.NullTranslations()


def _(message: str) -> str:
    """
    Translate a string.
    
    Use this function to wrap all user-visible strings:
        _("Hello, world!")
    
    Args:
        message: The string to translate
        
    Returns:
        Translated string, or original if no translation available
    """
    global _translation
    
    if _translation is None:
        init_i18n()
    
    return _translation.gettext(message)


def ngettext(singular: str, plural: str, n: int) -> str:
    """
    Translate a string with plural forms.
    
    Args:
        singular: Singular form
        plural: Plural form
        n: Count
        
    Returns:
        Appropriate translated form
    """
    global _translation
    
    if _translation is None:
        init_i18n()
    
    return _translation.ngettext(singular, plural, n)


def get_available_languages() -> list[str]:
    """Get list of available translations."""
    available = ['en']  # English is always available (fallback)
    
    for locale_dir in [LOCALE_DIR] + SYSTEM_LOCALE_DIRS:
        if locale_dir.exists():
            for lang_dir in locale_dir.iterdir():
                if lang_dir.is_dir():
                    mo_path = lang_dir / "LC_MESSAGES" / f"{DOMAIN}.mo"
                    if mo_path.exists():
                        lang = lang_dir.name
                        if lang not in available:
                            available.append(lang)
    
    return sorted(available)
