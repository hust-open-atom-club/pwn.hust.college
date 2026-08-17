import re
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SSHD_DOCKERFILE = REPOSITORY_ROOT / "sshd/Dockerfile"
PIP_INSTALL_PATTERN = re.compile(r"\bpip\d*\s+install\b")


def test_sshd_pip_installations_suppress_root_warning():
    installLines = [
        (lineNumber, line.strip())
        for lineNumber, line in enumerate(
            SSHD_DOCKERFILE.read_text(encoding="utf-8").splitlines(), start=1
        )
        if PIP_INSTALL_PATTERN.search(line)
    ]

    assert installLines
    for lineNumber, installLine in installLines:
        assert "PIP_ROOT_USER_ACTION=ignore" in installLine, (
            f"{SSHD_DOCKERFILE}:{lineNumber} 未显式处理 root pip 警告"
        )
