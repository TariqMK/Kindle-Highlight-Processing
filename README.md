# README

_**Disclaimer:** Most if not all of the code here has been written in Python with the help of AI_

---

![klippings_logo_v6](https://github.com/user-attachments/assets/a666dc12-6672-4d0a-9ffa-3d43c4fbae91)<?xml version="1.0" encoding="UTF-8" standalone="no"?><!DOCTYPE svg PUBLIC "-//W3C//DTD SVG 1.1//EN" "http://www.w3.org/Graphics/SVG/1.1/DTD/svg11.dtd"><svg width="100%" height="100%" viewBox="0 0 2834 834" version="1.1" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" xml:space="preserve" xmlns:serif="http://www.serif.com/" style="fill-rule:evenodd;clip-rule:evenodd;stroke-linejoin:round;stroke-miterlimit:2;"><g><g><path d="M966.667,262.5l0,133.333c0,22.996 -18.67,41.667 -41.667,41.667l-133.333,0c-22.996,0 -41.667,-18.67 -41.667,-41.667l0,-133.333c0,-22.996 18.67,-41.667 41.667,-41.667l133.333,0c22.996,0 41.667,18.67 41.667,41.667Z" style="fill:#d1a041;fill-opacity:0.9;"/><text x="783.272px" y="406.714px" style="font-family:'ArialMT', 'Arial', sans-serif;font-size:216.667px;fill:#fff;">K</text></g><text x="974.316px" y="406.714px" style="font-family:'ArialMT', 'Arial', sans-serif;font-size:216.667px;fill:#faf9f5;">lippings</text></g></svg>

## What is Klippings?

Klippings is a Kindle Highlight Processor aimed for use with Kindle's `My Clippings.txt` file, where book highlights for (sideloaded) documents reside.

The intent behind these scripts are to aid anyone who wishes for more granular control over their highlights and to be able to export and store them in an orgainsed, systematic manner.

Your original `MyClippings.txt` file is not amended in any way.

---

## How Does it Work?

The highlights contained within `My Clippings.txt` contain entries from all the sideloaded books one has read on the Kindle device. For long term flexibility this is both inefficient and prone to data corruption and loss, especially over time as the file size grows ever larger.

This application takes `My Clippings.txt` as the input, scans it for all highlights, recognises if there are multiple books and then outputs a text file per book containing all related higlights.

The option to output highlights with or without metadata is available, as illustrated in the screenshots below.

## Screenshots

User Interface:

![Screenshot 01](https://github.com/user-attachments/assets/f93c7afa-dc2b-4b5d-9a8d-fa4b79bcffa6)

Standard Export (Sample):

<img width="1036" height="1065" alt="image" src="https://github.com/user-attachments/assets/c6d55e20-c3c9-4cb8-86f8-9beb44296793" />

Simplified Export (Sample):

<img width="1037" height="1065" alt="image" src="https://github.com/user-attachments/assets/5daba761-894c-4dc4-822b-67b6a70df817" />

---

## Run Directly

Download the latest version from the [Releases](https://github.com/TariqMK/Kindle-Highlight-Processing/releases) Page and run the `.exe`. 

All required folders will be automatically created wherever you specify. 

Enjoy!

## Run From Source

The following libraries are required, installation command below:

```
pip install customtkinter tkinterdnd2
```

Then simply run the script to bring up the GUI:

```
python Kindle_Highlight_Processor.py
```

All required folders will be automatically created. Enjoy!

---

## Notes

- The new text files for each related book will be placed in a new folder in the specified directory named `Highlights_by_Book`. If this folder does not exist, it will be created
- You also have the option to strip the page location metadata and have your highlights stored cleanly for PKMS systems like Obsidian
- When the application is run and the highlights have been extracted, a summary of books and highlights processed will be displayed in the application itself

---

**Known Issues:**

- Over the years, Amazon has slightly changed the syntax of highlight metadata within `My Clippings.txt`. This script works best for highlights taken from 2020 onwards, but still works well for older files, though you may notice some formatting inconsistencies. If you experience any problems, pelase raise an issue and I will look into it
