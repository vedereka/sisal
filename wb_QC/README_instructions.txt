Checking workbook manual

This was updated 24th September 2018 by Laia

Download the latest wb_checkvX.py and plot_agemodelvX.R from https://www.dropbox.com/sh/j5mczavd57hol2j/AABKRx-ItA1JqdrGF-pvN4jRa?dl=0

Install python (python 2, perhaps using ANACONDA as default. See https://www.anaconda.com/download/)

Required modules in python (all likely installed with ANACONDA)
1. pandas
2. numpy
3. shutil
4. os
5. sys 

Install RStudio

Required packages in R (the R code installs this automatically just in case):

1. ggplot2
2. xlsx


Set-up; Step 1:
- Create a folder to store all the SISAL files that have been sent to you.
- Keep the python file in this folder.

Set-up; Step 2:

- Within this folder, create a folder called 'Checked'.
The 'Checked' folder will be where the files are moved into if they are checked. 

Set-up; Step3:
- Save the plot_agemodels_hiatus_vX.R file inside th Checked folder


The process to check the workbooks is as follows:

Python file checks the SISAL workbooks. This automatically moves the file to the 'Checked' folder if the workbook passed the checks. Make sure that the excel file is not opened in excel during this process

Step 1: Open Anaconda prompt

Step 2: Move to the folder with the python file and the workbook 

- if, for example, the folder is on your Desktop and is called SISAL, it is likely that you'll need to type the following:
	- cd Desktop/SISAL

Step 3, option 1: execute the python script as follows:

- python wb_checkv11.py SISAL_workbook_input_file_name_v11.xlsx

(make sure that there are no spaces in the file name and that you're using the wb_checkvX.py file that corresponds to that version of the workbook)

Step 3, option 2: execute the python script as follows:

- python wb_checkv11b.py SISAL_workbook_input_file_name.xlsx > log.txt

This option prints the warning into log.txt where you can view later. The text file would be best opened in text editor with no word wrap.

Step 4: if there are no warnings the workbook will automatically move from "~/SISAL" to "~/SISAL/Checked"

Setp 5: Open the corresponding plot_agemodels_hiatus_vX.R file in RStudio and update rows 3 with the name of the workbook.

Step 6: Run the R script. This just plots the age models, and plot of interp_age differences between consecutive depths vs the midpoint between consecutive depths (this plot can be used to identify unidentified hiatuses) and outputs a pdf for each entity present in that workbook. The file will be saved inside the "Checked" folder.

Once the workbook has passed these two checks, email the workbook to sisal@reading.ac.uk

Note (24/09/2018): If running the scripts in the command line produces some warnings from python (which may get in the way of the warnings with regards to the workbooks), you can run script as shown below and this will stop the python warnings from being printed in the command line:
- python -W ignore wb_checkv11b.py SISAL_workbook_input_file_name_v11.xlsx

Note (23/10/2018): If you get weird messages, see the word document in dropbox where the most common errors/problems are listed along with instructions on how to solve them.
 