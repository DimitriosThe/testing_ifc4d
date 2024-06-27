import pandas as pd
import ifcopenshell
import ifcopenshell.util.date
import ifcopenshell.util.element
import ifc4d.csv4d2ifc as csv4d2ifc
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime
import plotly.express as px



# Load the IFC file
ifc_file_path = "E:\SOFTWARE\IFC OPENSHELL\VSCode\IFCOPENSHELL\PRO-153-BTD-3DM-SD-STR-R23_detached.ifc"
#model = ifcopenshell.open(r"E:\SOFTWARE\IFC OPENSHELL\VSCode\IFCOPENSHELL\PRO-153-BTD-3DM-SD-STR-R23_detached.ifc")

ifc_file = ifcopenshell.open(ifc_file_path)

# Define the CSV file path
csv_filename = "E:\SOFTWARE\IFC OPENSHELL\VSCode\IFCOPENSHELL\Ifc4D\Testing_4D_-Copy_rel.csv" #construction_schedule.csv"#Testing_4D_-Copy_1.csv"
# Create tasks in the IFC file
#Hierarchy, Identification ,Name ,ScheduleStart ,ScheduleFinish ,ScheduleDuration ,ActualStart ,ActualFinish ,ActualDuration ,Relationships

# Let's create a new calendar.
calendar = ifcopenshell.api.run("sequence.add_work_calendar", ifc_file, name="5 Day Week")

# Let's start defining the times that we work during the week.
work_time = ifcopenshell.api.run("sequence.add_work_time", ifc_file,work_calendar=calendar, time_type="WorkingTimes")

# We create a weekly recurrence
pattern = ifcopenshell.api.run("sequence.assign_recurrence_pattern", ifc_file,parent=work_time, recurrence_type="WEEKLY")

# State that we work from weekdays 1 to 5 (i.e. Monday to Friday), 9am to 5pm
ifcopenshell.api.run("sequence.edit_recurrence_pattern", ifc_file,recurrence_pattern=pattern, attributes={"WeekdayComponent": [1, 2, 3, 4, 5]})
ifcopenshell.api.run("sequence.add_time_period", ifc_file,recurrence_pattern=pattern, start_time="08:00", end_time="16:00")

i =1
work_plan = ifcopenshell.api.run("sequence.add_work_plan", ifc_file, name="Construction")
schedule = ifcopenshell.api.run("sequence.add_work_schedule", ifc_file,name="Construction Schedule A", work_plan=work_plan)

# Load the csv file
csvLoader =  csv4d2ifc.Csv2Ifc()

csvLoader.csv = csv_filename 
# Parse the csv file
csvLoader.parse_csv()

# Parse relationships
#csvLoader.parse_task_rel("Relationships")

# Create the IFC file
sch_file = csvLoader.create_ifc()

# Extract tasks including relationships
tasks = csvLoader.tasks
#print(tasks)
#print()
task_data = []
#print(csvLoader.file.by_type("Ifctask"))
# We cascade the schedule
ifcopenshell.api.run("sequence.cascade_schedule", file = sch_file, task=csvLoader.file.by_type("Ifctask")[0]) #print(csvLoader.file.by_type("Ifctask")[0])
for task in csvLoader.file.by_type("Ifctask"):
    #print(task.TaskTime)
    task_name = task.Name
    task_time = task.TaskTime
    if task_time:
        scheduled_start = task_time.ScheduleStart
        scheduled_finish = task_time.ScheduleFinish
        task_data.append({
            "Name": task_name,
            "Scheduled Start": scheduled_start,
            "Scheduled Finish": scheduled_finish,
        })
#print(task_data)
# Create a data frame with the task data list
df = pd.DataFrame(task_data)
#print(df)
#print()

# Extract dependencies from Relationships and add them to the DataFrame
def get_dependencies(task_name):
    for task in tasks:
        #print(task.keys())
        if task["Task Name"] == task_name:
            return [rel['task_2'] for rel in task["Relationships"] if rel['rel_type'] == 'SS']
    return []

df['Relationships'] = df['Name'].apply(get_dependencies)
print(df)
#print(df.head())"""

#print(df)
#Convert data from string dates to datetime
df["Scheduled Start"] = pd.to_datetime(df["Scheduled Start"], errors='coerce')
df["Scheduled Finish"] = pd.to_datetime(df["Scheduled Finish"], errors='coerce')
#print(df)
# Plot Gant Chart
fig, ax = plt.subplots(figsize = (25,40))

