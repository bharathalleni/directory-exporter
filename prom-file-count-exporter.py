import os
import sys
import time
import socket
import logging
import yaml
from prometheus_client import start_http_server, Gauge


def count_files_in_dir(monitor):
    ext_count_dict = {ext: 0 for ext in monitor.get("extensions_to_watch")}
    ext_disk_space_dict = {ext: 0 for ext in monitor.get("extensions_to_watch")}
    total_file_count = 0
    empty_file_count = 0
    
    for path, subdirs, files in os.walk(monitor.get("directory_path")):
        total_file_count = total_file_count + len(files)
        for file in files:
            if os.stat(os.path.join(path, file)).st_size == 0:
                empty_file_count = empty_file_count + 1

            filename_parts = os.path.splitext(file)
            filename_ext_lower = filename_parts[1].lower()
            if len(filename_parts) >= 2 and filename_ext_lower in monitor.get("extensions_to_watch"):
                ext_count_dict[filename_ext_lower] = ext_count_dict[filename_ext_lower] + 1
                ext_disk_space_dict[filename_ext_lower] = (ext_disk_space_dict[filename_ext_lower] 
                                                           + os.stat(os.path.join(path, file)).st_size)
        
        if not monitor['recurse']:
            break

    return total_file_count, ext_count_dict, ext_disk_space_dict, empty_file_count

def load_config(config_filename='config.yaml'):
    with open('config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    return config

def get_log_handlers(config):
    handlers = []
    if config['log_to_file']:
        handlers.append(logging.FileHandler(config['log_filename']))
    if config['log_to_stdout']:
        handlers.append(logging.StreamHandler(sys.stdout))
    return handlers

def main(argv):
    config = load_config()

    logging.basicConfig(format='%(asctime)s %(levelname)-8s %(message)s',
                        level=logging.INFO, 
                        datefmt='%Y-%m-%dT%H:%M:%S',
                        handlers=get_log_handlers(config))

    port = config['listen_port']

    # Start the Prometheus Exporter server
    start_http_server(port)
    server_ip = socket.gethostbyname(socket.gethostname())
    logging.info(f"Prometheus File Count Exporter started at http://{server_ip}:{port}")

    # Create Prometheus metrics
    file_count_gauge = Gauge('file_count', 'Number of files in directory', ['path', 'name', 'server'])
    file_count_by_ext_gauge = Gauge('file_count_by_extension', 
                                    'Number of files with extension', 
                                    ['path', 'name', 'extension', 'server'])
    file_disk_space_by_extension = Gauge('file_disk_space_by_extension', 
                                         'Disk space used by files with extension', 
                                         ['path', 'name', 'extension', 'server'])
    empty_file_count_gauge = Gauge('empty_file_count', 'Number of empty files', ['path', 'name', 'server'])
    
    while (True):
        for monitor in config['monitors']:
            logging.info("Collecting file counts for: {}".format(monitor))

            try:
                file_count, ext_count_dict, ext_size_dict, empty_file_count = count_files_in_dir(monitor)

                file_count_gauge.labels(path=monitor.get("directory_path"), 
                                        name=monitor.get("directory_name"), 
                                        server=server_ip).set(file_count)
                
                empty_file_count_gauge.labels(path=monitor.get("directory_path"), 
                                              name=monitor.get("directory_name"), 
                                              server=server_ip).set(empty_file_count)
                
                for ext, count in ext_count_dict.items():
                    file_count_by_ext_gauge.labels(path=monitor.get("directory_path"), 
                                                   name=monitor.get("directory_name"), 
                                                   extension=ext, 
                                                   server=server_ip).set(count)

                for ext, count in ext_size_dict.items():
                    file_disk_space_by_extension.labels(path=monitor.get("directory_path"), 
                                                        name=monitor.get("directory_name"), 
                                                        extension=ext, 
                                                        server=server_ip).set(count)                    
            except Exception as e:
                logging.error(f"Error occurred while processing directory {monitor.get('directory_path')}: {e}")
        
        time.sleep(config.get('update_interval_seconds'))


if __name__ == '__main__':
    main(sys.argv)
    
