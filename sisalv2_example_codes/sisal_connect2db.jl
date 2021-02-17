################################################################################
#
# Put all SISALv2 csv files into the folder of this Julia file.
# Then this program is printing records from a certain area, specified by
# lat_min, lat_max, lon_min and lon_max, covering some interval between
# two time points xx and yy (defined at lines 60-67)
#
# Attention: at least two U-Th ages must exist in the specified period
# Attention, no 'stacks' will be found and plotted
#################################################################################

# The following 6 lines can be put into comment style, after your your first run of this program
using Pkg
Pkg.add("CSV")
Pkg.add("DataFrames")
Pkg.add("DataFramesMeta")
Pkg.add("Infiltrator")      # shall enable a matlab like 'keyboard' comand: @infiltrate
Pkg.add("Plots")

using CSV, Infiltrator, Plots, Plots.Measures
using DataFrames, DataFramesMeta, Logging, DelimitedFiles

################################################################################
# reading data files
################################################################################

cd(@__DIR__) # to change to path of this *.jl file
#cd("SISALv2_csv") # to change the path relative to where it was before
entity = CSV.read("entity.csv",missingstring = "NULL")
gap = CSV.read("gap.csv",types=(Int64,String)) # reads CSV file relative to where the julia is running
            # Surprisingly this is not the same, where your *.jl file is located
composite_link_entity = CSV.read("composite_link_entity.csv")
d13C = CSV.read("d13C.csv",missingstring = "NULL")
d18O = CSV.read("d18O.csv",missingstring = "NULL")
dating_lamina = CSV.read("dating_lamina.csv")
dating = CSV.read("dating.csv",missingstring = "NULL",copycols=true)#treating all NULL as missing values, enabling to change DataFrameEntries
names!(dating,Symbol.([:dating_id,
    :entity_id,:date_type,:depth_dating,:dating_thickness,:lab_num,:material_dated,
    :min_weight,:max_weight,:uncorr_age,:uncorr_age_uncert_pos,:uncorr_age_uncert_neg,
    :C14_correction,:calib_used,:date_used,:c238U_content,:c238U_uncertainty,
    :c232Th_content,:c232Th_uncertainty,:c230Th_content,:c230Th_uncertainty,
    :a230Th_232Th_ratio,:a230Th_232Th_ratio_uncertainty,:a230Th_238U_activity,
    :a230Th_238U_activity_uncertainty,:a234U_238U_activity,:a234U_238U_activity_uncertainty,
    :ini_230Th_232Th_ratio,:ini_230Th_232Th_ratio_uncertainty,:decay_constant,
    :corr_age,:corr_age_uncert_pos,:corr_age_uncert_neg,:date_used_lin_interp,
    :date_used_lin_reg, :date_used_Bchron,:date_used_Bacon,:date_used_OxCal,
    :date_used_copRa, :date_used_StalAge]))    # it is necessary to rename those lines with a number on first position
    # it is necessary to rename those lines with a number on first position
entity_link_reference = CSV.read("entity_link_reference.csv")
hiatus = CSV.read("hiatus.csv")
notes = CSV.read("notes.csv")
original_chronology = CSV.read("original_chronology.csv")
reference = CSV.read("reference.csv")
sample = CSV.read("sample.csv")
sisal_chronology = CSV.read("sisal_chronology.csv")
site = CSV.read("site.csv")
cd(@__DIR__)
################################################################################

xx = 6000   #minimum age [a] of required period
yy = 8000  #maximum age of [a] required period

# coordinates for required region
lat_min = 0
lat_max = 30
lon_min = -150
lon_max = -45

dating = dropmissing(dating, :decay_constant) # removes all events and 14C data
dating = dropmissing(dating, :corr_age) # removes dirty samples

################################################################################
### find stalagmites in the required region
################################################################################
stal1 = sort(unique(dating,:entity_id),:entity_id)
entity1 = entity[findall(in(stal1[!,:entity_id]),entity.entity_id),[:site_id,:entity_id,:entity_name,:contact,:data_DOI_URL]]
site1 = site[findall(in(entity1[!,:site_id]),site.site_id),[:site_id, :site_name, :latitude, :longitude, :elevation]]

# find different stalagmites in 'dating' data frame
i = findall(x->x!=0,diff(stal1.entity_id)).+1
i1= zeros(length(i)+2)
i1[1]=1
i1[2:length(i)+1] = i
i1[length(i)+2] = length(stal1.entity_id)+1
i1=convert(Vector{Int},i1)      # i1 provides first index of a stal (except of i1[length(i1)] )

global dating0 = DataFrame(dating)
deleterows!(dating0,1:size(dating0,1))
for i = 1:length(i1)-1
    idx = findall(x -> x == entity1.site_id[i], site1.site_id)[1]
    if lat_min <= site1.latitude[idx] <= lat_max && lon_min <= site1.longitude[idx] <= lon_max
        idx2 = findall(x -> x == site1.site_id[idx],entity1.site_id)
        for mm =1:length(idx2)
            idx3 = findall(x -> x == entity1.entity_id[idx2[mm]], dating.entity_id)
            for mmm = 1:length(idx3)
                push!(dating0,dating[idx3[mmm],:])
            end
        end
    end
end
dating0 = sort(unique(dating0,:dating_id),:dating_id)
################################################################################

