# coding=utf-8
import matplotlib.pyplot as plt
import matplotlib.gridspec as grid
import matplotlib.colors as mplcol
import matplotlib.cm as cmx
import numpy.polynomial.polynomial as polynomial
import numpy as np

from UselessNow.NotFromImages import main_functions


def plot_color_mag(cluster, color, band, predictions=True, distinguish_red_sequence=False, return_axis=False):
    """
    Makes a color-magnitude plot for the given cluster. Can plot EzGal predictions and plot RS in red.

    The CMDs are designed to look like the ones in Stanford 2014. The plot dimensions are similar to those.

    :param cluster: Cluster object that the data will be taken from.
    :param color: string holding color to be plotted on te y axis. Should be of the form "band1-band2"
    :param band: string telling which band's magnitudes will be plotted on the x axis.
    :param predictions: Boolean of whether or not to plot the EzGal predictions.
    :param distinguish_red_sequence: Boolean of whether or not to plot the RS members in red.
    :return: first: figure object the CMD was plotted on.
             second: axes object for the CMD itself. This is needed because I need to over plot things later, and
             returning the object is easier than making this function way more complicated than it already is.
    """

    # Need to make lists that can be plotted on the CMD
    # start by initializing empty lists to append to
    non_rs_mags, rs_mags, non_rs_colors, rs_colors, rs_color_errs, non_rs_color_errs = [], [], [], [], [], []
    for gal in cluster.galaxy_list:
        if gal.sources_list < 5.0:  # Don't want huge errors crowding out the plot
            if distinguish_red_sequence:  # If the user wants the RS in red, we need separate lists for RS and not
                if gal.RS_member:
                    rs_mags.append(gal.mag)
                    rs_colors.append(gal.color)
                    rs_color_errs.append(gal.color_error)
                else:
                    non_rs_mags.append(gal.mag)
                    non_rs_colors.append(gal.color)
                    non_rs_color_errs.append(gal.color_error)
            else:
                non_rs_mags.append(gal.mag)
                non_rs_colors.append(gal.color)
                non_rs_color_errs.append(gal.color_error)

    # Set up the plot
    fig = plt.figure(figsize=(9, 6))
    # Configure subplots
    whole_plot = grid.GridSpec(1, 2, width_ratios=[50, 1], left=0.08, right=0.92, wspace=0.1)
    # Still automatically leave room for the color bar, even if not needed, to make code simpler. It doesn't take up
    #     that much space, so it looks fine blank anyway
    color_mag_ax = plt.subplot(whole_plot[0, 0])

    # the predictions will have a color bar that needs its own axis
    if predictions:
        color_bar_ax = plt.subplot(whole_plot[0, 1])
        # Plot the predictions now
        _add_predictions_to_cmd(fig, color_mag_ax, color_bar_ax)

    # Now we can plot the points on the CMD (including errors)
    # check to make sure they have something in them
    if len(non_rs_colors) > 0:
        color_mag_ax.errorbar(x=non_rs_mags, y=non_rs_colors, yerr=non_rs_color_errs, c="k", fmt=".", elinewidth=0.35,
                              capsize=0, markersize=5)
    if len(rs_colors) > 0:
        color_mag_ax.errorbar(x=rs_mags, y=rs_colors, yerr=rs_color_errs, c="r", fmt=".", elinewidth=0.35, capsize=0,
                              markersize=5)  # Only difference is that this is plotted in red.

    color_mag_ax.set_title(cluster.name + ",  spec z = " + str(cluster.spec_z))
    color_mag_ax.set_xlabel(cluster.filters[1] + " Band Magnitude")
    color_mag_ax.set_ylabel(cluster.filters[0] + " - " + cluster.filters[1] + " Color")

    # Change the scale to match Stanford 14. Each filter set will be different
    if cluster.filters == ["r", "z"]:
        color_mag_ax.set_xlim([20, 24.5])  # should be [20, 23.5] Changed to see high redshift better
        # color_mag_ax.set_xlim([18, 26])
        color_mag_ax.set_ylim([0, 3.5])
    elif cluster.filters == ["i", "[3.6]"]:
        color_mag_ax.set_xlim([18, 21.5])
        color_mag_ax.set_ylim([-.5, 4.5])
    elif cluster.filters == ["[3.6]", "[4.5]"]:
        color_mag_ax.set_xlim([18.5, 21.5])
        color_mag_ax.set_ylim([-1, 0.5])
    if return_axis:
        return fig, color_mag_ax
    else:
        return fig

def _make_mag_color_lists(cluster, color, band):
    # TODO: document
    """

    :param cluster:
    :param color:
    :param band:
    :return:
    """


