# GmsOne
<img src="https://livedoor.blogimg.jp/commencement_wisdom/imgs/4/1/41f73c7b.png" width="600px">  

GmsOne is a GUI launcher for macOS designed to simplify job management for the computational chemistry software "GAMESS."  
It allows users to add multiple jobs to a queue and run them sequentially without complex command-line operations.    

For more details on Avocute, please go to [https://pc-chem-basics.blog.jp/archives/38065995.html](https://pc-chem-basics.blog.jp/archives/38065995.html)  

## Requirements

GmsOne requires the following environment to run from source:

* **Python 3.8 or higher**
* [**customtkinter**](https://customtkinter.tomschimansky.com/) library

### Installation

1.  **Check your Python version**
    Make sure you have Python 3.8+ installed:
    ```bash
    python3 --version
    ```

2.  **Install the required package**
    Install `customtkinter` via pip:
    ```bash
    pip install customtkinter
    ```

3.  **Run the application**
    ```bash
    python3 GmsOne.py
    ```
> [!CAUTION]
> ### Supported GAMESS Versions
> This application is specifically optimized for **GAMESS version 30Jun2020R1**.
> 
> Older versions (e.g., **30Sep2018R3-Lion** or earlier) are **not supported** due to differences in path handling within the `rungms` script, which may cause execution errors (e.g., path modifier errors).

### Tips for Path Settings
To ensure stable execution, please follow these rules in the **SETTINGS** window:
- Use **Absolute Paths** (starting with `/Users/...`).
- **Do not** add a trailing slash `/` at the end of directory paths.
  - Good: `/Users/name/gamess`
  - Bad: `/Users/name/gamess/`

## Building the App (.app)

If you want to package GmsOne as a standalone macOS application using [`py2app`](https://py2app.readthedocs.io/en/latest/), follow these steps. 
This build configuration is optimized for **Intel (x86_64)** architecture.

### Build Commands

Run the following commands in your terminal:

```bash
# Set environment variable to skip internal packaging if necessary
export PY2APP_SKIP_PACKAGING=1

# Build the .app for x86_64 architecture
python3.12 setup.py py2app --arch=x86_64
