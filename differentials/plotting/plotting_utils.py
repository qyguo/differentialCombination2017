import itertools, copy
import differentials.core
import differentials.logger as logger
import ROOT

from array import array

ROOTCOUNTER = 1000
def get_unique_rootname():
    global ROOTCOUNTER
    name = 'root{0}_{1}'.format(ROOTCOUNTER, differentials.core.__uniqueid__().next())
    ROOTCOUNTER += 1
    return name

def get_plot_base(
        x_min = 0, x_max = 1,
        y_min = 0, y_max = 1,
        x_title = 'x', y_title = 'y',
        set_title_sizes = True,
       ):
    base = ROOT.TH1F()
    ROOT.SetOwnership(base, False)
    base.SetName(get_unique_rootname())
    base.GetXaxis().SetLimits(x_min, x_max)
    base.SetMinimum(y_min)
    base.SetMaximum(y_max)
    base.SetMarkerColor(0)
    base.GetXaxis().SetTitle(x_title)
    base.GetYaxis().SetTitle(y_title)
    if set_title_sizes:
        base.GetXaxis().SetTitleSize(0.06)
        base.GetYaxis().SetTitleSize(0.06)
    return base

def set_color_palette(option=None):
    # n_stops = 3
    # stops  = [ 0.0, 0.5, 1.0 ]
    # reds   = [ 0.0, 1.0, 1.0 ]
    # blues  = [ 1.0, 1.0, 0.0 ]
    # greens = [ 0.0, 1.0, 0.0 ]

    # n_stops = 2
    # stops  = [ 0.0, 1.0 ]
    # reds   = [ 55./255.,  1.0 ]
    # greens = [ 138./255., 1.0 ]
    # blues  = [ 221./255., 1.0 ]

    if option == 'twocolor':
        n_stops = 3
        stops  = [ 0.0, 0.3, 1.0 ]
        reds   = [ 55./255.,  1.0, 1.0 ]
        greens = [ 138./255., 1.0, 26./255. ]
        blues  = [ 221./255., 1.0, 26./255. ]
    else:
        n_stops = 3
        stops  = [ 0.0, 0.3, 1.0 ]
        reds   = [ 55./255.,  166./255., 1.0 ]
        greens = [ 138./255., 203./255., 1.0 ]
        blues  = [ 221./255., 238./255., 1.0 ]

    ROOT.TColor.CreateGradientColorTable(
        n_stops,
        array('d', stops),
        array('d', reds),
        array('d', greens),
        array('d', blues),
        255)

def new_color_cycle():
    return itertools.cycle(
        range(2,5) + range(6,10)
        + range(40,50)
        + [ 30, 32, 33, 35, 38, 39 ]
       )



def get_contours_from_H2(H2_original, threshold):
    # Open a temporary canvas so the contour business does not screw up other plots
    ctemp = ROOT.TCanvas('ctemp', 'ctemp', 1000, 800)
    ctemp.cd()

    H2 = H2_original.Clone()
    H2.SetName(get_unique_rootname())
    H2.SetContour(1, array('d', [threshold]))

    logger.info(
        'Trying to get contours from \'{0}\''
        .format(H2.GetName())
        + (' ({0})'.format(H2_original.name) if hasattr(H2_original, 'name') else '')
        )

    H2.Draw('CONT Z LIST')
    ROOT.gPad.Update()

    contours_genObj = ROOT.gROOT.GetListOfSpecials().FindObject('contours')

    Tgs = []
    for iContour in xrange(contours_genObj.GetSize()):
        contour_TList = contours_genObj.At(iContour)
        for iVal in xrange(contour_TList.GetSize()):
            Tg = contour_TList.At(iVal)

            TgClone = Tg.Clone()
            ROOT.SetOwnership(TgClone, False)
            Tgs.append(TgClone)

    logger.info('    {0} contours found for threshold {1}'.format(len(Tgs), threshold))
    for i_Tg, Tg in enumerate(Tgs):
        N = Tg.GetN()
        xList = [ Tg.GetX()[iPoint] for iPoint in xrange(N) ]
        yList = [ Tg.GetY()[iPoint] for iPoint in xrange(N) ]
        xMin = min(xList)
        xMax = max(xList)
        yMin = min(yList)
        yMax = max(yList)
        logger.debug(
            '  Contour {0} ({1} points): '
            'xMin = {2:+9.4f}, xMax = {3:+9.4f}, yMin = {4:+9.4f}, yMax = {5:+9.4f}'
            .format(i_Tg, N, xMin, xMax, yMin, yMax)
            )

    del H2
    del contours_genObj

    ctemp.Close()
    del ctemp

    from canvas import c
    c.cd()
    ROOT.gPad.Update()

    return Tgs

def get_x_y_from_TGraph(Tg):
    N = Tg.GetN()
    xs = []
    ys = []
    x_Double = ROOT.Double(0)
    y_Double = ROOT.Double(0)
    for i in xrange(N):
        Tg.GetPoint( i, x_Double, y_Double )
        xs.append( float(x_Double) )
        ys.append( float(y_Double) )
    return xs, ys