# find different stalagmites in 'dating0' data frame
i = findall(x->x!=0,diff(dating0.entity_id)).+1
i1= zeros(length(i)+2)
i1[1]=1
i1[2:length(i)+1] = i
i1[length(i)+2] = length(dating0.entity_id)+1
i1=convert(Vector{Int},i1)      # i1 provides first index of a stal (except of i1[length(i1)] )

################################################################################
### Find all stalagmites, which have at least 2 U-Th ages within the
### required period
################################################################################
global dating1 = DataFrame()
for m = 1:length(i1)-1
    global idx = 0
    count = 0
    for n = i1[m]:i1[m+1]-1
        if xx <=dating0.corr_age[n] <= yy
            count = count + 1
        end
    end
    if count >=2
        global idx = dating0.entity_id[i1[m]]
    end
    append!(dating1,dating0[dating0.entity_id.==idx,:])
end
################################################################################

sample1 = sample[findall(in(dating1[!,:entity_id]),sample.entity_id),:]

sort!(sample1,(:entity_id, :sample_id))
# find different stalagmites of sample1
i = findall(x->x!=0,diff(sample1.entity_id)).+1
i2= zeros(length(i)+2)
i2[1]=1
i2[2:length(i)+1] = i
i2[length(i)+2] = length(sample1.entity_id)+1
i2=convert(Vector{Int},i2)      # i2 provides first index of a stal (except of i2[length(i2)] )
#@infiltrate
################################################################################
### extracting isotope data for all identified speleothems
################################################################################
for m = 1:length(i2)-1

    ### info for plot title ####################################################
    idx = findall(x -> x == sample1.entity_id[i2[m]],entity.entity_id)
    idx1 = findall(x -> x == entity.site_id[idx[1]],site.site_id)
    sample_id_dummy = sample1.sample_id[i2[m]:i2[m+1]-1]
    ############################################################################
    println(m," extracting data for stalagmite ",entity.entity_name[idx][1])

    ### extract d18O, d13C and age data ########################################
    d18O_dummy = zeros(length(sample_id_dummy))
    age_dummy = zeros(length(sample_id_dummy))
    d13C_dummy = zeros(length(sample_id_dummy))

    for n = 1:length(sample_id_dummy)
        dummy1 = findall(x-> x.==sample_id_dummy[n],d18O.sample_id)
        if isempty(dummy1)
        else
            d18O_dummy[n] = d18O[d18O.sample_id .== sample_id_dummy[n],:d18O_measurement][1]
        end
        dummy = findall(x-> x.==sample_id_dummy[n],d13C.sample_id)
        if isempty(dummy)
        else
            d13C_dummy[n] = d13C[d13C.sample_id .== sample_id_dummy[n],:d13C_measurement][1]
        end
        dummy2 = findall(x-> x.==sample_id_dummy[n],original_chronology.sample_id)
        if isempty(dummy2)
        else
            age_dummy[n] = original_chronology[original_chronology.sample_id .== sample_id_dummy[n],:interp_age][1]
        end
    end
    age_dummy = age_dummy[d18O_dummy.!=0.0]    # removing those wrongly inserted data in SISAL
    d13C_dummy = d13C_dummy[d18O_dummy.!=0.0]    # removing those wrongly inserted data in SISAL
    d18O_dummy = d18O_dummy[d18O_dummy.!=0.0]    # removing those wrongly inserted data in SISAL

    ############################################################################

    ### sort in time-increasing order ##########################################
    p = sortperm(age_dummy)
    d18O_dummy = d18O_dummy[p]
    d13C_dummy = d13C_dummy[p]
    age_dummy = age_dummy[p]

    d18O_dummy=d18O_dummy[xx .< age_dummy .< yy]
    d13C_dummy=d13C_dummy[xx .< age_dummy .< yy]
    age_dummy=age_dummy[xx .< age_dummy .< yy]
    if isempty(age_dummy)
    else
        ### for figures: fix x-axis range for plot
        x_low = floor(minimum(age_dummy)./1000).*1000
        x_high = ceil(maximum(age_dummy)./1000).*1000
        ############################################################################
        p2 = plot( age_dummy, d18O_dummy,
            legend = false, title = "$(sample1.entity_id[i2[m]]), $(entity.entity_name[idx][1]), $(site.site_name[idx1][1])
            lat = $(site.latitude[idx1][1]),lon = $(site.longitude[idx1][1])",
            titlefontsize = 6,size=[600,240], seriestype=:line,
            xlabel = "time [a BP]", ylabel= "d18O [permil VPDB]",
            xflip = true, linecolor = :blue,
            yguidefont = font(:blue),right_margin = 20mm,
            ytickfont = font(:blue),framestyle = :box,
            xlims = (x_low,x_high))
        p2 = plot!(twinx(), age_dummy, d13C_dummy,
            seriestype=:line, label = "d13C",
            legend = false, ylabel= "d13C [permil VPDB]",
            linecolor = :red, xflip = true,
            yguidefont = font(:red),ytickfont = font(:red),
            xlims = (x_low,x_high))#:best, legendfont = font(2) ))

            ############################################################################

        plot(p2,size=[600,240])
        savefig("$(m)$(entity.entity_name[idx][1]).pdf")
    end

end
