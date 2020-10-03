import ConfigParser


class EvoProject(object):
    __slots__ = 'mpl_monitor', 'exp_title', 'exp_subtitle', 'pdf_filename', \
                'eval_scene', 'start_from_seed', 'seed_load_name', 'start_from_file', 'save_best_genome', 'seed_save_name', \
                'genomes_per_client', 'client_ip', 'client_count', 'path_to_gene_pool', 'nn_in', 'nn_hidden', 'nn_outs', 'nn_start_minimal'

    def __init__(self, project_name):
        folder = 'projects/' + project_name + "/"
        config_filename = folder + project_name + ".cfg"
        config = ConfigParser.ConfigParser()
        config.read(config_filename)

        self.mpl_monitor = config.getboolean('Visualization', 'mpl_monitor')
        self.exp_title = config.get('Visualization', 'exp_title')
        self.pdf_filename = folder + config.get('Visualization', 'pdf_filename')

        self.eval_scene = folder + config.get('Training', 'eval_scene')
        self.exp_subtitle = 'Scene : ' + config.get('Training', 'eval_scene')
        self.start_from_seed = config.getboolean('Training', 'start_from_seed')
        self.seed_load_name = folder + config.get('Training', 'seed_load_name')
        self.start_from_file = config.getboolean('Training', 'start_from_file')
        self.save_best_genome = config.getboolean('Training', 'save_best_genome')
        self.seed_save_name = folder + config.get('Training', 'seed_save_name')
        self.genomes_per_client = config.getint('Training', 'genomes_per_client')
        self.client_ip = config.get('Training', 'client_ip')
        self.client_count = config.getint('Training', 'client_count')
        self.path_to_gene_pool = folder + config.get('Training', 'gene_pool_folder_name') + "/"

        self.nn_in = config.getint('Network', 'nn_in')
        self.nn_hidden = config.getint('Network', 'nn_hidden')
        self.nn_outs = config.getint('Network', 'nn_outs')
        self.nn_start_minimal = config.getboolean('Network', 'start_minimal')
