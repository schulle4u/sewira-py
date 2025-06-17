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
from pathlib import Path


class SeWiRa:
    def __init__(self):
        # Determine current script directory
        if getattr(sys, 'frozen', False):
            self.scriptdir = Path(sys.executable).parent
        else:
            self.scriptdir = Path(__file__).parent.absolute()

        # Set a nice title for windows users
        if (os.name=="nt"):
            os.system("title SeWiRa")

        # Save all status messages
        self.current_status_message = ""

        # Load configuration
        self.load_config()

        # Setup localization
        self.setup_localization()

        # Player process
        self.player_process = None
        
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
            
        self.current_status_message = message # Save the message for later usage in the menu

        # Print directly if error or force_display is True
        if is_error or force_display:
            print(message)

    def load_config(self):
        """Load configuration from file"""
        config = configparser.ConfigParser()
        
        try:
            config.read(self.scriptdir / 'sewira.ini')

            # Read settings from config, fallback to default values
            self.player = config.get('Settings', 'player', fallback='mpv')
            self.player_options = config.get('Settings', 'player_options', fallback='--no-terminal')
            self.autoplay = config.get('Settings', 'autoplay', fallback='')
            self.directory = Path(config.get('Settings', 'directory', 
                                            fallback=str(self.scriptdir / 'streams')))
            self.language = config.get('Settings', 'language', fallback='')
            self.debug = config.getboolean('Settings', 'debug', fallback=False)

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
                self.directory = self.scriptdir / 'streams'
                self.directory.mkdir(exist_ok=True)
    
    def setup_localization(self):
        """Setup localization settings"""
        if self.language:
            os.environ['LANG'] = self.language

        try:
            if self.language:
                locale.setlocale(locale.LC_ALL, self.language)
            else:
                locale.setlocale(locale.LC_ALL, '')
        except locale.Error as e:
            print(f"Warning: Locale {self.language} not available, falling back to system default.")

        gettext.bindtextdomain('sewira', str(self.scriptdir / 'locale'))
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

    def play_stream(self, url, stream_name=""):
        """Play a stream URL"""
        # Stop previous stream if any
        self.stop_stream()

        # Start new stream
        try:
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
            
            self.player_process = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)

        except FileNotFoundError:
            self.status_message(self._("Error: The player %(player_name)s cannot be found.") % {'player_name': self.player}, is_error=True)
        except Exception as e:
            self.status_message(self._("An error occurred: %(error_message)s") % {'error_message': str(e)}, is_error=True)

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
    parser = argparse.ArgumentParser(description='SeWiRa - Selfmade Wifi Radio')
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