# Releasing the `yod` Python package (PyPI)

This SDK uses modern packaging (`pyproject.toml` + `hatchling`). You publish by building a wheel/sdist and uploading them with `twine`.

## One-time setup

- Create accounts:
  - TestPyPI: `https://test.pypi.org/account/register/`
  - PyPI: `https://pypi.org/account/register/`
- Create API tokens (recommended):
  - PyPI token: `https://pypi.org/manage/account/token/`
  - TestPyPI token: `https://test.pypi.org/manage/account/token/`
- Keep the tokens secret (use environment variables or CI secrets).

## Release checklist

1) Pick the version

- Bump `src/yod/_version.py` (this project’s version is read from that file).

2) Clean old artifacts (important!)

This repo may contain older `dist/` artifacts (e.g. `amemo-*`). Always delete `dist/` before building so you only upload the current package.

PowerShell:

```powershell
cd sdk
if (Test-Path dist) { Remove-Item -Recurse -Force dist }
```

3) Build + validate

```powershell
cd sdk
python -m pip install --upgrade build twine
python -m build
python -m twine check dist/*
```

4) Upload to TestPyPI (recommended)

```powershell
cd sdk
$env:TWINE_USERNAME="__token__"
$env:TWINE_PASSWORD="pypi-XXXXXXXXXXXXXXXXXXXXXXXXXXXX"
python -m twine upload --repository-url https://test.pypi.org/legacy/ dist/*
```

Test install from TestPyPI:

```powershell
python -m pip install --upgrade pip
python -m pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple yod
python -c "import yod; print(yod.__version__)"
```

5) Upload to PyPI

```powershell
cd sdk
$env:TWINE_USERNAME="__token__"
$env:TWINE_PASSWORD="pypi-XXXXXXXXXXXXXXXXXXXXXXXXXXXX"
python -m twine upload dist/*
```

## Optional: use the helper script

See `scripts/release.ps1` for a repeatable build + upload flow.

Example:

```powershell
.\scripts\release.ps1 -Repository testpypi -Upload
.\scripts\release.ps1 -Repository pypi -Upload
```

If `TWINE_PASSWORD` is not set, the script will securely prompt you for a token (input hidden).


