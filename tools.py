from __future__ import unicode_literals
import youtube_dl
import os
import hashlib
import logging
import threading
import subprocess
from Queue import Queue
from datetime import datetime

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(filename)s[line:%(lineno)d] - %(levelname)s: %(message)s')


def md5(content):
    m = hashlib.md5()
    m.update(content)
    return m.hexdigest()


class TarFileInfo():
    def __init__(self, name=None, time=None, size=None, files=None):
        self.name = name
        self.time = time
        self.size = size
        self.files = files


class Manager(threading.Thread):
    def __init__(self, root, max_size, ydl_opts=None):
        threading.Thread.__init__(self)
        self.root = root
        self.max_size = max_size
        self.ydl_opts = {'outtmpl': str(os.path.join(self.root, 'youtube-videos/%(title)s-%(id)s.%(ext)s')),
                         'writesubtitles': True,
                         'allsubtitles': True}
        if ydl_opts is not None:
            self.ydl_opts.update(ydl_opts)

        self.queue = Queue()

    def submit_task(self, urls):
        self.queue.put(urls)

    def run(self):
        while True:
            urls = self.queue.get()
            self.keep_directory_in_proper_size()
            try:
                self.youtube_videos_download(urls)
            except Exception as e:
                logging.error(e)
            self.tar_video_files()

    def keep_directory_in_proper_size(self):
        tar_files = self.get_tar_file_list()
        sizes = [os.path.getsize(fn) / 1024.0 / 1024.0 for fn in tar_files]
        tot_size = 0
        for fn, size in zip(tar_files, sizes):
            tot_size += size
            if tot_size > self.max_size:
                os.remove(fn)
                logging.info("shrink directory size.")

    def youtube_videos_download(self, urls):
        logging.info("urls are: " + str(urls))
        os.makedirs(os.path.join(self.root, 'youtube-videos'))
        with youtube_dl.YoutubeDL(self.ydl_opts) as ydl:
            ydl.download(urls)
        # for url in urls:
        #     open(os.path.join(os.path.join(self.root, 'youtube-videos'), url), "w+").close()
        logging.info("youtube videos download task success.")

    def tar_video_files(self):
        cmd = ['tar', 'cf', str(os.path.join(self.root, md5(os.urandom(512)) + '.tar')), '--remove-files', '-C',
               self.root, 'youtube-videos']
        subprocess.check_call(cmd)
        logging.info("tar video files.")

    def get_tar_file_list(self, absolute=True):
        files = os.listdir(self.root)
        tar_files = [os.path.join(self.root, fn) for fn in files]
        tar_files.sort(key=lambda fn: os.path.getmtime(fn), reverse=True)
        if not absolute:
            tar_files = [os.path.relpath(fn, self.root) for fn in tar_files]
        return tar_files

    def describe_tar_file(self, tar_file):
        info = TarFileInfo()
        info.name = tar_file.split('/')[-1]
        info.time = datetime.fromtimestamp(os.path.getmtime(tar_file)).strftime('%Y-%m-%d %H:%M:%S')
        info.size = "%.1f" % (os.path.getsize(tar_file) / 1024.0 / 1024.0)

        cmd = ['tar', 'tf', str(tar_file)]
        # result = subprocess.check_output(cmd).split()
        result = subprocess.Popen(cmd, stdout=subprocess.PIPE).communicate()[0].strip().split(b'\n')
        info.files = [path.decode('utf-8') for path in result]
        return info
