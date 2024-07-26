import os
import re
import speech_recognition as sr

from moviepy.editor import VideoFileClip, AudioFileClip
from gtts import gTTS
from pydub import AudioSegment
from googletrans import Translator


def extract_audio(video_file):
    # Загрузите видео
    video = VideoFileClip(video_file)

    if not os.path.exists('extract_audio/'):
        os.makedirs('extract_audio/')

    # Извлечение аудио
    audio = video.audio
    audio.write_audiofile("extract_audio/extracted_audio.wav")


def convert_audio_format(input_audio_path, output_audio_path):
    audio = AudioSegment.from_file(input_audio_path)
    audio = audio.set_frame_rate(16000).set_channels(1)
    audio.export(output_audio_path, format="wav")


def split_audio(input_audio_path, chunk_length_ms=60000):
    audio = AudioSegment.from_file(input_audio_path)
    chunks = [audio[i:i + chunk_length_ms] for i in
              range(0, len(audio), chunk_length_ms)]

    os.makedirs('extract_audio/chunks', exist_ok=True)
    chunk_paths = []

    for i, chunk in enumerate(chunks):
        chunk_path = f"extract_audio/chunks/chunk_{i}.wav"
        chunk.export(chunk_path, format="wav")
        chunk_paths.append(chunk_path)

    return chunk_paths


def transcribe_audio(audio_path):
    recognizer = sr.Recognizer()
    audio_file = sr.AudioFile(audio_path)
    with audio_file as source:
        audio_data = recognizer.record(source)
        text = recognizer.recognize_google(audio_data)
    return text


def translate_text(text, src_lang='en', dest_lang='ru', chunk_size=500):
    # перевод для маленького текста (оставим для наглядности)
    # translator = Translator()
    # translation = translator.translate(text, src=src_lang, dest=dest_lang)
    # return translation.text

    # перевод больших текстов
    translator = Translator()
    words = text.split()
    chunks = []

    # создаем list, где каждый элемент == 500 строк
    for i in range(0, len(words), chunk_size):
        chunk = ' '.join(words[i:i + chunk_size])
        chunks.append(chunk)

    # переводим каждый элемент list
    translated_chunks = []
    for chunk in chunks:
        translation = translator.translate(chunk, src=src_lang, dest=dest_lang)
        translated_chunks.append(translation.text)

    return ' '.join(translated_chunks)


def text_to_speech(text, output_audio_path, lang='ru'):
    if not os.path.exists('translated_audio/'):
        os.makedirs('translated_audio/')
    # os.makedirs('translated_audio/', exist_ok=True)

    tts = gTTS(text, lang=lang)
    tts.save(output_audio_path)


def replace_audio_in_video(video_path, new_audio_path, output_video_path):
    if not os.path.exists('translated_video/'):
        os.makedirs('translated_video/')

    video = VideoFileClip(video_path)
    translated_audio = AudioFileClip(new_audio_path)
    new_video = video.set_audio(translated_audio)
    new_video.write_videofile(output_video_path)


if __name__ == '__main__':
    # Пути к файлам
    video_path = "video/What_is_Python.mp4"

    extracted_audio_path = "extract_audio/extracted_audio.wav"
    converted_audio_path = "extract_audio/converted_audio.wav"

    translated_audio_path = "translated_audio/translated_audio.mp3"
    output_video_path = "translated_video/translated_video.mp4"

    # -------------------------------------------------------------------------

    # step 1 - Извлечение аудио из видео
    print("step - 1")
    extract_audio(video_path)

    # -------------------------------------------------------------------------

    # Шаг 2 - Конвертация аудио в нужный формат
    print("step - 2")
    convert_audio_format(extracted_audio_path, converted_audio_path)

    # -------------------------------------------------------------------------

    # Шаг 3 - Разбивка аудио на сегменты
    print("step - 3")
    chunk_paths = split_audio(converted_audio_path)
    print(f"Chunks: {chunk_paths}")

    # -------------------------------------------------------------------------

    # Шаг 4 - промежуточный, готовим переменную которая будет содержать все
    # файлы, который мы разбили выше на куски

    print("step - 4")

    # получаем все куски аудио из папки
    directory = "extract_audio/chunks/"
    files = os.listdir(directory)

    # Фильтрация и сортировка файлов по номеру
    chunk_paths = sorted(
        [os.path.join(directory, f) for f in files if f.endswith('.wav')],
        key=lambda f: int(re.search(r'chunk_(\d+)\.wav', f).group(1))
    )

    # -------------------------------------------------------------------------

    # Шаг 5 - Транскрибирование аудио
    # Транскрибирование — это процесс преобразования аудиозаписи в текст.
    # В контексте данного проекта это означает прослушивание аудиофайлов и
    # распознавание речи, содержащейся в них, для создания текстовой
    # версии сказанного.

    print("step - 5")
    transcribed_texts = []
    recognizer = sr.Recognizer()

    for chunk_path in chunk_paths:
        try:
            transcribed_text = transcribe_audio(chunk_path)
            transcribed_texts.append(transcribed_text)
            print(f"Transcribed chunk: {chunk_path}")
        except sr.UnknownValueError:
            print(f"Could not understand audio chunk: {chunk_path}")
        except sr.RequestError as e:
            print(f"Could not request results for chunk: {chunk_path}; {e}")

    full_transcribed_text = ' '.join(transcribed_texts)
    print("Full Transcribed Text:", full_transcribed_text)

    # -------------------------------------------------------------------------

    # Шаг 6 - Создание аудио из переведенного текста
    print("step - 6")
    translated_text = translate_text(full_transcribed_text, src_lang='en', dest_lang='ru')
    text_to_speech(translated_text, translated_audio_path)

    # -------------------------------------------------------------------------

    # Шаг 7 - Замена аудио в видео
    print("step - 7")
    replace_audio_in_video(video_path, translated_audio_path, output_video_path)
