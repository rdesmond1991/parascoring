import configargparse
from scoring import scorer


def main():
    print("Scoring IGC file")
    parser = configargparse.ArgumentParser(description='Score the IGC file against a WPT file.')
    parser.add('-c', '--config', required=True, is_config_file=True, help='config file path')
    parser.add_argument('IGC File', type=str, nargs='+', dest='igc',
                        help='an integer for the accumulator')
    parser.add('vcf', nargs='+', help='variant file(s)')
    args = parser.parse_args()
    score_report = s.(args.igc)


if __name__ == "__main__":
    # execute only if run as a script
    main()


