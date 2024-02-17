import os
import shutil
import subprocess
from fastapi import FastAPI, File, UploadFile, Form
from fastapi.responses import JSONResponse, HTMLResponse
from pydub import AudioSegment
import tempfile
import speech_recognition as sr

app = FastAPI()
r = sr.Recognizer()

def resample_audio(input_path, output_path, target_sample_rate):
    ffmpeg_cmd = [
        "ffmpeg",
        "-i", input_path,
        "-ar", str(target_sample_rate),
        output_path
    ]
    subprocess.run(ffmpeg_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

def convert_to_wav(input_path, output_path):
    audio = AudioSegment.from_file(input_path)
    audio.export(output_path, format="wav")

def get_sampling_rate(audio_file_path):
    audio = AudioSegment.from_file(audio_file_path)
    return audio.frame_rate

@app.get("/", response_class=HTMLResponse)
async def read_root():
    with open("front-end3.html", "r") as file:
        html_content = file.read()
    return html_content

@app.post("/process_audio")
async def process_audio(audio: UploadFile = File(...), language: str = Form(...)):
    if not audio or not language:
        return JSONResponse(content={"success": False}, status_code=400)

    try:
        # Save the received audio to a temporary file
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
            temp_file_path = temp_file.name
            if audio.content_type != "audio/wav":
                # Convert to WAV if the uploaded file is not in WAV format
                print("Converting to WAV...")
                convert_to_wav(audio.file, temp_file_path)
            else:
                shutil.copyfileobj(audio.file, temp_file)
        print(temp_file_path)
        output_path = tempfile.mktemp(suffix=".wav")

        # Resample the audio to 16000 Hz
        # print("Resampling audio...")
        resample_audio(temp_file_path, output_path, target_sample_rate=16000)

        sampling_rate = get_sampling_rate(output_path)

        if sampling_rate != 16000:
            # If sampling rate is still not 16000 Hz, resample again
            print("Resampling again to 16000 Hz...")
            resample_audio(output_path, output_path, target_sample_rate=16000)

    except Exception as e:
        print("Error processing audio:", e)
        return JSONResponse(content={"success": False, "message": "Error processing audio."}, status_code=500)

    # print("Processing complete. Calling ASR...")
    return JSONResponse(content={"success": True, "language": calling_asr(output_path, language)})

def calling_asr(wav_file, lid):
    AUDIO_FILE = wav_file
    file = open(wav_file + ".txt", "w")
    text = "cant read wav file"
    try:
        with sr.AudioFile(AUDIO_FILE) as source:
            audio = r.record(source)
        text = r.recognize_google(audio, language=lid)
        return text
    except:
        return text
