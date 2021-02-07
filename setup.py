from setuptools import find_packages
from setuptools import setup


setup(
    name='bdmap',
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        'Flask',
        'dams @ git+https://github.com/hottolink/pydams.git@master',
    ],
)
