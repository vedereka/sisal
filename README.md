# sisal
Scripts used to QC the SISAL workbooks, upload them to the db, query and plot the database.
Created by Laia Comas Bru in February 2021.

# README

## `/db_uploads/`

`Upload_workbooks.py`
Script uploads workbook to the database. This is executed from the command line as follows:
* python Upload_workbooks.py input.xlsx

`Example_upload_SISAL_agemodels.R`
Script showing an example on how to upload the SISAL chronology and the date_used fields to the database.

`Upload_SISAL_agemodels.R`
Script with the functions needed to run `/DB_uploads/Example_upload_SISAL_agemodels.R`

`SISAL - documentation for database managers.pdf` Documentation for db manager 

---

## `/sisal_wokam_plot/`

`map_sites_count_labels.R`
Script to produce Figure X in Baker et al., 2021 (ESR accepted). Output saved in `/SISAL_sites_wokam_plot/output/map_sites_count_labels_plot.pdf`

`map_sites_versions.R`
Scripts to produce Figure 2 in Comas-Bru et al. 2020 (ESSD; https://doi.org/10.5194/essd-12-2579-2020). Output is saved in `/SISAL_sites_wokam_plot/output/`

`/input/wokam/`
World Karst Aquifer Map shp data file from Goldscheider, N., Chen, Z., Auler, A.S. et al. Global distribution of carbonate rocks and karst water resources. Hydrogeol J 28, 1661–1677 (2020). https://doi.org/10.1007/s10040-020-02139-5

`/input/ne_110m_land/`
Coastal shp data file from http://www.naturalearthdata.com/downloads/110m-physical-vectors/

---

## `/sisal_regional_map_resolution/`

`sisalv2_map_resolution_region.R`
Script to create regional maps with the location of SISAL sites and the number of entities per site (with the World Karst Aquifer map in the background) as well as the “resolution map” for all the sisal entities in that region.

`/input/wokam/` World Karst Aquifer Map shp data file from Goldscheider, N., Chen, Z., Auler, A.S. et al. Global distribution of carbonate rocks and karst water resources. Hydrogeol J 28, 1661–1677 (2020). https://doi.org/10.1007/s10040-020-02139-5 

`/input/ne_110m_land/` Coastal shp data file from http://www.naturalearthdata.com/downloads/110m-physical-vectors/ 

---

## `/sisalv2_example_codes/`

SQL, Matlab, Julia, Python and R scripts to access the latest version of the database. These are also available http://dx.doi.org/10.17864/1947.256

---

## `/sisalv2_paper/`

Scripts used to either produce figures or extract information used in Comas-Bru et al., 2020 (ESSD; https://doi.org/10.5194/essd-12-2579-2020).

`sisalv2_compare_versions.R`
Script to extract the information used to create Table 4 

`sisalv2_regional_coverage_numbers.R`
Script to obtain numbers in Table 6

`sisalv2_uncert_dating_age.R`
Scripot to produce Figure 6

`sisalv2_coverage_period_text.R`
Script used to extract the numbers mentioned at the end of the conclusions' section

---

## `/wb_QC/`

`wb_check.py`
Version-controlled script used by SISAL regional coordinators to quality check the submitted workbooks.  This is executed from the command line as follows: * python wb_checkv12.py input.xlsx

`plot_agemodels_hiatus`
Version-controlled scripts used by SISAL regional coordinators to quality check the submitted workbooks.
Script plot agemodels and their hiatuses from the workbook. The script is to be run in R, changing the path to the input workbook file. PDFs will be generated in the workspace.

`README_instructions.txt`
Instructions to run `wb_check.py` and `plot_agemodels_hiatus`

`SISAL_workbook.xlsx`
Latest version of the SISAL workbook.

`decimalisation.xls`
Excel document to automatically convert geographical coordinates from decimal to minutes (and viceversa).

`Atomic-Activity-deltaU Calculator.xlsx`
Excel document to automatically convert ratios to activities. 

`SISAL_v2_QC_details.pdf` Details of automatic and manual checks 

---

## `Additional documents for wb_QC`:

- The workbook used to submit data to SISAL and the codes for its quality assessment are also available
at https://doi.org/10.5281/zenodo.3631403 (Atsawawaranunt and Comas-Bru, 2020; scripts licensed by the right holder(s) under a Creative Commons Attribution 4.0 International.).

- The workbook is also available as a supplementary document of Comas-Bru and Harrison (2019) under a Creative
Commons Attribution 4.0 International license.

- The codes to assess the dating table in SISALv2 are available at https://github.com/jensfohlmeister/QC_SISALv2_dating_metadata (last access: 23 July 2020; licensed under a
GPL-3 license) and https://doi.org/10.5281/zenodo.3631443 (Comas-Bru et al., 2020b; licensed under a Creative Commons Attribution 4.0 License). 

- Details on the quality control assessments are available in the Supplement of Comas-Bru et al., 2020.(ESSD; https://doi.org/10.5194/essd-12-2579-2020).

---

## `REFERENCES`

These scripts work with the latest version of the SISAL database:

Comas-Bru, Laia, Atsawawaranunt, Kamolphat, Harrison, Sandy and SISAL working group members (2020): SISAL (Speleothem Isotopes Synthesis and AnaLysis Working Group) database version 2.0. University of Reading. Dataset. http://dx.doi.org/10.17864/1947.256

Comas-Bru, L., Rehfeld, K., Roesch, C., Amirnezhad-Mozhdehi, S., Harrison, S. P., Atsawawaranunt, K., Ahmad, S. M., Brahim, Y. A., Baker, A., Bosomworth, M., Breitenbach, S. F. M., Burstyn, Y., Columbu, A., Deininger, M., Demény, A., Dixon, B., Fohlmeister, J., Hatvani, I. G., Hu, J., Kaushal, N., Kern, Z., Labuhn, I., Lechleitner, F. A., Lorrey, A., Martrat, B., Novello, V. F., Oster, J., Pérez-Mejías, C., Scholz, D., Scroxton, N., Sinha, N., Ward, B. M., Warken, S., Zhang, H., and SISAL Working Group members: SISALv2: a comprehensive speleothem isotope database with multiple age–depth models, Earth Syst. Sci. Data, 12, 2579–2606, https://doi.org/10.5194/essd-12-2579-2020, 2020. 

---
