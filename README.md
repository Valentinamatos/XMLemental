# XMLemental

A project to swap XML layers by name into a designated position.

## Quick Install

1. **Download and install Miniconda**

   Follow the instructions [here](https://docs.anaconda.com/miniconda/) to download and install Miniconda.

2. **Create and activate an environment to run your codes**

    Open your terminal or command prompt and run the following commands:

    ```sh
    conda create -n XMLemental python=3.9.19
    conda activate XMLemental
    ```

3. **Install XMLemental**

    Install the XMLemental package using pip:

    ```sh
    pip install -e git+https://github.com/Valentinamatos/XMLemental.git#egg=xml-layer-swapper
    ```
    *Note: You might need to install Git from the following [link](https://git-scm.com/downloads/win) to be able to run the pip install command. After installing, restart your IDE.

## Dependencies

This package automatically installs the following dependencies:
- xmltodict
- glob2