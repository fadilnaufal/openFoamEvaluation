############################################################################
# openFoamEvaluation.py : Python script for evaluating OpenFOAM simulation #
############################################################################
# Important: use suffix | tee log.txt
# when doing the simulation to produce the log file.

# To use this, execute this line once in Command Prompt or Terminal
# pip install matplotlib numpy scipy statsmodels
# to install the dependencies used in this script.
# Ignore this if they are already installed.













# The rest of the code.

import time
start = time.time()
import argparse
import sys
import re
import csv
import numpy as np
import matplotlib.pyplot as plt

def parse_arguments():
    parser = argparse.ArgumentParser(description="Parse and plot OpenFOAM log file data.")
    parser.add_argument("--file", required=True, help="Path to the OpenFOAM log file")
    return parser.parse_args()

def detect_variables_single_step(log_file):
    variables = set()
    with open(log_file, 'r') as file:
        in_time_step = False
        for line in file:
            # Start scanning after finding the first "Time = ..." marker
            if line.startswith("Time ="):
                if in_time_step:  # Already inside a time step, exit after second marker
                    break
                in_time_step = True
            
            # Look for solver lines
            if in_time_step:
                match = re.search(r"Solving for (\S+),", line)
                if match:
                    variables.add(match.group(1))
    return sorted(variables)

# Options to smooth data plot: "False", "Gauss", or "Lowess"
# "False" -> no smoothing
# "Gauss" -> smoothing using 1D Gaussian Filter Kernel method
# "Lowess" -> smoothing using Locally Weighted Regression (Lowess) method
smooth = "Lowess"

if smooth == "Gauss":
    from scipy.ndimage import gaussian_filter1d
elif smooth == "Lowess":
    from statsmodels.nonparametric.smoothers_lowess import lowess

# option to show plot viewing using matplotlib: True or False
show = True

def parse_log_file(filename):
    with open(filename, 'r') as file:
        lines = file.readlines()

    # initializing variables
    is_transient = False
    time_steps = []
    courant_mean = []
    courant_max = []
    cont_error_local = []
    cont_error_global = []
    cont_error_cumulative = []
    for n in variables:
        globals()[n] = []

    # identifying transient or steady-state simulation
    for line in lines:
        if "Courant" in line:
            is_transient = True
            break

    if is_transient:
        data = ["Time", "mean Courant number", "max Courant number", "local time step continuity error", "global time step continuity error", "cumulative time step contiuinty error"]
    else:
        data = ["Time", "local time step continuity error", "global time step continuity error", "cumulative time step contiuinty error"]

    print(f"\nEvaluating {log_filename}")
    print("Parsing:")
    for item in data:
        print(f"    {item}")
    for item in variables:
        print(f"    {item} Residual")

    # parse data starting from line "Starting time loop"
    start_parsing = False
    for line in lines:
        if "Starting time loop" in line:
            start_parsing = True
            continue

        if not start_parsing:
            continue

        # extracting time steps
        time_match = re.match(r"^Time = ([0-9.e+-]+)", line)
        if time_match:
            time_steps.append(float(time_match.group(1)))

        # extracting Courant numbers (if transient)
        if is_transient:
            if line.startswith("Courant Number"):
                mean_match = re.search(r"mean: ([\d\.e\+\-\d]+)", line)
                max_match = re.search(r"max: ([\d\.e\+\-\d]+)", line)
                if mean_match and max_match:
                    courant_mean.append(abs(float(mean_match.group(1))))
                    courant_max.append(abs(float(max_match.group(1))))

        # extracting time step continuity errors
        cont_match = re.search(r"time step continuity errors : sum local = ([\d\.e\+\-\d]+), global = ([\d\.e\+\-\d]+), cumulative = ([\d\.e\+\-\d]+)", line)
        if cont_match:
            cont_error_local.append(abs(float(cont_match.group(1))))
            cont_error_global.append(abs(float(cont_match.group(2))))
            cont_error_cumulative.append(abs(float(cont_match.group(3))))

        # extracting residuals
        for var in variables:
            res_match = re.search(fr"Solving for {var}, Initial residual = ([\d\.e\+\-\d]+)", line)
            if res_match:
                globals()[var].append(abs(float(res_match.group(1))))

    res = {key: globals()[key] for key in variables}

    error = {
        "is_transient": is_transient,
        "time_steps": time_steps,
        "courant_mean": courant_mean,
        "courant_max": courant_max,
        "cont_error_local": cont_error_local,
        "cont_error_global": cont_error_global,
        "cont_error_cumulative": cont_error_cumulative
    }

    return {**error, **res}

def occurrence_adjustment(data):
    if data["is_transient"]:
        base_data = ["time_steps", "courant_mean", "courant_max", "cont_error_local", "cont_error_global", "cont_error_cumulative"]
    else:
        base_data = ["time_steps", "cont_error_local", "cont_error_global", "cont_error_cumulative"]
    var_data = variables
    global all_data
    all_data = base_data + var_data
    lengths = [len(data[name]) for name in all_data]
    reference_length = lengths[0]

    wrong_length_items = []
    for i, l in enumerate(lengths):
        if l != reference_length:
            wrong_length_items.append({
                "name": all_data[i],
                "index": i,
                "length": l
            })

    for item in wrong_length_items:
        occurrence = item['length'] // reference_length
        index = list(range(occurrence-1, item['length'], occurrence))
        data[item['name']] = [data[item['name']][i] for i in index]

