# SeWiRa
A self-made Wifi Radio.

## Introduction

One day I asked myself: How easy can it be to build a Wifi radio without using soldering irons, 3D printers, or a degree in computer science? Well, this project was the result. My Wifi radio consists of a Raspberry Pi with Raspberry Pi OS Lite, an external sound card, a numeric keypad as remote control and any active speaker or amplifier. SeWiRa is the software component for the radio and can be used not just in this project. It is a shell program that creates a station menu from a directory of m3u files. The stations are numbered and can be selected using the numeric keypad. The principle is similar to old shortwave receivers, where you only had to enter the correct frequency for the desired station. The radio can therefore be used completely without a screen; direct or remote access is of course required to edit the station list. You'll have to forgo the comfort of having a station database with thousands of programs from normal Wifi radios, but with this project you'll get a reliable radio that won't give you any nasty surprises if the portal operator cuts off database access. And if the station operator changes his stream, it is a matter of minutes to add the new address in the station list. 

This is the Python port of SeWiRa. It is more customizable than the bash script, and can be run not just on Linux/Unix-like operating systems. If you still prefer the original idea, [here is the pure bash version](https://github.com/schulle4u/sewira). 

## Setup

### Requirements

* Python3 (built using v3.12, but should also run on any other Python3 installation)
* [MPV](https://mpv.io/) for stream playback. Available on many operating systems. Can be easily adjusted for other players, they only should be able to play radio streams. 

### Running from source

* Clone or download this repository into any folder, e.g. `/home/username/sewira-py`.
* Optional: copy `sewira.ini.dist` to `sewira.ini` and configure individual settings.
* Add more M3U files to the streams directory. Only one URL per file is allowed. 
* Optional: If you want station announcements, create a virtual environment and install pyttsx3 dependency by running `pip install -e .`
* Run the script: `python ./run_sewira.py`

## Usage

After calling `sewira.py` a menu with numbered stations appears. The desired channel is activated by typing the displayed number and pressing Enter. If a channel is not available, an error message is displayed. Press 0 to exit the menu. The channels are sorted by filename, usually alphabetically. By prefixing the filename with a number, you can influence the sorting like in a playlist. Use the pattern `nnn-station.m3u` in your streams directory to automatically remove unwanted characters from the station list, where `nnn` is the prefixed number in your file name (up to 3 digits). MPV is used by default for playback, but the player is only active in the background to keep the station menu open for the next input. It is therefore not possible to control the player itself. 

## Configuration

The following options are available in `sewira.ini`: 

`player` = the program to use for stream playback as full or environment path (default: `mpv`)  
`player_options` = a space-separated list of program options for the desired player  
`autoplay` = automatically play one of the available streams at startup (menu number)  
`directory` = the directory to look for M3U files (default: `streams`)  
`language` = override automatic language detection, usually needed for windows (example: `de_DE.UTF-8`)  
`debug` = activate a more verbose output (default: False)  
`tts_enabled` = Enable station announcements (default: True)  
`tts_voice` = Enter an optional voice name, the program will try a substring match (Example: Zira)  
`tts_rate` = Speech rate (Default: 0)  
`tts_volume` = Speech volume (Default: -1)

Some options are also available as command line parameter. Start sewira with the `--help` parameter to get a list of available commands.

## More information and similar projects

* [RadioBrowser](https://radio-browser.info): A community-maintained database of stream URLs.
* [Terminal Radio](https://github.com/shinokada/tera): Another TUI radio, but with much more options and using radio-browser as station database. 

## Development

Steffen Schultz. Use it at own risk. Your house can explode! 😁
