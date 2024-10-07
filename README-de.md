<p align="right"><a href="README.md">English</a> &nbsp; <a href="README-de.md">Deutsch</a></p>

# SeWiRa
Ein Selfmade Wifi Radio.

## Hintergrund

Wie einfach kann es sein, ein WLAN-Radio zu bauen, ohne auf Lötkolben, 3d-Drucker oder ein Informatikstudium angewiesen zu sein? Ausgehend von solchen Fragen ist dieses Projekt entstanden. Mein WLAN-Radio besteht aus einem Raspberry Pi mit Raspberry Pi OS Lite, dazu eine externe Soundkarte, ein Ziffernblock als Fernbedienung sowie ein beliebiger Aktivlautsprecher oder HiFi-Verstärker. SeWiRa ist die Softwarekomponente für das Radio, und kann beliebig eingesetzt werden. Es ist ein Programm für die Shell, welches aus einem Verzeichnis mit M3u-Dateien ein Sendermenü erstellt. Die einzelnen Sender werden nummeriert und lassen sich über den Ziffernblock ansteuern. Das Prinzip ähnelt alten Kurzwellenempfängern, bei denen man nur die richtige Frequenz eingeben musste. Das Radio kann daher völlig ohne einen Bildschirm genutzt werden, lediglich für das Bearbeiten der Senderliste ist natürlich ein Zugang notwendig. Auf die von normalen WLAN-Radios gewohnte Senderdatenbank mit tausenden von Programmen muss man allerdings verzichten, bekommt mit diesem Projekt aber ein zuverlässig funktionierendes Radio, das einem keine bösen Überraschungen bereitet, wenn der Portalbetreiber den Datenbankzugang abschaltet. Und sollte der Senderbetreiber seinen Stream ändern, ist es eine Frage von Minuten, die neue Adresse im Sendermenü zu hinterlegen. 

Dies ist eine experimentelle Python-Version des ursprünglichen SeWiRa, welche eine bessere Konfiguration bietet, und nicht nur auf Linux/Unix-artigen Systemen lauffähig ist. Wer das Original bevorzugt, [hier ist das Bash-Script](https://github.com/schulle4u/sewira). 

## Einrichtung

### Voraussetzungen

* Python3 mit Gettext-Support
* [MPV](https://mpv.io/) für die Wiedergabe der Streams. Der Player ist in den Paketquellen vieler Distributionen bereits vorhanden. Natürlich kann mit wenigen Handgriffen eine andere Software konfiguriert werden, sie sollte nur in der Lage sein, Radiostreams abzuspielen.

### Aus dem Quellcode starten

* Das Repository clonen oder [Alle Dateien herunterladen](https://github.com/schulle4u/sewira-py/archive/refs/heads/main.zip) und in einem beliebigen Ordner entpacken, z. B. nach `/home/Benutzer/sewira-py`. 
* System- und Python-Abhängigkeiten installieren: `pip install python-gettext`
* Linux-Nutzer müssen möglicherweise mit virtualenv arbeiten oder das Argument `--break-system-packages` an pip übergeben. 
* Optional: `sewira.ini` anpassen, um den verwendeten Player, das Verzeichnis der Streams oder die Sprache zu ändern.
* Weitere M3U-Dateien im Streams-Ordner ablegen. In jeder M3U-Datei sollte nur eine URL hinterlegt sein. 
* Script aufrufen: `python ./sewira.py`

## Verwendung

Nach dem Aufruf von `sewira.py` erscheint ein Menü mit nummerierten Sendern. Der gewünschte Sender wird durch Eingabe der dargestellten  Nummer und Enter aktiviert. Ist ein Sender nicht vorhanden, erfolgt eine entsprechende Fehlermeldung. Die ziffer 0 beendet das Menü. Die Sortierung der Sender erfolgt anhand des  Dateinamens, also in der Regel alphabetisch. Durch das Voranstellen einer Ziffer am Dateinamen kann die Sortierung wie in einer Playliste beeinflusst werden. Die Dateinamen sollten das Muster `nnn-Station.m3u` verwenden, damit unnötige Zeichen automatisch aus der Stationsliste entfernt werden können. Das Muster `nnn` entspricht hierbei der bis zu dreistelligen Indexnummer im Dateinamen. Für die Wiedergabe wird standardmäßig MPV verwendet, jedoch ist der Player nur im Hintergrund aktiv, damit das Sendermenü immer für die nächste Eingabe geöffnet bleiben kann. Eine Steuerung des Players ist daher nicht vorgesehen. 

## Weitere Informationen und Projekte

* [RadioBrowser](https://radio-browser.info): Eine Datenbank zum Auffinden direkter Streamadressen für eure Favoritenliste.
* [Terminal Radio](https://github.com/shinokada/tera): Ein weiteres Internetradio im Textmodus, jedoch sehr viel umfangreicher und mit RadioBrowser-Zugriff. 

## Entwicklung

Steffen Schultz. Nutzung auf eigene Gefahr, euer Haus könnte explodieren! 😁
