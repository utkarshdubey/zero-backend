import openai
from flask import Flask, request, jsonify
import subprocess, os

app = Flask(__name__)

openai.api_key = os.environ.get('OPENAI_API_KEY')

def check_format(file_path):
    try:
        file_extension = os.path.splitext(file_path)[1]
        return file_extension in ['.flac', '.m4a', '.mp3', '.mp4', '.mpeg', '.mpga', '.oga', '.ogg', '.wav', '.webm']
    except Exception as e:
        print(f"An error occurred: {e}")
        return False

def convert_to_mp3(input_file_path, output_file_path):
    try:
        result = subprocess.run([
            "ffmpeg", "-i", input_file_path,
            "-codec:a", "libmp3lame", "-qscale:a", "2",
            output_file_path
        ], check=True)  # The check=True will raise an exception if the command fails
        print(f"Conversion successful: {output_file_path}")
    except subprocess.CalledProcessError as e:
        print(f"Conversion failed: {e}")
    except Exception as e:
        print(f"An error occurred: {e}")

@app.route("/", methods=["POST"])
def transcribe_audio():
    audio_file = request.files.get('audio')

    if audio_file is None:
        return jsonify({'error': 'No audio file provided'}), 400

    # Save the file to disk temporarily
    temp_file_path = "temp_audio_file"
    audio_file.save(temp_file_path)

    # Check the format and convert to MP3 if necessary
    if not check_format(temp_file_path):
        temp_mp3_file_path = "temp_audio_file.mp3"
        convert_to_mp3(temp_file_path, temp_mp3_file_path)
        os.remove(temp_file_path)  # Remove the original file
        temp_file_path = temp_mp3_file_path

    try:
        # Open the file and pass the file object to the OpenAI API
        print(temp_file_path)
        with open(temp_file_path, 'rb') as audio_file:
            transcript = openai.Audio.transcribe("whisper-1", audio_file)
        os.remove(temp_file_path)  # Clean up the temporary file
        return jsonify({'transcript': transcript.text})
    except Exception as e:
        if os.path.exists(temp_file_path):
            error_file_path = "error_audio_file.mp3"
            os.rename(temp_file_path, error_file_path)
            print(f"Saved error file to: {error_file_path}")
        print(e)
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True)
