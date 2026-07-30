import subprocess
import tarfile
import zipfile
from pathlib import Path


def test_distribution_artifacts_include_license(tmp_path):
    root = Path(__file__).resolve().parents[1]
    dist_dir = tmp_path / "dist"
    subprocess.run(
        ["uv", "build", "--out-dir", str(dist_dir)],
        cwd=root,
        check=True,
    )

    wheels = list(dist_dir.glob("*.whl"))
    sdists = list(dist_dir.glob("*.tar.gz"))
    assert len(wheels) == 1
    assert len(sdists) == 1

    expected_notice = (root / "LICENSE").read_bytes()

    with zipfile.ZipFile(wheels[0]) as wheel:
        license_paths = [
            name
            for name in wheel.namelist()
            if name.endswith(".dist-info/licenses/LICENSE")
        ]
        assert len(license_paths) == 1
        assert wheel.read(license_paths[0]) == expected_notice

        metadata_paths = [
            name
            for name in wheel.namelist()
            if name.endswith(".dist-info/METADATA")
        ]
        assert len(metadata_paths) == 1
        metadata_headers = wheel.read(metadata_paths[0]).split(b"\n\n", 1)[0]
        assert b"License-File: LICENSE" in metadata_headers.splitlines()

    sdist_root = sdists[0].name.removesuffix(".tar.gz")
    license_path = f"{sdist_root}/LICENSE"
    with tarfile.open(sdists[0], "r:gz") as sdist:
        assert license_path in sdist.getnames()
        license_member = sdist.extractfile(license_path)
        assert license_member is not None
        with license_member:
            assert license_member.read() == expected_notice
