# Python Environment Setup — Organizational Brain

## Prerequisites

* Anaconda or Miniconda must be installed.
* A `requirements.txt` file must exist inside the `data-science` directory.

## Setup Instructions

### 1. Open the Terminal

Open your terminal in the following project directory:

```text
brain-co\data-science\
```

**Important:** Make sure the terminal is opened inside the `data-science` directory before executing the following commands. The installation command requires `requirements.txt` to be available in the current working directory.

### 2. Create the Conda Environment

```bash
conda create -n brain_co python=3.11 -y
```

This command creates a Conda environment named `brain_co` using Python 3.11.

### 3. Activate the Environment

```bash
conda activate brain_co
```

This activates the `brain_co` environment so that all subsequent package installations take place inside it.

### 4. Install Dependencies

```bash
pip install -r requirements.txt
```

This command installs all Python libraries and dependencies specified in `requirements.txt`.

### 5. Verify the Python Version

```bash
python --version
```

Expected output:

```text
Python 3.11.x
```

### 6. Verify the Installed Environment

```bash
conda env list
```

Make sure `brain_co` appears in the list of available Conda environments.

## Important Notes

* Always activate the `brain_co` environment before running project scripts.
* Run the installation command from the directory containing `requirements.txt`.
* If the `brain_co` environment already exists, activate it instead of creating it again.
* If dependency installation fails, review the error message and resolve any compatibility issues before retrying.
* Package installation may take some time because some dependencies, such as PyTorch and Sentence Transformers, are relatively large.

## Quick Setup

Run the following commands in the terminal opened inside `brain-co\data-science\`:

```bash
conda create -n brain_co python=3.11 -y
conda activate brain_co
pip install -r requirements.txt
```

## Project Structure

Ensure the directory structure looks like this:

```text
brain-co/
└── data-science/
    ├── setup.md
    └── requirements.txt
```
