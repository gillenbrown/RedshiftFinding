from PhotoZ import SExtractor
from PhotoZ import functions
from PhotoZ import global_paths
from PhotoZ import read_in_catalogs
from PhotoZ import config_data
import cPickle


# Tell the program where to start
# 0: will run everything. Starts with doing SExtractor in the images in the directory specified.
# 1: Starts by reading in catalogs, turning the different catalogs into Cluster objects
# 2: Starts by reading in saved Cluster objects from the specified directory.
# 3: Starts by reading in saved Cluster list after it has finished, so they all have redshifts. There is still the
#       correction to be done.
# note: selecting a lower number will still run everything after it. You may want to start at a later location, for
# example, if you've already read in catalogs and don't want to waste time doing it again. The code is smart enough to
# save it's progress after each step, so you don't need to worry about that.
START_WITH = 1

# TODO: run images through astrometry.net to correct astrometry.

# TODO: see if the color mag plot can be improved by chaning the way the colorbar is created. Rather than giving it its
# own axis, I would like it to steal from the other axis instead. That looks possible, so see if it works.

# initialize the resources file if it doesn't exist already.
# try:
#     open(global_paths.resources, "r")
# except IOError:
#     print "making new resources file"
#     resources = open(global_paths.resources, "w")
#     cPickle.dump(dict(), resources, -1)
#     resources.close()

if START_WITH == 0:
    print "Starting SExtractor\n"
    # Find all images in the desired directory. Will have a list of file paths.
    image_list = functions.find_all_objects(global_paths.images_directory, [".fits"], [])

    SExtractor.sextractor_main(image_list)

    print "\nDone with SExtractor\n"

if START_WITH <= 1:
    print "\nStarted reading catalogs."
    cluster_list = read_in_catalogs.read_sex_catalogs()

    # Do color calculations
    for c in cluster_list:
        c.calculate_color()

    # save cluster list to disk
    pickle_file1 = open(global_paths.pickle_file, 'w')
    cPickle.dump(cluster_list, pickle_file1, -1)
    pickle_file1.close()

    print "\nDone reading catalogs\n"


if START_WITH == 2:
    # read in cluster objects
    pickle_file2 = open(global_paths.pickle_file, 'r')
    cluster_list = cPickle.load(pickle_file2)
    pickle_file2.close()

if START_WITH <= 2:
    print "\nStarting redshift fitting.\n"

    # find the red sequence redshifts
    for c in cluster_list:
        for color in config_data.fitted_colors:
            bluer_color, redder_color = color.split("-")
            if bluer_color in c.bands and redder_color in c.bands:
                c.fit_z(color, plot_figures=True)

    # save cluster list to disk
    pickle_file3 = open(global_paths.finished_pickle_file, 'w')
    cPickle.dump(cluster_list, pickle_file3, -1)
    pickle_file3.close()

    print "\nDone fitting.\n"


if START_WITH == 3:
    cluster_list = cPickle.load(open(global_paths.finished_pickle_file, 'r'))

# fit the corrections
functions.fit_corrections(cluster_list, read_in=True, plot=True)
#
# write results to a file
functions.write_results(cluster_list)

# TODO: look at clusters that calibration doens't work for. Use the crossID thing in SDSS to see if there really
# aren't stars there.



# TODO: make a function to calibrate catalogs to SDSS, rather than just starting from images. Can base it off of
# existing calibration function