from pathlib import Path
from setuptools import setup, find_namespace_packages

pkg = "url_cache"
setup(
    name=pkg,
    version="0.0.5",
    url="https://github.com/seanbreckenridge/url_cache",
    author="Sean Breckenridge",
    author_email="seanbrecke@gmail.com",
    description=(
        """A file system cache which saves URL metadata and summarizes content"""
    ),
    long_description=Path("README.md").read_text(),
    long_description_content_type="text/markdown",
    license="http://www.apache.org/licenses/LICENSE-2.0",
    packages=find_namespace_packages("src"),
    zip_safe=False,
    package_dir={"": "src"},
    package_data={pkg: ["py.typed"]},
    install_requires=Path("requirements.txt").read_text().splitlines(),
    keywords="url cache metadata youtube subtitles",
    test_suite="tests",
    entry_points={
        "console_scripts": [
            "url_cache = url_cache.__main__:main",
        ]
    },
    extras_require={
        "testing": [
            "pytest",
            "mypy",
            "flake8",
            "vcrpy",
        ]
    },
    classifiers=[
        "License :: OSI Approved :: Apache Software License",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
    ],
)
