"""Compatibility functions."""


def linux_distribution(full_distribution_name=True):
    try:
        # Python < 3.8
        from platform import linux_distribution
        return linux_distribution(
            full_distribution_name=full_distribution_name)
    except ImportError:
        pass

    try:
        from distro import linux_distribution
        return linux_distribution(
            full_distribution_name=full_distribution_name)
    except ImportError:
        pass

    # TODO: use platform.freedesktop_os_release for Python >= 3.10

    return '', '', ''
