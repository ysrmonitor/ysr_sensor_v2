from distutils.core import setup

setup(name='ysr_monitor',
      version='0.0.5',
      packages=['src'],
      license='MIT',
      description='ysr_monitor',
      author='YSR',
      author_email='ysr.monitor@gmail.com',
      url='https://github.com/ysrmonitor/ysr_monitor.git',
      download_url='https://github.com/ysrmonitor/ysr_monitor/archive/refs/tags/v0.0.5.tar.gz',
      keywords=['seed', 'monitoring', 'sensing', 'rpi'],
      install_requires=[
      ],
      classifiers=[
            'Development Status :: 3 - Alpha',      # Chose either "3 - Alpha", "4 - Beta" or "5 - Production/Stable" as the current state of your package
            'Intended Audience :: Developers',      # Define that your audience are developers
            'Topic :: Software Development :: Build Tools',
            'License :: OSI Approved :: MIT License',   # Again, pick a license
            'Programming Language :: Python :: 3',      #Specify which pyhton versions that you want to support
            'Programming Language :: Python :: 3.4',
            'Programming Language :: Python :: 3.5',
            'Programming Language :: Python :: 3.6',
      ],
      )
