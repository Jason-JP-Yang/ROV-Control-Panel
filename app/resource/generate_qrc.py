from pathlib import Path
import subprocess, json

current_directory = Path(__file__).parent

def generate_qrc(_config_path: str, compile: bool):
    config_path = current_directory / Path(_config_path)
    config_directory = config_path.parent

    qrc_lines = ['<RCC>']

    config_file = open(config_path, 'r')
    config = json.load(config_file)

    qrc_path = config_directory / Path(config['qrc_path'])
    qrc_directory = qrc_path.parent
    py_path = config_directory / Path(config['resource_py_path'])

    for prefix in config['prefixes']:
        qrc_lines.append('    <qresource prefix="{prefix}">'.format(prefix=prefix['prefix']))
        
        for dir in prefix['dirs']:
            dir_path = config_directory / Path(dir)
            if not dir_path.exists():
                raise FileNotFoundError(f"Directory {dir} does not exist.")
            
            for file in dir_path.rglob('*'):
                if file.is_file():
                    qrc_lines.append('        <file>{file}</file>'.format(file=file.relative_to(qrc_directory)))
            qrc_lines.append('')
        qrc_lines.append('    </qresource>')
    
    qrc_lines.append('</RCC>')
    config_file.close()

    print("\n".join(qrc_lines))
    qrc_directory.mkdir(parents=True, exist_ok=True)
    with open(qrc_path, 'w', encoding='utf-8') as f:
        f.write("\n".join(qrc_lines))

    if compile: compile_resource(qrc_path, py_path)

def compile_resource(_qrc_path: str, _py_path: str):
    qrc_path = current_directory / Path(_qrc_path)

    py_path = current_directory / Path(_py_path)

    cmd = ['pyrcc5', str(qrc_path), '-o', str(py_path)]

    pipe = subprocess.run(cmd, capture_output=True, text=True)

    if pipe.returncode == 0:
        print('Resource file generated successfully')
    else:
        print('Resource file generation failed')
        raise RuntimeError(f"Compilation failed:\n{pipe.stderr}")

if __name__ == '__main__':
    generate_qrc('./resource.json', True)