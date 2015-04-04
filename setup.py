from setuptools import setup, find_packages
import os

version = '0.9.1'

setup(name='wheelcms_axle',
      version=version,
      description="WheelCMS core package",
      long_description=open("README.md").read(),
      classifiers=[
        "Programming Language :: Python",
        ],
      keywords='',
      author='Ivo van der Wijk',
      author_email='wheelcms@in.m3r.nl',
      url='http://github.com/wheelcms/wheelcms_axle',
      license='BSD',
      packages=find_packages(exclude=['ez_setup']),
      namespace_packages=[],
      include_package_data=True,
      zip_safe=False,
      install_requires=[
          'setuptools',
          'pytest',
          'mock',
          'wrapt',
          'reg==0.8',
          'django_drole',
          'django-haystack==2.1.0',
          'django-userena==1.4.0'
      ],
      entry_points={
      },

      )

