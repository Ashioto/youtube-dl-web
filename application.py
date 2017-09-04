from flask import Flask
from flask import request, render_template, send_file
import os
import tools
from tools import Manager

app = Flask(__name__)

app.config['DEBUG'] = False
app.config['DOWNLOAD_DIRECTORY'] = os.path.join(os.getcwd(), 'tars')
app.config['CODE_LIST'] = ['TESTER']
app.config['DIRECTORY_SIZE_MAX_LIMIT'] = 1500  # In MB
app.config['HOST'] = '0.0.0.0'
app.config['PORT'] = 9003

app.secret_key = os.urandom(512)

manager = Manager(root=app.config.get('DOWNLOAD_DIRECTORY'), max_size=app.config.get('DIRECTORY_SIZE_MAX_LIMIT'))
manager.setDaemon(True)
manager.start()


@app.route('/')
def index_page():
    return tools.md5(os.urandom(512))


@app.route('/youtube')
def youtube_videos_download_and_query():
    return render_template("youtube_videos_download_and_query.html")


@app.route('/youtube/submit', methods=['POST'])
def youtube_videos_submit_tasks():
    if request.form['code'] not in app.config.get('CODE_LIST'):
        return "Please ask someone for a valid key."
    urls = request.form['urls'].strip().split()
    manager.submit_task(urls)
    return str("Success! You can query and download your file in about 30 seconds. And please do not submit it again.")


@app.route('/youtube/query', methods=['POST'])
def youtube_videos_query():
    if request.form['code'] not in app.config.get('CODE_LIST'):
        return "Please ask someone for a valid key."
    tar_files = manager.get_tar_file_list()
    tar_files_info = [manager.describe_tar_file(fn) for fn in tar_files]
    return render_template("download_addresses.html", tar_files_info=tar_files_info)


@app.route('/youtube/download/<filename>', methods=['GET'])
def youtube_videos_download(filename):
    if not os.path.exists(os.path.join(app.config.get('DOWNLOAD_DIRECTORY'), filename)):
        return "No such file."
    return send_file('tars/' + filename)


@app.route('/youtube/delete/<filename>', methods=['GET'])
def youtube_videos_delete(filename):
    absolute_path = os.path.join(app.config.get('DOWNLOAD_DIRECTORY'), filename)
    if not os.path.exists(absolute_path):
        return "No such file."
    os.remove(absolute_path)
    return "Sucess! %s has been deleted." % filename


if __name__ == '__main__':
    app.run(host=app.config.get('HOST'), port=app.config.get('PORT'), debug=app.config.get('DEBUG'), threaded=True)
