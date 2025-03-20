import gettext
from pathlib import Path


localedir = Path(__file__).parent

translations: gettext.GNUTranslations = gettext.translation('src.app.cta_strategy', localedir=localedir, fallback=True)

_ = translations.gettext
