import pandas as pd
import argparse

def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--data_path', type=str)
    parser.add_argument('--save_path', type=str)
    parser.add_argument('--year', type=int)
    args = parser.parse_args()
    return args

def main():
    # save reporting data for arg.year only
    args = get_args()
    df = pd.read_csv(args.data_path)
    df['Created Year'] = pd.DatetimeIndex(df['Created Date']).year
    year_df = df[df['Created Year'] == args.year]
    year_df.to_csv('{}/data_{}.csv'.format(args.save_path, args.year))
    
if __name__ == "__main__":
    main()         