import ConfigParser


class EvoProject(object):
    __slots__ = 'mpl_monitor', 'exp_title', 'pdf_filename', \
                'eval_scene', 'start_from_seed', 'seed_load_name', 'seed_save_name'

    def __init__(self, filename):
        config = ConfigParser.ConfigParser()
        config.read(filename)

        self.mpl_monitor = config.getboolean('Visualization', 'mpl_monitor', True)
        self.exp_title = config.get('Visualization', 'exp_title')
        self.pdf_filename = config.get('Visualization', 'pdf_filename')

        self.eval_scene = config.get('Training', 'eval_scene')
        self.start_from_seed = config.get('Training', 'start_from_seed', False)
        self.seed_load_name = config.get('Training', 'seed_load_name')
        self.seed_save_name = config.get('Training', 'seed_save_name')
