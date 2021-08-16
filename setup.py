from setuptools import setup

setup(
    name='youtube-downloader-cli',
    version='0.1.0',
    description='This tool is used to parse and download the youtube videos.',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'Operating System :: POSIX',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Topic :: Text Processing :: Linguistic',
    ],
    keywords='youtube download parser video',
    url='https://github.com/xingheng/youtube-downloader-cli',
    author='Will Han',
    author_email='xingheng.hax@qq.com',
    license='unlicense',
    python_requires='>=3',
    packages=['youtube_downloader_cli'],
    install_requires=[
        'click>=7.0',
        'configparser>=4.0',
        'peewee>=3.11',
        'requests>=2.22',
        'youtube-dl>=2020.1.15',
        'translate==3.6.1',
    ],
    entry_points={
        'console_scripts': ['youtube-downloader-cli=main'],
    },
    include_package_data=True,
    zip_safe=False
)
