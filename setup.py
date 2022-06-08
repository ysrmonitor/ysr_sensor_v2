from distutils.core import setup

setup(name='ysr_monitor_v2',
      version='0.1.6',
      packages=['src'],
      license='MIT',
      description='ysr_monitor',
      author='YSR',
      author_email='ysr.monitor@gmail.com',
      url='https://github.com/ysrmonitor/ysr_monitor.git',
      download_url='https://github.com/ysrmonitor/ysr_monitor/archive/refs/tags/v0.1.6.tar.gz',
      keywords=['seed', 'monitoring', 'sensing', 'rpi'],
      install_requires=[
            'datetime~=4.4',
            'pathlib~=1.0.1',
            'smbus2~=0.4.1',
            'tabulate~=0.8.9',
            'pillow~=9.1.0',
            'adafruit-circuitpython-ssd1306',
            'adafruit-blinka',
            'pytz~=2022.1',
            'httplib2~=0.20.4',
            'google-api-python-client',
            'google-auth-httplib2',
            'google-auth-oauthlib',
            'RPi.bme280',
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
