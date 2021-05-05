
#!/usr/bin/env python
"""
Thomas Klijnsma
"""

########################################
# Imports
########################################

import os

from OptionHandler import flag_as_option, flag_as_parser_options

import differentials
import differentials.core as core
import LatestPaths

import logging
import copy
import re
import random
random.seed(1002)


########################################
# Main
########################################

@flag_as_parser_options
def scalecorrelations_parser_options(parser):
    parser.add_argument( '--theorybinning', action='store_true' )
    parser.add_argument( '--writefiles', action='store_true' )


@flag_as_option
def top_central_values(args):
    top_exp_binning = [ 0., 15., 30., 45., 80., 120., 200., 350., 600., 800. ]
    sm = differentials.theory.theory_utils.FileFinder(
        ct=1.0, cg=0.0, cb=1.0, muR=1.0, muF=1.0, Q=1.0,
        directory=LatestPaths.theory.top.filedir
        ).get()[0]
    print sm.file
    xs = differentials.integral.Rebinner(sm.binBoundaries, sm.crosssection, top_exp_binning).rebin()
    print xs
    print ' '.join(['{0:.2g}'.format(v) for v in xs])
    print ' & '.join([
        re.sub(
            r'e\-\d(\d)',
            r'\\times 10^{-\1}',
            '{0:.{ndec}{mode}}'.format(v, ndec = 1 if v < 0.1 else 2, mode = 'e' if v < 0.1 else 'f')
            )
        for v in xs ]) + ' \\\\'

@flag_as_option
def top_scalecorrelations(args):
    variations = differentials.theory.theory_utils.FileFinder(
        ct=1.0, cg=0.0, cb=1.0,
        directory=LatestPaths.theory.top.filedir
        ).get()
    sm = [v for v in variations if v.muR==1.0 and v.muF==1.0 and v.Q==1.0][0]


    scalecorrelation = differentials.theory.scalecorrelation.ScaleCorrelation()

    top_exp_binning = [ 0., 15., 30., 45., 80., 120., 200., 350., 600., 800. ]
    if not sm.binBoundaries[-1] == top_exp_binning[-1]:
        raise ValueError('Expected ends of pt binings do not match!')
    scalecorrelation.set_bin_boundaries(top_exp_binning)

    for variation in variations:
        scalecorrelation.add_variation(
            differentials.integral.Rebinner(variation.binBoundaries, variation.crosssection, top_exp_binning).rebin(),
            {},
            is_central=(variation is sm),
            )
    scalecorrelation.plot_correlation_matrix('tophighpt')
    scalecorrelation.write_errors_to_texfile('tophighpt')
    if args.writefiles:
        scalecorrelation.make_scatter_plots(subdir='scatterplots_tophighpt')
        scalecorrelation.write_correlation_matrix_to_file('tophighpt')
        scalecorrelation.write_errors_to_file('tophighpt')

    if args.theorybinning:
        scalecorrelation_theory = differentials.theory.scalecorrelation.ScaleCorrelation()
        scalecorrelation_theory.tags.append('theorybinning')
        scalecorrelation_theory.set_bin_boundaries(sm.binBoundaries)
        for variation in variations:
            scalecorrelation_theory.add_variation(
                variation.crosssection,
                {},
                is_central=(variation is sm),
                )
        scalecorrelation_theory.plot_correlation_matrix('tophighpt')
        scalecorrelation_theory.write_errors_to_texfile('tophighpt')
        if args.writefiles:
            scalecorrelation_theory.make_scatter_plots(subdir='scatterplots_tophighpt_theorybinning')
            scalecorrelation_theory.write_correlation_matrix_to_file('tophighpt')
            scalecorrelation_theory.write_errors_to_file('tophighpt')


@flag_as_option
def yukawa_central_values(args):
    yukawa_exp_binning = [0.0, 15., 30., 45., 80., 120.]
    sm = differentials.theory.theory_utils.FileFinder(
        kappab=1.0, kappac=1.0, muR=1.0, muF=1.0, Q=1.0,
        directory='out/theories_Apr27_yukawa_summed/'
        ).get()[0]
    print sm.file
    xs = differentials.integral.Rebinner(sm.binBoundaries, sm.crosssection, yukawa_exp_binning).rebin()
    print xs
    print ' '.join(['{0:.2g}'.format(v) for v in xs])
    print ' & '.join([
        re.sub(
            r'e\-\d(\d)',
            r'\\times 10^{-\1}',
            '{0:.{ndec}{mode}}'.format(v, ndec = 1 if v < 0.1 else 2, mode = 'e' if v < 0.1 else 'f')
            )
        for v in xs ]) + ' \\\\'

@flag_as_option
def yukawa_scalecorrelations(args):
    #InputDirTheories = 'out/theories_May05_yukawa_summed/'
    InputDirTheories = 'out/theories_%s_yukawa_summed/'%(core.datestr())
    if os.path.isdir(InputDirTheories):
        logging.info('File {} exists.'.format(InputDirTheories))
    else:
        logging.info('File {} does not exists.'.format(InputDirTheories))
        exit()
    variations = differentials.theory.theory_utils.FileFinder(
        kappab=1.0, kappac=1.0,
        directory=InputDirTheories
        ).get()
    sm = [v for v in variations if v.muR==1.0 and v.muF==1.0 and v.Q==1.0][0]

    scalecorrelation = differentials.theory.scalecorrelation.ScaleCorrelation()

    yukawa_exp_binning = [0.0, 15., 30., 45., 80., 120.]
    scalecorrelation.set_bin_boundaries(yukawa_exp_binning)

    for variation in variations:
        scalecorrelation.add_variation(
            differentials.integral.Rebinner(variation.binBoundaries, variation.crosssection, yukawa_exp_binning).rebin(),
            {},
            is_central=(variation is sm),
            )

    scalecorrelation.plot_correlation_matrix('yukawa')
    scalecorrelation.write_errors_to_texfile('yukawa')
    if args.writefiles:
        scalecorrelation.make_scatter_plots(subdir='scatterplots_yukawa')
        scalecorrelation.write_correlation_matrix_to_file('yukawa')
        scalecorrelation.write_errors_to_file('yukawa')

    if args.theorybinning:
        scalecorrelation_theory = differentials.theory.scalecorrelation.ScaleCorrelation()
        scalecorrelation_theory.tags.append('theorybinning')
        scalecorrelation_theory.set_bin_boundaries(sm.binBoundaries)
        for variation in variations:
            scalecorrelation_theory.add_variation(
                variation.crosssection,
                {},
                is_central=(variation is sm),
                )
        scalecorrelation_theory.plot_correlation_matrix('yukawa')
        scalecorrelation_theory.write_errors_to_texfile('yukawa')
        if args.writefiles:
            scalecorrelation_theory.make_scatter_plots(subdir='scatterplots_yukawa_theorybinning')
            scalecorrelation_theory.write_correlation_matrix_to_file('yukawa')
            scalecorrelation_theory.write_errors_to_file('yukawa')
