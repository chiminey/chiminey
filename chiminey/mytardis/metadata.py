
class MetadataBuilder:
    def build_experiment_metadata(self, **kwargs):
        experiment_paramset = []
        return experiment_paramset

    def build_metadata_for_input(self, **kwargs):
        experiment_paramset = []
        dataset_paramset = []
        return (experiment_paramset, dataset_paramset)

    def build_metadata_for_intermediate_output(self, output_dir_path,
     outputs, **kwargs):
        dataset_paramset = []
        datafile_paramset = []
        dfile_extract_func = {}
        continue_loop = False
        return (continue_loop, dataset_paramset, datafile_paramset, dfile_extract_func)

    def build_metadata_for_final_output(self, m, output_dir_path, **kwargs):
        dataset_paramset = []
        datafile_paramset = []
        experiment_paramset = []
        dfile_extract_func = {}
        return (experiment_paramset, dataset_paramset, datafile_paramset, dfile_extract_func)
