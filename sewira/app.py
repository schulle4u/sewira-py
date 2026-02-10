# -*- coding: utf-8 -*-
# SeWiRa - the Selfmade Wifi Radio
# Copyright (c) 2024 Steffen Schultz
import sys
import os
import subprocess
import configparser
import gettext
import locale
import re
import signal
import argparse
import threading
from pathlib import Path

try:
    import pyttsx3
except ImportError:
    pyttsx3 = None


class SeWiRa:
    def __init__(self):
        # Package directory (for locale and other package data)
        if getattr(sys, 'frozen', False):
            self.package_dir = Path(sys._MEIPASS) / 'sewira'
            self.basedir = Path(sys.executable).parent
        else:
            self.package_dir = Path(__file__).parent.absolute()
            self.basedir = Path.cwd()

        # Set a nice title for windows users
        if (os.name == "nt"):
            os.system("title SeWiRa")

        # Save all status messages
        self.current_status_message = ""

        # Load configuration
        self.load_config()

        # Setup localization
        self.setup_localization()

        # Player process
        self.player_process = None
        self._play_generation = 0

        # Setup signal handlers
        self.setup_signal_handlers()

    def clear_console(self):
        """Clears the console screen."""
        os.system('cls' if os.name == 'nt' else 'clear')

    def status_message(self, message, is_error=False, force_display=False):
        """
        Handles displaying and storing status messages.

        Args:
            message (str): The message to display/store.
            is_error (bool): True if this is an error message (adds '\a' and forces immediate display).
            force_display (bool): True to force immediate display of the message, even if not an error.
        """

        # Terminal bell for error messages
        if is_error:
            message = "\a" + message

        self.current_status_message = message  # Save message for later usage

        # Print directly if error or force_display is True
        if is_error or force_display:
            print(message)

    def load_config(self):
        """Load configuration from file"""
        config = configparser.ConfigParser()

        try:
            config.read(self.basedir / 'sewira.ini')

            # Read settings from config, fallback to default values
            self.player = config.get('Settings', 'player', fallback='mpv')
            self.player_options = config.get('Settings', 'player_options',
                                            fallback='--no-terminal')
            self.autoplay = config.get('Settings', 'autoplay', fallback='')
            self.directory = Path(config.get('Settings', 'directory', fallback=str(self.basedir / 'streams')))
            self.language = config.get('Settings', 'language', fallback='')
            self.debug = config.getboolean('Settings', 'debug', fallback=False)
            self.tts_enabled = config.getboolean('Settings', 'tts_enabled', fallback=True)
            self.tts_voice = config.get('Settings', 'tts_voice', fallback='')
            self.tts_rate = config.getint('Settings', 'tts_rate', fallback=0)
            self.tts_volume = config.getfloat('Settings', 'tts_volume', fallback=-1)

        except configparser.NoSectionError as e:
            print(f"Error: Configuration section not found: {e}")
        except configparser.NoOptionError as e:
            print(f"Error: Configuration option not found: {e}")
        except Exception as e:
            print(f"Unexpected error while loading config: {e}")

        # Validate directory
        if not self.directory.is_dir():
            print(f"Warning: Directory {self.directory} does not exist. Creating it...")
            try:
                self.directory.mkdir(parents=True, exist_ok=True)
            except PermissionError:
                print(f"Error: Cannot create directory {self.directory}. Using script directory instead.")
                self.directory = self.basedir / 'streams'
                self.directory.mkdir(exist_ok=True)

    def setup_localization(self):
        """Setup localization settings"""
        system_language = locale.getlocale()
        try:
            if self.language:
                if os.name == 'nt': os.environ['LANG'] = self.language
                locale.setlocale(locale.LC_ALL, self.language)
            else:
                if os.name == 'nt':
                    os.environ['LANG'] = system_language[0] + '.utf8'
                    locale.setlocale(locale.LC_ALL, system_language[0] + '.utf8')
                else:
                    locale.setlocale(locale.LC_ALL, '')
        except locale.Error as e:
            print(f"Warning: Error while setting locale: {e} Trying fallback to default 'C' locale.")
            try:
                locale.setlocale(locale.LC_ALL, 'C')
            except locale.Error as e_fallback:
                print(f"Error falling back to 'C' locale: {e_fallback}. Locale not set.")

        gettext.bindtextdomain('sewira', str(self.package_dir / 'locale'))
        gettext.textdomain('sewira')
        self._ = gettext.gettext

    def setup_signal_handlers(self):
        """Setup signal handlers for graceful termination"""
        signal.signal(signal.SIGINT, self.handle_exit_signal)
        signal.signal(signal.SIGTERM, self.handle_exit_signal)

    def handle_exit_signal(self, signum, frame):
        """Handle exit signals"""
        print("\n" + self._("Exiting..."))
        self.stop_stream()
        sys.exit(0)

    def list_m3u_files(self):
        """List all M3U files in the directory"""
        try:
            return sorted([f for f in self.directory.iterdir() if f.suffix.lower() == '.m3u'])
        except FileNotFoundError:
            print(self._("The entered directory could not be found."))
            return []

    def print_menu(self, m3u_files):
        """Display the menu of available streams"""
        self.clean_names = {}
        print(f"{'SeWiRa':^40}")
        print("\n" + self._("Available streams:"))

        for idx, file_path in enumerate(m3u_files, start=1):
            filename = file_path.name
            # Remove leading numbers and file extension
            clean_name = re.sub(r'^\d{0,3}-', '', filename)
            clean_name = clean_name.removesuffix('.m3u')
            self.clean_names[str(file_path)] = clean_name
            print(f"{idx}. {clean_name}")

        print("0. " + self._("Exit"))

    def get_stream_url(self, m3u_file):
        """Extract stream URL from M3U file"""
        try:
            with open(m3u_file, 'r') as file:
                for line in file:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        return line
            self.status_message(self._("No valid stream in file %(file)s.") % {'file': m3u_file}, is_error=True)
            return None
        except FileNotFoundError:
            self.status_message(self._("File %(file)s not found.") % {'file': m3u_file}, is_error=True)
            return None
        except Exception as e:
            self.status_message(self._("Error reading file %(filename)s: %(error)s") % {'filename': m3u_file, 'error': str(e)}, is_error=True)
            return None

    def speak(self, text):
        """Announce text via text-to-speech using pyttsx3."""
        if pyttsx3 is None or self.tts_enabled == False:
            if self.debug:
                print("pyttsx3 is not installed or has been disabled, skipping speech output.")
            return
        try:
            engine = pyttsx3.init()

            if self.tts_voice:
                # Try substring match on voice name first
                matched = False
                for voice in engine.getProperty('voices'):
                    if self.tts_voice.lower() in voice.name.lower():
                        engine.setProperty('voice', voice.id)
                        matched = True
                        break
                # Fall back to direct ID (covers espeak IDs like de+Max)
                if not matched:
                    engine.setProperty('voice', self.tts_voice)

            if self.tts_rate > 0:
                engine.setProperty('rate', self.tts_rate)

            if 0 <= self.tts_volume <= 1:
                engine.setProperty('volume', self.tts_volume)

            engine.say(text)
            engine.runAndWait()
            engine.stop()
        except Exception as e:
            if self.debug:
                print(self._("Error during speech output: %(error_message)s") % {'error_message': str(e)})

    def stop_stream(self):
        """Stop the currently playing stream"""
        if self.player_process and self.player_process.poll() is None:
            # Terminate current player process
            try:
                self.player_process.terminate()
                # Give it some time to terminate gracefully
                try:
                    self.player_process.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    # Force kill if it doesn't terminate in time
                    self.player_process.kill()
                    self.player_process.wait()
            except Exception as e:
                if self.debug:
                    print(self._("Error stopping player: %(error_message)s") % {'error_message': str(e)})

    def _start_player(self, cmd):
        """Start the player subprocess."""
        try:
            self.player_process = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
        except FileNotFoundError:
            self.status_message(self._("Error: The player %(player_name)s cannot be found.") % {'player_name': self.player}, is_error=True)
        except Exception as e:
            self.status_message(self._("An error occurred: %(error_message)s") % {'error_message': str(e)}, is_error=True)

    def play_stream(self, url, stream_name=""):
        """Play a stream URL"""
        # Stop previous stream if any
        self.stop_stream()

        # Invalidate any pending background thread
        self._play_generation += 1
        current_generation = self._play_generation

        # Split player options into a list for proper argument passing
        cmd = [self.player] + self.player_options.split() + [url]

        display_message = ""

        if stream_name:
            display_message = self._("Now playing: %(stream_name)s") % {'stream_name': stream_name}
        else:
            display_message = self._("Playing...")

        if self.debug:
            command_message = self._("Command: %(command)s") % {'command': " ".join(cmd)}
            display_message = f"{display_message}\n{command_message}"

        self.status_message(display_message, force_display=True)

        if stream_name and pyttsx3 is not None:
            # Speak first, then start player — both in background
            def _speak_then_play():
                self.speak(stream_name)
                if self._play_generation != current_generation:
                    return
                self._start_player(cmd)
            thread = threading.Thread(target=_speak_then_play, daemon=True)
            thread.start()
        else:
            self._start_player(cmd)

    def handle_autoplay(self):
        """Handle autoplay functionality using menu number"""
        m3u_files = self.list_m3u_files()

        if not m3u_files:
            print(self._("No M3U files found for autoplay."))
            return

        try:
            # Convert autoplay value to integer
            index = int(self.autoplay) - 1

            if 0 <= index < len(m3u_files):
                m3u_file = m3u_files[index]
                stream_url = self.get_stream_url(m3u_file)

                if stream_url:
                    # Get clean name for display
                    filename = m3u_file.name
                    clean_name = re.sub(r'^\d{0,3}-', '', filename)
                    clean_name = clean_name.removesuffix('.m3u')

                    self.play_stream(stream_url, clean_name)
                else:
                    self.status_message(self._("Autoplay failed: No valid stream URL found in %(file)s.") % {'file': m3u_file}, is_error=True)
            else:
                self.status_message(self._("Autoplay failed: Invalid menu number %(number)s.") % {'number': self.autoplay}, is_error=True)
        except ValueError:
            self.status_message(self._("Autoplay failed: '%(number)s' is not a valid menu number.") % {'number': self.autoplay}, is_error=True)

    def run(self):
        """Main application loop"""
        # Check if valid directory
        if not self.directory.is_dir():
            self.status_message(self._("Directory does not exist: %(directory)s") % {'directory': self.directory}, is_error=True)
            return

        if self.autoplay:
            self.handle_autoplay()

        # Main loop
        while True:
            m3u_files = self.list_m3u_files()

            if not m3u_files:
                self.status_message(self._("No M3U files found in %(directory)s.") % {'directory': self.directory}, is_error=True)
                return

            self.clear_console()

            self.print_menu(m3u_files)

            if self.current_status_message:
                print()
                print(self.current_status_message)

            # Prompt for program number input
            choice = input(self._("Program number (0 to exit): "))

            if choice == '0':
                self.clear_console()
                self.status_message(self._("Bye!"), force_display=True)
                self.stop_stream()  # Terminate player process
                break

            try:
                index = int(choice) - 1
                if 0 <= index < len(m3u_files):
                    m3u_file = m3u_files[index]
                    stream_url = self.get_stream_url(m3u_file)

                    if stream_url:
                        # Get clean name for display
                        clean_name = self.clean_names[str(m3u_file)]

                        self.play_stream(stream_url, clean_name)
                    else:
                        self.status_message(self._("No valid stream URL found in %(file)s.") % {'file': m3u_file}, is_error=True)
                else:
                    self.status_message(self._("Invalid selection."), is_error=True)
            except ValueError:
                self.status_message(self._("Please enter a valid number."), is_error=True)


def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description='Creates a station menu from a directory of m3u files.', epilog='Source code is available at https://github.com/schulle4u/sewira-py')
    parser.add_argument('-a', '--autoplay', help='Automatically play a stream at startup')
    parser.add_argument('-d', '--directory', help='Directory containing M3U files')
    parser.add_argument('-p', '--player', help='Media player executable')
    parser.add_argument('--debug', action='store_true', help='Enable debug output')
    return parser.parse_args()


def main():
    """Application entry point"""
    # Parse command line arguments
    args = parse_arguments()

    # Create and run the application
    app = SeWiRa()

    # Override settings with command line arguments if provided
    if args.autoplay:
        app.autoplay = args.autoplay
    if args.directory:
        app.directory = Path(args.directory)
    if args.player:
        app.player = args.player
    if args.debug:
        app.debug = True

    app.run()


if __name__ == "__main__":
    main()
