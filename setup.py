import io
from setuptools import setup, find_namespace_packages

with open("requirements.txt", "r") as f:
    requirements = f.read().splitlines()

# Use the README.md content for the long description:
with io.open("README.md", encoding="utf-8") as fo:
    long_description = fo.read()

pkg = "url_cache"
setup(
    name=pkg,
    version="0.0.1",
    url="https://github.com/seanbreckenridge/url_cache",
    author="Sean Breckenridge",
    author_email="seanbrecke@gmail.com",
    description=("""A filesystem cache which saves URL metadata and summarizes content"""),
    long_description=long_description,
    long_description_content_type="text/markdown",
    license="http://www.apache.org/licenses/LICENSE-2.0",
    packages=find_namespace_packages("src"),
    zip_safe=False,
    package_dir={"": "src"},
    package_data={pkg: ["py.typed"]},
    install_requires=requirements,
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
    ],
)
