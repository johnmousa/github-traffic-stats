import setuptools

with open("README.md", "r") as readme_file:
  readme = readme_file.read()

setuptools.setup(
  name='github_traffic_stats_aws',
  version='21.0.0',
  description='A project extended from'
              ' https://github.com/seladb/github-traffic-stats to pull and store traffic stats for GitHub projects '
              'using GitHub API.',
  long_description = readme,
  long_description_content_type='text/markdown',
  author='jmousa',
  author_email='samy.john@gmail.com',
  entry_points={
    "console_scripts": ['github_traffic_stats = github_traffic_stats:main']
  },
  url='https://github.com/johnmousa/github-traffic-stats',
  download_url='https://github.com/johnmousa/github-traffic-stats/archive/master.tar.gz',
  py_modules=['github_traffic_stats_aws'],
  keywords=['github', 'github-traffic', 'github-api'],
  classifiers=[
    "Programming Language :: Python :: 3",
    "License :: OSI Approved :: MIT License",
    "Operating System :: OS Independent",
  ],
  python_requires='>=3',
  install_requires=['githubpy', 'pickledb', 'simplejson', 'aws-cdk.core==1.94.1',],
)
