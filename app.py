from flask import Flask, request, jsonify
import os
import uuid
import docker

app = Flask(__name__)

UPLOAD_FOLDER = 'containers'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

UPLOAD_HOST_FOLDER = '/home/burak/project/repo-rest/containers'

DOCKERFILES_PATH = '/app/containers/'
client = docker.from_env()

def get_file_suffix(filename):
    if filename.endswith('requirements.txt'):
        return 'python'
    elif filename.endswith('pom.xml'):
        return 'maven'
    elif filename.endswith('package.json'):
        return 'npm'
    else:
        return None
    
def replace_multiple_texts_in_file(input_file_path, output_file_path, replacements):
    # Dosyayı okuma
    with open(input_file_path, 'r', encoding='utf-8') as file:
        file_contents = file.read()
    
    # Belirtilen metinleri yenisiyle değiştirme
    for old_text, new_text in replacements.items():
        file_contents = file_contents.replace(old_text, new_text)
    
    # Yeni dosyayı oluşturma ve yazma
    with open(output_file_path, 'w', encoding='utf-8') as new_file:
        new_file.write(file_contents)

    # Kullanım


def run_docker_container(file_path, suffix,filename):
    container_command = {
        'python': f"pip install -r requirements.txt",
        'maven': f"mvn install",
        'npm': f"npm install"
    }

    input_file = f"{DOCKERFILES_PATH}Dockerfile-{suffix}"  # Giriş dosyasının yolu
    output_file = f"{DOCKERFILES_PATH}Dockerfile-{suffix}.{filename}"    # Çıkış dosyasının yolu
    lang = request.form.get('lang')
    ver = request.form.get('ver')
    replacements = {
        '<version>': ver,
        '<package_file>': f"./{lang}/{os.path.basename(file_path)}"
    }

    replace_multiple_texts_in_file(input_file, output_file, replacements)


    try:
        client.images.build(path=f"{DOCKERFILES_PATH}",dockerfile=f"{output_file}", tag=f"{suffix}-{filename}")
    except docker.errors.BuildError as e:
        return (f"Error building image: {e}")

    container_image = {
        'python': f"{suffix}-{filename}",
        'maven': f"{suffix}-{filename}",
        'npm': f"{suffix}-{filename}"
    }

    command = container_command.get(suffix)
    image = container_image.get(suffix)

    if not command or not image:
        return None

    container = client.containers.run(
        image,
        command,
        volumes={os.path.abspath(DOCKERFILES_PATH): {'bind': '/data', 'mode': 'rw'}},
        detach=True,
        auto_remove=False
    )
    return container

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    suffix = get_file_suffix(file.filename)
    if suffix:
        folder_path = os.path.join(UPLOAD_FOLDER, suffix)
        os.makedirs(folder_path, exist_ok=True)
        filename = f"{uuid.uuid4()}_{file.filename}"
        file_path = os.path.join(folder_path, filename)
        file.save(file_path)

        container = run_docker_container(file_path, suffix,filename)
        if container:
            container.wait()
            logs = container.logs().decode('utf-8')
            #container.remove()
            return jsonify({'message': 'File uploaded and container completed', 'logs': logs}), 200
        else:
            return jsonify({'error': 'Failed to start container'}), 500
    else:
        return jsonify({'error': 'Invalid file format, only requirements.txt, pom.xml, and package.json files are allowed'}), 400

if __name__ == '__main__':
    host = '0.0.0.0'
    port = 5000
    debug = True
    use_reloader = True
    threaded = True

    app.run(
        host=host,
        port=port,
        debug=debug,
        use_reloader=use_reloader,
        threaded=threaded
    )
