import os
import datetime
import pytz
import PIL
import numpy as np
import kivy
from kivy.core.window import Window
# from kivy.config import Config
from kivy.app import App
from kivy.clock import Clock
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.image import Image
# from kivy.properties import NumericProperty, StringProperty
import clockmath
import astroimage
import time # to time code

class BackGroundSky(Image):
    pass

class ForeGroundImg(Image):
    pass

class Sun(Image):
    pass

class Moon(Image):
    pass

class Mercury(Image):
    pass

class Venus(Image):
    pass

class Mars(Image):
    pass

class Jupiter(Image):
    pass

class Saturn(Image):
    pass

class Uranus(Image):
    pass

class Neptune(Image):
    pass

# class Alnilam(Image):
#     pass

class Timev3AstroClockApp(App):

    def build(self):
        self.img_dims = [1920,1080]
        self.earth_latlng = [40.2986,-83.0558] # for now images need to be close to one another. Local clock. Global clock someday?
        self.elevation_meters = 287
        self.local_industrial_timezone_pytz = pytz.timezone('US/Eastern')
        self.timezone_offset = -4

        # all images, sky images, awim images
        images_path = './images/'
        all_images_list = [os.path.join(images_path, f) for f in os.listdir(images_path) if os.path.isfile(os.path.join(images_path, f))]

        daysky = [filename for filename in all_images_list if 'sky6_day' in filename][0]
        eveningsky = [filename for filename in all_images_list if 'sky5_evening' in filename][0]
        transitionsky = [filename for filename in all_images_list if 'sky4_transition' in filename][0]
        civilsky = [filename for filename in all_images_list if 'sky3_civil' in filename][0]
        nauticalsky = [filename for filename in all_images_list if 'sky2_nautical' in filename][0]
        astronomicalsky = [filename for filename in all_images_list if 'sky1_astronomical' in filename][0]
        nightsky = [filename for filename in all_images_list if 'sky0_night' in filename][0]
        self.sky_filenames_dictionary = {'day':daysky, 'evening':eveningsky, 'transition':transitionsky, 'civil twighlight':civilsky, 'nautical twighlight':nauticalsky, 'astronomical twighlight':astronomicalsky, 'night':nightsky}

        self.all_moons_list = [filename for filename in all_images_list if 'moon' in filename]
        self.all_moons_list.sort()
        
        self.all_awims_list = [filename for filename in all_images_list if 'awim' in filename]
        self.placeholder_image = [filename for filename in all_images_list if 'placeholder' in filename][0]

        self.sun_moon_size_px = (70,70)
        self.sun_pointer = self.root.ids.sun
        self.sun_pointer.size = self.sun_moon_size_px
        self.moon_pointer = self.root.ids.moon_image
        self.moon_pointer.size = self.sun_moon_size_px
        # self.planets_size_px = (7,7)
        self.mercury_pointer = self.root.ids.mercury
        self.mercury_pointer.size = self.sun_moon_size_px
        self.venus_pointer = self.root.ids.venus
        self.venus_pointer.size = self.sun_moon_size_px
        self.mars_pointer = self.root.ids.mars
        self.mars_pointer.size = self.sun_moon_size_px
        self.jupiter_pointer = self.root.ids.jupiter
        self.jupiter_pointer.size = self.sun_moon_size_px
        self.saturn_pointer = self.root.ids.saturn
        self.saturn_pointer.size = self.sun_moon_size_px
        self.uranus_pointer = self.root.ids.uranus
        self.uranus_pointer.size = self.sun_moon_size_px
        self.neptune_pointer = self.root.ids.neptune
        self.neptune_pointer.size = self.sun_moon_size_px
        # self.alnilam_pointer = self.root.ids.alnilam
        # self.alnilam_pointer.size = self.sun_moon_size_px

        sky_pointer = self.root.ids.background_sky
        sky_pointer.source = self.sky_filenames_dictionary['day']
        foreground_pointer = self.root.ids.foreground
        foreground_pointer.source = self.all_awims_list[0]

        self.initialize_time_v3_clock()

    # animations separated by when tasks should be completed:
    # prepare_: to do the calculating ahead and store results for quick response. Includes everything pre-user input
    # show_: to receive the user command to show the animation, finalize the animation parameters, call tick_
    # tick finished with conditional to say what to do after the tick goes through all the moments. Could move to next show_now or call a function to repeat through moments with different image for example.
    # tick_ to step through the moments of already-built animation. schedule this from run_. shows on clock. All variables prefixed with bymoment_ or working_

    def initialize_time_v3_clock(self):
        self.tick_counter = 0
        self.now_resolution = 5*60
        self.now_duration = 24*60*60
        self.prepare_timev3_clock()
        self.show_timev3_clock('now', self.now_resolution)

    def prepare_timev3_clock(self):
        # self.disp_dims = self.root.size
        # self.disp_dims_ratio = np.divide(self.disp_dims, self.img_dims)

        self.now_moments = clockmath.moments_generator('now', self.now_duration, self.now_resolution)

        # in case I want to select from them later based on user input
        animation_awims_list = self.all_awims_list
        celestial_objects_list = ['sun', 'moon', 'mercury', 'venus', 'mars', 'jupiter', 'saturn', 'uranus', 'neptune']

        print('calculating daily rises and sets')
        code_time1 = time.perf_counter()
        self.sun_daily, self.moon_daily, self.day_night_length_str = clockmath.calculate_astro_risesandsets(self.now_moments[0], self.earth_latlng, self.elevation_meters)
        mark_time_dailyevents = time.perf_counter() - code_time1
        print('time to calculate daily events was %.2f seconds' % (mark_time_dailyevents))

        print('calculating new moon, full moon, illumination')
        code_time1 = time.perf_counter()
        self.nearest_new_moon, self.nearest_full_moon, self.moon_illumination_percent = clockmath.calculate_astro_newfullmoon_andillum(self.now_moments[0])
        mark_time_moonphase = time.perf_counter() - code_time1
        print('time to calculate moon was %.2f seconds' % (mark_time_moonphase))
        # TODO find moon phase, moon appearance angle in images for gibbouses and crescents

        print('calculating celestial objects dictionary')
        code_time1 = time.perf_counter()
        self.now_celestial_objs_dictionary = clockmath.calculate_astro_data(self.now_moments, celestial_objects_list, self.earth_latlng)
        mark_time_celestial = time.perf_counter() - code_time1
        print('time to calculate celestial objects dictionary of %i objects, %i moments was %.2f seconds' % (len(celestial_objects_list), self.now_moments.size, mark_time_celestial))

        print('calculating moon illum direction angles')
        code_time1 = time.perf_counter()
        self.now_moon_brightsidedirection = clockmath.calculate_astro_moon_brightsidedirection(self.now_celestial_objs_dictionary['moon'][:,[1,2]], self.now_celestial_objs_dictionary['sun'][:,[1,2]])
        mark_time_moonillum = time.perf_counter() - code_time1
        print('time to calculate moon illum direction angles trigonometry was %.6f seconds' % (mark_time_moonillum))

        print('calculating images objects dictionary')
        code_time1 = time.perf_counter()
        self.now_imgs_objs_dictionary, self.now_TOC = clockmath.calculate_astro_data_to_images(self.now_moments, self.now_celestial_objs_dictionary, animation_awims_list, self.img_dims, self.sun_moon_size_px)
        mark_time_imgs = time.perf_counter() - code_time1
        print('time to calculate imgs objects dictionary of %i images, %i objects was %.2f seconds' % (len(animation_awims_list), len(celestial_objects_list), mark_time_imgs))
        print('ratio of calculation times: %.1f' % (mark_time_celestial / mark_time_imgs))

        print('choosing AWIM images')
        code_time1 = time.perf_counter()
        self.now_bymoment_awims = clockmath.awim_chooser('time v3 clock', self.now_moments, self.now_celestial_objs_dictionary, self.now_imgs_objs_dictionary, self.now_TOC, self.placeholder_image)
        mark_time_awimchooser = time.perf_counter() - code_time1
        print('time to shoose awim images of %i images, %i objects was %.2f seconds' % (len(animation_awims_list), len(celestial_objects_list), mark_time_awimchooser))

    def prepare_lapses(self):
        pass
        # aaron visit replay
        # start_moment = datetime.datetime(year=2022, month=3, day=20, hour=20, tzinfo=datetime.timezone.utc) + datetime.timedelta(hours=5)
        # end_moment = start_moment + datetime.timedelta(hours=6)
        # step_length = datetime.timedelta(minutes=15)

    def show_timev3_clock(self, start_where, tick_time):
        self.moon_angle = 0

        self.working_moments = self.now_moments

        if start_where == 'now':
            moment_now = np.datetime64('now')
            moments_minus_now = np.subtract(self.working_moments, moment_now)
            future_times_indexes = np.where(np.greater_equal(moments_minus_now, np.timedelta64(0, 's')))[0]
            if future_times_indexes.size > 1:
                self.tick_counter = future_times_indexes.min()
            else:
                self.tick_schedule.cancel()
                self.initialize_time_v3_clock()
        elif start_where == 'lapse from beginning':
            self.tick_counter = 0

        self.working_celestial_objs_dictionary = self.now_celestial_objs_dictionary
        self.working_moon_brightsidedirection = self.now_moon_brightsidedirection
        self.working_imgs_objs_dictionary = self.now_imgs_objs_dictionary
        self.working_TOC = self.now_TOC
        self.working_bymoment_awims = self.now_bymoment_awims

        # 6. select sky image by moment. Note: correct size only because the array for sun altitude is correct size
        sun_alts = self.working_celestial_objs_dictionary['sun'][:,2]
        skylight_conditions = [sun_alts >= 6, (sun_alts < 6)&(sun_alts >= 0.5334), (sun_alts < 0.5334)&(sun_alts >= -0.833), (sun_alts < -0.833)&(sun_alts >= -6), (sun_alts < -6)&(sun_alts >= -12), (sun_alts < -12)&(sun_alts >= -18), (sun_alts < -18)]
        skylight_names = ['day', 'evening', 'transition', 'civil twighlight', 'nautical twighlight', 'astronomical twighlight', 'night']
        self.bymoment_skylights = np.select(skylight_conditions, skylight_names, default='day')

        # 8. list which celestial objects to display by moment? (already partially defined in the images_obejcts_dictionary numpy arrays)
    
        self.tick_schedule = Clock.schedule_once(self.tick)
        self.tick_schedule = Clock.schedule_interval(self.tick, tick_time)

    def show_day_lapse(self):
        self.tick_schedule.cancel()
        tick_time = 0.6
        lapse_speed = self.now_resolution / tick_time
        print('lapse speed is %.2f' % (lapse_speed))
        self.show_timev3_clock('lapse from beginning', tick_time)

    # use images_objects_dictionary, plus some type of selection of which image to show by moment, and display the moments as appropriate
    def tick(self, *args):
        code_time1 = time.perf_counter()

        # get the data for the current moment
        moment_now = self.working_moments[self.tick_counter]
        tick_datetime_aware = moment_now.tolist().replace(tzinfo=datetime.timezone.utc) # I can't believe this works, but it appears to be the way to do it. Happy I'm only doing this once.

        # can be based on index number / counter, display by setting kivy variables.
        skylight_name = self.bymoment_skylights[self.tick_counter]
        sky_img_filename = self.sky_filenames_dictionary[skylight_name]
        sky_pointer = self.root.ids.background_sky
        sky_pointer.source = sky_img_filename
        awim_img_filename = self.working_bymoment_awims[self.tick_counter]
        foreground_pointer = self.root.ids.foreground
        foreground_pointer.source = awim_img_filename

        moon_phase_str, moon_day_index, moon_qtr_day = clockmath.get_moon_nearest_and_quarter(moment_now, self.nearest_new_moon, self.nearest_full_moon)
        moon_phase_str += ', %.0f percent illuminated.' % (self.moon_illumination_percent)

        moon_img_filename = self.all_moons_list[moon_day_index]
        self.moon_pointer.source = moon_img_filename

        # needs to be a real loop to include indefinite number of stars
        for celestial_object in self.working_celestial_objs_dictionary:
            if celestial_object == 'moon':
                moon_KVpx = self.working_imgs_objs_dictionary[awim_img_filename]['moon'][self.tick_counter, [0,1]]
                moon_placer_dictionary = clockmath.img_placer(moon_KVpx, self.img_dims, self.moon_pointer.size)
                moon_brightsidedirection = round(self.working_moon_brightsidedirection[self.tick_counter])
                self.root.moon_angle = moon_brightsidedirection
            elif celestial_object == 'sun':
                sun_KVpx = self.working_imgs_objs_dictionary[awim_img_filename]['sun'][self.tick_counter, [0,1]]
                sun_placer_dictionary = clockmath.img_placer(sun_KVpx, self.img_dims, self.sun_pointer.size)
            elif celestial_object == 'mercury':
                mercury_KVpx = self.working_imgs_objs_dictionary[awim_img_filename]['mercury'][self.tick_counter, [0,1]]
                mercury_placer_dictionary = clockmath.img_placer(mercury_KVpx, self.img_dims, self.mercury_pointer.size)
            elif celestial_object == 'venus':
                venus_KVpx = self.working_imgs_objs_dictionary[awim_img_filename]['venus'][self.tick_counter, [0,1]]
                venus_placer_dictionary = clockmath.img_placer(venus_KVpx, self.img_dims, self.venus_pointer.size)
            elif celestial_object == 'mars':
                mars_KVpx = self.working_imgs_objs_dictionary[awim_img_filename]['mars'][self.tick_counter, [0,1]]
                mars_placer_dictionary = clockmath.img_placer(mars_KVpx, self.img_dims, self.mars_pointer.size)
            elif celestial_object == 'jupiter':
                jupiter_KVpx = self.working_imgs_objs_dictionary[awim_img_filename]['jupiter'][self.tick_counter, [0,1]]
                jupiter_placer_dictionary = clockmath.img_placer(jupiter_KVpx, self.img_dims, self.jupiter_pointer.size)
            elif celestial_object == 'saturn':
                saturn_KVpx = self.working_imgs_objs_dictionary[awim_img_filename]['saturn'][self.tick_counter, [0,1]]
                saturn_placer_dictionary = clockmath.img_placer(saturn_KVpx, self.img_dims, self.saturn_pointer.size)
            elif celestial_object == 'uranus':
                uranus_KVpx = self.working_imgs_objs_dictionary[awim_img_filename]['uranus'][self.tick_counter, [0,1]]
                uranus_placer_dictionary = clockmath.img_placer(uranus_KVpx, self.img_dims, self.uranus_pointer.size)
            elif celestial_object == 'neptune':
                neptune_KVpx = self.working_imgs_objs_dictionary[awim_img_filename]['neptune'][self.tick_counter, [0,1]]
                neptune_placer_dictionary = clockmath.img_placer(neptune_KVpx, self.img_dims, self.neptune_pointer.size)
            elif celestial_object == 'alnilam':
                alnilam_KVpx = self.working_imgs_objs_dictionary[awim_img_filename]['alnilam'][self.tick_counter, [0,1]]
                alnilam_placer_dictionary = clockmath.img_placer(alnilam_KVpx, self.img_dims, self.alnilam_pointer.size)

        self.sun_pointer.pos_hint = sun_placer_dictionary
        self.moon_pointer.pos_hint = moon_placer_dictionary
        self.mercury_pointer.pos_hint = mercury_placer_dictionary
        self.venus_pointer.pos_hint = venus_placer_dictionary
        self.mars_pointer.pos_hint = mars_placer_dictionary
        self.jupiter_pointer.pos_hint = jupiter_placer_dictionary
        self.saturn_pointer.pos_hint = saturn_placer_dictionary
        self.uranus_pointer.pos_hint = uranus_placer_dictionary
        self.neptune_pointer.pos_hint = neptune_placer_dictionary
        # self.alnilam_pointer.pos_hint = alnilam_placer_dictionary

        # info for info corner and testing. Calculate, make strings, display.
        sun_azalt = self.working_celestial_objs_dictionary['sun'][self.tick_counter, [1,2]]
        moon_azalt = self.working_celestial_objs_dictionary['moon'][self.tick_counter, [1,2]]
        local_industrial_time = tick_datetime_aware.astimezone(self.local_industrial_timezone_pytz)

        sun_daily_str, moon_daily_str = clockmath.get_nearest_dailyevents(moment_now, self.sun_daily, self.moon_daily)
        local_industrial_time_str = local_industrial_time.strftime('%H:%M %Z(%z) on %A %d %B %Y')
        sun_azalt_str = 'Sun az, alt: %.3i°, %.0f°' % (sun_azalt[0], sun_azalt[1])
        moon_azalt_str = 'Moon az, alt: %.3i°, %.0f°' % (moon_azalt[0], moon_azalt[1])

        # sun_opacity1 = self.working_imgs_objs_dictionary[awim_img_filename]['sun'][self.tick_counter, 4]
        # sun_opacity2 = self.working_imgs_objs_dictionary[awim_img_filename]['sun'][self.tick_counter, 5]
        # moon_opacity1 = self.working_imgs_objs_dictionary[awim_img_filename]['moon'][self.tick_counter, 4]
        # moon_opacity2 = self.working_imgs_objs_dictionary[awim_img_filename]['moon'][self.tick_counter, 5]
        # coding_info_str =  'sun KVx, KVy: %.1f, %.1f | SmallBlur, BigBlur: %.1f, %.1f; moon KVx, KVy: %.1f, %.1f | SmallBlur, BigBlur: %.1f, %.1f' % (sun_KVpx[0], sun_KVpx[1], sun_opacity1, sun_opacity2, moon_KVpx[0], moon_KVpx[1], moon_opacity1, moon_opacity2)
        # coding_info_pointer = self.root.ids.coding_info
        # coding_info_pointer.text = coding_info_str

        sun_daily_pointer = self.root.ids.sun_daily_events
        sun_daily_pointer.text = sun_daily_str
        sun_azalt_pointer = self.root.ids.sun_azalt
        sun_azalt_pointer.text = sun_azalt_str
        day_length_pointer = self.root.ids.day_length
        day_length_pointer.text = self.day_night_length_str
        moon_phase_pointer = self.root.ids.moon_phase
        moon_phase_pointer.text = moon_phase_str
        moon_daily_pointer = self.root.ids.moon_daily_events
        moon_daily_pointer.text = moon_daily_str
        moon_azalt_pointer = self.root.ids.moon_azalt
        moon_azalt_pointer.text = moon_azalt_str
        industrial_time_pointer = self.root.ids.industrial_time
        industrial_time_pointer.text = local_industrial_time_str

        self.tick_counter += 1
        mark_time_tick = time.perf_counter() - code_time1
        print('time to tick: %.6f' % (mark_time_tick))
        if self.tick_counter >= self.working_moments.size:
            self.tick_schedule.cancel()
            self.show_timev3_clock('now', self.now_resolution) # always return to the clock when finished

# try 7 seems to be the best solution
# Window.fullscreen = True
# Window.maximize()
# Window.size = (1920,1080)

# this works fine from Raspberry Pi to computer monitor but not to TV
# Window.fullscreen = 'auto'
# Window.fullscreen = False

if __name__ == '__main__':
    # Config.set('graphics', 'fullscreen', 0)
    # Config.set('graphics', 'width', '720')
    # Config.set('graphics', 'height', '480')
    # Config.set('graphics', 'window_state', 'visible')
    # Config.set('graphics', 'resizable', 1)
    # Config.write()

    Timev3AstroClockApp().run()