# plot Scheduled dates
"""Set left parameter in ax.barh to row['Scheduled Start']: This positions the bars starting at the correct dates."""
"""df.iloc[::-1] reverses the DataFrame. to show in the plot as in the """
for idx, row in df.iloc[::-1].iterrows():
    ax.barh(row['Name'], (row['Scheduled Finish'] - row['Scheduled Start']).days, left=  row['Scheduled Start'])
    #print(idx, row)
    # Add dependencies as arrows
    #print(row["Relationships"])
    for dep in row["Relationships"]:
        dep_finish = df[df['Name'] == dep]['Scheduled Finish'].values[0]
        dep_finish_pos = df[df['Name'] == dep].index[0]
        print(dep)
        start_x = mdates.date2num(dep_finish)
        start_y = dep_finish_pos
        end_x = mdates.date2num(row['Scheduled Start'])
        end_y = idx

        ax.annotate('', xy=(end_x, end_y), xytext=(start_x, start_y),
                    arrowprops=dict(arrowstyle="->", color='red'))
# Set date format on x-axis
""" This tells Matplotlib to treat the x-axis values as dates."""
ax.xaxis_date()

"""Set the title for the x-axis Values"""
ax.set_xlabel('Scheduled Dates', labelpad = 25)

""" This formats the dates on the x-axis."""
ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))

""" This sets the interval for the date ticks."""
ax.xaxis.set_major_locator(mdates.DayLocator(interval=15))
#ax.xaxis.grid(True, alpha=0.5)

""" This sets the Title of the chart."""
ax.set_title('"As scheduled" activities Gantt chart', pad = 25)

# Add a vertical line for today's date

""" Add a vertical line: Using ax.axvline with today as the position. 
    The color, linewidth, and linestyle parameters are used to customize the appearance of the line. 
    The label parameter is used to add a label for the legend."""
today = datetime.now()
ax.axvline(today, color='red', linewidth=2, linestyle='--', label="Today's Date")
ax.text(x=today, y=0, s=(today), color='red')

# Add horizontal grid lines
"""Add horizontal grid lines: ax.grid(which='both', axis='y', linestyle='--', linewidth=0.5, color='gray') adds horizontal grid lines. The parameters are:
which='both': Apply to both major and minor grid lines.
axis='y': Apply grid lines to the y-axis.
linestyle='--': Dashed line style for the grid.
linewidth=0.5: Width of the grid lines.
color='gray': Color of the grid lines."""
ax.grid(which='both', axis='y', linestyle='--', linewidth=0.5, color='gray')

# Add legend
"""Add legend: plt.legend() to display the legend with the label "Today's Date"."""
plt.legend()

# Rotate date labels for better readability
"""plt.gcf().autofmt_xdate(): This automatically adjusts the date labels to fit better, often rotating them for clarity."""
plt.gcf().autofmt_xdate()  
plt.show()

# Assign the task to a project (adjust based on your IFC structure)
# For example, if tasks are related to an IfcProject object:
#task_object.IsDefinedBy.append(ifc_file.createIfcRelAssignsToControl(RelatingControl=project_object,RelatedObjects=[task_object]))

"""Explanation:
Import mdates: This is essential for date formatting.
Make sure your DataFrame df has the 'Scheduled Start' and 'Scheduled Finish' columns in datetime format. If not, you can convert them using pd.to_datetime."""
"""
# Iterate through all the tasks in the csv file and create "IfcTask","IfcTaskTime" entities
for task in tasks:
    i+=1
    if task["ScheduleStart"]==None or task["ScheduleDuration"]==None:break
    print(task["Name"])
    print(task["ScheduleStart"])
    task_object = ifcopenshell.api.run("sequence.add_task", ifc_file,work_schedule=schedule, name=task["Name"], identification=task["Identification"],predefined_type="CONSTRUCTION")
    time_object = ifcopenshell.api.run("sequence.add_task_time", ifc_file, task=task_object)
    print(i)
    if task["ScheduleStart"]==None or task["ScheduleDuration"]==None: 
        break
    else:task_time_object = ifcopenshell.api.run(
        "sequence.edit_task_time",
        ifc_file,
        task_time=time_object,
        attributes={"ScheduleStart": (task["ScheduleStart"]), "ScheduleDuration": (task["ScheduleDuration"])
                    }
        )



# Save the modified IFC file
#ifc_file.save("modified_example.ifc")

# Print a success message
print(f"Tasks from {csv_file_path} were successfully created in modified_example.ifc")
"""