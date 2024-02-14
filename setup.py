from setuptools import setup, find_packages


setup(
    name="srcyaml",
    packages=find_packages(),
    # install_requires=["src"],
    entry_points={"console_scripts": ["realpython=reader.__main__:main"]}
)
