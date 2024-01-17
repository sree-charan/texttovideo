from flask import Flask, render_template, request, send_file
from main import usage  # Assuming usage is a function in main.py
import os

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/generate', methods=['POST'])
def generate_video_route():
    # Retrieve form data
    question = request.form.get('question')
    keyword = request.form.get('keyword')

    suffix = "Write the answer to the question in exact 150 words: "
    per_page = 12
    output_folder = os.getcwd()
    merged_video = 'merged_video.mp4'
    audio_filename = "tts.mp3"
    audio_video = "audiovideo.mp4"
    final_output_file = "final_video.mp4"
    # Call the usage function from main.py
    usage(question, keyword, suffix, per_page, output_folder, merged_video, audio_filename, audio_video, final_output_file)

    # Return the generated video file to the user
    return send_file(final_output_file, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)