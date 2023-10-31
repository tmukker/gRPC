import matplotlib.pyplot as plt
import numpy as np

# Data
operations = [
    "Search by ID",
    "Search by Key-Value Pair",
    "Search within a Range",
    "Calculate Percentile",
    "Update Value"
]

average_response_times = [0.02211019992828369, 0.023590428829193114, 0.0003346061706542969, 0.022787318229675294, 0.04352011442184448]
standard_deviations = [0.01898577041036138, 0.02197730034645888, 0.00017766412759579332, 0.02081288973158473, 0.027855735653561694]

# Set the width of the bars
bar_width = 0.35

# Create an array of indices for the x-axis
x = np.arange(len(operations))

# Create subplots
fig, ax = plt.subplots()

# Plot average response times
bar1 = ax.bar(x - bar_width/2, average_response_times, bar_width, color='b', alpha=0.5, label='Average Response Time')

# Plot standard deviations
bar2 = ax.bar(x + bar_width/2, standard_deviations, bar_width, color='r', alpha=0.5, label='Standard Deviation')

# Set the y-axis label
ax.set_ylabel('Time (seconds)')
ax.set_xlabel('Operations')

# Set the x-axis ticks and labels
ax.set_xticks(x)
ax.set_xticklabels(operations, rotation=15)

# Add a legend
ax.legend(loc='upper left')

# Add text annotations on top of the bars
for bar, data in zip(bar1 + bar2, average_response_times + standard_deviations):
    ax.annotate(f'{data:.4f}', xy=(bar.get_x() + bar.get_width() / 2, data), xytext=(0, 3),
                textcoords='offset points', ha='center', fontsize=9)

# Title
plt.title('Average Response Time and Standard Deviation for Different Operations')

# Display the plot
plt.tight_layout()
plt.show()