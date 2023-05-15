
# directory-exporter
A Prometheus exporter to count the number of files in multiple directories and expose them as Prometheus metrics. This exporter supports counting empty files, file with specific extension etc. Supports Windows, linux and MacOS

# Usage

### Testing
```
git clone https://github.com/bharathalleni/directory-exporter.git
cd directory-exporter
pip install -r requirements.txt
python3 main.py
```
The script will start monitoring the specified directories in the configuration file and expose the Prometheus metric at `http://localhost:9028/metrics`.

### Build for Windows, Linux and MacOS
```
pip3 install pyinstaller
pyinstaller --onefile ./main.py
```
The installer will be created in ``dist`` directory. You can install it as a Windows service using [NSSM](https://nssm.cc/) or run it as a service using systemd in Linux.

**Note:** PyInstaller is capable of generating executables for Windows, Linux, and macOS platforms individually, but it does not support cross-compilation. Consequently, you cannot create an executable targeting one operating system from another operating system. To distribute executables across multiple operating systems, you will require a dedicated build machine for each supported platform.

### Prometheus Integration

To scrape the metrics exposed by the Directory exporter, configure Prometheus to scrape the `/metrics` endpoint of the script. Add the following job configuration to your Prometheus `prometheus.yml` file:

```
scrape_configs:
 - job_name: directory-exporter
   static_configs:
     - targets: ['localhost:9028']
```
# Sample metrics

```
# HELP file_count Number of files in directory
# TYPE file_count gauge
file_count{path="/Users/Username/data/exporters/file-count-exporter/",server="127.0.0.1"} 4.0
file_count{path="/Users/Username/data/POS",server="127.0.0.1"} 14.0
# HELP file_count_by_extension Count of files with extension
# TYPE file_count_by_extension gauge
file_count_by_extension{extension=".py",path="/Users/Username/data/exporters/file-count-exporter/",server="127.0.0.1"} 1.0
file_count_by_extension{extension=".txt",path="/Users/Username/data",server="127.0.0.1"} 1.0
# HELP empty_file_count Number of empty files
# TYPE empty_file_count gauge
empty_file_count{path="/Users/Username/data/file-count-exporter/",server="127.0.0.1"} 1.0
empty_file_count{path="/Users/Username/data/POS",server="127.0.0.1"} 0.0
```
