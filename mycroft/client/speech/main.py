# Copyright 2017 Mycroft AI Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
from threading import Lock

from mycroft import dialog
from mycroft.client.enclosure.api import EnclosureAPI
from mycroft.client.speech.listener import RecognizerLoop
from mycroft.configuration import Configuration
from mycroft.identity import IdentityManager
from mycroft.lock import Lock as PIDLock  # Create/Support PID locking file
from mycroft.messagebus.client.ws import WebsocketClient
from mycroft.messagebus.message import Message
from mycroft.util import create_daemon, wait_for_exit_signal, \
    reset_sigint_handler
from mycroft.util.log import LOG

ws = None
lock = Lock()
loop = None


def handle_record_begin():
    LOG.info("Begin Recording...")
    ws.emit(Message('recognizer_loop:record_begin'))


def handle_record_end():
    LOG.info("End Recording...")
    ws.emit(Message('recognizer_loop:record_end'))


def handle_no_internet():
    LOG.debug("Notifying enclosure of no internet connection")
    ws.emit(Message('enclosure.notify.no_internet'))


def handle_awoken():
    """ Forward mycroft.awoken to the messagebus. """
    LOG.info("Listener is now Awake: ")
    ws.emit(Message('mycroft.awoken'))


def handle_wakeword(event):
    LOG.info("Wakeword Detected: " + event['utterance'])
    ws.emit(Message('recognizer_loop:wakeword', event))


def handle_utterance(event):
    LOG.info("Utterance: " + str(event['utterances']))
    context = {'client_name': 'mycroft_listener', "source": "speech",
                     'destinatary': 'skills'}
    if 'ident' in event:
        ident = event.pop('ident')
        context['ident'] = ident
    ws.emit(Message('recognizer_loop:utterance', event, context))


def handle_unknown():
    ws.emit(Message('mycroft.speech.recognition.unknown'))


def handle_speak(event):
    """
        Forward speak message to message bus.
    """
    ws.emit(Message('speak', event))


def handle_complete_intent_failure(event):
    LOG.info("Failed to find intent.")
    data = {'utterance': dialog.get('not.loaded')}
    ws.emit(Message('speak', data))


def handle_hotword(event):
    ww = config["listener"].get("wake_word", "hey mycroft")
    suw = config["listener"].get("stand_up_word", "wake up")
    if event["hotword"] != ww and event["hotword"] != suw:
        LOG.info("Hotword Detected: " + event['hotword'])
        ws.emit(Message('recognizer_loop:hotword', event))


def handle_sleep():
    loop.sleep()


def handle_wake_up(event):
    loop.awaken()


def handle_mic_mute(event):
    loop.mute()


def handle_mic_unmute(event):
    loop.unmute()


def handle_paired(event):
    IdentityManager.update(event.data)


def handle_audio_start(event):
    """
        Mute recognizer loop
    """
    loop.mute()


def handle_audio_end(event):
    """
        Request unmute, if more sources has requested the mic to be muted
        it will remain muted.
    """
    loop.unmute()  # restore


def handle_stop(event):
    """
        Handler for mycroft.stop, i.e. button press
    """
    loop.force_unmute()


def handle_open():
    # TODO: Move this into the Enclosure (not speech client)
    # Reset the UI to indicate ready for speech processing
    EnclosureAPI(ws).reset()


def main():
    global ws
    global loop
    reset_sigint_handler()
    PIDLock("voice")
    ws = WebsocketClient()
    Configuration.init(ws)
    loop = RecognizerLoop()
    loop.on('recognizer_loop:utterance', handle_utterance)
    loop.on('recognizer_loop:speech.recognition.unknown', handle_unknown)
    loop.on('speak', handle_speak)
    loop.on('recognizer_loop:record_begin', handle_record_begin)
    loop.on('recognizer_loop:awoken', handle_awoken)
    loop.on('recognizer_loop:wakeword', handle_wakeword)
    loop.on('recognizer_loop:hotword', handle_hotword)
    loop.on('recognizer_loop:record_end', handle_record_end)
    loop.on('recognizer_loop:no_internet', handle_no_internet)
    ws.on('open', handle_open)
    ws.on('complete_intent_failure', handle_complete_intent_failure)
    ws.on('recognizer_loop:sleep', handle_sleep)
    ws.on('recognizer_loop:wake_up', handle_wake_up)
    ws.on('mycroft.mic.mute', handle_mic_mute)
    ws.on('mycroft.mic.unmute', handle_mic_unmute)
    ws.on("mycroft.paired", handle_paired)
    ws.on('recognizer_loop:audio_output_start', handle_audio_start)
    ws.on('recognizer_loop:audio_output_end', handle_audio_end)
    ws.on('mycroft.stop', handle_stop)

    create_daemon(ws.run_forever)
    create_daemon(loop.run)

    wait_for_exit_signal()


if __name__ == "__main__":
    main()
