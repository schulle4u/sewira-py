# -*- coding: utf-8 -*-
# SeWiRa - the Selfmade Wifi Radio
# Copyright (c) 2024 Steffen Schultz
import sys
import os
import subprocess
import configparser
import gettext
import locale

# Determine current script directory
if getattr(sys, 'frozen', False):
    scriptdir = os.path.dirname(sys.executable)
else:
    scriptdir = os.path.dirname(os.path.abspath(__file__))

# Load config file
config = configparser.ConfigParser()
config.read(os.path.join(scriptdir, 'sewira.ini'))

# Read settings from config, fallback to default values
player = config.get('Settings', 'player', fallback='mpv')
player_options = config.get('Settings', 'player_options', fallback='--no-terminal')
directory = config.get('Settings', 'directory', fallback=os.path.join(scriptdir, 'streams'))
language = config.get('Settings', 'language', fallback='')

# Setup l10n
os.environ['LANG'] = language

try:
    if language:
        locale.setlocale(locale.LC_ALL, language)
    else:
        locale.setlocale(locale.LC_ALL, '')
except locale.Error as e:
    print(f"Warning: Locale {language} not available, falling back to system default.")
    locale.setlocale(locale.LC_ALL, '')

gettext.bindtextdomain('sewira', os.path.join(scriptdir, 'locale'))
gettext.textdomain('sewira')
_ = gettext.gettext

# Set global variable for the player process
player_process = None

def list_m3u_files(directory):
    # List of all m3u files in the directory
    try:
        m3u_files = [f for f in os.listdir(directory) if f.endswith('.m3u')]
        return m3u_files
    except FileNotFoundError:
        print(_("The entered directory could not be found."))
        return []

def print_menu(m3u_files):
    # Show the menu
    print(f"{'SeWiRa':^40}")
    print("\n" + _("Available streams:"))
    for idx, file in enumerate(m3u_files, start=1):
        print(f"{idx}. {file}".removesuffix('.m3u'))
    print("0. " + _("Exit"))

def get_stream_url(m3u_file):
    # Get URL from file
    try:
        with open(m3u_file, 'r') as file:
            for line in file:
                line = line.strip()
                if line and not line.startswith('#'):
                    return line
        print("\a" + _("No valid stream in file %s.") % m3u_file)
        return None
    except FileNotFoundError:
        print("\a" + _("File %s not found.") % m3u_file)
        return None

def stop_previous_stream():
    global player_process
    if player_process and player_process.poll() is None:
        # Terminates current player process
        player_process.terminate()
        player_process.wait()

def play_stream(url):
    global player_process

    # Stop previous stream
    stop_previous_stream()

    # And start a new one
    try:
        player_process = subprocess.Popen([player, player_options, url], stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
        print(_("Opening stream with %s: %s") % (player, url))
    except FileNotFoundError:
        print("\a" + _("Error: The player %s cannot be found.") % player)
    except Exception as e:
        print("\a" + _("An error occurred: %s") % str(e))

def main():
    global directory, player

    # Check if valid directory
    if not os.path.isdir(directory):
        print("\a" + _("This directory doesn't exist."))
        return

    # Main loop
    while True:
        m3u_files = list_m3u_files(directory)
        
        if not m3u_files:
            print("\a" + _("No M3U files found."))
            break
        
        print_menu(m3u_files)
        
        # Prompt for program number input
        choice = input(_("Program number (0 to exit): "))
        
        if choice == '0':
            print(_("Bye!"))
            stop_previous_stream()  # Terminate player process
            break
        
        try:
            index = int(choice) - 1
            if 0 <= index < len(m3u_files):
                m3u_file = os.path.join(directory, m3u_files[index])
                stream_url = get_stream_url(m3u_file)
                
                if stream_url:
                    play_stream(stream_url)
                else:
                    print("\a" + _("No valid stream URL found in %s.") % file)
            else:
                print("\a" + _("Invalid selection."))
        except ValueError:
            print("\a" + _("Please enter a valid number."))

if __name__ == "__main__":
    main()
