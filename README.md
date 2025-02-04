# openFoamEvaluation
openFoamEvaluation : Python script for evaluating OpenFOAM simulation

---

## Description
This Python script evaluates OpenFOAM simulations by analyzing the log file generated during computations. The script automatically detects whether a simulation is steady-state or transient. For transient simulations, it plots Courant number evaluations. By default, the script plots time step continuity errors and identifies available variables for residual plotting.

---

## Features
- Automatic detection of steady-state or transient simulations
- Time step continuity error plotting
- Automatic detection of all available variables for residual plotting
- Courant number evaluation for transient cases
- Graph smoothing with optional method choices
- Interactive and auto-saved graph
- CSV table generation from evaluated data

---

## Important Notes
To generate a log file for evaluation, use the `tee` command in Terminal or WSL:
```bash
$ interFoam | tee log.txt
```
For Windows users, please consult additional references for equivalent commands in Command Prompt or PowerShell.

---

## Prerequisites
Install the required dependencies with the following command:
```bash
$ pip install matplotlib numpy scipy statsmodels
```
If the dependencies are already installed, you can skip this step.

---

## Usage

### Command Prompt, Terminal, or Python Console
To evaluate an OpenFOAM simulation log file, use the following command:
```bash
python openFoamEvaluation.py --file logfilename
```
**Arguments:**
- `--file`: Specifies the log file to be analyzed. Replace `logfilename` with the actual name of your log file, e.g., `log.txt`.

### Jupyter Notebook or Google Colab
If running the script in a Jupyter Notebook or Google Colab environment, simply use:
```python
!python openFoamEvaluation.py
```
In this case, no argument is required. The script will prompt you to input the log file name interactively.

---

## Optional Modifications

### Graph Smoothing
Options for data smoothing are:
- `"Lowess"` (default) — uses Locally Weighted Regression method
- `"Gauss"` — applies a 1D Gaussian Filter Kernel method
- `"False"` — no smoothing

To modify this, change the value of `smooth` on line 62 in the script. Example:
```python
smooth = "Gauss"
```

### Customized Residual Variables
To manually specify custom variables for residual plotting, modify the `variables` list on line 302 of the script:
```python
variables = ["alpha.water", "Ux", "Uy", "Uz", "p_rgh", "omega", "k"]
```
