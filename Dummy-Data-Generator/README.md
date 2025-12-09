# Dummy Payload Forge 🧪📂  
_Advanced CLI tool for generating tons of realistic dummy files_

[![Python](https://img.shields.io/badge/python-3.8%2B-blue)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Status](https://img.shields.io/badge/status-active-success)](#)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](#contributing)

Dummy Payload Forge is a fast, flexible command-line tool for generating **lots of small files** for:

- Filesystem & storage testing  
- Backup & sync tool benchmarking  
- Search / indexing engine stress tests  
- Automation pipelines & CI experiments  

You tell it **how big the dataset should be (MB/GB)** and it creates **thousands (or millions) of files** with configurable extensions and size ranges — all in a single output folder.

---

## 📸 Demo

![Dummy Payload Forge Demo](assets/demo.png)

---

## ✨ Features

- **Fast generation**  
  Uses efficient random byte generation and single-shot writes for small files for good throughput.

- **Single output directory**  
  All dummy files are written to one target folder (easy to delete / test / mount).

- **Multiple file types**  
  Supports a mix of common extensions, e.g. `txt`, `log`, `csv`, `json`, `xml`, `png`, `pdf`, `zip` (and more as you evolve the script). :contentReference[oaicite:1]{index=1}  

- **Target dataset size (MB)**  
  - Pass a target size with `--target-mb`  
  - Or use the interactive menu to quickly choose “100 MB / 500 MB / 1 GB / custom” (depending on your script logic).

- **Approximate file count**  
  - Use `--approx-files` to say **how many files** you want  
  - The script then adjusts file size ranges around:  
    `target_mb / approx_files` (in KB/bytes). :contentReference[oaicite:2]{index=2}  

- **Fine-grained control**  
  - `--ext` → restrict to specific extensions  
  - `--min-size-kb` / `--max-size-kb` → override default file size range

- **Dry-run mode**  
  - See how many files _would_ be created and approximate disk usage  
  - No files actually written (useful for planning).

- **Reproducible runs**  
  - `--seed` → fix the random seed so runs are repeatable.

- **Zero external dependencies**  
  - Pure Python standard library. :contentReference[oaicite:3]{index=3}  

---
🚀 Installation

Clone the repository:

- git clone https://github.com/pankajjjat/Dummy-Data-Generator.git
- cd Dummy-Data-Generator
- python dummy.py
