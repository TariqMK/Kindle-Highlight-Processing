# README

_**Disclaimer:** Most if not all of the code here has been written in Python with the help of AI_

---

The scripts within this folder are aimed for use with Kindle's `My Clippings.txt` file, where book highlights for (sideloaded) documents reside.

The intent behind these scripts are to aid anyone who wishes for more granular control over their highlights.

Details for each individual script are as below.

---

## MyClippings_Highlight_Parser.py

**Intent:**

The highlights contained within `My Clippings.txt` contain entries from all the sideloaded books one has read on the Kindle device. For long term flexibility this is both inefficient and prone to data corruption and loss, especially over time as the file size grows ever larger.

This script takes `My Clippings.txt` as the input, scans it for all highlights, recognises if there are multiple books and then outputs a text file per book containing all related higlights.

**Usage Specifics:**

Download/copy the script and run using:

```
python3 MyClippings_Highlight_Parser.py
```

- The `My Clippings.txt` file must be placed in the same directory as the script
- The `My Clippings.txt` file must not be renamed, otherwise it will not be detected
- The new text files for each related book will be placed in a new folder in the same directory named `Highlights_by_Book`
  - If this folder does not exist, it will be created
- When the script has been run, a summary of books and highlights processed will be displayed in the terminal

Example:

<p align="center">
  <img width="676" height="130" alt="image" src="https://github.com/user-attachments/assets/3b03e84a-928a-48d8-a46a-ab5cd9372fb5" />
</p>

**Known Issues:**

- Over the years, Amazon has slightly changed the syntax of highlight metadata within `My Clippings.txt`. This script works best for files from 2020 onwards, but still works well for older files, though you may notice some formatting inconsistencies
