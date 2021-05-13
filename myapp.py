import pandas as pd
import numpy as np
from bokeh.io import show
from bokeh.plotting import output_file, save, figure
from bokeh.models import (CategoricalColorMapper, HoverTool, 
						  ColumnDataSource, Panel, 
						  FuncTickFormatter, SingleIntervalTicker, LinearAxis)
from bokeh.models.widgets import (CheckboxGroup, Slider, RangeSlider, 
								  Tabs, CheckboxButtonGroup, 
								  TableColumn, DataTable, Select)
from bokeh.layouts import column, row, WidgetBox
from bokeh.palettes import Category20, Set3
from bokeh.io import curdoc

output_file_name = "histogram_tripDistance_bokeh.html"
# Dictionary with name-number for each month
MONTH_TO_NUMBER = { "January": "01", "February": "02", "March": "03", "April": "04", 
			"May": "05", "June": "06", "July": "07", "August": "08", 
			"September": "09", "October": "10", "November": "11", "December": "12"}   

def get_data(list_of_months):
    months = list_of_months
    dfs_19 = {}
    dfs_20 = {}
    # Read data
    for m in months:
        dfs_19[m] = pd.read_csv(f'./data/df_{m}_19.csv', index_col=0, sep=',',encoding='utf8')
        dfs_20[m] = pd.read_csv(f'./data/df_{m}_20.csv', index_col=0, sep=',',encoding='utf8')       
        # Filter the colums needed
        dfs_19[m] = dfs_19[m].filter(['tpep_pickup_datetime', 'trip_distance'])
        dfs_20[m] = dfs_20[m].filter(['tpep_pickup_datetime','trip_distance'])
        dfs_19[m]['tpep_pickup_datetime'] = pd.to_datetime(dfs_19[m]['tpep_pickup_datetime']) 
        dfs_20[m]['tpep_pickup_datetime'] = pd.to_datetime(dfs_20[m]['tpep_pickup_datetime'])
        # Add column with month name and year
        dfs_19[m]['month'] = dfs_19[m]['tpep_pickup_datetime'].dt.month_name()
        dfs_19[m]['year'] = dfs_19[m]['tpep_pickup_datetime'].dt.year
        dfs_20[m]['month'] = dfs_20[m]['tpep_pickup_datetime'].dt.month_name()
        dfs_20[m]['year'] = dfs_20[m]['tpep_pickup_datetime'].dt.year

        available_years = ["2019", "2020"]

    return dfs_19, dfs_20, available_years


# Function to make plot with histogram
def histogram_taxi(dfs_19, dfs_20, available_years, available_months):

	def make_dataset(year, month_list, range_start = 0, range_end = 31, bin_width = 2):

		# Dataframe to save info
		by_month = pd.DataFrame(columns=['proportion', 'left', 'right', 
									'f_proportion', 'f_interval',
									'name', 'color', 'year'])
		
		range_extent = range_end - range_start
		if year != []:
			# Iterate through each year
			for y in year:
				if y == "2019":
					taxi = dfs_19
					color_palette = Category20[12]
				elif y == "2020": 
					taxi = dfs_20
					color_palette = Set3[12]
					
				# Iterate through the available month
				for i, month_name in enumerate(month_list):
					# Subset to the current month
					subset = taxi[MONTH_TO_NUMBER[month_name]]

					# Create a histogram with 2 minute bins
					arr_hist, edges = np.histogram(subset['trip_distance'], 
												   bins = int(range_extent / bin_width), 
												   range = [range_start, range_end])

					# Normalize the count
					arr_df = pd.DataFrame({'proportion': arr_hist * 100/ np.sum(arr_hist), 'left': edges[:-1], 'right': edges[1:] })

					# Message to show in the hoverTool 
					arr_df['f_proportion'] = ['%0.2f' % proportion + '%' for proportion in arr_df['proportion']]

					# Message to show in the hoverTool 
					arr_df['f_interval'] = ['%d to %d miles' % (left, right) for left, right in zip(arr_df['left'], arr_df['right'])]

					# Month label
					arr_df['name'] = month_name

					# Year label
					arr_df['year'] = int(y)					

					# Color each bar month differently
					arr_df['color'] = color_palette[i]

					# Add to the final dataframe
					by_month = by_month.append(arr_df)

		return ColumnDataSource(by_month)

	def style(p):
		# Title 
		p.title.align = 'center'
		p.title.text_font_size = '20pt'
		p.title.text_font = 'serif'

		# Axis titles
		p.xaxis.axis_label_text_font_size = '14pt'
		p.xaxis.axis_label_text_font_style = 'bold'
		p.yaxis.axis_label_text_font_size = '14pt'
		p.yaxis.axis_label_text_font_style = 'bold'

		# Tick labels
		p.xaxis.major_label_text_font_size = '12pt'
		p.yaxis.major_label_text_font_size = '12pt'

		return p
	
	def make_plot(src):
		# Blank plot
		p = figure(plot_width = 650, plot_height = 500, 
				  title = 'Histogram of trip distance by month',
				  x_axis_label = 'Trip distance(miles)', y_axis_label = 'Proportion(%)')

		# Create histogram
		p.quad(source = src, bottom = 0, top = 'proportion', left = 'left', right = 'right',
			   color = 'color', fill_alpha = 0.5, hover_fill_color = 'color',
			   hover_fill_alpha = 0.8, line_color = 'black')

		# Create Hover Tool
		hover = HoverTool(tooltips=[('Color', '$swatch:color'),
									('Details', '@name @year. From @f_interval'),
									('Value', '@f_proportion')], 
						  mode='vline')

		p.add_tools(hover)

		# Styling
		p = style(p)

		return p
	
	
	def update(attr, old, new):
		# Update year and month labels
		year_to_plot = [year_selection.labels[i] for i in year_selection.active]
		months_to_plot = [month_selection.labels[i] for i in month_selection.active]
		# Update src
		new_src = make_dataset(year_to_plot, months_to_plot,
							   bin_width = binwidth_select.value)							   
		
		src.data.update(new_src.data)

	# Create widget and callbacks
	year_selection = CheckboxGroup(labels = available_years, 
								   active = [0, 1])
	year_selection.on_change('active', update)
		
	month_selection = CheckboxGroup(labels = available_months, 
									active = [0, 1])
	month_selection.on_change('active', update)
	
	binwidth_select = Slider(start = 1, end = 10, 
						 step = 1, value = 2,
						 title = 'Distance Width (miles)')
	binwidth_select.on_change('value', update)
	
	# Initial year and month and data source
	initial_years = [year_selection.labels[i] for i in year_selection.active]
	initial_months = [month_selection.labels[i] for i in month_selection.active]

	src = make_dataset(initial_years, initial_months,
					   bin_width = binwidth_select.value)

	p = make_plot(src)
	
	# Put controls in a single element
	controls = WidgetBox(year_selection, month_selection, binwidth_select)
	
	# Create a row layout
	layout = row(controls, p)

	return layout

def histogram_tripDistance_bokeh(MONTH_TO_NUMBER):
    # Read data into dataframes
    dfs_19, dfs_20, available_years = get_data(list(MONTH_TO_NUMBER.values()))                                             

    # Create histogram
    layout = histogram_taxi(dfs_19, dfs_20, available_years, list(MONTH_TO_NUMBER.keys()))

    # Put the layout in the current document for display
    curdoc().add_root(layout)

if __name__ == "__main__":
    histogram_tripDistance_bokeh(MONTH_TO_NUMBER)
