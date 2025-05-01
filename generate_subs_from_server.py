import os
import tempfile
import shutil
import subprocess
import sys
import paramiko
import stat
from tqdm import tqdm

# -------------- CONFIGURATION --------------
SERVER_IP = "69.69.69.69"        # <--- EDIT
SERVER_PORT = 420                # <--- EDIT
USERNAME = "usser"          # <--- EDIT
PRIVATE_KEY_PATH = os.path.expanduser("~/.ssh/id_rsa")
# ------------------------------------------

AUDIO_EXTENSIONS = {
    'aac': 'm4a',
    'mp3': 'mp3',
    'opus': 'opus',
    'ogg': 'ogg',
    'flac': 'flac',
    'wav': 'wav',
    'm4a': 'm4a',
    'ac3': 'ac3',
    'eac3': 'eac3',
}

def is_audio(filename):
    ext = filename.lower().split('.')[-1]
    return ext in AUDIO_EXTENSIONS.values()

import stat  # ADD THIS AT THE TOP

def list_audio_files_sftp(sftp, directory):
    audio_files = []
    for entry in sftp.listdir_attr(directory):
        fullpath = os.path.join(directory, entry.filename)
        if stat.S_ISDIR(entry.st_mode):  # <-- FIXED LINE
            audio_files += list_audio_files_sftp(sftp, fullpath)
        else:
            if is_audio(entry.filename):
                audio_files.append(fullpath)
    return audio_files

def download_files(sftp, filepaths, tmpdir):
    local_paths = []
    for remote_path in tqdm(filepaths, desc='Downloading audio files'):
        filename = os.path.basename(remote_path)
        local_path = os.path.join(tmpdir, filename)
        sftp.get(remote_path, local_path)
        local_paths.append((remote_path, local_path))
    return local_paths

def convert_to_wav(local_path):
    if local_path.lower().endswith('.wav'):
        return local_path
    wav_path = os.path.splitext(local_path)[0] + '.wav'
    cmd = ['ffmpeg', '-y', '-i', local_path, wav_path]
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return wav_path

def run_whisperx(wav_path, tmpdir):
    cmd = ['whisperx', wav_path, '--compute_type', 'int8', '--language', 'en', '--output_format', 'srt', '--segment_resolution', 'chunk', '--output_dir', tmpdir, '--model', 'distil-small.en']
    subprocess.run(cmd, check=True)

def upload_subtitle(sftp, remote_audio_path, tmpdir):
    base = os.path.splitext(os.path.basename(remote_audio_path))[0]
    srt_local = os.path.join(tmpdir, base + '.srt')
    remote_dir = os.path.dirname(remote_audio_path)
    srt_remote = os.path.join(remote_dir, base + '.srt')
    if os.path.exists(srt_local):
        sftp.put(srt_local, srt_remote)
        print(f"Uploaded: {srt_remote}")
    else:
        print(f"srt file not found for {base}!")

def process_all(remote_path):
    print("Connecting to server...")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    key = paramiko.RSAKey.from_private_key_file(PRIVATE_KEY_PATH)
    ssh.connect(SERVER_IP, port=SERVER_PORT, username=USERNAME, pkey=key)
    sftp = ssh.open_sftp()
    
    print("Searching for audio files...")
    audio_files = list_audio_files_sftp(sftp, remote_path)
    print(f"Found {len(audio_files)} audio files.")

    tmpdir = tempfile.mkdtemp()

    try:
        local_audio_files = download_files(sftp, audio_files, tmpdir)
        
        for remote_path, local_path in tqdm(local_audio_files, desc='Processing audio files'):
            wav_path = convert_to_wav(local_path)
            print(f"Transcribing {wav_path}...")
            run_whisperx(wav_path,tmpdir)
            upload_subtitle(sftp, remote_path, tmpdir)
    finally:
        print("Cleaning up temporary files...")
        shutil.rmtree(tmpdir)
        sftp.close()
        ssh.close()

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Usage: python script.py /path/on/server")
        sys.exit(1)
    remote_path = sys.argv[1]
    process_all(remote_path)

