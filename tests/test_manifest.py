import pytest

from runwisp_jobkit.manifest import JobConfigurationError, JobManifest, load_manifest


def test_load_manifest_returns_typed_values(job_dir):
    assert load_manifest(job_dir) == JobManifest(
        job_dir=job_dir.resolve(),
        job_id="example-job",
        argv=("bash", "run.sh"),
        cwd=job_dir.resolve(),
        required_env=("EXAMPLE_MESSAGE",),
        required_files=((job_dir / "run.sh").resolve(),),
    )


def test_optional_fields_receive_documented_defaults(job_dir):
    (job_dir / "job.toml").write_text(
        """schema = 1
id = "minimal-job"
kind = "command"
argv = ["true"]
""",
        encoding="utf-8",
    )

    assert load_manifest(job_dir) == JobManifest(
        job_dir=job_dir.resolve(),
        job_id="minimal-job",
        argv=("true",),
        cwd=job_dir.resolve(),
        required_env=(),
        required_files=(),
    )


def test_unknown_field_is_rejected(job_dir):
    manifest = job_dir / "job.toml"
    manifest.write_text(
        manifest.read_text(encoding="utf-8") + 'timeout = "5m"\n',
        encoding="utf-8",
    )
    with pytest.raises(JobConfigurationError, match="unknown job.toml field"):
        load_manifest(job_dir)


def test_schema_bool_is_not_accepted_as_integer(job_dir):
    manifest = job_dir / "job.toml"
    manifest.write_text(
        manifest.read_text(encoding="utf-8").replace("schema = 1", "schema = true"),
        encoding="utf-8",
    )

    with pytest.raises(JobConfigurationError, match="schema"):
        load_manifest(job_dir)


def test_empty_argv_is_rejected(job_dir):
    manifest = job_dir / "job.toml"
    manifest.write_text(
        manifest.read_text(encoding="utf-8").replace(
            'argv = ["bash", "run.sh"]', "argv = []"
        ),
        encoding="utf-8",
    )

    with pytest.raises(JobConfigurationError, match="argv"):
        load_manifest(job_dir)


def test_cwd_parent_traversal_is_rejected(job_dir):
    manifest = job_dir / "job.toml"
    manifest.write_text(
        manifest.read_text(encoding="utf-8").replace('cwd = "."', 'cwd = ".."'),
        encoding="utf-8",
    )

    with pytest.raises(JobConfigurationError, match="cwd"):
        load_manifest(job_dir)


def test_required_file_parent_traversal_is_rejected(job_dir):
    outside = job_dir.parent / f"{job_dir.name}-outside.txt"
    outside.write_text("outside\n", encoding="utf-8")
    manifest = job_dir / "job.toml"
    manifest.write_text(
        manifest.read_text(encoding="utf-8").replace(
            'required_files = ["run.sh"]',
            f'required_files = ["../{outside.name}"]',
        ),
        encoding="utf-8",
    )

    with pytest.raises(JobConfigurationError, match="required_files"):
        load_manifest(job_dir)


def test_required_file_symlink_escape_is_rejected(job_dir):
    outside = job_dir.parent / f"{job_dir.name}-outside.txt"
    outside.write_text("outside\n", encoding="utf-8")
    (job_dir / "escape.txt").symlink_to(outside)
    manifest = job_dir / "job.toml"
    manifest.write_text(
        manifest.read_text(encoding="utf-8").replace(
            'required_files = ["run.sh"]', 'required_files = ["escape.txt"]'
        ),
        encoding="utf-8",
    )

    with pytest.raises(JobConfigurationError, match="required_files"):
        load_manifest(job_dir)


def test_missing_required_file_names_the_file(job_dir):
    (job_dir / "missing.txt").mkdir()
    manifest = job_dir / "job.toml"
    manifest.write_text(
        manifest.read_text(encoding="utf-8").replace(
            'required_files = ["run.sh"]', 'required_files = ["missing.txt"]'
        ),
        encoding="utf-8",
    )

    with pytest.raises(JobConfigurationError, match="required file") as error:
        load_manifest(job_dir)

    assert "missing.txt" in str(error.value)
