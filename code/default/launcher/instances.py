import os


current_path = os.path.dirname(os.path.abspath(__file__))
root_path = os.path.abspath( os.path.join(current_path, os.pardir))
data_path = os.path.abspath(os.path.join(root_path, os.pardir, os.pardir, 'data'))
data_launcher_path = os.path.join(data_path, 'launcher')


from xlog import Logger
log_file = os.path.join(data_launcher_path, "launcher.log")
xlog = Logger(file_name=log_file)
