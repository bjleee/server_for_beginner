import sys
from pathlib import Path
from sys import argv

from server import check_hostname


def validate_command_line_args(args):
    # check number of arguments passed in
    if len(args) != 2:
        print('invalid arguments')
        sys.exit()
    # parse that 2 args
    master_file_path = args[0]
    dir_path = args[1]

    return master_file_path, dir_path


def load_config_file(dir_path, fobj, file_type="master"):
    try:  # extract file and read it
        fobj = dir_path / fobj
        with open(fobj, 'r') as filename:
            lines = filename.readlines()
    except IOError:
        print(f'invalid {file_type}')
        sys.exit()
    # check if the file has only one line containing the port of the server
    if len(lines) == 1:
        print(f'invalid {file_type}')
        sys.exit()
    # extract port of server and check invalid port number
    try:
        port_of_server = int(lines[0].strip())
        if not (1024 <= port_of_server <= 65535):
            print(f'invalid {file_type}')
            sys.exit()
    except ValueError:
        print(f'invalid {file_type}')
        sys.exit()

    # create a dictionary to attach each port number of a domain
    record = {}
    # loop through the list containing all information we extracted before except the first line
    for each_line in lines[1:]:
        # split the line and check if it's valid
        parts = each_line.strip().split(',')
        if len(parts) != 2:
            print(f'invalid {file_type}')
            sys.exit()
        domain, port_identifier = parts
        # check invalid domain and partial domain
        if not check_hostname(domain) or len(domain.split('.')) < 3:
            print(f'invalid {file_type}')
            sys.exit()
        try:  # check invalid port identifier
            if not (1024 <= int(port_identifier) <= 65535):
                print(f'invalid {file_type}')
                sys.exit()
        except ValueError:
            print(f'invalid {file_type}')
            sys.exit()

        # check for contradicting records
        if domain in record:  # access to dictionary
            if record.get(domain) != int(port_identifier):  # check if the domain get 2 port then print Invalid
                print(f'invalid {file_type}')
                sys.exit()

        # set the pair < key, value > in dictionary with each domain and port identifier
        record[domain] = int(port_identifier)

        # return the dictionary as the library contains address of all books and the port of the server
    return record, port_of_server


# validate content and existence first before compare
def validate_master_file(file: str):
    master_file_path = Path(file)
    # check existence of master_path
    if not master_file_path.exists():
        print("invalid master")
        sys.exit()

    # check the content of the file by try read mode and catch the Error IOERROR if cannot open
    return load_config_file("", master_file_path)


def validate_and_compare_single_file_path(master_record: dict, file: str):
    dir_path = Path(file)
    # check existence of dir_path
    if not dir_path.is_dir():
        print('singles io error')
        sys.exit()

    # try separate the path that already contains single file into each file first before read
    list_of_file = []
    for file in dir_path.iterdir():
        list_of_file.append(file.name)
    # TODO: initiate the dict
    # Dictionary to map top-level domains
    mapped_tld = {}
    # Load the root configuration file and extract the TLD-port mapping
    with open(dir_path.joinpath('root.conf'), 'r') as f:
        lines = f.readlines()
    for each_line in lines[1:]:
        parts = each_line.strip().split(',')
        domain, port = parts
        mapped_tld[domain] = port
    # Validate each individual configuration file against the master record
    for file in list_of_file:
        # Skip the root configuration file
        if file.startswith('root'):
            continue
        # Validate TLD configuration files
        if file.startswith('tld'):
            x = dir_path.joinpath(file)
            with open(x, 'r') as f_obj:
                lines = f_obj.readlines()
            # Check if the TLD-port mapping matches the root configuration
            if lines[0].strip() == mapped_tld[file.split('.')[0].strip("tld-")]:
                continue
            else:
                print('neq')
                sys.exit()
        # Validate auth configuration files
        if file.startswith('auth-'):
            x = dir_path.joinpath(file)
            with open(x, 'r') as f_obj:
                lines = f_obj.readlines()
            for each_line in lines[1:]:
                parts = each_line.strip().split(',')
                # Check the validity of the domain
                if not check_hostname((parts[0])):
                    print('invalid single')
                    sys.exit()
                # Ensure the port is present in the master record
                if not parts[1] not in list(master_record.values()):
                    print('neq')
                    sys.exit()
                else:
                    continue
            continue
        # Validate other configuration files
        if len(file.split('.')) <= 2:
            x = dir_path.joinpath(file)
            with open(x, 'r') as f_obj:
                lines = f_obj.readlines()
            if len(file.split('.')[0].split('-')) < 2:
                # check the port of tld server
                if lines[0].strip() == mapped_tld[file.split('.')[0]]:
                    continue
                else:
                    print('neq')
                    sys.exit()
            else:
                if lines[0].strip() == mapped_tld[file.split('.')[0].split('-')[0]] and \
                        lines[0].strip() == mapped_tld[file.split('.')[0].split('-')[1]]:
                    continue
                else:
                    print('neq')
                    sys.exit()
        # Load and validate the configuration file
        if not load_config_file(dir_path, file, "single"):
            print("invalid single")
            sys.exit()

    return 'eq'


def main(args: list[str]) -> None:
    # TODO: handling command line arguments
    master_file_path, single_files_dir_path = validate_command_line_args(args)
    # done

    # TODO: validate master file path
    record, port_of_server = validate_master_file(master_file_path)
    # TODO: validate 'single' file is invalid or not and compare them

    print(validate_and_compare_single_file_path(record, single_files_dir_path))


if __name__ == "__main__":
    main(argv[1:])