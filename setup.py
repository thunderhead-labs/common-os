from setuptools import setup, find_packages

setup(
    name="common",
    version="0.1",
    description="Common package for thunderhead repos",
    url="https://github.com/thunderhead-labs/common-os",
    author="claps-mvp",
    packages=find_packages(),
    install_requires=[
        "pexpect",
        "psycopg2-binary",
        "tenacity",
        "requests",
        "SQLAlchemy",
        "hexbytes",
        "cryptography",
        "pycoingecko",
        "pika",
        "pandas",
        "logaugment",
    ],
    test_suite="testing",
    tests_require=["nose"],
    zip_safe=False,
)
