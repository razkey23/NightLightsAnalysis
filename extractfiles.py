import os, sys, tarfile,argparse

def extract(tar_url, extract_path='.'):
    if not os.path.isdir(extract_path):
        os.mkdir(extract_path)
    print(tar_url)
    tar = tarfile.open(tar_url, 'r')
    for item in tar:
        tar.extract(item, extract_path)
        if item.name.find(".tgz") != -1 or item.name.find(".tar") != -1:
            extract(item.name, "./" + item.name[:item.name.rfind('/')])

def removecvg(extractdir):
    try:
        files = os.listdir(extractdir)
        for f in files:
            if "cvg" in f:
                print("Here",f)
                os.remove(os.path.join(extractdir,f)) 
    except:
        print("Error occured with reading the files")


if __name__ == '__main__':

    # Argument setup
    parser = argparse.ArgumentParser(description='Process some integers.')
    parser.add_argument('--zipdir', metavar='zipdir', type=str,
                        help='Directory where the stored zipped files are stored. Default: --zipdir storage')

    parser.add_argument('--extractdir', metavar='extractdir', type=str,
                        help='Directory where the extracted files are stored. Default: --zipdir storage')
    
    parser.add_argument('--avoidcvg',metavar='avoidcvg',choices=["False","True"],
                        help="set as True to avoid extracting cvg files (takes up less space)")
    # Get all files in zip directory
    args = parser.parse_args()

    # Get files to extract
    try:
        filesToExtract = os.listdir(args.zipdir)
    except:
        sys.exit("Error in the given path")
    
    # Check if we have extracted some files already
    try:
        alreadyExtracted = os.listdir(args.extractdir)
        extracted = []
        for f in alreadyExtracted:
            extracted.append(f.split(".")[0])
        extracted = set(extracted)
    except:
        print(" Extracting All Files")
    

    # Extract Files
    for file in filesToExtract:
        if file.split(".")[0] in extracted:
            continue
        extract(os.path.join(args.zipdir,file),args.extractdir)
        
        # Delete .cvg files if flag is set to True
        if args.avoidcvg == "True":
            removecvg(args.extractdir)
        