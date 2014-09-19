from PhotoZ.files import functions
from PhotoZ.files import global_paths
from PhotoZ.files import catalog
from PhotoZ.files import Cluster
from PhotoZ.files import other_classes
from PhotoZ.files import sdss_calibration
import re

def read_sex_catalogs():
    # TODO: document

    # First find all catalogs
    catalog_path_list = functions.find_all_objects(global_paths.catalogs_look_directory, [".cat", ".dat"], [])

    # Initialize an empty list of clusters
    cluster_list = []

    for cat in catalog_path_list:
        # Match the catalog to a cluster if there is one already in the list with the same name. If not,
        # make a new cluster with that name.
        cat_filename = cat.split("/")[-1]
        cluster_name = functions.make_cluster_name(cat_filename)

        for c in cluster_list:
            if c.name == cluster_name:
                this_cluster = c
                break
        else: # no break, which means a matching cluster wasn't found
            this_cluster = Cluster.Cluster(cluster_name, [])
            cluster_list.append(this_cluster)



        # Use regular expressions to determine what type a catalog is.
        sextractor_catalog = re.compile(r"MOO[0-9]{4}([+]|[-])[0-9]{4}_(r|z)[.]cat")
        # MOO, 4 digits, + or -, 4 more digits, _, r or z, .cat

        gemini_catalog = re.compile(r"m[0-9]{4}(p|m)[0-9]{4}[.]phot[.]dat")
        # m, 4 digits, p or m, 4 more digits, .phot.dat

        irac_catalog = re.compile(r"MOO_[0-9]{4}([+]|[-])[0-9]{4}_irac1_bg[.]fits[.]cat")
        # MOO_, 4 digits, + or -, 4 more digits, _irac_bg.fits.cat

        if sextractor_catalog.match(cat_filename):  # If it is a SExtractor catalog
            # find the band the catalog has data for
            band = functions.get_band_from_filename(cat_filename)

            # tell the cluster it has data in this band
            if band == "r":
                this_cluster.r_data = True
            elif band == "i":
                this_cluster.i_data = True
            elif band == "z":
                this_cluster.z_data = True

            # Read in the catalog
            cat_table = catalog.read_catalog(cat, ["ALPHA_J2000", "DELTA_J2000", "MAG_APER", "MAGERR_APER"],
                                             label_type="m", data_start=8, filters=["FLAGS < 4"])
            # Turn the table into source objects, and assign source list to cluster object
            this_cluster.sources_list = [other_classes.Source(line[0], line[1], [band], [line[2]], [line[3]])
                                         for line in cat_table]

            # Match sources to existing ones in the cluster
            for line in cat_table:
                this_source = other_classes.Source(line[0], line[1], [band], [line[2]], [line[3]])
                matching_source = sdss_calibration.match_sources(this_source, this_cluster.sources_list)
                # Will return either a source object or None
                if matching_source:  # If it already exists in the cluster
                    matching_source.add_band(band, line[2], line[3])
                else:  # If it doesn't exist, append it
                    this_cluster.sources_list.append(this_source)



        elif gemini_catalog.match(cat_filename):  # catalogs that end in .phot.dat
            # Have less desirable formatting, so need to be wrangled
            # Read in the catalog data
            cat_table = catalog.read_catalog(cat, ["ra", "dec", 3, 4, 5], label_type='s', label_row=0, data_start=2)
            # Columns 3, 4, 5 are mag, color, color error

            # find the bands in the catalog, and let the cluster know it has data in these bands
            band_labels = catalog.column_labels(cat, [3, 4])
            if band_labels[1] == 'rmz':
                band = 'r'
                this_cluster.r_data = True
                this_cluster.z_data = True
            elif band_labels[1] == 'imch1':
                band = 'i'
                this_cluster.i_data = True
                this_cluster.ch1_data = True
            elif band_labels[1] == 'ch1mch2':
                band = 'ch1'
                this_cluster.ch1_data = True
                this_cluster.ch2_data = True

            # Convert them to source objects
            # I don't worry about adding each source at once, since clusters that are from these catalogs will not be
            #  used with any other catalogs. They are independent.
            this_cluster.sources_list = [other_classes.Source(line[0], line[1], mag_bands=[band], mags=[line[2]],
                                                              mag_errors=[0], color_bands=[band_labels[1]],
                                                              color_values=[line[3]], color_errors=[line[4]])
                                         for line in cat_table]


        elif irac_catalog.match(cat_filename):
            pass # Don't do anything with them for now.

        else:
            print cat_filename, "no match"

    return cluster_list

