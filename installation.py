import subprocess

def install_packages_from_readme(file_path):
    try:
        with open(file_path, 'r') as file:
            for line in file:
                command = line.strip()
                if command:  # Check if the line is not empty
                    print(f"Running: {command}")
                    subprocess.run(command, shell=True, check=True)
                    print(f"Successfully installed: {command}")
    except subprocess.CalledProcessError as e:
        print(f"An error occurred while running the command: {e.cmd}")
        print(f"Error details: {e}")
    except FileNotFoundError:
        print(f"The file '{file_path}' was not found.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

# Call the function with the path to your readme.txt file
install_packages_from_readme('readme.txt')