def validate_data(data):
    lengths = [len(data[name]) for name in all_data]
    if len(set(lengths)) > 1:
        raise ValueError(f"Recheck {log_filename}. Mismatch in data lengths:", dict(zip(all_data,lengths)))

# scale of y axis, either "log" or "symlog"
scale = "log"

# smoothing method
if smooth == "Gauss":
    def smooth_data(y, sigma=2):
        return gaussian_filter1d(y, sigma=sigma)
elif smooth == "Lowess":
    def smooth_data(y, frac=0.1):
        x = np.arange(len(y))
        smoothed = lowess(y, x, frac=frac, return_sorted=False)
        return smoothed
else:
    def smooth_data(y):
        return y

def plot_data(data, output_prefix):
    time_steps = data["time_steps"]

    # x axis label
    if data["is_transient"]: label = "Time (s)"
    else: label = "Iteration"

    # plot Courant numbers (if transient)
    if data["is_transient"]:
        plt.figure()
        plt.plot(time_steps, smooth_data(data["courant_mean"]), label="Courant Mean")
        plt.plot(time_steps, smooth_data(data["courant_max"]), label="Courant Max")
        plt.yscale(scale)
        plt.xlabel(label)
        plt.ylabel("Courant Numbers (-)")
        legend = plt.legend(loc='best')
        legend.set_draggable(True)
        plt.tight_layout()
        plt.savefig(f"{output_prefix}_courant.png", dpi=300)
        if show == True: plt.show()

    # plot time step continuity errors
    plt.figure()
    plt.plot(time_steps, smooth_data(data["cont_error_local"]), label="Local Error")
    plt.plot(time_steps, smooth_data(data["cont_error_global"]), label="Global Error")
    plt.plot(time_steps, smooth_data(data["cont_error_cumulative"]), label="Cumulative Error")
    plt.yscale(scale)
    plt.xlabel(label)
    plt.ylabel("Time Step Continuity Errors (-)")
    legend = plt.legend(loc='best')
    legend.set_draggable(True)
    plt.tight_layout()
    plt.savefig(f"{output_prefix}_continuity.png", dpi=300)
    if show == True: plt.show()

    # plot residuals
    plt.figure()
    plt.yscale(scale)
    plt.xlabel(label)
    plt.ylabel("Residuals (-)")
    for var in variables:
        plt.plot(time_steps, smooth_data(data[var]), label=f"{var} Residual")
    legend = plt.legend(loc='best')
    legend.set_draggable(True)
    plt.tight_layout()
    plt.savefig(f"{output_prefix}_residual.png", dpi=300)
    if show == True: plt.show()

# exporting the parsed data to a CSV file
def save_to_csv(data, output_file):
    with open(output_file, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        if data["is_transient"]:
            header = ["Time (s)"]
        else:
            header = ["Iteration"]

        if data["is_transient"]:
            header += ["Courant Mean", "Courant Max"]

        header += ["Local Continuity Error", "Global Continuity Error", "Cumulative Continuity Error"]
        header += variables
        writer.writerow(header)

        for i in range(len(data["time_steps"])):
            row = [data["time_steps"][i]]

            if data["is_transient"]:
                row += [data["courant_mean"][i], data["courant_max"][i]]

            row += [
                data["cont_error_local"][i],
                data["cont_error_global"][i],
                data["cont_error_cumulative"][i]
            ]

            for var in variables:
                row.append(data[var][i])

            writer.writerow(row)

# main script execution
if __name__ == "__main__":
    output_prefix = "output"
    print("\n======================\n| openFoamEvaluation |\n======================")
    print("Python script for evaluating OpenFOAM simulation")

    if len(sys.argv) > 1:
        args = parse_arguments()
        if args.file:
            log_filename = args.file
        else:
            log_filename = input("\nPlease enter the log file name: ")
    else:
        log_filename = input("\nPlease enter the log file name: ")

    try:
        file = open(log_filename, 'r')
        file.close()

        variables = detect_variables_single_step(log_filename)

        # If needed, modify the hardcoded variables for residuals - list of strings.
        # variables = ["alpha.water", "Ux", "Uy", "Uz", "p_rgh", "omega", "k"]

        print("\nThis may take a few minutes. Please wait.")
        try:
            parsed_data = parse_log_file(log_filename)
            occurrence_adjustment(parsed_data)
            validate_data(parsed_data)
            end = time.time()
            plot_data(parsed_data, output_prefix)
            save_to_csv(parsed_data, f"{output_prefix}.csv")
            print("\nFinished evaluating log file.")
            print("Graphs are saved and the data are exported as")
            if parsed_data["is_transient"]: print(f"    {output_prefix}_courant.png")
            print(f"    {output_prefix}_continuity.png")
            print(f"    {output_prefix}_residual.png")
            print(f"    {output_prefix}.csv")
            print(f"\nExecution time = {end - start} s.")
            print("Processes completed successfully.\n")
        except Exception as e:
            print(f"\nError: {e}\n")

    except:
        print(f"\nError: The file '{log_filename}' was not found. Exiting...\n")
        quit()
