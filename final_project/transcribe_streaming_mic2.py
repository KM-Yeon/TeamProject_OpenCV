from __future__ import division

import re
import sys
from youtubesearchpython import VideosSearch
from google.cloud import speech
import json
import pyaudio
from six.moves import queue
import os
# Audio recording parameters
RATE = 16000
CHUNK = int(RATE / 10)  # 100ms


class MicrophoneStream(object):
    """Opens a recording stream as a generator yielding the audio chunks."""

    def __init__(self, rate, chunk):
        self._rate = rate
        self._chunk = chunk

        # Create a thread-safe buffer of audio data
        self._buff = queue.Queue()
        self.closed = True

    def __enter__(self):
        self._audio_interface = pyaudio.PyAudio()
        self._audio_stream = self._audio_interface.open(
            format=pyaudio.paInt16,
            # The API currently only supports 1-channel (mono) audio
            # https://goo.gl/z757pE
            channels=1,
            rate=self._rate,
            input=True,
            frames_per_buffer=self._chunk,
            # Run the audio stream asynchronously to fill the buffer object.
            # This is necessary so that the input device's buffer doesn't
            # overflow while the calling thread makes network requests, etc.
            stream_callback=self._fill_buffer,
        )

        self.closed = False

        return self

    def __exit__(self, type, value, traceback):
        self._audio_stream.stop_stream()
        self._audio_stream.close()
        self.closed = True
        # Signal the generator to terminate so that the client's
        # streaming_recognize method will not block the process termination.
        self._buff.put(None)
        self._audio_interface.terminate()

    def _fill_buffer(self, in_data, frame_count, time_info, status_flags):
        """Continuously collect data from the audio stream, into the buffer."""
        self._buff.put(in_data)
        return None, pyaudio.paContinue

    def generator(self):
        while not self.closed:
            # Use a blocking get() to ensure there's at least one chunk of
            # data, and stop iteration if the chunk is None, indicating the
            # end of the audio stream.
            chunk = self._buff.get()
            if chunk is None:
                return
            data = [chunk]

            # Now consume whatever other data's still buffered.
            while True:
                try:
                    chunk = self._buff.get(block=False)
                    if chunk is None:
                        return
                    data.append(chunk)
                except queue.Empty:
                    break

            yield b"".join(data)



voice_command = ""

def listen_print_loop(responses, stream, limit_cnt):
    num_chars_printed = 0
    print("-------------listen start------------")
    for response in responses:

        movie_dict_list = []
        movie_list = []
        if not response.results:
            continue

        result = response.results[0]
        if not result.alternatives:
            continue

        transcript = result.alternatives[0].transcript
        overwrite_chars = " " * (num_chars_printed - len(transcript))

        if not result.is_final:
            sys.stdout.write(transcript + overwrite_chars + "\r")
            sys.stdout.flush()
            num_chars_printed = len(transcript)
        else:
            voice_command = transcript + overwrite_chars
            print(voice_command)

            videosSearch = VideosSearch(voice_command, limit=limit_cnt)
            #videosSearch = VideosSearch('나루토', limit=2)
            json_res = videosSearch.result()
            print(json.dumps(json_res['result'], sort_keys=True, indent=4))

            print("검색", len(json_res['result']))

            movie_list = json_res['result']
            for movie in movie_list:
                movie_thum_link_dict = {}
                movie_thum_link_dict["MY_THUM"] = movie['thumbnails'][0]['url']
                movie_thum_link_dict["MY_TITLE"] = movie['title']
                movie_thum_link_dict["MY_VCNT"] = movie["viewCount"]["text"]
                movie_thum_link_dict["MY_TIME"] = movie['publishedTime']
                movie_thum_link_dict["MY_LINK"] = movie['link']
                movie_dict_list.append(movie_thum_link_dict)
                # print(movie['thumbnails'][0]['url'])
                # print(movie['link'])


            # Exit recognition if any of the transcribed phrases could be
            # one of our keywords.
            if re.search(r"\b(exit|quit)\b", transcript, re.I):
                print("Exiting..")
                # stream.__exit__()
                break

            num_chars_printed = 0
            return movie_dict_list

def call_runner(limit_cnt=1):
    # See http://g.co/cloud/speech/docs/languages
    # for a list of supported languages.
    language_code = "ko-KR"  # a BCP-47 language tag

    client = speech.SpeechClient()
    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=RATE,
        language_code=language_code,
    )

    streaming_config = speech.StreamingRecognitionConfig(
        config=config, interim_results=True
    )

    with MicrophoneStream(RATE, CHUNK) as stream:
        audio_generator = stream.generator()
        requests = (
            speech.StreamingRecognizeRequest(audio_content=content)
            for content in audio_generator
        )

        responses = client.streaming_recognize(streaming_config, requests)
        # Now, put the transcription responses to use.
        movie_dict_list = listen_print_loop(responses, stream,limit_cnt)
    print("====", movie_dict_list)

    # call_runner()
    return movie_dict_list



# if __name__ == "__main__":
#     print(os.environ['GOOGLE_APPLICATION_CREDENTIALS'])
#     call_runner()

