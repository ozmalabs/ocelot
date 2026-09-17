from pathlib import Path
from evaluation.p5_r0.native import hardened_crun_argv

def test_hardened_native_command_has_no_mounts_or_network():
    profile = Path('evaluation/p4/seccomp.json')
    argv = hardened_crun_argv(podman='podman', image_digest='sha256:' + 'a' * 64, seccomp_profile=profile)
    assert '--pull=never' in argv and '--network=none' in argv
    assert '--read-only' in argv and '--cap-drop=ALL' in argv
    assert '--pid=private' in argv and '--ipc=private' in argv and '--uts=private' in argv
    assert not any(arg.startswith('--volume') or arg.startswith('--mount') for arg in argv)
