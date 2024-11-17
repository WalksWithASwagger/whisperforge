import sys
from pydub import AudioSegment
from openai import OpenAI
import time
import os
import asyncio
import aiofiles
from concurrent.futures import ThreadPoolExecutor
from typing import List, Optional
from pathlib import Path

# Initialize the OpenAI client
client = OpenAI()

# Step 1: Split the Audio File into mp3 Chunks
def split_audio(file_path, chunk_length_ms):
    filename = os.path.splitext(os.path.basename(file_path))[0]
    print(f"Loading the audio file: {file_path}")
    audio = AudioSegment.from_file(file_path)

    print(f"Splitting the audio into chunks of {chunk_length_ms / 1000 / 60:.2f} minutes each...")
    chunks = [audio[i:i + chunk_length_ms] for i in range(0, len(audio), chunk_length_ms)]

    chunk_files = []
    for i, chunk in enumerate(chunks):
        chunk_file = f"whisperforge_{filename}_chunk_{i}.mp3"
        chunk.export(chunk_file, format="mp3")
        chunk_files.append(chunk_file)
        print(f"Exported {chunk_file}")

    return chunk_files

# Step 2: Transcribe Each Chunk
def transcribe_chunks(chunk_files):
    transcriptions = []

    for chunk_file in chunk_files:
        filename = os.path.splitext(chunk_file)[0]
        print(f"Starting transcription for {chunk_file}...")
        total_start_time = time.time()

        try:
            with open(chunk_file, "rb") as audio_file:
                print("File opened successfully.")
                print("Sending file to OpenAI for transcription...")
                transcription = client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file
                )
                print(f"Transcription for {chunk_file} completed successfully.")
                transcriptions.append(transcription.text)

                # Save the transcription to a file
                transcription_file = f"{filename}_transcription.txt"
                with open(transcription_file, "w") as text_file:
                    text_file.write(transcription.text)
                print(f"Transcription saved to {transcription_file}")

        except Exception as e:
            print(f"An error occurred during the transcription of {chunk_file}:")
            print(e)

        total_end_time = time.time()
        print(f"Total time taken for {chunk_file}: {total_end_time - total_start_time:.2f} seconds")

    return transcriptions

# Step 3: Combine Transcriptions into a Single File
def combine_transcriptions(transcriptions, output_file):
    print(f"Combining all transcriptions into {output_file}...")
    with open(output_file, "w") as outfile:
        for transcription in transcriptions:
            outfile.write(transcription + "\n")
    print(f"All transcriptions combined into {output_file}")

# Main function to run all steps
def main():
    if len(sys.argv) < 2:
        print("Usage: python whisperforge.py <audio_file_path>")
        sys.exit(1)

    # Get the file path from the command line argument
    file_path = sys.argv[1]
    filename = os.path.splitext(os.path.basename(file_path))[0]
    chunk_length_ms = 5 * 60 * 1000  # 5 minutes per chunk

    # Run the steps
    chunk_files = split_audio(file_path, chunk_length_ms)
    transcriptions = transcribe_chunks(chunk_files)
    combine_transcriptions(transcriptions, f"whisperforge_{filename}_full_transcription.txt")

    # Optionally, clean up the chunk files if you no longer need them
    for chunk_file in chunk_files:
        os.remove(chunk_file)
    print("Cleanup completed. Chunk files removed.")

if __name__ == "__main__":
    main()
