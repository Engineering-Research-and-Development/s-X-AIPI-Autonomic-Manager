from setuptools import setup, find_packages

setup(name='dagster_service',
      version='0.0.1',
      install_requires=["dagster", "numpy", "dagster-webserver", "kafka-python"],
      package_dir={'dagster_service': 'dagster_service'},
      packages=find_packages(),
      )