def _add_predictions_to_cmd(fig, color_mag_ax, color_bar_ax):
    """
    Plot lines representing the EzGal predictions of the RS for redshifts 0.5 ≤ z ≤ 1.5, with spacing of 0.05.

    Assumes the filter set is r-z
    Todo: Make this work for all available filters

    :param fig: figure object all the axes belong to
    :param color_mag_ax: axes object for plotting the CMD on
    :param color_bar_ax: axes object where the color bar will go
    :return: none. Figure and axes are modified in place
    """

    # first need to get the model's predictions
    predictions_dict = main_functions.make_prediction_dictionary(0.05)
    # Returns a dictionary with keys = redshifts, values = predictions objects

    # Set the colormap, to color code lines by redshift
    spectral = plt.get_cmap("spectral")
    # Normalize the colormap so that the the range of colors maps to the range of redshifts
    c_norm = mplcol.Normalize(vmin=min(predictions_dict), vmax=max(predictions_dict))
    scalar_map = cmx.ScalarMappable(norm=c_norm, cmap=spectral)

    for z in predictions_dict:
        # Get color
        color_val = scalar_map.to_rgba(predictions_dict[z].redshift)

        # Plot the predicted line, with the correct color
        color_mag_ax.plot(predictions_dict[z].rz_line.xs, predictions_dict[z].rz_line.ys, color=color_val,
                          linewidth=0.2)

        # Plot the points that correspond to L_star projected at those redshifts
        color_mag_ax.scatter(predictions_dict[z].z_mag,
                             predictions_dict[z].r_mag - predictions_dict[z].z_mag,
                             color=color_val)

    # Add a color bar
    scalar_map.set_array([])  # I don't know what this does, but I do know it needs to be here.
    fig.colorbar(scalar_map, cax=color_bar_ax)
    color_bar_ax.set_ylabel("Redshift")


def plot_residuals(cluster):
    """
    Plot the color residuals for each galaxy in the image.

    :param cluster: cluster object containing all the galaxies
    :return: figure object the plot was made on
    """

    # make lists of the galaxies' color residuals, magnitudes, and errors
    mags, color_residuals, errors = [], [], []
    for gal in cluster.galaxy_list:
        mags.append(gal.mag)
        color_residuals.append(gal.color_residual)
        errors.append(gal.color_error)

    # Plot them
    fig = plt.figure(figsize=(9, 6))
    # Use gridspec to configure the subplots
    whole_plot = grid.GridSpec(1, 2, width_ratios=[6, 1], left=0.08, right=0.92, wspace=0.0)
    residual_ax = plt.subplot(whole_plot[0])
    histo_ax = plt.subplot(whole_plot[1])

    # Plot the residuals
    residual_ax.errorbar(x=mags, y=color_residuals, yerr=errors, c="k", fmt=".", elinewidth=0.35, capsize=0,
                         markersize=5)
    residual_ax.set_xlim([20, 23.5])
    residual_ax.set_ylim([-1, 1])
    # Plot a line at zero, for easier visual inspection of any residual slope
    residual_ax.axhline(0)
    residual_ax.set_title(str(cluster.name) + ", spec z = " + str(cluster.spec_z) +
                          ", photo z = " + str(cluster.photo_z))
    residual_ax.set_xlabel("z Band Magnitude")
    residual_ax.set_ylabel("Color Difference From Best Fit Model")

    # Plot histogram
    histo_ax.hist(color_residuals, bins=20, range=(-1, 1), orientation="horizontal", color="k")
    # Move the histogram color labels to the right, so they don't overlap the CMD
    histo_ax.yaxis.tick_right()
    # Get rid of the horizontal ticks, since values clutter the plot, and only relative values actually matter here.
    histo_ax.xaxis.set_ticks([])

    return fig


def plot_z_comparison(clusters, directory, filename):
    """
    Plot and save the spectroscopic redshift vs calculated photometric redshift.

    :param clusters: list of image objects that contain the two redshifts
    :param directory: Directory where the plot will be saved
    :param filename: Filename the plot will be saved as. Do not include the extension, will always be a .pdf
    :return: none. Plot is saved, though.
    """
    # Make lists of spectroscopic and photometric redshifts, since that's what the plot function takes
    spec, photo, upper_photo_err, lower_photo_err, weights = [], [], [], [], []
    for c in clusters:
        if c.spec_z:  # Can't plot comparison if the cluster doesn't have a spectroscopic redshift
            spec.append(float(c.spec_z))
            photo.append(float(c.photo_z))
            lower_photo_err.append(c.lower_photo_z_error)
            upper_photo_err.append(c.upper_photo_z_error)
            weights.append(1.0 / ((c.upper_photo_z_error + c.lower_photo_z_error)/2))  # Average the errors
            # TODO: Find a better way to do the weighting for the fit. Simple averaging of the errors is WRONG.
    total_error = [lower_photo_err, upper_photo_err]

    # Find the best fit line
    fit = polynomial.polyfit(spec, photo, 1, w=weights)  # returns coefficients of a linear fit
    # Turn these coefficients into a line
    x = np.arange(0, 1.5, 0.01)
    fit_line = fit[0] + x * fit[1]

    # Plot everything
    # TODO: make work with lopsided error bars
    fig = plt.figure(figsize=(5, 5))
    ax = fig.add_subplot(1, 1, 1)
    # Plot points for individual clusters
    ax.errorbar(spec, photo, yerr=total_error, c="k", fmt=".", capsize=2, elinewidth=0.5)
    # Plot where the best fit line should be
    ax.plot([0.5, 1.5], [0.5, 1.5], "k-", lw=0.5)
    # Plot the best fit line
    ax.plot(x, fit_line, "b")
    # Add a grid, to make for easier viewing
    ax.grid(which="both")
    ax.minorticks_on()
    ax.set_xlabel("Spectroscopic Redshift")
    ax.set_ylabel("Photometric Redshift")
    ax.set_title("Spectroscopic vs Photometric Redshifts")
    ax.set_xlim((0.5, 1.5))
    ax.set_ylim((0.5, 1.5))

    fig.savefig(directory + filename + ".pdf", format="pdf")


