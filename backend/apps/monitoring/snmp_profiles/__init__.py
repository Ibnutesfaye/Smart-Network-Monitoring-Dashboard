from .generic import GenericProfile

PROFILES = {"generic": GenericProfile}


def get_profile(name="generic"):
    return PROFILES.get(name, GenericProfile)()
