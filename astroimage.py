from io import StringIO
import math
import numpy as np
import pandas as pd
import datetime


class AstroImage(object):

    """
	A container class for information about the properties of a particular
	image, especially the direction of each pixel
	ImageAWIM is specific to an individual image and thus has an ID retrieved from the image file to associate it with an image

	Note, TODO pixels are referenced to the center. The center is given in Photoshop reference then all pixel references
    after are relative to the center with right and up as positive.
    TODO
	i.e. (x, y), top-left to bottom-right:
	e.g. the top-left pixel is (0, 0), top-right is (1919, 0), bottom-left is (0, 1079), bottom-right is (1919, 1079)
	"""

    def __init__(self, awim_dictionary_text):
        
        self.latlng = [float(value) for value in (awim_dictionary_text['Location']).split(',')]
        self.capture_moment = datetime.datetime.fromisoformat(awim_dictionary_text['Capture Moment'])
        self.dimensions = [int(value) for value in (awim_dictionary_text['Dimensions']).split(',')]
        self.max_image_index = [self.dimensions[0]-1, self.dimensions[1]-1]
        self.center_PSpx = [float(value) for value in (awim_dictionary_text['Center Pixel']).split(',')]
        self.center_KVpx = [self.center_PSpx[0], self.max_image_index[1] - self.center_PSpx[1]]
        self.center_azalt = [float(value) for value in (awim_dictionary_text['Center AzAlt']).split(',')]
        px_models_df = pd.read_csv(StringIO(awim_dictionary_text['Pixel Models']), index_col=0)
        self.px_predict_features = px_models_df.columns
        self.x_px_predict_coeff = px_models_df.loc[['x_px_predict']].values[0]
        self.y_px_predict_coeff = px_models_df.loc[['y_px_predict']].values[0]
        self.pixel_map_type = awim_dictionary_text['Pixel Map Type']
        xyangs_models_df = pd.read_csv(StringIO(awim_dictionary_text['x,y Angle Models']), index_col=0)
        self.ang_predict_features = xyangs_models_df.columns
        self.xang_predict_coeff = xyangs_models_df.loc[['xang_predict']].values[0]
        self.yang_predict_coeff = xyangs_models_df.loc[['yang_predict']].values[0]
        # borders used for determining if azalt is present on photo and for a display showing the extent of the image in radec for example
        self.border_azalts = self.border_finder()
        self.x_delta_pxsperdeg = self.dimensions[0] / abs(self.border_azalts[1,4]-self.border_azalts[1,0])
        self.y_delta_pxsperdeg = self.dimensions[1] / abs(self.border_azalts[0,3]-self.border_azalts[2,3])
        self.pxsperdeg_ballpark = (self.x_delta_pxsperdeg + self.y_delta_pxsperdeg) / 2


    # get the px of an azalt in requested coord type (default is Kivy)
    # calculation is 3 parts via azalt to 1. xy_angs to 2. px to 3. KVpx
    def azalts_to_pxs(self, azalts, coord_type):
        if isinstance(azalts, list):
            azalts = np.asarray(azalts)

        input_shape = azalts.shape
        azalts = azalts.reshape(-1,2)

        # Part 1, azalts to xy_angs
        # find az_rels, convert to -180 < x <= 180, then abs value + direction matrix
        # also need az_rel compliment angle + store which are behind camera
        # then to radians
        simple_subtract = np.subtract(azalts[:,0], self.center_azalt[0])
        big_angle_correction = np.where(simple_subtract > 0, -360, 360)
        az_rel = np.where(np.abs(simple_subtract) <= 180, simple_subtract, np.add(simple_subtract, big_angle_correction))
        az_rel_direction = np.where(az_rel < 0, -1, 1)
        az_rel_abs = np.abs(az_rel)
        az_rel_behind_observer = np.where(az_rel_abs <= 90, False, True) # true if point is behind observer - assume because camera pointed up very high past zenith or below nether-zenith
        # Note: cannot allow az_rel_compliment (and therefore d2) to be negative because must simple_ang_totalsmallcircle (-) if alt_seg_ is (-), which is good.
        az_rel_compliment = np.where(az_rel_abs <= 90, np.subtract(90, az_rel_abs), np.subtract(az_rel_abs, 90)) # 0 to 90 angle from line perpendicular to az
        az_rel_compliment_rad = np.multiply(az_rel_compliment, math.pi/180) # (+) only, 0 to 90
        center_azalt_rad = np.multiply(self.center_azalt, math.pi/180)

        # altitude direction matrix, then altitudes to radians, keep sign just convert to radian
        alt_direction = np.where(azalts[:,1] < 0, -1, 1)
        alt_rad = np.multiply(azalts[:,1], math.pi/180)

        # trigonometry, see photoshop diagrams for variable descriptions. segment ending with underscore_ means can be "negative distance"
        alt_seg_ = np.sin(alt_rad) # notice: (-) for (-) alts
        d3 = np.cos(alt_rad) # (+) only, because alts are always -90 to 90
        d2 = np.multiply(np.sin(az_rel_compliment_rad), d3) # (+) only
        d1 = np.multiply(np.cos(az_rel_compliment_rad), d3) # (+) only because az_rel_compliment_rad is 0 to 90
        r2 = np.sqrt(np.square(d2), np.square(alt_seg_))
        xang_abs = np.subtract(math.pi/2, np.arccos(d1)) # TODO? what if xang is actually > 90? would be unusual, difficult to combine with large yang
        xang = np.multiply(xang_abs, az_rel_direction)
        pt1_alt_ = np.multiply(r2, np.sin(center_azalt_rad[1])) # (-) for (-) cam_alts, which is good
        lower_half = np.where(alt_seg_ < pt1_alt_, True, False) # true if px is below middle of photo
        ang_smallcircle_fromhorizon = np.arctan(np.divide(alt_seg_, d2)) # -90 to 90, (-) for (-) alt_seg_, bc d2 always (+)
        # for yang, if in front, simple, but behind observer, the angle from must be subtracted from 180 or -180 because different angle meaning see photoshop diagram
        ang_totalsmallcircle = np.where(np.logical_not(az_rel_behind_observer), ang_smallcircle_fromhorizon, np.subtract(np.multiply(alt_direction, math.pi), ang_smallcircle_fromhorizon))
        yang = np.subtract(ang_totalsmallcircle, center_azalt_rad[1]) # simply subtract because |ang_totalsmallcircle| < 180 AND |center_azalt[1]| < 90 AND if |ang_totalsmallcircle| > 90, then they are same sign

        xy_angs = np.zeros(azalts.shape)
        xy_angs[:,0] = np.multiply(xang, 180/math.pi)
        xy_angs[:,1] = np.multiply(yang, 180/math.pi)

        # Part 2: xy_angs to pxs
        xy_angs_direction = np.where(xy_angs < 0, -1, 1)
        xy_angs_abs = np.abs(xy_angs)

        if self.pixel_map_type == '3d_degree_poly_fit_abs_from_center':
            xy_angs_poly = np.zeros((xy_angs.shape[0], 9))
            xy_angs_poly[:,0] = xy_angs_abs[:,0]
            xy_angs_poly[:,1] = xy_angs_abs[:,1]
            xy_angs_poly[:,2] = np.square(xy_angs_abs[:,0])
            xy_angs_poly[:,3] = np.multiply(xy_angs_abs[:,0], xy_angs_abs[:,1])
            xy_angs_poly[:,4] = np.square(xy_angs_abs[:,1])
            xy_angs_poly[:,5] = np.power(xy_angs_abs[:,0], 3)
            xy_angs_poly[:,6] = np.multiply(np.square(xy_angs_abs[:,0]), xy_angs_abs[:,1])
            xy_angs_poly[:,7] = np.multiply(xy_angs_abs[:,0], np.square(xy_angs_abs[:,1]))
            xy_angs_poly[:,8] = np.power(xy_angs_abs[:,1], 3)

        pxs = np.zeros(azalts.shape)
        pxs[:,0] = np.dot(xy_angs_poly, self.x_px_predict_coeff)
        pxs[:,1] = np.dot(xy_angs_poly, self.y_px_predict_coeff)

        pxs = np.multiply(pxs, xy_angs_direction)

        # Part 3. pxs to coord_type
        if coord_type == 'KVpx':
            pxs[:,0] = pxs[:,0] + self.center_KVpx[0]
            pxs[:,1] = pxs[:,1] + self.center_KVpx[1]

        return pxs


    def pxs_to_azalts(self, pxs):
        if isinstance(pxs, list): # models require numpy arrays
            pxs = np.asarray(pxs)

        input_shape = pxs.shape
        angs_direction = np.where(pxs < 0, -1, 1) # models are positive values only. Save sign. Same sign for xyangs
        pxs = np.abs(pxs)
        pxs = pxs.reshape(-1,2)

        if self.pixel_map_type == '3d_degree_poly_fit_abs_from_center':
            pxs_poly = np.zeros((pxs.shape[0], 9))
            pxs_poly[:,0] = pxs[:,0]
            pxs_poly[:,1] = pxs[:,1]
            pxs_poly[:,2] = np.square(pxs[:,0])
            pxs_poly[:,3] = np.multiply(pxs[:,0], pxs[:,1])
            pxs_poly[:,4] = np.square(pxs[:,1])
            pxs_poly[:,5] = np.power(pxs[:,0], 3)
            pxs_poly[:,6] = np.multiply(np.square(pxs[:,0]), pxs[:,1])
            pxs_poly[:,7] = np.multiply(pxs[:,0], np.square(pxs[:,1]))
            pxs_poly[:,8] = np.power(pxs[:,1], 3)

        xyangs = np.zeros(pxs.shape)
        xyangs[:,0] = np.dot(pxs_poly, self.xang_predict_coeff)
        xyangs[:,1] = np.dot(pxs_poly, self.yang_predict_coeff)

        xyangs_pretty = np.multiply(xyangs.reshape(input_shape), angs_direction)

        # prepare to convert xyangs to azalts. Already have angs_direction from above. abs of xangs only, keep negative yangs
        angs_direction = angs_direction.reshape(-1,2)
        xyangs = xyangs_pretty.reshape(-1,2)
        xyangs[:,0] = np.abs(xyangs[:,0])
        xyangs = np.multiply(xyangs, math.pi/180)
        center_azalt_rad = np.multiply(self.center_azalt, math.pi/180)

        # see photoshop diagram of sphere, circles, and triangles for variable names
        xang_compliment = np.subtract(math.pi/2, xyangs[:,0]) # always (+) because xang < 90
        d1 = 1*np.cos(xang_compliment) # always (+)
        r2 = 1*np.sin(xang_compliment) # always (+)
        ang_totalsmallcircle = np.add(center_azalt_rad[1], xyangs[:,1]) # -180 to 180
        d2_ = np.multiply(np.cos(ang_totalsmallcircle), r2) # (-) for ang_totalsmallcircle > 90 or < -90, meaning px behind observer
        alt_seg_ = np.multiply(np.sin(ang_totalsmallcircle), r2) # (-) for (-) ang_totalsmallcircle
        alts = np.arcsin(alt_seg_) # (-) for (-) alt_seg_
        az_rel = np.subtract(math.pi/2, np.arctan(np.divide(d2_, d1))) # d2 (-) for px behind observer and therefore az_rel > 90 because will subtract (-) atan
        az_rel = np.multiply(az_rel, angs_direction[:,0])
        azs = np.mod(np.add(center_azalt_rad[0], az_rel), 2*math.pi)

        azalts = np.zeros(xyangs.shape)
        azalts[:,0] = np.multiply(azs, 180/math.pi)
        azalts[:,1] = np.multiply(alts, 180/math.pi)

        return azalts.reshape(input_shape)


    def border_finder(self):

        left = 0-self.center_KVpx[0]
        right = self.max_image_index[0] - self.center_KVpx[0]
        top = self.max_image_index[1] - self.center_KVpx[1]
        bottom = 0-self.center_KVpx[1]

        px_LT = [left, top]
        px_top = [0, top]
        px_RT = [right, top]
        px_left = [left, 0]
        px_center = [0, 0]
        px_right = [right, 0]
        px_LB = [left, bottom]
        px_bottom = [0, bottom]
        px_RB = [right, bottom]
        self.pxs_borders = np.concatenate((px_LT, px_top, px_RT, px_left, px_center, px_right, px_LB, px_bottom, px_RB)).reshape(3,6)

        azalts_borders = self.pxs_to_azalts(self.pxs_borders)

        return azalts_borders