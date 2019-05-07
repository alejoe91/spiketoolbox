from spiketoolkit.sorters.basesorter import BaseSorter
import spikeextractors as se

try:
    import herdingspikes as hs
    HAVE_HS = True
except ImportError:
    HAVE_HS = False


class HerdingspikesSorter(BaseSorter):
    """
    HerdingSpikes is a sorter based on estimated spike location, developed by
    researchers at the University of Edinburgh. It's a fast and scalable choice.

    See: HILGEN, Gerrit, et al. Unsupervised spike sorting for large-scale,
    high-density multielectrode arrays. Cell reports, 2017, 18.10: 2521-2532.
    """

    sorter_name = 'herdingspikes'
    installed = HAVE_HS
    SortingExtractor_Class = se.HS2SortingExtractor

    _gui_params = [
        {'name': 'clustering_bandwidth', 'type': 'float', 'value':6.0, 'default':6.0,  'title': "Meanshift bandwidth"},
        {'name': 'clustering_alpha', 'type': 'float', 'value':6.0, 'default':6.0,  'title': "Scalar for the PC components when clustering"},
        {'name': 'clustering_n_jobs', 'type': 'int', 'value':-1, 'default':-1,  'title': "Number of cores. Default uses all cores."},
        {'name': 'clustering_bin_seeding', 'type': 'bool', 'value':False, 'default':False, 'title': "Clustering bin seeding"},
        {'name': 'clustering_subset', 'type': 'int', 'value':None, 'default':None, 'title': "Number of spikes used to build clusters. All by default."},
        {'name': 'left_cutout_time', 'type': 'float', 'value':1.0, 'default':1.0, 'title': "Cutout size before peak (ms)"},
        {'name': 'right_cutout_time', 'type': 'float', 'value':2.2, 'default':2.2, 'title': "Cutout size after peak (ms)"},
        {'name': 'detection_threshold', 'type': 'int', 'value':20, 'default':20, 'title': "Detection threshold"},
        {'name': 'probe_masked_channels', 'type': 'list', 'value':[], 'default':[], 'title': "Masked channels"},
    ]

    _default_params = None  # later

    installation_mesg = """
    More information on HerdingSpikes at:
      * https://github.com/mhhennig/hs2
    """

    def __init__(self, **kargs):
        BaseSorter.__init__(self, **kargs)

    def _setup_recording(self, recording, output_folder):
        # reset the output folder
        # if output_folder.is_dir():
        #     pass
            # shutil.rmtree(str(output_folder))

        # this should have its name changed
        self.Probe = hs.probe.RecordingExtractor(
            recording, masked_channels=self.params['probe_masked_channels'],
            **self.params['extra_probe_params'])

    def _run(self, recording, output_folder):

        H = hs.HSDetection(self.Probe, file_directory_name=str(output_folder),
                           left_cutout_time=self.params['left_cutout_time'],
                           right_cutout_time=self.params['right_cutout_time'],
                           threshold=self.params['detection_threshold'],
                           **self.params['extra_detection_params'])

        H.DetectFromRaw(load=True)

        C = hs.HSClustering(H)
        C.ShapePCA(**self.params['extra_pca_params'])
        C.CombinedClustering(bandwidth=self.params['clustering_bandwidth'],
                             alpha=self.params['clustering_alpha'],
                             n_jobs=self.params['clustering_n_jobs'],
                             bin_seeding=self.params['clustering_bin_seeding'])

        sorted_file = str(output_folder / 'HS2_sorted.hdf5')
        if(not H.spikes.empty):
            C = hs.HSClustering(H)
            C.ShapePCA(**self.params['extra_pca_params'])
            C.CombinedClustering(alpha=self.params['clustering_alpha'],
                                 cluster_subset=self.params['clustering_subset'],
                                 bandwidth=self.params['clustering_bandwidth'],
                                 bin_seeding=self.params['clustering_bin_seeding'],
                                 n_jobs=self.params['clustering_n_jobs']
                                 )
            C.SaveHDF5(sorted_file)
        else:
            C = hs.HSClustering(H)
            C.SaveHDF5(sorted_file)

    @staticmethod
    def get_result_from_folder(output_folder):
        return se.HS2SortingExtractor(output_folder / 'HS2_sorted.hdf5')

HerdingspikesSorter._default_params = {
    'clustering_bandwidth': 6.0,
    'clustering_alpha': 6.0,
    'clustering_n_jobs': -1,
    'clustering_bin_seeding': False,
    'clustering_subset': None,
    'left_cutout_time': 1.0,
    'right_cutout_time': 2.2,
    'detection_threshold': 20,
    'probe_masked_channels': [],

    'extra_probe_params': {
        'inner_radius': 50,
        'neighbor_radius': 50,
        'event_length': 0.5,
        'peak_jitter': 0.2
    },

    'extra_detection_params': {
        'to_localize': True,
        'num_com_centers': 1,
        'maa': 0,
        'ahpthr': 0,
        'out_file_name': "HS2_detected",
        'decay_filtering': False,
        'save_all': False,
        'amp_evaluation_time': 0.4,
        'spk_evaluation_time': 1.7
    },

    'extra_pca_params': {
        'pca_ncomponents': 2,
        'pca_whiten': True
    },
}
