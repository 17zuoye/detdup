from setuptools import setup

setup(
    name='detdup',
    version='0.0.2',
    url='http://github.com/17zuoye/detdup/',
    license='MIT',
    author='David Chen',
    author_email=''.join(reversed("moc.liamg@emojvm")),
    description='Detect duplicated items.',
    long_description='Detect duplicated items.',
    packages=['detdup', 'detdup/data_model', 'detdup/features', 'detdup/services'],
    include_package_data=True,
    zip_safe=False,
    platforms='any',
    install_requires=[
        'etl_utils >= 0.1.7',
        'peewee',
        'pymongo',
        'sqlitebck',
        'mongomock',
        'termcolor',
        'model_cache >=0.0.9',
    ],
    classifiers=[
        'Intended Audience :: Developers',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Software Development :: Libraries :: Python Modules'
    ],
)
