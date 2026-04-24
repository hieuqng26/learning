import os
import sys
import matplotlib.pyplot as plt
import matplotlib.ticker
from project.logger import get_logger

matplotlib.use('Agg')

logger = get_logger(__name__)

def print_on_console(line):
    logger.info(line)
    sys.stdout.flush()

def get_times(output):
    print_on_console("Get times from the log file:")
    logfile = open(output)
    for line in logfile.readlines():
        if "ValuationEngine completed" in line:
            times = line.split(":")[-1].strip().split(",")
            for time in times:
                print_on_console("\t" + time.split()[0] + ": " + time.split()[1])

class XVAPricerChart:
    def __init__(self):
        self.ax = None
        self.plot_name = ""
    def setup_plot(self, filename):
        self.fig = plt.figure(figsize=plt.figaspect(0.4))
        self.ax = self.fig.add_subplot(111)
        self.plot_name = "mpl_" + filename
    def plot(self, filename, colIdxTime, colIdxVal, color, label, offset=1, marker='', linestyle='-'):
        self.ax.plot(self.get_output_data_from_column(filename, colIdxTime, offset),
                     self.get_output_data_from_column(filename, colIdxVal, offset),
                     linewidth=2,
                     linestyle=linestyle,
                     color=color,
                     label=label,
                     marker=marker)
    def plot_line(self, xvals, yvals, color, label):
        self.ax.plot(xvals, yvals, color=color, label=label, linewidth=2)
    def decorate_plot(self, title, ylabel="Exposure", xlabel="Time / Years", legend_loc="upper right", y_format_as_int = True, display_grid = False):
        self.ax.set_title(title)
        self.ax.set_xlabel(xlabel)
        self.ax.set_ylabel(ylabel)
        self.ax.legend(loc=legend_loc, shadow=True)
        if y_format_as_int:
            self.ax.get_yaxis().set_major_formatter(
                matplotlib.ticker.FuncFormatter(lambda x, p: format(int(x), ',')))
        if display_grid:
            self.ax.grid()
    def get_output_data_from_column(self, csv_name, colidx, offset=1):
        f = open(os.path.join(os.path.join(os.getcwd(), "Output"), csv_name))
        data = []
        for line in f:
            if colidx < len(line.split(',')):
                data.append(line.split(',')[colidx])
            else:
                data.append("Error")
        return [float(i) for i in data[offset:]]
    def save_plot_to_file(self, subdir="Output"):
        file = os.path.join(subdir, self.plot_name + ".pdf")
        plt.savefig(file)
        print_on_console("Saving plot...." + file)
        plt.close()