def plot_initial_redshift_finding(cluster, z_list, galaxies_list, best_z):
    """Plots a bar graph of the number of galaxies at the RS for each redshift.

    :param cluster: Cluster object in the plot
    :param z_list: list of redshifts that were used in the calculation
    :param galaxies_list: list of galaxies near each redshift. Needs to be the same length as z_list, and the numbers
           in galaxies_list should correspond with the redshifts in z_list
    :param best_z: Redshift calculated as the best fit
    :return: None, but plot is saved.
    """
    # z_list may be in string format, so change it to floats
    z_list = [float(z) for z in z_list]

    # Plot the bar plot of galaxies as a function of redshift
    bar_fig = plt.figure(figsize=(6, 5))
    bar_ax = bar_fig.add_subplot(1, 1, 1)
    bar_ax.bar(z_list, galaxies_list, width=0.01, color="0.5", align="center")
    bar_ax.set_title(cluster.name + ", z = " + str(cluster.spec_z))
    # Show the cluster's redshift, and the initial redshift the code picked
    bar_ax.axvline(x=cluster.spec_z, c="r", lw=4)
    bar_ax.axvline(x=best_z, c="k", lw=4)
    plt.savefig("/Users/gbbtz7/GoogleDrive/Research/Plots/InitialZ/" + cluster.name + "_histo.pdf", format="pdf")


def plot_fitting_procedure(cluster, redshift, other_info=None, color_red_sequence=True):
    """Plot the red sequence members for the cluster on a CMD, with a line indicating the redshift of the current fit.

    :param cluster: Cluster that holds info that will be plotted
    :param redshift: Redshift for the prediction line that will be plotted
    :param other_info: Info that will go into the subtitle.
    :return: figure holding the plot
    """
    fig, ax = plot_color_mag(cluster, predictions=False, distinguish_red_sequence=color_red_sequence, return_axis=True)
    line = cluster.predictions_dict[redshift].rz_line
    ax.plot(line.xs, line.ys, "k-", linewidth=0.5, label="Initial z")
    ax.scatter(cluster.predictions_dict[redshift].z_mag, cluster.predictions_dict[redshift].r_mag -
               cluster.predictions_dict[redshift].z_mag, c="r", s=10)  # Plot characteristic magnitude point
    fig.suptitle(cluster.name + ", spec z = " + str(cluster.spec_z) + ", current z=" + str(redshift))
    ax.set_title(str(other_info), fontsize=10)

    return fig


def plot_location(cluster):

    # make lists of ra and dec for both RS members and non RS members
    rs_ras, rs_decs, non_rs_ras, non_rs_decs = [], [], [], []
    for gal in cluster.galaxy_list:
        if gal.RS_member:
            rs_ras.append(gal.ra)
            rs_decs.append(gal.dec)
        else:
            non_rs_ras.append(gal.ra)
            non_rs_decs.append(gal.dec)

    # Then plot them
    fig = plt.figure(figsize=(8, 6))
    ax = fig.add_subplot(1, 1, 1)
    ax.scatter(non_rs_ras, non_rs_decs, c="k", s=3)
    ax.scatter(rs_ras, rs_decs, c="r", s=6, edgecolors=None, linewidth=0)  # don't want black borders
    ax.set_title(cluster.name)
    ax.set_xlabel("RA")
    ax.set_ylabel("Dec")

    return fig

def plot_chi_data(cluster, chi_redshift_pairs, left_limit, best_z, right_limit):
    # TODO: document
    redshifts, chi_squared_values = [], []
    for pair in chi_redshift_pairs:
        redshifts.append(pair[0])
        chi_squared_values.append(pair[1])
    fig = plt.figure(figsize=(8, 6))
    ax = fig.add_subplot(1, 1, 1)
    ax.plot(redshifts, chi_squared_values, "k-")
    ax.scatter([float(left_limit), float(best_z), float(right_limit)], [1.0, 1.0, 1.0])
    ax.set_ylim((0.0, 5.0))
    ax.set_xlabel("Redshift")
    ax.set_ylabel("Chi squared value")
    ax.set_title(cluster.name + ", spec z = " + str(cluster.spec_z))

    return fig
