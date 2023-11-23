import os
import re

import my_tunes


TESTPATH = os.path.dirname(os.path.abspath(__file__))
CHANGES = os.path.join(TESTPATH, "..", "CHANGES.MD")


def test_version_consistency():
    """Test CHANGELOG.md latest version consistency with module version"""
    # Assumption: version info is in a header line (starting with #)
    # We capture the version info in the second group
    version_match = re.compile(r"(#*.*)(\d+\.\d+\.\d+[a-zA-Z0-9_.]*)")
    
    with open(CHANGES, "r") as cf:
        for line in cf:
            pot_match = re.match(version_match, line)
            if pot_match:
                version_changelog = pot_match.groups()[1]
                break
        else:
            raise ValueError("No version information found in the CHANGES file")
    assert (
        my_tunes.__version__.startswith(version_changelog)
    ), f"Version module({my_tunes.__version__}) - CHANGES.MD do not match({version_changelog})"
