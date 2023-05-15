import os
import sys
import time
import socket
import logging
import yaml
from prometheus_client import start_http_server, Gauge

logging.basicConfig(filename="file_exporter.log", filemode='a', format='%(asctime)s %(levelname)-8s %(message)s',
                    level=logging.INFO, datefmt='%Y-%m-%d %H:%M:%S')

def count_files_in_dir(dir_path, ext_list):
    file_count = 0
    ext_count_dict = {}

    for file_name in os.scandir(dir_path):
        if os.path.isfile(os.path.join(dir_path, file_name)):
            file_count += 1
            ext = os.path.splitext(file_name)[1]
            if ext in ext_list:
                if ext not in ext_count_dict:
                    ext_count_dict[ext] = 0
                ext_count_dict[ext] += 1

    empty_files = [f for f in os.scandir(dir_path) if os.stat(os.path.join(dir_path, f)).st_size == 0]
    empty_file_count = len(empty_files)

    return file_count, ext_count_dict, empty_file_count


if __name__ == '__main__':
    try:
        with open('config.yaml', 'r') as f:
            config = yaml.safe_load(f)

        port = config['listen_port']

        # Start the Prometheus server
        start_http_server(port)
        logging.info(f"Prometheus Exporter started at http://0.0.0.0:{port}")

        # Create Prometheus metrics
        num_files = Gauge('file_count', 'Number of files in directory', ['path', 'name', 'server'])
        ext_count = Gauge('file_count_by_extension', 'Count of files with extension', ['path', 'name', 'extension', 'server'])
        empty_files = Gauge('empty_file_count', 'Number of empty files', ['path', 'name', 'server'])
        server_ip = socket.gethostbyname(socket.gethostname())
        
        while (True):
            # Collect metrics from each directory and export them to Prometheus
            for monitor in config['monitors']:
                # print(monitor)
                dir_path = monitor.get("directory_path")
                dir_name = monitor.get("directory_name")
                ext_list = monitor.get("extensions_to_watch")
                try:
                    file_count, ext_count_dict, empty_file_count = count_files_in_dir(dir_path, ext_list)
                    num_files.labels(path=dir_path, name=dir_name, server=server_ip).set(file_count)
                    empty_files.labels(path=dir_path, name=dir_name, server=server_ip).set(empty_file_count)
                    for ext, count in ext_count_dict.items():
                        ext_count.labels(path=dir_path, name=dir_name, extension=ext, server=server_ip).set(count)
                except Exception as e:
                    logging.error(f"Error occurred while processing directory {dir_path}: {e}")
            time.sleep(config.get('update_interval_seconds'))
    except Exception as e:
        logging.error(f"Error occurred while reading config file: {e}")
        sys.exit(1)
