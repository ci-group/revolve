from pyrevolve.revolve_bot.revolve_bot import RevolveBot
import sys

def main():
    yaml_file_num = sys.argv[1]
    path = f'/home/amir/projects/revolve/experiments/default_experiment/data_fullevolution/phenotypes/phenotype_{yaml_file_num}.yaml'
    bot = RevolveBot()
    bot.load_file(path)
    bot.render_body(f'/home/amir/projects/revolve/robotimage{yaml_file_num}.png')

if __name__ == '__main__':
    main()

